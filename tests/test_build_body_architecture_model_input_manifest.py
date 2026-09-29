from __future__ import annotations

import importlib.util
import json
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "build_body_architecture_model_input_manifest.py"
)
DATA = (
    Path(__file__).resolve().parents[1]
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_body_architecture_model_input_manifest",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_inputs() -> tuple[dict, dict]:
    queue = json.loads(
        (
            DATA
            / "body-architecture-benchmark-sanitization-queue.json"
        ).read_text(encoding="utf-8")
    )
    candidates = json.loads(
        (
            DATA
            / "body-architecture-benchmark-sanitization-candidates.json"
        ).read_text(encoding="utf-8")
    )
    return queue, candidates


def approval(candidate: dict, *, decision: str = "approved") -> dict:
    return {
        "review_id": "sanreview-test",
        "source_record_id": candidate["source_record_id"],
        "source_file_sha256": candidate["source_file_sha256"],
        "sanitized_pixel_sha256": candidate["sanitized_pixel_sha256"],
        "sanitized_png_sha256": candidate["sanitized_png_sha256"],
        "decision": decision,
        "checks": {
            "identity_preserved": True,
            "primary_figure_complete": True,
            "forbidden_text_absent": True,
            "task_confounders_absent": True,
            "architecture_evidence_preserved": True,
            "no_material_transform_artifacts": True,
        },
        "model_input_allowed": decision == "approved",
    }


def test_live_manifest_defaults_to_four_clean_raw_inputs() -> None:
    tool = load_tool()
    queue, candidates = live_inputs()

    result = tool.build(queue, candidates)

    assert result["summary"] == {
        "total_cases": 27,
        "model_input_allowed_cases": 4,
        "approved_raw_cases": 4,
        "approved_sanitized_cases": 0,
        "blocked_cases": 23,
    }
    assert sum(
        row["blocked_reason"] == "pending_visual_review"
        for row in result["entries"]
    ) == 15
    assert sum(
        row["blocked_reason"] == "requires_segmentation_or_manual_cleanup"
        for row in result["entries"]
    ) == 8


def test_exact_valid_approval_promotes_one_candidate() -> None:
    tool = load_tool()
    queue, candidates = live_inputs()
    candidate = candidates["records"][0]

    result = tool.build(
        queue,
        candidates,
        [approval(candidate)],
    )

    assert result["summary"]["model_input_allowed_cases"] == 5
    assert result["summary"]["approved_sanitized_cases"] == 1
    row = next(
        entry
        for entry in result["entries"]
        if entry["source_record_id"] == candidate["source_record_id"]
    )
    assert row["status"] == "approved_sanitized"
    assert row["asset_sha256"] == candidate["sanitized_png_sha256"]
    assert row["expected_local_asset"].endswith(".png")


def test_stale_hash_review_cannot_promote_candidate() -> None:
    tool = load_tool()
    queue, candidates = live_inputs()
    candidate = candidates["records"][0]
    row = approval(candidate)
    row["sanitized_png_sha256"] = "0" * 64

    result = tool.build(queue, candidates, [row])
    entry = next(
        item
        for item in result["entries"]
        if item["source_record_id"] == candidate["source_record_id"]
    )

    assert entry["model_input_allowed"] is False
    assert entry["blocked_reason"] == "no_valid_exact_approval"


def test_rejected_or_revise_candidate_stays_blocked() -> None:
    tool = load_tool()
    queue, candidates = live_inputs()

    for decision, reason in (
        ("rejected", "candidate_rejected"),
        ("revise", "candidate_revision_required"),
    ):
        candidate = candidates["records"][0]
        row = approval(candidate, decision=decision)
        result = tool.build(queue, candidates, [row])
        entry = next(
            item
            for item in result["entries"]
            if item["source_record_id"] == candidate["source_record_id"]
        )
        assert entry["model_input_allowed"] is False
        assert entry["blocked_reason"] == reason


def test_conflicting_exact_reviews_block_candidate() -> None:
    tool = load_tool()
    queue, candidates = live_inputs()
    candidate = candidates["records"][0]
    approved = approval(candidate)
    rejected = approval(candidate, decision="rejected")
    rejected["review_id"] = "sanreview-rejected"

    result = tool.build(queue, candidates, [approved, rejected])
    entry = next(
        item
        for item in result["entries"]
        if item["source_record_id"] == candidate["source_record_id"]
    )

    assert entry["model_input_allowed"] is False
    assert entry["blocked_reason"] == "conflicting_reviews"


def test_unvalidated_approval_flag_cannot_be_omitted() -> None:
    tool = load_tool()
    queue, candidates = live_inputs()
    candidate = candidates["records"][0]
    row = approval(candidate)
    row.pop("model_input_allowed")

    result = tool.build(queue, candidates, [row])
    entry = next(
        item
        for item in result["entries"]
        if item["source_record_id"] == candidate["source_record_id"]
    )

    assert entry["model_input_allowed"] is False
    assert entry["blocked_reason"] == "no_valid_exact_approval"
