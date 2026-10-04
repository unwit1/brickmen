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
CANDIDATES = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "exact-release-multiview-source-candidates-v1.json"
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


def load_candidates() -> list[dict]:
    return list(json.loads(CANDIDATES.read_text(encoding="utf-8"))["candidates"])


def test_gap_queue_never_infers_hidden_content() -> None:
    tool = load_tool()
    result = tool.build(load_reference_sets(), load_candidates())

    assert result["source_reference_sets"] == 23
    assert result["queued_reference_sets"] == 23
    assert all(
        target["content_inferred"] is False
        for item in result["queue"]
        for target in item["targets"]
    )


def test_known_complete_torso_pairs_do_not_request_torso_rear() -> None:
    tool = load_tool()
    result = tool.build(load_reference_sets(), load_candidates())
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
    result = tool.build(load_reference_sets(), load_candidates())
    by_id = {item["reference_set_id"]: item for item in result["queue"]}

    johnny = by_id["refset-flatart-adv010-fig-000359"]
    targets = {target["target"] for target in johnny["targets"]}
    assert "head_rear_evidence" in targets
    assert "torso_rear_evidence" in targets
    assert "physical_left_side_view" in targets
    assert "physical_right_side_view" in targets


def test_checked_in_gap_queue_matches_generator() -> None:
    tool = load_tool()
    expected = tool.build(load_reference_sets(), load_candidates())
    actual = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert actual == expected


def test_seeded_multiview_candidates_are_exact_release_and_noncanonical() -> None:
    candidate_path = (
        ROOT
        / "knowledge"
        / "libraries"
        / "lego-minifigure-customs"
        / "data"
        / "exact-release-multiview-source-candidates-v1.json"
    )
    doc = json.loads(candidate_path.read_text(encoding="utf-8"))
    refs = {row["reference_set_id"]: row for row in load_reference_sets()}

    assert len(doc["candidates"]) >= 2
    for candidate in doc["candidates"]:
        ref = refs[candidate["reference_set_id"]]
        assert candidate["identifiers"] == ref["identifiers"]
        assert candidate["byte_verified"] is True
        assert candidate["canonical_eligible"] is False
        assert candidate["training_eligible"] is False
        assert isinstance(candidate["exact_image_sha256"], str)
        assert len(candidate["exact_image_sha256"]) == 64
        assert candidate["visual_review"]["status"] == "verified_rear_view"
        assert candidate["visual_review"]["image_sha256"] == candidate["exact_image_sha256"]


def test_verified_rear_views_close_only_directly_satisfied_targets() -> None:
    tool = load_tool()
    result = tool.build(load_reference_sets(), load_candidates())
    by_id = {item["reference_set_id"]: item for item in result["queue"]}

    for ref_id in (
        "refset-flatart-col106-fig-000935",
        "refset-flatart-sw0070-fig-003522",
    ):
        item = by_id[ref_id]
        remaining = {target["target"] for target in item["targets"]}
        satisfied = set(item["satisfied_targets_from_reviewed_evidence"])
        assert "torso_rear_evidence" in satisfied
        assert "lower_body_rear_or_side_evidence" in satisfied
        assert "torso_rear_evidence" not in remaining
        assert "lower_body_rear_or_side_evidence" not in remaining
        assert "head_rear_evidence" in remaining
        assert "physical_left_side_view" in remaining
        assert "physical_right_side_view" in remaining
        assert all(e["image_sha256"] for e in item["reviewed_evidence"])


def test_reviewed_rear_evidence_reduces_current_gap_counts() -> None:
    tool = load_tool()
    result = tool.build(load_reference_sets(), load_candidates())
    assert result["reviewed_reference_sets"] == 2
    assert result["reviewed_satisfied_target_counts"] == {
        "lower_body_rear_or_side_evidence": 2,
        "torso_rear_evidence": 2,
    }
    assert result["target_counts"]["torso_rear_evidence"] == 13
    assert result["target_counts"]["lower_body_rear_or_side_evidence"] == 5
