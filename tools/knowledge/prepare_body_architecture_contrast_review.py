#!/usr/bin/env python3
"""Prepare transient, hash-verified source images for same-character contrast review.

The output directory is intentionally local/artifact-only. Raw image bytes are never
written into the repository by this tool. Every downloaded image must match the
SHA-256 and dimensions already pinned in the contrast corpus.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

VERSION = "body-architecture-contrast-review-bundle/v1"
USER_AGENT = "BrickmenContrastReview/1.0"
DEFAULT_ALLOWED_HOSTS = {"img.bricklink.com"}


def validate_url(url: str, allowed_hosts: set[str]) -> None:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https":
        raise ValueError("source URL must use https")
    if host not in allowed_hosts:
        raise ValueError(f"source host not allowlisted: {host}")


def unique_assets(corpus: dict[str, Any]) -> list[dict[str, Any]]:
    by_hash: dict[str, dict[str, Any]] = {}
    for pair in corpus.get("pairs", []):
        for side_name in ("left", "right"):
            side = pair[side_name]
            sha = side.get("source_file_sha256")
            if not isinstance(sha, str) or len(sha) != 64:
                raise ValueError(f"unpinned asset in {pair['pair_id']}:{side_name}")
            row = {
                "pair_id": pair["pair_id"],
                "side": side_name,
                "character_id": pair["character_id"],
                "source_record_id": side["source_record_id"],
                "architecture_id": side["architecture_id"],
                "exact_image_url": side["exact_image_url"],
                "source_file_sha256": sha,
                "dimensions": side["dimensions"],
                "model_input_state": side["model_input_state"],
            }
            prior = by_hash.get(sha)
            if prior and prior["source_record_id"] != row["source_record_id"]:
                raise ValueError("same source hash assigned to multiple record IDs")
            by_hash[sha] = row
    return sorted(by_hash.values(), key=lambda row: row["source_record_id"])


def fetch_asset(
    asset: dict[str, Any],
    *,
    output_dir: Path,
    allowed_hosts: set[str],
    timeout_seconds: float,
    max_bytes: int,
) -> dict[str, Any]:
    url = str(asset["exact_image_url"])
    validate_url(url, allowed_hosts)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "image/*"},
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        final_url = response.geturl()
        validate_url(final_url, allowed_hosts)
        data = response.read(max_bytes + 1)
        content_type = (
            response.headers.get("Content-Type", "")
            .split(";", 1)[0]
            .strip()
            .lower()
        )
    if len(data) > max_bytes:
        raise ValueError(f"asset exceeds max_bytes={max_bytes}")
    observed = hashlib.sha256(data).hexdigest()
    if observed != asset["source_file_sha256"]:
        raise ValueError(
            f"SHA-256 mismatch for {asset['source_record_id']}: "
            f"{observed} != {asset['source_file_sha256']}"
        )

    from PIL import Image
    import io

    with Image.open(io.BytesIO(data)) as image:
        image.load()
        dimensions = list(image.size)
        image_format = str(image.format or "").lower()
    if dimensions != list(asset["dimensions"]):
        raise ValueError(
            f"dimension mismatch for {asset['source_record_id']}: "
            f"{dimensions} != {asset['dimensions']}"
        )

    suffix = ".png" if image_format == "png" else ".jpg"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{asset['source_record_id']}--{observed[:16]}{suffix}"
    path.write_bytes(data)
    return {
        **asset,
        "final_url": final_url,
        "observed_sha256": observed,
        "observed_dimensions": dimensions,
        "content_type": content_type,
        "image_format": image_format,
        "local_review_filename": path.name,
        "status": "verified_written_for_transient_review",
    }


def build(
    corpus_path: Path,
    *,
    output_dir: Path,
    allowed_hosts: set[str],
    timeout_seconds: float = 30.0,
    max_bytes: int = 25 * 1024 * 1024,
) -> dict[str, Any]:
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    records = [
        fetch_asset(
            asset,
            output_dir=output_dir / "sources",
            allowed_hosts=allowed_hosts,
            timeout_seconds=timeout_seconds,
            max_bytes=max_bytes,
        )
        for asset in unique_assets(corpus)
    ]
    return {
        "schema": "body-architecture-contrast-review-bundle/v1",
        "processor_version": VERSION,
        "source_corpus": str(corpus_path),
        "asset_count": len(records),
        "records": records,
        "policy": (
            "Exact source bytes are written only to the requested local/artifact "
            "directory after SHA-256 and dimension verification. Do not commit them."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--allow-host", action="append", default=[])
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args()
    allowed = set(args.allow_host) or set(DEFAULT_ALLOWED_HOSTS)
    result = build(
        args.corpus,
        output_dir=args.output_dir,
        allowed_hosts=allowed,
        timeout_seconds=args.timeout_seconds,
    )
    report = args.output_dir / "contrast-review-report.json"
    report.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"asset_count": result["asset_count"], "report": str(report)}, indent=2))


if __name__ == "__main__":
    main()
