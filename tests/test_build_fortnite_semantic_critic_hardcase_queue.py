from __future__ import annotations

import importlib.util
import json
from pathlib import Path

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


def test_hardcase_builder_is_deterministic() -> None:
    tool = load_tool()
    rows = load_jsonl(INPUT)
    first = tool.build(rows)
    second = tool.build(rows)
    assert first == second
