#!/usr/bin/env python3
"""Canonicalize a complete SAM2 architecture-segmentation report.

The raw GitHub Actions report may contain ephemeral file paths and partial runs.
This tool emits a metadata-only supplemental candidate manifest only when:
- the SAM2 run has zero errors;
- generated source_record_id values exactly equal the active deterministic blockers;
- every source hash/dimension still matches the canonical sanitization queue;
- provider/checkpoint provenance is present and consistent;
- no generated record claims model-input approval.

The output remains review-required. It can supplement the deterministic candidate
manifest in build_body_architecture_model_input_manifest.py after exact visual review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VERSION = "body-architecture-sam2-candidate-canonicalizer/v1"
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
DEFAULT_QUEUE = DATA / "body-architecture-benchmark-sanitization-queue.json"
DEFAULT_DETERMINISTIC = DATA / "body-architecture-benchmark-sanitization-candidates.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonicalize(
    report: dict[str, Any],
    queue: dict[str, Any],
    deterministic: dict[str, Any],
    *,
    workflow_run_id: int | None = None,
    workflow_artifact_id: int | None = None,
) -> dict[str, Any]:
    if report.get("errors") != 0 or report.get("error_records"):
        raise ValueError("SAM2 report must be complete with zero errors")

    active_blockers = {
        row["source_record_id"]
        for row in deterministic.get("blockers", [])
    }
    records = report.get("records") or []
    generated_ids = {row["source_record_id"] for row in records}
    if generated_ids != active_blockers:
        missing = sorted(active_blockers - generated_ids)
        extra = sorted(generated_ids - active_blockers)
        raise ValueError(
            f"SAM2 coverage mismatch: missing={missing}, extra={extra}"
        )
    if len(records) != len(generated_ids):
        raise ValueError("SAM2 report contains duplicate source_record_id values")

    queue_by_id = {
        row["source_record_id"]: row
        for row in queue.get("queue", [])
    }
    provider_revision = report.get("provider_revision")
    checkpoint_sha256 = report.get("checkpoint_sha256")
    model_config = report.get("model_config")
    device = report.get("device")
    if not all(
        isinstance(value, str) and value
        for value in (
            provider_revision,
            checkpoint_sha256,
            model_config,
            device,
        )
    ):
        raise ValueError("SAM2 report is missing provider/checkpoint provenance")
    if len(checkpoint_sha256) != 64:
        raise ValueError("checkpoint_sha256 must be a SHA-256 digest")

    canonical_records: list[dict[str, Any]] = []
    for row in records:
        record_id = row["source_record_id"]
        queue_row = queue_by_id.get(record_id)
        if queue_row is None:
            raise ValueError(f"SAM2 candidate missing queue row: {record_id}")
        source = queue_row["source"]
        if row.get("source_file_sha256") != source.get("source_file_sha256"):
            raise ValueError(f"SAM2 source hash mismatch: {record_id}")
        if list(row.get("source_dimensions") or []) != [
            source.get("source_width"),
            source.get("source_height"),
        ]:
            raise ValueError(f"SAM2 source dimensions mismatch: {record_id}")
        if row.get("provider_revision") != provider_revision:
            raise ValueError(f"SAM2 provider revision drift: {record_id}")
        if row.get("checkpoint_sha256") != checkpoint_sha256:
            raise ValueError(f"SAM2 checkpoint drift: {record_id}")
        if row.get("model_input_allowed") is not False:
            raise ValueError(
                f"SAM2 candidate must remain review-blocked: {record_id}"
            )
        for key in (
            "sanitized_pixel_sha256",
            "sanitized_png_sha256",
            "mask_sha256",
        ):
            value = row.get(key)
            if not isinstance(value, str) or len(value) != 64:
                raise ValueError(f"{record_id}.{key} must be SHA-256")

        canonical_records.append(
            {
                "source_record_id": record_id,
                "case_id": row.get("case_id"),
                "split": row.get("split"),
                "source_id": row.get("source_id"),
                "source_file_sha256": row["source_file_sha256"],
                "source_dimensions": row["source_dimensions"],
                "candidate_kind": "sam2_segmentation",
                "provider_id": row.get("provider_id"),
                "provider_api": row.get("provider_api"),
                "provider_revision": provider_revision,
                "checkpoint_sha256": checkpoint_sha256,
                "model_config": row.get("model_config"),
                "device": row.get("device"),
                "prompt_status": row.get("prompt_status"),
                "box_norm": row.get("box_norm"),
                "positive_points_norm": row.get("positive_points_norm") or [],
                "negative_points_norm": row.get("negative_points_norm") or [],
                "selected_mask_index": row.get("selected_mask_index"),
                "sam_best_mask_index": row.get("sam_best_mask_index"),
                "mask_selection": row.get("mask_selection"),
                "predicted_mask_score": row.get("predicted_mask_score"),
                "mask_cleanup": row.get("mask_cleanup") or "none",
                "mask_cleanup_stats": row.get("mask_cleanup_stats"),
                "raw_selected_mask_sha256": row.get(
                    "raw_selected_mask_sha256"
                ),
                "mask_area_fraction": row.get("mask_area_fraction"),
                "mask_sha256": row.get("mask_sha256"),
                "crop_pixels": row.get("crop_pixels"),
                "output_dimensions": row.get("output_dimensions"),
                "sanitized_pixel_sha256": row["sanitized_pixel_sha256"],
                "sanitized_png_sha256": row["sanitized_png_sha256"],
                "sanitized_png_size_bytes": row.get("sanitized_png_size_bytes"),
                "expected_local_asset": (
                    f"{record_id}--"
                    f"{row['sanitized_pixel_sha256'][:16]}.png"
                ),
                "candidate_status": "generated_pending_visual_review",
                "model_input_allowed": False,
            }
        )

    canonical_records.sort(key=lambda row: row["source_record_id"])
    return {
        "schema_version": "0.1",
        "created_at": report.get("created_at"),
        "status": "sam2_candidates_pending_visual_review",
        "processor_version": VERSION,
        "source_processor_version": report.get("processor_version"),
        "provider_id": report.get("provider_id"),
        "provider_revision": provider_revision,
        "checkpoint_sha256": checkpoint_sha256,
        "model_config": model_config,
        "device": device,
        "workflow_run_id": workflow_run_id,
        "workflow_artifact_id": workflow_artifact_id,
        "metadata_only": True,
        "derivative_media_committed": False,
        "generated_candidates": len(canonical_records),
        "errors": 0,
        "records": canonical_records,
        "blockers": [],
        "policy": (
            "SAM2 candidates are supplemental exact-hash review inputs only. "
            "They do not supersede deterministic blocker provenance and never "
            "authorize model input until separately visually approved."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument(
        "--deterministic-candidates",
        type=Path,
        default=DEFAULT_DETERMINISTIC,
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workflow-run-id", type=int)
    parser.add_argument("--workflow-artifact-id", type=int)
    args = parser.parse_args()

    result = canonicalize(
        load(args.report),
        load(args.queue),
        load(args.deterministic_candidates),
        workflow_run_id=args.workflow_run_id,
        workflow_artifact_id=args.workflow_artifact_id,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "generated_candidates": result["generated_candidates"],
                "provider_revision": result["provider_revision"],
                "checkpoint_sha256": result["checkpoint_sha256"],
                "output": str(args.output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
