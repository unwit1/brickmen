from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "validate_body_architecture_sanitized_asset_reviews.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "validate_body_architecture_sanitized_asset_reviews",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidate() -> dict:
    return {
        "source_record_id": "test",
        "source_file_sha256": "a" * 64,
        "sanitized_pixel_sha256": "b" * 64,
        "sanitized_png_sha256": "c" * 64,
        "candidate_status": "generated_pending_visual_review",
    }


def review(*, decision: str = "approved") -> dict:
    return {
        "schema": "body-architecture-sanitized-asset-review/v1",
        "source_record_id": "test",
        "source_file_sha256": "a" * 64,
        "sanitized_pixel_sha256": "b" * 64,
        "sanitized_png_sha256": "c" * 64,
        "decision": decision,
        "checks": {
            "identity_preserved": True,
            "primary_figure_complete": True,
            "forbidden_text_absent": True,
            "task_confounders_absent": True,
            "architecture_evidence_preserved": True,
            "no_material_transform_artifacts": True,
        },
        "reviewer": {
            "reviewer_id": "reviewer-a",
            "reviewer_type": "human",
            "model_id": None,
            "model_revision": None,
        },
        "review_confidence": 0.95,
        "notes": ["visually inspected exact derivative"],
        "reviewed_at": "2026-09-29T00:00:00Z",
        "provenance": [],
    }


def test_exact_approved_candidate_is_valid() -> None:
    tool = load_tool()
    row = review()

    assert tool.validate_record(row, {"test": candidate()}) == []
    normalized = tool.normalize_record(row)
    assert normalized["review_id"].startswith("sanreview-")
    assert normalized["model_input_allowed"] is True


def test_stale_source_hash_is_rejected() -> None:
    tool = load_tool()
    row = review()
    row["source_file_sha256"] = "d" * 64

    assert (
        "source_file_sha256 does not match the generated candidate"
        in tool.validate_record(row, {"test": candidate()})
    )


def test_wrong_derivative_hash_is_rejected() -> None:
    tool = load_tool()
    row = review()
    row["sanitized_png_sha256"] = "d" * 64

    assert (
        "sanitized_png_sha256 does not match the generated candidate"
        in tool.validate_record(row, {"test": candidate()})
    )


def test_approval_requires_every_visual_check_true() -> None:
    tool = load_tool()
    row = review()
    row["checks"]["architecture_evidence_preserved"] = False

    errors = tool.validate_record(row, {"test": candidate()})
    assert any(
        "approved review requires all checks true" in error
        and "architecture_evidence_preserved" in error
        for error in errors
    )


def test_revise_can_have_failed_checks_but_requires_notes() -> None:
    tool = load_tool()
    row = review(decision="revise")
    row["checks"]["forbidden_text_absent"] = False
    row["notes"] = ["label remains visible"]

    assert tool.validate_record(row, {"test": candidate()}) == []
    assert tool.normalize_record(row)["model_input_allowed"] is False

    row["notes"] = []
    assert (
        "rejected/revise review requires explanatory notes"
        in tool.validate_record(row, {"test": candidate()})
    )


def test_model_review_requires_model_provenance() -> None:
    tool = load_tool()
    row = review()
    row["reviewer"]["reviewer_type"] = "model"

    errors = tool.validate_record(row, {"test": candidate()})
    assert "model/hybrid review requires reviewer.model_id" in errors
    assert "model/hybrid review requires reviewer.model_revision" in errors


def test_unknown_candidate_cannot_be_approved() -> None:
    tool = load_tool()
    row = review()

    errors = tool.validate_record(row, {})
    assert "source_record_id is not a generated sanitization candidate" in errors


def test_review_id_is_deterministic() -> None:
    tool = load_tool()
    row = review()

    assert tool.review_id(row) == tool.review_id(row)
