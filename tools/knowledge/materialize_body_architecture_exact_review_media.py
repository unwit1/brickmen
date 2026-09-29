#!/usr/bin/env python3
"""Materialize exact byte-pinned architecture media for ephemeral visual review.

This tool is deliberately review-only:
- selects explicitly requested source_record_id values from a benchmark manifest;
- requires an exact HTTPS image URL plus pinned SHA-256;
- enforces an explicit host allowlist, including redirects;
- sends the source-page URL as Referer when available;
- verifies SHA-256 and decoded dimensions before writing bytes;
- writes only to the requested local/CI output directory.

It never changes model-input approval state and should not write into the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from verify_body_architecture_reference_media import (
    AllowlistedRedirectHandler,
    image_dimensions,
    sniff_image_format,
    validate_https_url,
)

USER_AGENT = "BrickmenExactMediaReview/1.0"
VERSION = "body-architecture-exact-media-review-materializer/v1"


def load_selected(
    benchmark_path: Path,
    record_ids: set[str],
) -> list[dict[str, Any]]:
    doc = json.loads(benchmark_path.read_text(encoding="utf-8"))
    by_id = {
        row["source_record_id"]: row
        for row in doc.get("cases", [])
    }
    missing = sorted(record_ids - set(by_id))
    if missing:
        raise ValueError(f"unknown source_record_id values: {missing}")

    selected: list[dict[str, Any]] = []
    for record_id in sorted(record_ids):
        case = by_id[record_id]
        locators = [
            locator
            for locator in (case.get("input_asset") or {}).get(
                "reference_locators", []
            )
            if locator.get("exact_image_url")
            and locator.get("source_file_sha256")
        ]
        if len(locators) != 1:
            raise ValueError(
                f"{record_id} must have exactly one byte-pinned exact image locator"
            )
        selected.append(
            {
                "case_id": case.get("case_id"),
                "source_record_id": record_id,
                "source": locators[0],
            }
        )
    return selected


def fetch_bytes(
    url: str,
    *,
    referer: str | None,
    allowed_hosts: set[str],
    timeout_seconds: float,
    max_bytes: int,
) -> tuple[bytes, str, str | None]:
    validate_https_url(url, allowed_hosts)
    opener = urllib.request.build_opener(
        AllowlistedRedirectHandler(allowed_hosts)
    )
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "image/*",
    }
    if referer:
        parsed = urllib.parse.urlparse(referer)
        if parsed.scheme.lower() != "https" or not parsed.hostname:
            raise ValueError(f"invalid HTTPS referer: {referer}")
        headers["Referer"] = referer

    request = urllib.request.Request(url, headers=headers)
    with opener.open(request, timeout=timeout_seconds) as response:
        final_url = response.geturl()
        validate_https_url(final_url, allowed_hosts)
        content_type = (
            response.headers.get("Content-Type", "")
            .split(";", 1)[0]
            .strip()
            .lower()
            or None
        )
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError(f"asset exceeds max_bytes={max_bytes}")
    return data, final_url, content_type


def materialize(
    benchmark_path: Path,
    *,
    record_ids: set[str],
    output_dir: Path,
    allowed_hosts: set[str],
    timeout_seconds: float,
    max_bytes: int,
) -> dict[str, Any]:
    selected = load_selected(benchmark_path, record_ids)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []

    for item in selected:
        locator = item["source"]
        data, final_url, content_type = fetch_bytes(
            str(locator["exact_image_url"]),
            referer=(
                str(locator.get("url"))
                if locator.get("url")
                else None
            ),
            allowed_hosts=allowed_hosts,
            timeout_seconds=timeout_seconds,
            max_bytes=max_bytes,
        )
        observed_sha = hashlib.sha256(data).hexdigest()
        expected_sha = str(locator["source_file_sha256"])
        if observed_sha != expected_sha:
            raise ValueError(
                f"SHA-256 mismatch for {item['source_record_id']}: "
                f"{observed_sha} != {expected_sha}"
            )

        image_format = sniff_image_format(data)
        if not image_format:
            raise ValueError(
                f"unsupported image bytes for {item['source_record_id']}"
            )
        width, height = image_dimensions(data, image_format)
        expected_dimensions = (
            locator.get("source_width"),
            locator.get("source_height"),
        )
        if all(value is not None for value in expected_dimensions):
            if (width, height) != expected_dimensions:
                raise ValueError(
                    f"dimension mismatch for {item['source_record_id']}: "
                    f"{width}x{height} != "
                    f"{expected_dimensions[0]}x{expected_dimensions[1]}"
                )

        extension = {
            "jpeg": ".jpg",
            "png": ".png",
            "gif": ".gif",
            "webp": ".webp",
            "bmp": ".bmp",
            "tiff": ".tiff",
        }[image_format]
        path = output_dir / (
            f"{item['source_record_id']}--{observed_sha[:16]}{extension}"
        )
        path.write_bytes(data)
        rows.append(
            {
                "case_id": item["case_id"],
                "source_record_id": item["source_record_id"],
                "source_id": locator.get("source_id"),
                "source_page_url": locator.get("url"),
                "exact_image_url": locator.get("exact_image_url"),
                "final_url": final_url,
                "sha256": observed_sha,
                "width": width,
                "height": height,
                "image_format": image_format,
                "content_type": content_type,
                "file_name": path.name,
                "size_bytes": len(data),
            }
        )

    return {
        "schema": "body-architecture-exact-media-review-materialization/v1",
        "processor_version": VERSION,
        "benchmark": str(benchmark_path),
        "record_count": len(rows),
        "records": rows,
        "policy": (
            "Ephemeral exact-media review bundle. Bytes are written only to the "
            "requested output directory and do not alter approval state."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--source-record-id", action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--allow-host", action="append", default=[])
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--max-bytes", type=int, default=25 * 1024 * 1024)
    args = parser.parse_args()

    allowed_hosts = {
        str(host).strip().lower()
        for host in args.allow_host
        if str(host).strip()
    }
    if not allowed_hosts:
        raise SystemExit("At least one --allow-host is required.")

    result = materialize(
        args.benchmark,
        record_ids={
            str(value).strip()
            for value in args.source_record_id
            if str(value).strip()
        },
        output_dir=args.output_dir,
        allowed_hosts=allowed_hosts,
        timeout_seconds=args.timeout_seconds,
        max_bytes=args.max_bytes,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(
        {
            "record_count": result["record_count"],
            "records": [
                {
                    "source_record_id": row["source_record_id"],
                    "sha256": row["sha256"],
                    "width": row["width"],
                    "height": row["height"],
                    "file_name": row["file_name"],
                }
                for row in result["records"]
            ],
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
