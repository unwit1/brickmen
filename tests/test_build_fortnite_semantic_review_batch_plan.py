from __future__ import annotations

import importlib.util
import json
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
    assert result["materialized_batch_count"] == 1
    assert result["planned_batch_count"] == 29

    first = result["batches"][0]
    last = result["batches"][-1]
    assert first["batch_index"] == 1
    assert first["batch_id"] == "fortnite-review-first_review-056fd3e0773faee9"
    assert first["selected_records"] == 25
    assert first["materialized"] is True
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
