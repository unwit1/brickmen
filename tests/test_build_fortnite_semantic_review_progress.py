from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

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
    assert result["complete_first_review_batch_count"] == 10
    assert result["submitted_reviewer_records"] == 250
    assert result["submitted_first_review_pairs"] == 250
    assert result["remaining_first_review_pairs"] == 494
    assert result["submitted_semantic_annotations"] == 1017
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
