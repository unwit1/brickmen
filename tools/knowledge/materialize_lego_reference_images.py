#!/usr/bin/env python3
"""Materialize image URLs from a LEGO reference manifest into a local content-addressed store.

This tool intentionally requires explicit host allowlisting. It is meant for sources whose
terms/permissions the user has reviewed. It does not crawl pages; it only fetches exact image
URLs already present in a manifest.

Input JSONL records should contain:
  reference_asset_id
  source_url

Output:
  materialized_reference_manifest.jsonl
  blobs/sha256/<first2>/<sha256>.<ext>
  import_report.json

The store deduplicates exact byte-identical images across different source URLs while
preserving each source occurrence as a separate manifest record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROCESSOR_VERSION = "reference-image-materializer/v1"
USER_AGENT = "PersonalAgentOS-LEGOReferenceResearch/1.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ext_for(content_type: str, url: str) -> str:
    content_type = (content_type or "").split(";", 1)[0].strip().lower()
    known = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/bmp": ".bmp",
        "image/tiff": ".tif",
    }
    if content_type in known:
        return known[content_type]
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}:
        return ".jpg" if suffix == ".jpeg" else ".tif" if suffix == ".tiff" else suffix
    guessed = mimetypes.guess_extension(content_type) if content_type else None
    return guessed or ".bin"


def fetch(url: str, timeout: float, max_bytes: int) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "image/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content_type = resp.headers.get("Content-Type", "")
        if content_type and not content_type.lower().startswith("image/"):
            raise ValueError(f"non-image content type: {content_type}")
        content_length = resp.headers.get("Content-Length")
        if content_length and int(content_length) > max_bytes:
            raise ValueError(f"content length exceeds max_bytes: {content_length}")
        data = resp.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError(f"download exceeds max_bytes={max_bytes}")
        return data, content_type


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--allow-host", action="append", default=[], help="Repeat for each reviewed/allowed hostname")
    ap.add_argument("--delay-seconds", type=float, default=0.35)
    ap.add_argument("--timeout-seconds", type=float, default=30.0)
    ap.add_argument("--max-bytes", type=int, default=25 * 1024 * 1024)
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    allowed = {host.lower() for host in args.allow_host}
    if not allowed:
        raise SystemExit("At least one --allow-host is required; review each source's terms before bulk materialization.")

    manifest = args.manifest.resolve()
    out = args.output_dir.resolve()
    blobs = out / "blobs" / "sha256"
    out.mkdir(parents=True, exist_ok=True)

    result_manifest = out / "materialized_reference_manifest.jsonl"
    counts = Counter()
    unique_hashes: set[str] = set()
    processed = 0
    created_at = now_iso()

    with manifest.open("r", encoding="utf-8") as src, result_manifest.open("w", encoding="utf-8") as dst:
        for line_no, line in enumerate(src, 1):
            if args.limit is not None and processed >= args.limit:
                break
            if not line.strip():
                continue
            record = json.loads(line)
            url = str(record.get("source_url") or "").strip()
            if not url:
                counts["missing_url"] += 1
                continue
            parsed = urllib.parse.urlparse(url)
            host = (parsed.hostname or "").lower()
            if parsed.scheme != "https":
                counts["non_https"] += 1
                continue
            if host not in allowed:
                counts["host_not_allowed"] += 1
                continue

            occurrence = dict(record)
            occurrence["materialization"] = {
                "attempted_at": now_iso(),
                "host": host,
                "status": "pending",
                "processor_version": PROCESSOR_VERSION,
            }

            try:
                data, content_type = fetch(url, args.timeout_seconds, args.max_bytes)
                digest = hashlib.sha256(data).hexdigest()
                ext = ext_for(content_type, url)
                blob = blobs / digest[:2] / f"{digest}{ext}"
                blob.parent.mkdir(parents=True, exist_ok=True)
                already = blob.exists()
                if not already:
                    blob.write_bytes(data)
                unique_hashes.add(digest)
                occurrence["materialized_locally"] = True
                occurrence["sha256"] = digest
                occurrence["local_path"] = str(blob)
                occurrence["content_type"] = content_type
                occurrence["size_bytes"] = len(data)
                occurrence["materialization"]["status"] = "duplicate_blob" if already else "downloaded"
                counts["duplicate_blob" if already else "downloaded"] += 1
            except Exception as exc:
                occurrence["materialized_locally"] = False
                occurrence["materialization"]["status"] = "error"
                occurrence["materialization"]["error"] = str(exc)[:1000]
                counts["error"] += 1

            dst.write(json.dumps(occurrence, ensure_ascii=False) + "\n")
            processed += 1
            if args.delay_seconds > 0:
                time.sleep(args.delay_seconds)

    report = {
        "schema": "reference-image-materializer-report/v1",
        "created_at": created_at,
        "processor_version": PROCESSOR_VERSION,
        "input_manifest": str(manifest),
        "allowed_hosts": sorted(allowed),
        "processed_records": processed,
        "unique_blobs": len(unique_hashes),
        "counts": dict(counts),
        "output_manifest": str(result_manifest),
        "blob_root": str(blobs),
        "policy": "exact URLs only; no crawling; explicit source-host allowlist required",
    }
    (out / "import_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
