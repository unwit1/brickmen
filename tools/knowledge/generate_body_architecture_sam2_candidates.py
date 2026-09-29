#!/usr/bin/env python3
"""Generate review-required sanitized candidates for segmentation blockers with SAM 2.

This wrapper follows the public SAM2ImagePredictor image API. Prompt seeds are
hash-pinned to verified source images. The highest SAM score selects a *candidate*
mask only; generated derivatives remain blocked until explicit visual approval.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_body_architecture_sanitization_candidates import (  # noqa: E402
    _pixel_hash,
    _png_bytes,
    fetch_source_bytes,
)

VERSION = "body-architecture-sam2-sanitization/v1"
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
DEFAULT_QUEUE = DATA / "body-architecture-benchmark-sanitization-queue.json"
DEFAULT_PROMPTS = DATA / "body-architecture-benchmark-segmentation-prompts.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_revision(repo: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo.resolve()), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def _norm_xy(point: list[float], width: int, height: int) -> list[float]:
    if len(point) != 2:
        raise ValueError("point must contain x,y")
    x, y = map(float, point)
    if not (0 <= x <= 1 and 0 <= y <= 1):
        raise ValueError("normalized point values must be in [0,1]")
    return [x * width, y * height]


def norm_box_to_pixels(
    box: list[float],
    width: int,
    height: int,
) -> list[float]:
    if len(box) != 4:
        raise ValueError("box must contain x0,y0,x1,y1")
    x0, y0 = _norm_xy(box[:2], width, height)
    x1, y1 = _norm_xy(box[2:], width, height)
    if x1 <= x0 or y1 <= y0:
        raise ValueError("box must have positive area")
    return [x0, y0, x1, y1]


def norm_points_to_pixels(
    positive: list[list[float]],
    negative: list[list[float]],
    width: int,
    height: int,
) -> tuple[list[list[float]], list[int]]:
    points = [
        _norm_xy(point, width, height)
        for point in positive
    ] + [
        _norm_xy(point, width, height)
        for point in negative
    ]
    labels = [1] * len(positive) + [0] * len(negative)
    if not points:
        raise ValueError("at least one point prompt is required")
    return points, labels


def select_best_mask(masks, scores):
    import numpy as np

    masks = np.asarray(masks)
    scores = np.asarray(scores).reshape(-1)
    if masks.ndim != 3 or len(masks) != len(scores) or len(scores) == 0:
        raise ValueError("SAM2 returned unexpected mask/score shapes")
    index = int(np.argmax(scores))
    mask = masks[index].astype(bool)
    if not mask.any():
        raise ValueError("selected SAM2 mask is empty")
    return mask, float(scores[index]), index


def render_masked_candidate(image, mask, margin_fraction: float = 0.035):
    import numpy as np
    from PIL import Image

    rgba = image.convert("RGBA")
    mask = np.asarray(mask, dtype=bool)
    if mask.shape != (rgba.height, rgba.width):
        raise ValueError("mask dimensions do not match source image")
    ys, xs = np.where(mask)
    if len(xs) == 0:
        raise ValueError("mask is empty")

    alpha = Image.fromarray((mask.astype("uint8") * 255), mode="L")
    canvas = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    canvas.paste(rgba, (0, 0), alpha)

    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    margin = max(
        2,
        int(max(x1 - x0, y1 - y0) * float(margin_fraction)),
    )
    crop = (
        max(0, x0 - margin),
        max(0, y0 - margin),
        min(rgba.width, x1 + margin),
        min(rgba.height, y1 + margin),
    )
    return canvas.crop(crop), list(crop)


def load_sam2_predictor(
    sam2_repo: Path,
    checkpoint: Path,
    model_config: str,
    device: str,
):
    repo = sam2_repo.resolve()
    if not (repo / "sam2" / "sam2_image_predictor.py").is_file():
        raise ValueError("SAM2 repository missing sam2/sam2_image_predictor.py")
    if not checkpoint.is_file():
        raise ValueError(f"SAM2 checkpoint not found: {checkpoint}")

    sys.path.insert(0, str(repo))
    from sam2.build_sam import build_sam2  # type: ignore
    from sam2.sam2_image_predictor import SAM2ImagePredictor  # type: ignore

    model = build_sam2(
        model_config,
        str(checkpoint.resolve()),
        device=device,
    )
    return SAM2ImagePredictor(model)


def validate_prompt(
    prompt: dict[str, Any],
    queue_row: dict[str, Any],
) -> None:
    source = queue_row["source"]
    if prompt.get("source_file_sha256") != source.get("source_file_sha256"):
        raise ValueError(
            f"segmentation prompt source hash is stale: "
            f"{queue_row['source_record_id']}"
        )
    expected = list(prompt.get("source_dimensions") or [])
    actual = [source.get("source_width"), source.get("source_height")]
    if expected != actual:
        raise ValueError(
            f"segmentation prompt dimensions are stale: "
            f"{queue_row['source_record_id']}"
        )
    if queue_row.get("status") != "sanitization_required":
        raise ValueError(
            f"queue row is not sanitization_required: "
            f"{queue_row['source_record_id']}"
        )


def generate(
    queue_row: dict[str, Any],
    prompt: dict[str, Any],
    predictor,
    *,
    allowed_hosts: set[str],
    timeout_seconds: float,
    max_bytes: int,
    output_dir: Path | None = None,
    variant_output_dir: Path | None = None,
    provider_revision: str | None = None,
    checkpoint_sha256: str | None = None,
    model_config: str | None = None,
    device: str | None = None,
) -> dict[str, Any]:
    validate_prompt(prompt, queue_row)
    source = queue_row["source"]
    data, final_url = fetch_source_bytes(
        source["exact_image_url"],
        allowed_hosts=allowed_hosts,
        timeout_seconds=timeout_seconds,
        max_bytes=max_bytes,
    )
    observed_sha = hashlib.sha256(data).hexdigest()
    if observed_sha != source["source_file_sha256"]:
        raise ValueError(
            f"source SHA-256 mismatch: {queue_row['source_record_id']}"
        )

    import numpy as np
    import torch
    from PIL import Image

    with Image.open(io.BytesIO(data)) as opened:
        opened.load()
        rgb = opened.convert("RGB")
        width, height = rgb.size
        if [width, height] != prompt["source_dimensions"]:
            raise ValueError("decoded source dimensions changed")

        box = np.asarray(
            norm_box_to_pixels(prompt["box_norm"], width, height),
            dtype=np.float32,
        )
        point_coords, point_labels = norm_points_to_pixels(
            prompt.get("positive_points_norm") or [],
            prompt.get("negative_points_norm") or [],
            width,
            height,
        )
        point_coords = np.asarray(point_coords, dtype=np.float32)
        point_labels = np.asarray(point_labels, dtype=np.int32)

        with torch.inference_mode():
            predictor.set_image(np.asarray(rgb))
            masks, scores, _ = predictor.predict(
                point_coords=point_coords,
                point_labels=point_labels,
                box=box,
                multimask_output=True,
            )

        mask, score, selected_index = select_best_mask(masks, scores)
        sanitized, crop_pixels = render_masked_candidate(rgb, mask)

        mask_variants: list[dict[str, Any]] = []
        if variant_output_dir is not None:
            variant_output_dir.mkdir(parents=True, exist_ok=True)
            mask_array = np.asarray(masks)
            score_array = np.asarray(scores).reshape(-1)
            for index in range(len(score_array)):
                variant_mask = mask_array[index].astype(bool)
                if not variant_mask.any():
                    mask_variants.append(
                        {
                            "mask_index": index,
                            "predicted_mask_score": float(score_array[index]),
                            "error": "empty_mask",
                            "selected_by_sam_score": index == selected_index,
                        }
                    )
                    continue
                variant_image, variant_crop = render_masked_candidate(
                    rgb,
                    variant_mask,
                )
                variant_png = _png_bytes(variant_image)
                variant_pixel_sha = _pixel_hash(variant_image)
                variant_png_sha = hashlib.sha256(variant_png).hexdigest()
                variant_mask_bytes = np.packbits(
                    variant_mask.reshape(-1).astype(np.uint8)
                ).tobytes()
                variant_mask_sha = hashlib.sha256(
                    variant_mask_bytes
                ).hexdigest()
                variant_path = (
                    variant_output_dir
                    / (
                        f"{queue_row['source_record_id']}--m{index}--"
                        f"{variant_pixel_sha[:16]}.png"
                    )
                )
                variant_path.write_bytes(variant_png)
                mask_variants.append(
                    {
                        "mask_index": index,
                        "predicted_mask_score": float(score_array[index]),
                        "mask_area_fraction": round(
                            float(variant_mask.mean()),
                            8,
                        ),
                        "mask_sha256": variant_mask_sha,
                        "crop_pixels": variant_crop,
                        "output_dimensions": list(variant_image.size),
                        "sanitized_pixel_sha256": variant_pixel_sha,
                        "sanitized_png_sha256": variant_png_sha,
                        "sanitized_png_size_bytes": len(variant_png),
                        "written_derivative_path": str(variant_path),
                        "selected_by_sam_score": index == selected_index,
                    }
                )

    png = _png_bytes(sanitized)
    pixel_sha = _pixel_hash(sanitized)
    png_sha = hashlib.sha256(png).hexdigest()
    mask_bytes = np.packbits(mask.reshape(-1).astype(np.uint8)).tobytes()
    mask_sha = hashlib.sha256(mask_bytes).hexdigest()

    written = None
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        written = (
            output_dir
            / f"{queue_row['source_record_id']}--{pixel_sha[:16]}.png"
        )
        written.write_bytes(png)

    return {
        "source_record_id": queue_row["source_record_id"],
        "case_id": queue_row["case_id"],
        "split": queue_row["split"],
        "source_id": source["source_id"],
        "source_url": source["exact_image_url"],
        "final_source_url": final_url,
        "source_file_sha256": source["source_file_sha256"],
        "source_dimensions": prompt["source_dimensions"],
        "provider_id": "sam2",
        "provider_api": "SAM2ImagePredictor",
        "provider_revision": provider_revision,
        "checkpoint_sha256": checkpoint_sha256,
        "model_config": model_config,
        "device": device,
        "prompt_status": prompt.get("status"),
        "box_norm": prompt["box_norm"],
        "positive_points_norm": prompt.get("positive_points_norm") or [],
        "negative_points_norm": prompt.get("negative_points_norm") or [],
        "selected_mask_index": selected_index,
        "predicted_mask_score": score,
        "mask_variants": mask_variants,
        "mask_area_fraction": round(float(mask.mean()), 8),
        "mask_sha256": mask_sha,
        "crop_pixels": crop_pixels,
        "output_dimensions": list(sanitized.size),
        "sanitized_pixel_sha256": pixel_sha,
        "sanitized_png_sha256": png_sha,
        "sanitized_png_size_bytes": len(png),
        "written_derivative_path": str(written) if written else None,
        "candidate_status": "generated_pending_visual_review",
        "model_input_allowed": False,
        "generated_at": now_iso(),
        "processor_version": VERSION,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--prompts", type=Path, default=DEFAULT_PROMPTS)
    parser.add_argument("--sam2-repo", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument(
        "--model-config",
        default="configs/sam2.1/sam2.1_hiera_l.yaml",
    )
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--write-mask-variants-dir", type=Path)
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

    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    prompts = json.loads(args.prompts.read_text(encoding="utf-8"))
    queue_by_id = {
        row["source_record_id"]: row for row in queue["queue"]
    }

    checkpoint_sha256 = file_sha256(args.checkpoint)
    provider_revision = git_revision(args.sam2_repo)

    predictor = load_sam2_predictor(
        args.sam2_repo,
        args.checkpoint,
        args.model_config,
        args.device,
    )

    records = []
    errors = []
    for prompt in prompts.get("prompts", []):
        record_id = prompt["source_record_id"]
        row = queue_by_id.get(record_id)
        if row is None:
            errors.append(
                {
                    "source_record_id": record_id,
                    "error": "missing_queue_record",
                }
            )
            continue
        try:
            records.append(
                generate(
                    row,
                    prompt,
                    predictor,
                    allowed_hosts=allowed_hosts,
                    timeout_seconds=args.timeout_seconds,
                    max_bytes=args.max_bytes,
                    output_dir=args.output_dir,
                    variant_output_dir=args.write_mask_variants_dir,
                    provider_revision=provider_revision,
                    checkpoint_sha256=checkpoint_sha256,
                    model_config=args.model_config,
                    device=args.device,
                )
            )
        except Exception as exc:
            errors.append(
                {
                    "source_record_id": record_id,
                    "error": str(exc)[:1000],
                }
            )

    report = {
        "schema": "body-architecture-sam2-sanitization-report/v1",
        "created_at": now_iso(),
        "processor_version": VERSION,
        "provider_id": "sam2",
        "provider_revision": provider_revision,
        "model_config": args.model_config,
        "checkpoint": str(args.checkpoint),
        "checkpoint_sha256": checkpoint_sha256,
        "device": args.device,
        "generated_candidates": len(records),
        "errors": len(errors),
        "records": records,
        "error_records": errors,
        "policy": (
            "SAM2 score chooses a candidate mask only. Every derivative remains "
            "blocked until exact-hash visual approval."
        ),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "generated_candidates": len(records),
                "errors": len(errors),
                "report": str(args.report),
            },
            indent=2,
        )
    )
    return_code = 2 if errors else 0
    raise SystemExit(return_code)


if __name__ == "__main__":
    main()
