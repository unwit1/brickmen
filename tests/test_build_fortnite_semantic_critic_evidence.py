from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "build_fortnite_semantic_critic_evidence.py"
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
OUTPUT = DATA / "fortnite-semantic-critic-evidence-v1.jsonl"
SUMMARY = DATA / "fortnite-semantic-critic-evidence-v1-summary.json"


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_fortnite_semantic_critic_evidence",
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


def test_critic_evidence_is_explicit_and_noncanonical() -> None:
    tool = load_tool()
    critics, summary = tool.build()

    assert summary["submitted_reviews"] >= 200
    assert summary["unique_translation_pairs"] >= 200
    assert summary["critic_evidence_items"] > 0
    assert summary["training_eligible_items"] == 0
    assert summary["canonical_eligible_items"] == 0

    for row in critics:
        assert row["decision"] in tool.DECISION_CATEGORY
        assert row["critic_category"] == tool.DECISION_CATEGORY[row["decision"]]
        assert row["decision"] not in {"preserved", "not_applicable"}
        assert row["canonical_eligible"] is False
        assert row["training_eligible"] is False
        assert row["requires_independent_review_and_adjudication"] is True
        assert row["evidence"]["claims_unobserved_surfaces"] is False
        assert "measurement_signal_refs" not in row
        assert row["critic_id"] == tool.critic_id(row)


def test_checked_in_critic_corpus_matches_builder() -> None:
    tool = load_tool()
    expected, expected_summary = tool.build()
    assert load_jsonl(OUTPUT) == expected
    assert json.loads(SUMMARY.read_text(encoding="utf-8")) == expected_summary


def test_critic_ids_are_unique() -> None:
    tool = load_tool()
    critics, _ = tool.build()
    ids = [row["critic_id"] for row in critics]
    assert len(ids) == len(set(ids))
