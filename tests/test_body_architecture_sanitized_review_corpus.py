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


def test_canonical_sanitized_review_corpus_is_exact_hash_valid() -> None:
    tool = load_tool()
    candidates = tool.load_candidates(CANDIDATES)
    rows = load_reviews()

    assert len(rows) == 15
    assert sum(row["decision"] == "approved" for row in rows) == 8
    assert sum(row["decision"] == "revise" for row in rows) == 7

    for row in rows:
        assert tool.validate_record(row, candidates) == []
        assert row["model_input_allowed"] is (
            row["decision"] == "approved"
        )


def test_every_generated_candidate_has_exactly_one_review() -> None:
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    rows = load_reviews()

    candidate_ids = {
        row["source_record_id"] for row in candidates["records"]
    }
    review_ids = [row["source_record_id"] for row in rows]

    assert set(review_ids) == candidate_ids
    assert len(review_ids) == len(set(review_ids))


def test_failed_candidates_preserve_actionable_failure_evidence() -> None:
    rows = load_reviews()
    revise = [row for row in rows if row["decision"] == "revise"]

    assert revise
    for row in revise:
        assert row["notes"]
        assert any(value is False for value in row["checks"].values())
        assert row["model_input_allowed"] is False
