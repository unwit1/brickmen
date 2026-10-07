from __future__ import annotations

import importlib.util
import json
import copy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "build_fortnite_semantic_review_progress.py"
PROGRESS = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "semantic-review-batches"
    / "fortnite-semantic-review-progress.json"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_fortnite_semantic_review_progress",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_fortnite_semantic_review_progress_baseline() -> None:
    tool = load_tool()
    result = tool.build_progress()

    assert result["eligible_pairs"] == 744
    plan = json.loads((PROGRESS.parent / "fortnite-first-review-batch-plan.json").read_text(encoding="utf-8"))
    assert result["materialized_batch_count"] == plan["materialized_batch_count"]
    assert result["complete_first_review_batch_count"] == 16
    assert result["submitted_reviewer_records"] == 400
    assert result["submitted_first_review_pairs"] == 400
    assert result["remaining_first_review_pairs"] == 344
    assert result["submitted_semantic_annotations"] == 1800
    assert result["independently_double_reviewed_pairs"] == 0
    assert result["adjudicated_pairs"] == 0
    assert result["invalid_review_records"] == 0
    assert result["review_pairs_outside_materialized_plan"] == []

    if result["materialized_batch_count"] > result["complete_first_review_batch_count"]:
        assert result["next_materialized_incomplete_batch"]["batch_index"] == result["complete_first_review_batch_count"] + 1
    else:
        assert result["next_materialized_incomplete_batch"] is None
    if result["materialized_batch_count"] < result["plan_batch_count"]:
        assert result["next_planned_batch"]["batch_index"] == result["materialized_batch_count"] + 1


def test_progress_tracks_each_materialized_batch_without_manual_counts() -> None:
    tool = load_tool()
    result = tool.build_progress()

    materialized = [row for row in result["batch_progress"] if row["materialized"]]
    assert len(materialized) == result["materialized_batch_count"]
    assert [row["batch_index"] for row in materialized] == list(
        range(1, result["materialized_batch_count"] + 1)
    )

    complete_count = result["complete_first_review_batch_count"]
    assert all(row["first_review_complete"] for row in materialized[:complete_count])
    assert all(not row["first_review_complete"] for row in materialized[complete_count:])


def test_checked_in_progress_manifest_matches_generator() -> None:
    tool = load_tool()
    expected = tool.build_progress()
    actual = json.loads(PROGRESS.read_text(encoding="utf-8"))
    assert actual == expected


def test_progress_tool_supports_direct_script_execution() -> None:
    result = subprocess.run(
        [sys.executable, str(TOOL), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "--review-dir" in result.stdout


def synthetic_progress(tmp_path, monkeypatch, second_id="reviewer-beta", mutate=None):
    tool = load_tool()
    sample = PROGRESS.parent / "fortnite-first-review-batch-0011-codex-gpt6-submitted.jsonl"
    first = json.loads(sample.read_text(encoding="utf-8").splitlines()[0])
    first["reviewer"]["reviewer_id"] = "reviewer-alpha"
    second = copy.deepcopy(first)
    second["reviewer"]["reviewer_id"] = second_id
    if mutate:
        mutate(second)
    from tools.knowledge.validate_fortnite_semantic_reviews import canonical_review_id
    for row in (first, second):
        row["review_id"] = canonical_review_id(row)
    pair = first["translation_pair_id"]
    batch = tmp_path / "batch.json"
    batch.write_text(json.dumps({"items": [{"translation_pair_id": pair}]}), encoding="utf-8")
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({
        "eligible_records": 1, "batch_count": 1, "materialized_batch_count": 1,
        "batches": [{"batch_index": 1, "batch_id": "test", "path": "batch.json", "materialized": True, "selected_records": 1}],
    }), encoding="utf-8")
    (tmp_path / "test-submitted.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in (first, second)), encoding="utf-8"
    )
    monkeypatch.setattr(tool, "ROOT", tmp_path)
    return tool.build_progress(plan, tmp_path)


def test_double_review_requires_matching_exact_evidence(tmp_path, monkeypatch):
    result = synthetic_progress(tmp_path, monkeypatch)
    assert result["independently_double_reviewed_pairs"] == 1
    assert result["double_review_evidence_blocked_pairs"] == 0
    assert result["first_review_pairs_with_exact_evidence"] == 1


@pytest.mark.parametrize("field,value", [
    ("source_image_sha256", "f" * 64),
    ("lego_image_sha256", "e" * 64),
    ("source_image_sha256", None),
    ("evidence_scope", "wide_pair"),
])
def test_progress_exposes_incomparable_second_reviews(tmp_path, monkeypatch, field, value):
    result = synthetic_progress(tmp_path, monkeypatch, mutate=lambda row: row["evidence"].update({field: value}))
    assert result["submitted_first_review_pairs"] == 1
    assert result["distinct_reviewer_pairs"] == 1
    assert result["independently_double_reviewed_pairs"] == 0
    assert result["double_review_evidence_blocked_pairs"] == 1
    assert len(result["evidence_blocked_double_review_pair_ids"]) == 1
    assert result["batch_progress"][0]["independently_double_reviewed_pairs"] == 0


def test_reviewer_case_and_whitespace_cannot_inflate_independence(tmp_path, monkeypatch):
    result = synthetic_progress(tmp_path, monkeypatch, second_id=" Reviewer-ALPHA ")
    assert result["submitted_reviewer_records"] == 2
    assert result["distinct_reviewer_pairs"] == 0
    assert result["independently_double_reviewed_pairs"] == 0
