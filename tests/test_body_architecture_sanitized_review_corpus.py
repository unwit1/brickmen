from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = (
    ROOT
    / "tools"
    / "knowledge"
    / "validate_body_architecture_sanitized_asset_reviews.py"
)
DATA = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
)
REVIEWS = DATA / "body-architecture-benchmark-sanitized-asset-reviews.jsonl"
CANDIDATES = DATA / "body-architecture-benchmark-sanitization-candidates.json"


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "validate_body_architecture_sanitized_asset_reviews",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_reviews() -> list[dict]:
    return [
        json.loads(line)
        for line in REVIEWS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def exact_match(review: dict, candidate: dict) -> bool:
    return (
        review["source_record_id"] == candidate["source_record_id"]
        and review["source_file_sha256"] == candidate["source_file_sha256"]
        and review["sanitized_pixel_sha256"]
        == candidate["sanitized_pixel_sha256"]
        and review["sanitized_png_sha256"]
        == candidate["sanitized_png_sha256"]
    )


def test_canonical_sanitized_review_corpus_is_append_only_and_valid() -> None:
    tool = load_tool()
    candidates = tool.load_candidates(CANDIDATES)
    rows = load_reviews()

    assert len(rows) == 20
    assert sum(row["decision"] == "approved" for row in rows) == 13
    assert sum(row["decision"] == "revise" for row in rows) == 7

    for row in rows:
        assert tool.validate_record(row, candidates) == []
        assert row["model_input_allowed"] is (
            row["decision"] == "approved"
        )


def test_every_active_candidate_has_one_exact_current_approval() -> None:
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    rows = load_reviews()

    assert len(candidates["records"]) == 13
    for candidate in candidates["records"]:
        exact = [
            review
            for review in rows
            if exact_match(review, candidate)
        ]
        assert len(exact) == 1
        assert exact[0]["decision"] == "approved"
        assert exact[0]["model_input_allowed"] is True


def test_superseded_reviews_remain_historical_audit_evidence() -> None:
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    rows = load_reviews()

    historical = [
        review
        for review in rows
        if not any(
            exact_match(review, candidate)
            for candidate in candidates["records"]
        )
    ]

    assert len(historical) == 7
    assert all(row["decision"] == "revise" for row in historical)
    assert {
        row["source_record_id"] for row in historical
    }.issuperset(
        {
            "hulk_mrj_heart_comics",
            "venom_alpha_af328_ancient",
        }
    )


def test_failed_candidates_preserve_actionable_failure_evidence() -> None:
    rows = load_reviews()
    revise = [row for row in rows if row["decision"] == "revise"]

    assert len(revise) == 7
    for row in revise:
        assert row["notes"]
        assert any(value is False for value in row["checks"].values())
        assert row["model_input_allowed"] is False
