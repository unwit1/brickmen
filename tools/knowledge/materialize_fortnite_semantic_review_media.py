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

VERSION = "fortnite-semantic-review-media-materializer/v3"
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
    archive_manifest: dict[str, Any] | None = None,
    archive_root: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    items = batch.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("batch requires at least one review item")

    archived = {}
    if (archive_manifest is None) != (archive_root is None):
        raise ValueError("Archive manifest and archive root must be supplied together")
    if archive_manifest is not None:
        if not isinstance(archive_manifest, dict) or archive_manifest.get("schema") != "fortnite-semantic-review-media-manifest/v1" or not isinstance(archive_manifest.get("records"), list):
            raise ValueError("Archive requires an existing exact-media manifest")
        archive_root = archive_root.resolve()
        for row in archive_manifest["records"]:
            if not isinstance(row, dict) or not isinstance(row.get("translation_pair_id"), str) or not row["translation_pair_id"]:
                raise ValueError("Archive record requires translation_pair_id")
            pair_id = row["translation_pair_id"]
            if pair_id in archived:
                raise ValueError(f"Duplicate archive pair: {pair_id}")
            archived[pair_id] = row

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
            if evidence.get(evidence_url_key) not in (None, url):
                raise ValueError(f"{pair_id}: conflicting item/template {role} URLs")

            pins = [pin for pin in (item.get(evidence_hash_key), evidence.get(evidence_hash_key)) if pin is not None]
            if any(not isinstance(pin, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", pin) for pin in pins):
                raise ValueError(f"{pair_id}: invalid expected {role} hash")
            pins = {pin.lower() for pin in pins}
            if len(pins) > 1:
                raise ValueError(f"{pair_id}: conflicting item/template {role} hashes")
            expected_hash = next(iter(pins), None)
            archived_entry = None
            if archive_manifest is not None:
                archived_entry = archived.get(pair_id, {}).get(role)
                if not isinstance(archived_entry, dict) or archived_entry.get("url") != url:
                    raise ValueError(f"{pair_id}: missing or mismatched archived {role} URL")
                archive_hash = archived_entry.get("sha256")
                if not isinstance(archive_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", archive_hash):
                    raise ValueError(f"{pair_id}: invalid archived {role} hash")
                if expected_hash and expected_hash != archive_hash.lower():
                    raise ValueError(f"{pair_id}: exact evidence hash mismatch for archived {role}")
                expected_hash = archive_hash.lower()
            cached = cache.get(url)
            if cached is None:
                if archived_entry is None:
                    data, content_type, final_url = fetcher(url)
                    acquisition = "download"
                else:
                    local = archived_entry.get("local_asset")
                    if not isinstance(local, str) or not local:
                        raise ValueError(f"{pair_id}: archived {role} requires local_asset")
                    path = (archive_root / local).resolve()
                    if not path.is_relative_to(archive_root):
                        raise ValueError(f"{pair_id}: archived path escapes archive root")
                    with path.open("rb") as source:
                        data = source.read(MAX_IMAGE_BYTES + 1)
                    if not data or len(data) > MAX_IMAGE_BYTES:
                        raise ValueError(f"{pair_id}: archived media empty or exceeds size limit")
                    content_type = archived_entry.get("content_type")
                    final_url = archived_entry.get("final_url") or url
                    acquisition = "verified_archive"
                digest = hashlib.sha256(data).hexdigest()
                if expected_hash and expected_hash.lower() != digest:
                    raise ValueError(f"{pair_id}: exact evidence hash mismatch for {role}")
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
                    "acquisition": acquisition,
                }
                cache[url] = cached

            if expected_hash and expected_hash.lower() != cached["sha256"]:
                raise ValueError(f"{pair_id}: exact evidence hash mismatch for {role}")
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
                "acquisition": cached["acquisition"],
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
            "Hashes bind semantic review evidence to exact downloaded or verified archived bytes. "
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
    parser.add_argument("--archive-manifest", type=Path, help="Existing exact-media manifest; requires --archive-root")
    parser.add_argument("--archive-root", type=Path, help="Root containing archived local_asset paths; no network fallback")
    args = parser.parse_args()

    if bool(args.archive_manifest) != bool(args.archive_root):
        parser.error("--archive-manifest and --archive-root must be supplied together")
    inputs = {args.batch.resolve()}
    if args.archive_manifest:
        inputs.add(args.archive_manifest.resolve())
    outputs = {args.output_batch.resolve(), args.manifest.resolve()}
    if len(outputs) != 2 or inputs & outputs:
        parser.error("Output batch/manifest must be distinct and must not overwrite input evidence")
    try:
        batch = json.loads(args.batch.read_text(encoding="utf-8"))
        archive = json.loads(args.archive_manifest.read_text(encoding="utf-8")) if args.archive_manifest else None
        output, manifest = materialize_batch(batch, args.output_dir, archive_manifest=archive, archive_root=args.archive_root)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        for path in (args.output_batch, args.manifest):
            if path.is_file():
                path.unlink()  # A failed rerun must not retain a stale successful materialization.
        parser.exit(2, f"Exact review media materialization failed: {exc}\n")
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
