from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "canonicalize_body_architecture_sam2_report.py"


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "canonicalize_body_architecture_sam2_report",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixtures():
    source_sha = "a" * 64
    queue = {
        "queue": [
            {
                "source_record_id": "test",
                "source": {
                    "source_file_sha256": source_sha,
                    "source_width": 100,
                    "source_height": 200,
                },
            }
        ]
    }
    deterministic = {
        "records": [],
        "blockers": [
            {
                "source_record_id": "test",
                "status": "requires_segmentation",
            }
        ],
    }
    record = {
        "source_record_id": "test",
        "case_id": "archrec::test",
        "split": "test",
        "source_id": "source-test",
        "source_file_sha256": source_sha,
        "source_dimensions": [100, 200],
        "provider_id": "sam2",
        "provider_api": "SAM2ImagePredictor",
        "provider_revision": "b" * 40,
        "checkpoint_sha256": "c" * 64,
        "model_config": "configs/sam2.1/sam2.1_hiera_t.yaml",
        "device": "cpu",
        "prompt_status": "prompt_seed_unvalidated",
        "box_norm": [0.1, 0.1, 0.9, 0.9],
        "positive_points_norm": [[0.5, 0.5]],
        "negative_points_norm": [],
        "selected_mask_index": 0,
        "predicted_mask_score": 0.9,
        "mask_area_fraction": 0.4,
        "mask_sha256": "d" * 64,
        "crop_pixels": [1, 2, 90, 190],
        "output_dimensions": [89, 188],
        "sanitized_pixel_sha256": "e" * 64,
        "sanitized_png_sha256": "f" * 64,
        "sanitized_png_size_bytes": 123,
        "candidate_status": "generated_pending_visual_review",
        "model_input_allowed": False,
    }
    report = {
        "created_at": "2026-09-29T00:00:00+00:00",
        "processor_version": "body-architecture-sam2-sanitization/v1",
        "provider_id": "sam2",
        "provider_revision": "b" * 40,
        "checkpoint_sha256": "c" * 64,
        "model_config": "configs/sam2.1/sam2.1_hiera_t.yaml",
        "device": "cpu",
        "errors": 0,
        "error_records": [],
        "records": [record],
    }
    return report, queue, deterministic


def test_complete_report_canonicalizes_fail_closed_metadata() -> None:
    tool = load_tool()
    report, queue, deterministic = fixtures()

    result = tool.canonicalize(
        report,
        queue,
        deterministic,
        workflow_run_id=123,
        workflow_artifact_id=456,
    )

    assert result["generated_candidates"] == 1
    assert result["errors"] == 0
    assert result["workflow_run_id"] == 123
    assert result["workflow_artifact_id"] == 456
    row = result["records"][0]
    assert row["candidate_kind"] == "sam2_segmentation"
    assert row["candidate_status"] == "generated_pending_visual_review"
    assert row["model_input_allowed"] is False
    assert row["expected_local_asset"] == "test--eeeeeeeeeeeeeeee.png"


def test_partial_report_is_rejected() -> None:
    tool = load_tool()
    report, queue, deterministic = fixtures()
    report["errors"] = 1
    report["error_records"] = [{"source_record_id": "test", "error": "x"}]

    with pytest.raises(ValueError, match="zero errors"):
        tool.canonicalize(report, queue, deterministic)


def test_blocker_coverage_must_match_exactly() -> None:
    tool = load_tool()
    report, queue, deterministic = fixtures()
    deterministic["blockers"].append(
        {"source_record_id": "missing", "status": "requires_segmentation"}
    )

    with pytest.raises(ValueError, match="coverage mismatch"):
        tool.canonicalize(report, queue, deterministic)


def test_candidate_cannot_claim_approval() -> None:
    tool = load_tool()
    report, queue, deterministic = fixtures()
    report["records"][0]["model_input_allowed"] = True

    with pytest.raises(ValueError, match="review-blocked"):
        tool.canonicalize(report, queue, deterministic)
