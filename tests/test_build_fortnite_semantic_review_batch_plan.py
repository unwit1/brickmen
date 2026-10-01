from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "build_fortnite_semantic_review_batch_plan.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_fortnite_semantic_review_batch_plan",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_first_review_batch_plan_baseline() -> None:
    tool = load_tool()
    result = tool.build_plan()

    assert result["eligible_records"] == 744
    assert result["batch_count"] == 30
    assert result["batch_size"] == 25
    assert result["materialized_batch_count"] >= 2
    assert result["planned_batch_count"] == 30 - result["materialized_batch_count"]

    first = result["batches"][0]
    last = result["batches"][-1]
    assert first["batch_index"] == 1
    assert first["batch_id"] == "fortnite-review-first_review-056fd3e0773faee9"
    assert first["selected_records"] == 25
    assert first["materialized"] is True
    second = result["batches"][1]
    assert second["batch_id"] == "fortnite-review-first_review-dde51a69c8ff5a91"
    assert second["materialized"] is True
    assert second["first_translation_pair_id"] == "fortnitepair-1c84a038477fa48199de67cb"
    assert second["last_translation_pair_id"] == "fortnitepair-fb6013fe4fa25062ef7d8c95"
    assert last["batch_index"] == 30
    assert last["selected_records"] == 19
    assert last["offset"] == 725


def test_batch_plan_partitions_high_priority_pairs_without_overlap() -> None:
    tool = load_tool()
    result = tool.build_plan()

    assert sum(row["selected_records"] for row in result["batches"]) == 744
    offsets = [row["offset"] for row in result["batches"]]
    assert offsets == list(range(0, 744, 25))
    assert len({row["batch_id"] for row in result["batches"]}) == 30


def test_checked_in_batch_plan_matches_generator() -> None:
    tool = load_tool()
    expected = tool.build_plan()
    plan_path = (
        Path(__file__).resolve().parents[1]
        / "knowledge"
        / "libraries"
        / "lego-minifigure-customs"
        / "data"
        / "semantic-review-batches"
        / "fortnite-first-review-batch-plan.json"
    )
    actual = json.loads(plan_path.read_text(encoding="utf-8"))

    assert actual == expected


def test_batch_plan_supports_direct_script_execution() -> None:
    result = subprocess.run(
        [sys.executable, str(TOOL), "--help"],
        cwd=TOOL.parents[2],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "--min-priority-score" in result.stdout
