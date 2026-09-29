#!/usr/bin/env python3
"""Generate metadata-only sanitized benchmark image candidates.

Source and derivative image bytes are handled transiently in memory. By default this
tool writes only transformation metadata and hashes. Derivative image files are written
only when --write-derivatives-dir is explicitly supplied for local review.

Candidate generation is not approval: generated candidates remain blocked from model
input until their sanitized pixels are separately reviewed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import statistics
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from verify_body_architecture_reference_media import (
    AllowlistedRedirectHandler,
    validate_https_url,
)

VERSION = "body-architecture-sanitization-candidate-generator/v1"
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
DEFAULT_QUEUE = DATA / "body-architecture-benchmark-sanitization-queue.json"
DEFAULT_TRANSFORMS = DATA / "body-architecture-benchmark-sanitization-transforms.json"
USER_AGENT = "BrickmenSanitizationCandidateGenerator/1.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalized_box(
    bounds: list[float] | tuple[float, float, float, float],
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    if len(bounds) != 4:
        raise ValueError("bounds must contain four normalized coordinates")
    x0, y0, x1, y1 = (float(value) for value in bounds)
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ValueError(f"invalid normalized bounds: {bounds}")
    left = max(0, min(width - 1, math.floor(x0 * width)))
    top = max(0, min(height - 1, math.floor(y0 * height)))
    right = max(left + 1, min(width, math.ceil(x1 * width)))
    bottom = max(top + 1, min(height, math.ceil(y1 * height)))
    return left, top, right, bottom


def _median_color(image, box: tuple[int, int, int, int]) -> tuple[int, ...]:
    """Sample a narrow ring around a rectangle and return median channel values."""
    left, top, right, bottom = box
    width, height = image.size
    border = max(2, round(min(width, height) * 0.01))
    samples: list[tuple[int, ...]] = []

    strips = [
        (max(0, left - border), max(0, top - border), min(width, right + border), top),
        (max(0, left - border), bottom, min(width, right + border), min(height, bottom + border)),
        (max(0, left - border), top, left, bottom),
        (right, top, min(width, right + border), bottom),
    ]
    for strip in strips:
        x0, y0, x1, y1 = strip
        if x1 <= x0 or y1 <= y0:
            continue
        samples.extend(tuple(pixel) for pixel in image.crop(strip).getdata())

    if not samples:
        return tuple(255 for _ in range(len(image.getpixel((0, 0)))))

    channels = list(zip(*samples))
    return tuple(int(round(statistics.median(channel))) for channel in channels)


def _fill_rect_with_row_median_sample(
    image,
    target_box: tuple[int, int, int, int],
    sample_box: tuple[int, int, int, int],
) -> None:
    """Fill each target row from median pixels in a clean sample strip.

    This preserves studio-background vertical gradients better than a single flat
    color and avoids sampling the contaminated inset being removed.
    """
    from PIL import ImageDraw

    left, top, right, bottom = target_box
    sample_left, sample_top, sample_right, sample_bottom = sample_box
    if sample_right <= sample_left or sample_bottom <= sample_top:
        raise ValueError("row-median sample box must have positive area")

    draw = ImageDraw.Draw(image)
    for y in range(top, bottom):
        sample_y = min(max(y, sample_top), sample_bottom - 1)
        pixels = [
            tuple(image.getpixel((x, sample_y)))
            for x in range(sample_left, sample_right)
        ]
        if not pixels:
            raise ValueError("row-median sample produced no pixels")
        channels = list(zip(*pixels))
        fill = tuple(
            int(round(statistics.median(channel)))
            for channel in channels
        )
        draw.line((left, y, right - 1, y), fill=fill)


def apply_operations(image, operations: list[dict[str, Any]]):
    """Apply deterministic normalized crop/mask operations in order."""
    from PIL import ImageDraw

    current = image.convert("RGBA")
    applied: list[dict[str, Any]] = []

    for index, operation in enumerate(operations):
        op = operation.get("op")
        bounds = operation.get("bounds")
        box = normalized_box(bounds, *current.size)

        if op == "mask_rect_norm":
            fill_mode = operation.get("fill_mode", "border_median")
            sample_bounds = None
            sample_box = None
            if fill_mode == "border_median":
                fill = _median_color(current, box)
                draw = ImageDraw.Draw(current)
                draw.rectangle(box, fill=fill)
            elif fill_mode == "white":
                fill = (255, 255, 255, 255)
                draw = ImageDraw.Draw(current)
                draw.rectangle(box, fill=fill)
            elif fill_mode == "transparent":
                fill = (0, 0, 0, 0)
                draw = ImageDraw.Draw(current)
                draw.rectangle(box, fill=fill)
            elif fill_mode == "row_median_sample":
                fill = None
                sample_bounds = operation.get("sample_bounds")
                if sample_bounds is None:
                    raise ValueError(
                        "row_median_sample requires sample_bounds"
                    )
                sample_box = normalized_box(
                    sample_bounds, *current.size
                )
                _fill_rect_with_row_median_sample(
                    current, box, sample_box
                )
            else:
                raise ValueError(f"unsupported fill_mode: {fill_mode}")
            applied_row = {
                "index": index,
                "op": op,
                "requested_bounds": bounds,
                "pixel_bounds": list(box),
                "fill_mode": fill_mode,
                "result_dimensions": list(current.size),
            }
            if fill is not None:
                applied_row["fill_rgba"] = list(fill)
            if sample_bounds is not None and sample_box is not None:
                applied_row["sample_bounds"] = sample_bounds
                applied_row["sample_pixel_bounds"] = list(sample_box)
            applied.append(applied_row)
        elif op == "crop_norm":
            current = current.crop(box)
            applied.append(
                {
                    "index": index,
                    "op": op,
                    "requested_bounds": bounds,
                    "pixel_bounds": list(box),
                    "result_dimensions": list(current.size),
                }
            )
        else:
            raise ValueError(f"unsupported sanitization operation: {op}")

    return current, applied


def fetch_source_bytes(
    url: str,
    *,
    allowed_hosts: set[str],
    timeout_seconds: float,
    max_bytes: int,
) -> tuple[bytes, str]:
    validate_https_url(url, allowed_hosts)
    opener = urllib.request.build_opener(AllowlistedRedirectHandler(allowed_hosts))
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "image/*"},
    )
    with opener.open(request, timeout=timeout_seconds) as response:
        final_url = response.geturl()
        validate_https_url(final_url, allowed_hosts)
        content_type = (
            response.headers.get("Content-Type", "")
            .split(";", 1)[0]
            .strip()
            .lower()
        )
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError(f"source exceeds max_bytes={max_bytes}")
    if content_type and not content_type.startswith("image/"):
        raise ValueError(f"non-image content type: {content_type}")
    return data, final_url


def _pixel_hash(image) -> str:
    canonical = image.convert("RGBA")
    prefix = f"{canonical.width}x{canonical.height}|RGBA|".encode("ascii")
    return hashlib.sha256(prefix + canonical.tobytes()).hexdigest()


def _png_bytes(image) -> bytes:
    buffer = io.BytesIO()
    image.convert("RGBA").save(
        buffer,
        format="PNG",
        optimize=False,
        compress_level=9,
    )
    return buffer.getvalue()


def generate_candidate(
    queue_row: dict[str, Any],
    transform: dict[str, Any],
    *,
    allowed_hosts: set[str],
    timeout_seconds: float,
    max_bytes: int,
    write_derivatives_dir: Path | None = None,
) -> dict[str, Any]:
    source = queue_row["source"]
    expected_sha = str(transform["source_file_sha256"])
    if source.get("source_file_sha256") != expected_sha:
        raise ValueError(
            f"transform source hash is stale for {queue_row['source_record_id']}"
        )
    expected_dimensions = tuple(transform.get("source_dimensions") or ())
    actual_dimensions = (
        source.get("source_width"),
        source.get("source_height"),
    )
    if expected_dimensions and expected_dimensions != actual_dimensions:
        raise ValueError(
            f"transform source dimensions are stale for {queue_row['source_record_id']}: "
            f"{expected_dimensions} != {actual_dimensions}"
        )

    data, final_url = fetch_source_bytes(
        str(source["exact_image_url"]),
        allowed_hosts=allowed_hosts,
        timeout_seconds=timeout_seconds,
        max_bytes=max_bytes,
    )
    observed_sha = hashlib.sha256(data).hexdigest()
    if observed_sha != expected_sha:
        raise ValueError(
            f"source SHA-256 mismatch for {queue_row['source_record_id']}: "
            f"{observed_sha} != {expected_sha}"
        )

    from PIL import Image, __version__ as pillow_version

    with Image.open(io.BytesIO(data)) as opened:
        opened.load()
        if opened.size != actual_dimensions:
            raise ValueError(
                f"decoded dimensions changed for {queue_row['source_record_id']}: "
                f"{opened.size} != {actual_dimensions}"
            )
        sanitized, applied = apply_operations(opened, transform["operations"])

    png = _png_bytes(sanitized)
    pixel_sha = _pixel_hash(sanitized)
    png_sha = hashlib.sha256(png).hexdigest()

    written_path = None
    if write_derivatives_dir is not None:
        write_derivatives_dir.mkdir(parents=True, exist_ok=True)
        written_path = (
            write_derivatives_dir
            / f"{queue_row['source_record_id']}--{pixel_sha[:16]}.png"
        )
        written_path.write_bytes(png)

    return {
        "source_record_id": queue_row["source_record_id"],
        "case_id": queue_row["case_id"],
        "split": queue_row["split"],
        "source_id": source["source_id"],
        "source_url": source["exact_image_url"],
        "final_source_url": final_url,
        "source_file_sha256": expected_sha,
        "source_dimensions": list(actual_dimensions),
        "transform_status": transform["status"],
        "operations": transform["operations"],
        "applied_operations": applied,
        "output_dimensions": list(sanitized.size),
        "sanitized_pixel_sha256": pixel_sha,
        "sanitized_png_sha256": png_sha,
        "sanitized_png_size_bytes": len(png),
        "pillow_version": pillow_version,
        "candidate_status": "generated_pending_visual_review",
        "model_input_allowed": False,
        "written_derivative_path": str(written_path) if written_path else None,
        "generated_at": now_iso(),
        "processor_version": VERSION,
    }


def build(
    queue_path: Path = DEFAULT_QUEUE,
    transforms_path: Path = DEFAULT_TRANSFORMS,
    *,
    allowed_hosts: set[str],
    timeout_seconds: float = 30.0,
    max_bytes: int = 25 * 1024 * 1024,
    delay_seconds: float = 0.20,
    write_derivatives_dir: Path | None = None,
) -> dict[str, Any]:
    queue_doc = json.loads(queue_path.read_text(encoding="utf-8"))
    transforms_doc = json.loads(transforms_path.read_text(encoding="utf-8"))
    queue_by_record = {
        row["source_record_id"]: row for row in queue_doc["queue"]
    }

    records: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for transform in transforms_doc.get("transforms", []):
        record_id = transform["source_record_id"]
        if transform.get("status") != "candidate_transform":
            blockers.append(
                {
                    "source_record_id": record_id,
                    "status": transform.get("status"),
                    "rationale": transform.get("rationale"),
                }
            )
            continue
        queue_row = queue_by_record.get(record_id)
        if not queue_row:
            errors.append(
                {
                    "source_record_id": record_id,
                    "error": "missing_sanitization_queue_record",
                }
            )
            continue
        try:
            records.append(
                generate_candidate(
                    queue_row,
                    transform,
                    allowed_hosts=allowed_hosts,
                    timeout_seconds=timeout_seconds,
                    max_bytes=max_bytes,
                    write_derivatives_dir=write_derivatives_dir,
                )
            )
        except Exception as exc:
            errors.append(
                {
                    "source_record_id": record_id,
                    "error": str(exc)[:1000],
                }
            )
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    return {
        "schema": "body-architecture-sanitization-candidate-report/v1",
        "created_at": now_iso(),
        "processor_version": VERSION,
        "queue": str(queue_path),
        "transform_spec": str(transforms_path),
        "metadata_only": write_derivatives_dir is None,
        "raw_source_media_persisted": False,
        "candidate_derivative_media_persisted": write_derivatives_dir is not None,
        "generated_candidates": len(records),
        "segmentation_or_manual_blockers": len(blockers),
        "errors": len(errors),
        "records": records,
        "blockers": blockers,
        "error_records": errors,
        "policy": (
            "Generated candidate hashes are not benchmark approval. Sanitized pixels "
            "must be visually reviewed before model_input_allowed may become true."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--transforms", type=Path, default=DEFAULT_TRANSFORMS)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--allow-host", action="append", default=[])
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--max-bytes", type=int, default=25 * 1024 * 1024)
    parser.add_argument("--delay-seconds", type=float, default=0.20)
    parser.add_argument("--write-derivatives-dir", type=Path)
    parser.add_argument("--allow-errors", action="store_true")
    args = parser.parse_args()

    allowed_hosts = {
        str(host).strip().lower()
        for host in args.allow_host
        if str(host).strip()
    }
    if not allowed_hosts:
        raise SystemExit("At least one --allow-host is required.")

    result = build(
        args.queue,
        args.transforms,
        allowed_hosts=allowed_hosts,
        timeout_seconds=args.timeout_seconds,
        max_bytes=args.max_bytes,
        delay_seconds=args.delay_seconds,
        write_derivatives_dir=args.write_derivatives_dir,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary = {
        key: value
        for key, value in result.items()
        if key not in {"records", "blockers", "error_records"}
    }
    print(json.dumps(summary, indent=2))

    if result["errors"] and not args.allow_errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
