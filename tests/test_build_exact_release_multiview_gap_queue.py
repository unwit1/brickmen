from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "build_exact_release_multiview_gap_queue.py"
INPUT = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "exact-release-flat-art-reference-sets-v1.jsonl"
)
OUTPUT = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "exact-release-multiview-gap-queue-v1.json"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_exact_release_multiview_gap_queue",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_reference_sets() -> list[dict]:
    return [
        json.loads(line)
        for line in INPUT.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_gap_queue_never_infers_hidden_content() -> None:
    tool = load_tool()
    result = tool.build(load_reference_sets())

    assert result["source_reference_sets"] == 23
    assert result["queued_reference_sets"] == 23
    assert all(
        target["content_inferred"] is False
        for item in result["queue"]
        for target in item["targets"]
    )


def test_known_complete_torso_pairs_do_not_request_torso_rear() -> None:
    tool = load_tool()
    result = tool.build(load_reference_sets())
    by_id = {item["reference_set_id"]: item for item in result["queue"]}

    wonder_woman = by_id["refset-flatart-sh0004-fig-000008"]
    assert "torso_rear_evidence" not in {
        target["target"] for target in wonder_woman["targets"]
    }

    superman = by_id["refset-flatart-sh0003-fig-000227"]
    assert "torso_rear_evidence" not in {
        target["target"] for target in superman["targets"]
    }


def test_front_only_release_prioritizes_missing_counterparts() -> None:
    tool = load_tool()
    result = tool.build(load_reference_sets())
    by_id = {item["reference_set_id"]: item for item in result["queue"]}

    johnny = by_id["refset-flatart-adv010-fig-000359"]
    targets = {target["target"] for target in johnny["targets"]}
    assert "head_rear_evidence" in targets
    assert "torso_rear_evidence" in targets
    assert "physical_left_side_view" in targets
    assert "physical_right_side_view" in targets


def test_checked_in_gap_queue_matches_generator() -> None:
    tool = load_tool()
    expected = tool.build(load_reference_sets())
    actual = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert actual == expected
