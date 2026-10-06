from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "build_fortnite_semantic_critic_hardcase_queue.py"
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
INPUT = DATA / "fortnite-semantic-critic-evidence-v1.jsonl"
OUTPUT = DATA / "fortnite-semantic-critic-hardcase-queue-v1.json"


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_fortnite_semantic_critic_hardcase_queue",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_hardcase_queue_is_ranked_and_noncanonical() -> None:
    tool = load_tool()
    result = tool.build(load_jsonl(INPUT))
    queue = result["queue"]

    assert result["source_critic_items"] > 0
    assert result["queued_pairs"] > 0
    assert len(queue) == result["queued_pairs"]
    assert [row["rank"] for row in queue] == list(range(1, len(queue) + 1))
    assert [row["hardcase_score"] for row in queue] == sorted(
        (row["hardcase_score"] for row in queue),
        reverse=True,
    )

    for row in queue:
        assert row["canonical_eligible"] is False
        assert row["training_eligible"] is False
        assert row["requires_independent_review_and_adjudication"] is True
        assert row["evaluation_status"] == "provisional_submitted_review_evidence"
        assert row["source_image_sha256"]
        assert row["lego_image_sha256"]


def test_source_only_omission_scores_above_plain_simplification() -> None:
    tool = load_tool()
    common = {
        "schema": "fortnite-semantic-critic-evidence/v1",
        "critic_category": "detail_compression",
        "confidence": 0.99,
        "canonical_eligible": False,
        "training_eligible": False,
        "source_review_id": "review-1",
        "source_review_file": "review.jsonl",
        "evidence": {
            "source_image_sha256": "a" * 64,
            "lego_image_sha256": "b" * 64,
        },
    }
    rows = [
        {
            **common,
            "critic_id": "critic-simple",
            "translation_pair_id": "pair-simple",
            "region": "torso",
            "feature": "small seam",
            "decision": "simplified",
            "evidence_basis": "observed_in_both",
        },
        {
            **common,
            "critic_id": "critic-omit",
            "translation_pair_id": "pair-omit",
            "region": "accessory_or_silhouette",
            "feature": "cape",
            "decision": "omitted",
            "critic_category": "feature_loss",
            "evidence_basis": "source_only",
        },
    ]
    result = tool.build(rows)
    by_pair = {row["translation_pair_id"]: row for row in result["queue"]}
    assert by_pair["pair-omit"]["hardcase_score"] > by_pair["pair-simple"]["hardcase_score"]


def test_checked_in_hardcase_queue_matches_builder() -> None:
    tool = load_tool()
    expected = tool.build(load_jsonl(INPUT))
    actual = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert actual == expected


def critic(pair, identity, decision="uncertain", basis="source_only"):
    return {"schema": "fortnite-semantic-critic-evidence/v1", "critic_id": identity,
            "translation_pair_id": pair, "source_review_id": "review-1", "source_review_file": "original.jsonl",
            "region": "lower_body", "feature": "cropped legs", "decision": decision,
            "critic_category": "review_uncertainty", "confidence": .99, "evidence_basis": basis,
            "canonical_eligible": False, "training_eligible": False,
            "evidence": {"source_image_sha256": "a" * 64, "lego_image_sha256": "b" * 64}}


def test_unpaired_uncertainty_cannot_outrank_a_visible_discrepancy():
    rows = [critic("gap", f"missing-{i}") for i in range(12)]
    rows.append(critic("visible", "eye-mismatch", basis="observed_in_both"))
    result = load_tool().build(rows)
    visible, gap = result["queue"]
    assert visible["translation_pair_id"] == "visible" and visible["hardcase_score"] > 0
    assert gap["hardcase_score"] == gap["translation_priority_item_count"] == 0
    assert gap["unpaired_uncertainty_item_count"] == gap["critic_item_count"] == 12
    assert len(gap["unpaired_uncertainty_critic_ids"]) == 12
    assert result["pairs_with_source_only_loss"] == 0
    assert result["pairs_with_source_only_evidence"] == 1
    assert gap["training_eligible"] is False


def test_adding_unpaired_uncertainty_does_not_change_translation_priority():
    tool = load_tool()
    visible = critic("same", "visible", decision="simplified", basis="observed_in_both")
    baseline = tool.build([visible])["queue"][0]
    mixed = tool.build([visible, critic("same", "cropped")])["queue"][0]
    assert mixed["hardcase_score"] == baseline["hardcase_score"]
    assert mixed["translation_priority_item_count"] == baseline["translation_priority_item_count"]
    assert mixed["critic_item_count"] == 2


def test_duplicate_evidence_counts_once_and_preserves_all_source_links():
    tool = load_tool()
    row = critic("same", "unique", decision="omitted")
    copy = deepcopy(row);copy["source_review_file"] = "copied.jsonl"
    baseline = tool.build([row])["queue"][0]
    result = tool.build([row, copy])
    pair = result["queue"][0]
    assert pair["hardcase_score"] == baseline["hardcase_score"]
    assert pair["critic_item_count"] == result["unique_critic_items"] == 1
    assert pair["source_review_files"] == ["copied.jsonl", "original.jsonl"]
    assert result["duplicate_critic_items_ignored"] == 1
    assert result["pairs_with_source_only_loss"] == 1


def test_conflicting_duplicate_evidence_is_not_silently_discarded():
    first = critic("same", "duplicate")
    conflicting = deepcopy(first);conflicting["evidence"]["lego_image_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="conflicting duplicate critic_id"):
        load_tool().build([first, conflicting])


def test_equal_priority_is_not_tiebroken_by_unpaired_gap_volume():
    first = critic("pair-a", "a", decision="simplified", basis="observed_in_both")
    second = critic("pair-b", "b", decision="simplified", basis="observed_in_both")
    rows = [first, second, *(critic("pair-b", f"gap-{i}") for i in range(10))]
    assert [row["translation_pair_id"] for row in load_tool().build(rows)["queue"]] == ["pair-a", "pair-b"]


def test_low_confidence_unpaired_gap_is_reported_without_score_bonus():
    row = critic("same", "gap");row["confidence"] = .5
    result = load_tool().build([row])["queue"][0]
    assert result["lower_confidence_item_count"] == 1
    assert result["lower_confidence_priority_item_count"] == result["hardcase_score"] == 0


def test_missing_critic_identity_cannot_bypass_deduplication():
    row = critic("same", "");
    with pytest.raises(ValueError, match="missing critic_id"):
        load_tool().build([row])
