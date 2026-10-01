#!/usr/bin/env python3
"""Materialize exact Fortnite source/LEGO review media for semantic-review batches.

Remote review URLs are convenient but mutable. This tool downloads the exact bytes that
will be reviewed, computes SHA-256 digests, stores local artifact paths, and writes those
hashes into each review template. Materialization creates evidence only; it never creates
semantic labels or training eligibility.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

VERSION = "fortnite-semantic-review-media-materializer/v1"
ALLOWED_HOSTS = {"fortnite-api.com"}
MAX_IMAGE_BYTES = 25 * 1024 * 1024
SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")


def _validate_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"review media URL must use https: {url}")
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"review media host is not allowed: {host!r}")


def _suffix(url: str, content_type: str | None) -> str:
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return suffix
    by_type = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    return by_type.get((content_type or "").split(";", 1)[0].lower(), ".img")


def fetch_url(url: str) -> tuple[bytes, str | None, str]:
    _validate_url(url)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "BrickmenReviewMedia/1.0"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        final_url = response.geturl()
        content_type = response.headers.get("Content-Type")
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_IMAGE_BYTES:
            raise ValueError(f"review image exceeds {MAX_IMAGE_BYTES} bytes: {url}")
        data = response.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"review image exceeds {MAX_IMAGE_BYTES} bytes: {url}")
    if not data:
        raise ValueError(f"empty review image: {url}")
    if content_type and not content_type.lower().startswith("image/"):
        raise ValueError(f"review URL did not return image content: {content_type!r}")
    return data, content_type, final_url


def materialize_batch(
    batch: dict[str, Any],
    output_dir: Path,
    *,
    fetcher: Callable[[str], tuple[bytes, str | None, str]] = fetch_url,
) -> tuple[dict[str, Any], dict[str, Any]]:
    items = batch.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("batch requires at least one review item")

    output_dir.mkdir(parents=True, exist_ok=True)
    result = copy.deepcopy(batch)
    result["media_materializer_version"] = VERSION
    manifest_records: list[dict[str, Any]] = []
    cache: dict[str, dict[str, Any]] = {}

    for item in result["items"]:
        pair_id = item.get("translation_pair_id")
        if not isinstance(pair_id, str) or not pair_id:
            raise ValueError("every review item requires translation_pair_id")
        safe_pair = SAFE_ID.sub("_", pair_id)

        template = item.get("review_template")
        if not isinstance(template, dict):
            raise ValueError(f"{pair_id}: review_template must be an object")
        evidence = template.get("evidence")
        if not isinstance(evidence, dict):
            raise ValueError(f"{pair_id}: review_template.evidence must be an object")

        pair_manifest: dict[str, Any] = {"translation_pair_id": pair_id}
        for role, item_key, evidence_url_key, evidence_hash_key in (
            ("source", "source_image_url", "source_image_url", "source_image_sha256"),
            ("lego", "lego_image_url", "lego_image_url", "lego_image_sha256"),
        ):
            url = item.get(item_key)
            if not isinstance(url, str) or not url:
                raise ValueError(f"{pair_id}: missing {item_key}")
            _validate_url(url)

            cached = cache.get(url)
            if cached is None:
                data, content_type, final_url = fetcher(url)
                digest = hashlib.sha256(data).hexdigest()
                suffix = _suffix(url, content_type)
                filename = f"{safe_pair}--{role}--{digest[:16]}{suffix}"
                path = output_dir / filename
                path.write_bytes(data)
                cached = {
                    "url": url,
                    "final_url": final_url,
                    "sha256": digest,
                    "size_bytes": len(data),
                    "content_type": content_type,
                    "filename": filename,
                }
                cache[url] = cached

            local_asset = f"media/{cached['filename']}"
            item[f"{role}_image_local_asset"] = local_asset
            item[f"{role}_image_sha256"] = cached["sha256"]
            evidence[evidence_url_key] = url
            evidence[evidence_hash_key] = cached["sha256"]
            evidence[f"{role}_image_local_asset"] = local_asset
            pair_manifest[role] = {
                "url": url,
                "final_url": cached["final_url"],
                "sha256": cached["sha256"],
                "size_bytes": cached["size_bytes"],
                "content_type": cached["content_type"],
                "local_asset": local_asset,
            }

        provenance = template.setdefault("provenance", [])
        provenance.append(
            {
                "source": "fortnite_semantic_review_media_materialization",
                "processor_version": VERSION,
                "source_image_sha256": evidence["source_image_sha256"],
                "lego_image_sha256": evidence["lego_image_sha256"],
            }
        )
        manifest_records.append(pair_manifest)

    result["media_materialization"] = {
        "status": "complete",
        "records": len(manifest_records),
        "unique_urls": len(cache),
        "policy": (
            "Hashes bind semantic review evidence to exact downloaded bytes. "
            "Materialization does not create semantic annotations or training eligibility."
        ),
    }
    manifest = {
        "schema": "fortnite-semantic-review-media-manifest/v1",
        "processor_version": VERSION,
        "batch_id": result.get("batch_id"),
        "records": manifest_records,
        "unique_urls": len(cache),
        "policy": result["media_materialization"]["policy"],
    }
    return result, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-batch", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    batch = json.loads(args.batch.read_text(encoding="utf-8"))
    output, manifest = materialize_batch(batch, args.output_dir)
    args.output_batch.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output_batch.write_text(
        json.dumps(output, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "processor_version": VERSION,
                "batch_id": output.get("batch_id"),
                "records": len(manifest["records"]),
                "unique_urls": manifest["unique_urls"],
                "output_batch": str(args.output_batch),
                "manifest": str(args.manifest),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
