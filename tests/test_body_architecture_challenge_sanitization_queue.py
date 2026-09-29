from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = (
    ROOT
    / "tools"
    / "knowledge"
    / "build_body_architecture_benchmark_sanitization_queue.py"
)
DATA = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
)
CHALLENGE = DATA / "body-architecture-recognition-challenge-cases-v1.json"
REVIEWS = (
    DATA
    / "body-architecture-recognition-challenge-sanitization-reviews-v1.json"
)
QUEUE = (
    DATA
    / "body-architecture-recognition-challenge-sanitization-queue-v1.json"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_body_architecture_benchmark_sanitization_queue",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_challenge_queue_applies_completed_visual_reviews() -> None:
    tool = load_tool()
    result = tool.build(CHALLENGE, REVIEWS)

    assert result["summary"] == {
        "total_cases": 8,
        "raw_model_input_allowed_cases": 8,
        "blocked_model_input_cases": 0,
        "status_counts": {
            "approved_raw_model_input": 8,
        },
        "risk_counts": {
            "medium_review_required": 8,
        },
    }
    assert all(
        row["split"] == "challenge_test"
        for row in result["queue"]
    )
    assert all(
        row["raw_model_input_allowed"] is True
        for row in result["queue"]
    )
    centaur = next(
        row for row in result["queue"]
        if row["source_record_id"] == "challenge_centaur_hp236"
    )
    assert centaur["status"] == "approved_raw_model_input"
    assert centaur["review"]["visual_confounders"] == []
    assert centaur["source"]["verification_run_id"] == 36520358304
    assert all(
        isinstance(row["source"]["verification_run_id"], int)
        and row["source"]["verification_run_id"] > 0
        for row in result["queue"]
    )


def test_challenge_source_hashes_are_pinned_before_review() -> None:
    tool = load_tool()
    result = tool.build(CHALLENGE, REVIEWS)

    hashes = [
        row["source"]["source_file_sha256"]
        for row in result["queue"]
    ]
    assert len(hashes) == 8
    assert len(set(hashes)) == 8
    assert all(len(value) == 64 for value in hashes)


def test_checked_in_challenge_sanitization_queue_matches_builder() -> None:
    tool = load_tool()
    expected = tool.build(CHALLENGE, REVIEWS)
    actual = json.loads(QUEUE.read_text(encoding="utf-8"))

    assert actual == expected


def test_challenge_policy_matches_shared_fail_closed_rule() -> None:
    tool = load_tool()
    result = tool.build(CHALLENGE, REVIEWS)
    expected = (
        "Byte verification proves file identity, not benchmark suitability. "
        "Raw media remains blocked from model input until visual sanitization "
        "is explicitly approved."
    )

    assert all(row["policy"] == expected for row in result["queue"])


def test_challenge_source_reviews_are_complete() -> None:
    reviews = json.loads(REVIEWS.read_text(encoding="utf-8"))
    assert len(reviews["reviews"]) == 8
    assert reviews["reviewer"]["reviewer_type"] == "model"
    assert sum(
        row["status"] == "approved_raw"
        for row in reviews["reviews"]
    ) == 8
    assert sum(
        row["status"] == "sanitization_required"
        for row in reviews["reviews"]
    ) == 0
