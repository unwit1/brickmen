#!/usr/bin/env python3
"""Verify exact architecture-benchmark image URLs without persisting raw media.

The verifier downloads each selected image only into memory, enforces an explicit
HTTPS host allowlist (including redirects), validates basic image magic, computes
SHA-256/size/content type, and writes metadata-only JSON reports.

Raw image bytes are never written to disk by this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "body-architecture-reference-media-verifier/v1"
USER_AGENT = "BrickmenReferenceVerifier/1.0"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BENCHMARK = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "body-architecture-recognition-benchmark-cases.json"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def url_host(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return (parsed.hostname or "").lower()


def validate_https_url(url: str, allowed_hosts: set[str]) -> str:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme.lower() != "https":
        raise ValueError(f"non-HTTPS URL: {url}")
    if not host:
        raise ValueError(f"URL has no hostname: {url}")
    if host not in allowed_hosts:
        raise ValueError(f"host not allowed: {host}")
    return host


class AllowlistedRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects outside the reviewed HTTPS host allowlist."""

    def __init__(self, allowed_hosts: set[str]):
        super().__init__()
        self.allowed_hosts = allowed_hosts

    def redirect_request(
        self,
        req,
        fp,
        code,
        msg,
        headers,
        newurl,
    ):
        validate_https_url(newurl, self.allowed_hosts)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def sniff_image_format(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data.startswith(b"BM"):
        return "bmp"
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return "tiff"
    return None


def image_dimensions(data: bytes, image_format: str) -> tuple[int, int]:
    """Extract image dimensions from supported formats without decoding pixels."""
    if image_format == "png":
        if len(data) < 24 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("invalid PNG header")
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
    elif image_format == "gif":
        if len(data) < 10:
            raise ValueError("invalid GIF header")
        width = int.from_bytes(data[6:8], "little")
        height = int.from_bytes(data[8:10], "little")
    elif image_format == "bmp":
        if len(data) < 26:
            raise ValueError("invalid BMP header")
        width = int.from_bytes(data[18:22], "little", signed=True)
        height = abs(int.from_bytes(data[22:26], "little", signed=True))
    elif image_format == "jpeg":
        if len(data) < 4 or not data.startswith(b"\xff\xd8"):
            raise ValueError("invalid JPEG header")
        i = 2
        sof_markers = {
            0xC0, 0xC1, 0xC2, 0xC3,
            0xC5, 0xC6, 0xC7,
            0xC9, 0xCA, 0xCB,
            0xCD, 0xCE, 0xCF,
        }
        width = height = 0
        while i < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            while i < len(data) and data[i] == 0xFF:
                i += 1
            if i >= len(data):
                break
            marker = data[i]
            i += 1
            if marker in {0xD8, 0xD9}:
                continue
            if marker == 0xDA:
                break
            if i + 2 > len(data):
                break
            segment_length = int.from_bytes(data[i:i + 2], "big")
            if segment_length < 2 or i + segment_length > len(data):
                raise ValueError("invalid JPEG segment length")
            if marker in sof_markers:
                if segment_length < 7:
                    raise ValueError("invalid JPEG SOF segment")
                height = int.from_bytes(data[i + 3:i + 5], "big")
                width = int.from_bytes(data[i + 5:i + 7], "big")
                break
            i += segment_length
        if not width or not height:
            raise ValueError("JPEG dimensions not found")
    elif image_format == "webp":
        if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
            raise ValueError("invalid WebP header")
        chunk = data[12:16]
        if chunk == b"VP8X":
            width = 1 + int.from_bytes(data[24:27], "little")
            height = 1 + int.from_bytes(data[27:30], "little")
        elif chunk == b"VP8L":
            if len(data) < 25 or data[20] != 0x2F:
                raise ValueError("invalid WebP VP8L header")
            bits = int.from_bytes(data[21:25], "little")
            width = (bits & 0x3FFF) + 1
            height = ((bits >> 14) & 0x3FFF) + 1
        elif chunk == b"VP8 ":
            if len(data) < 30 or data[23:26] != b"\x9d\x01\x2a":
                raise ValueError("invalid WebP VP8 frame header")
            width = int.from_bytes(data[26:28], "little") & 0x3FFF
            height = int.from_bytes(data[28:30], "little") & 0x3FFF
        else:
            raise ValueError(f"unsupported WebP chunk: {chunk!r}")
    elif image_format == "tiff":
        raise ValueError("TIFF dimensions require full IFD parsing and are not supported")
    else:
        raise ValueError(f"unsupported image format: {image_format}")

    if width <= 0 or height <= 0:
        raise ValueError(f"invalid image dimensions: {width}x{height}")
    return width, height


def select_exact_images(benchmark: dict[str, Any]) -> list[dict[str, Any]]:
    """Select one deterministic exact-image locator per benchmark case."""
    rows: list[dict[str, Any]] = []
    for case in benchmark.get("cases", []):
        exact = [
            locator
            for locator in (case.get("input_asset") or {}).get(
                "reference_locators", []
            )
            if locator.get("exact_image_url")
        ]
        if not exact:
            raise ValueError(
                f"benchmark case lacks exact image URL: {case.get('source_record_id')}"
            )
        exact.sort(
            key=lambda locator: (
                str(locator.get("source_id") or ""),
                str(locator.get("exact_image_url") or ""),
            )
        )
        locator = exact[0]
        rows.append(
            {
                "case_id": case.get("case_id"),
                "source_record_id": case.get("source_record_id"),
                "split": case.get("split"),
                "scoring_track": case.get("scoring_track"),
                "source_id": locator.get("source_id"),
                "source_page_url": locator.get("url"),
                "exact_image_url": locator.get("exact_image_url"),
                "image_resolution_status": locator.get(
                    "image_resolution_status"
                ),
            }
        )
    return rows


def fetch_image_metadata(
    url: str,
    *,
    allowed_hosts: set[str],
    timeout_seconds: float,
    max_bytes: int,
) -> dict[str, Any]:
    initial_host = validate_https_url(url, allowed_hosts)
    opener = urllib.request.build_opener(
        AllowlistedRedirectHandler(allowed_hosts)
    )
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "image/*",
        },
    )

    with opener.open(request, timeout=timeout_seconds) as response:
        final_url = response.geturl()
        final_host = validate_https_url(final_url, allowed_hosts)
        content_type = (
            response.headers.get("Content-Type", "")
            .split(";", 1)[0]
            .strip()
            .lower()
        )
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                advertised = int(content_length)
            except ValueError:
                advertised = None
            if advertised is not None and advertised > max_bytes:
                raise ValueError(
                    f"advertised content length {advertised} exceeds max_bytes={max_bytes}"
                )

        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError(
                f"downloaded image exceeds max_bytes={max_bytes}"
            )

    image_format = sniff_image_format(data)
    if not image_format:
        raise ValueError("downloaded bytes do not match a supported image signature")
    if content_type and not content_type.startswith("image/"):
        raise ValueError(f"non-image content type: {content_type}")
    width, height = image_dimensions(data, image_format)

    return {
        "initial_host": initial_host,
        "final_url": final_url,
        "final_host": final_host,
        "content_type": content_type or None,
        "image_format": image_format,
        "width": width,
        "height": height,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def verify(
    benchmark: dict[str, Any],
    *,
    allowed_hosts: set[str],
    timeout_seconds: float = 30.0,
    max_bytes: int = 25 * 1024 * 1024,
    retries: int = 2,
    delay_seconds: float = 0.25,
) -> dict[str, Any]:
    selected = select_exact_images(benchmark)
    records: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    hashes: Counter[str] = Counter()

    for item in selected:
        occurrence = dict(item)
        occurrence["verified_at"] = now_iso()
        occurrence["verifier_version"] = VERSION
        last_error: str | None = None

        for attempt in range(retries + 1):
            try:
                metadata = fetch_image_metadata(
                    str(item["exact_image_url"]),
                    allowed_hosts=allowed_hosts,
                    timeout_seconds=timeout_seconds,
                    max_bytes=max_bytes,
                )
                occurrence.update(metadata)
                occurrence["status"] = "verified"
                occurrence["attempts"] = attempt + 1
                counts["verified"] += 1
                hashes[metadata["sha256"]] += 1
                last_error = None
                break
            except (
                OSError,
                ValueError,
                urllib.error.URLError,
                urllib.error.HTTPError,
            ) as exc:
                last_error = str(exc)[:1000]
                if attempt < retries:
                    time.sleep(delay_seconds * (attempt + 1))

        if last_error is not None:
            occurrence["status"] = "error"
            occurrence["attempts"] = retries + 1
            occurrence["error"] = last_error
            counts["error"] += 1

        records.append(occurrence)
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    duplicate_hashes = sorted(
        digest for digest, count in hashes.items() if count > 1
    )
    return {
        "schema": "body-architecture-reference-media-verification/v1",
        "created_at": now_iso(),
        "verifier_version": VERSION,
        "policy": (
            "Metadata-only verification. Raw image bytes are fetched transiently "
            "into memory and are never written by this tool."
        ),
        "allowed_hosts": sorted(allowed_hosts),
        "total_cases": len(selected),
        "verified_cases": counts["verified"],
        "error_cases": counts["error"],
        "unique_verified_hashes": len(hashes),
        "duplicate_hashes": duplicate_hashes,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--allow-host", action="append", default=[])
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--max-bytes", type=int, default=25 * 1024 * 1024)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--delay-seconds", type=float, default=0.25)
    parser.add_argument(
        "--allow-errors",
        action="store_true",
        help="Return success even if one or more images cannot be verified.",
    )
    args = parser.parse_args()

    allowed_hosts = {
        str(host).strip().lower()
        for host in args.allow_host
        if str(host).strip()
    }
    if not allowed_hosts:
        raise SystemExit(
            "At least one --allow-host is required; reviewed source hosts must be explicit."
        )

    benchmark = json.loads(args.benchmark.read_text(encoding="utf-8"))
    result = verify(
        benchmark,
        allowed_hosts=allowed_hosts,
        timeout_seconds=args.timeout_seconds,
        max_bytes=args.max_bytes,
        retries=args.retries,
        delay_seconds=args.delay_seconds,
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary = {
        key: value
        for key, value in result.items()
        if key != "records"
    }
    print(json.dumps(summary, indent=2))

    if result["error_cases"] and not args.allow_errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
