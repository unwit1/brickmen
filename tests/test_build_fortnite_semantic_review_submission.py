from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
BATCH_DIR = DATA / "semantic-review-batches"
TOOL = ROOT / "tools" / "knowledge" / "build_fortnite_semantic_review_submission.py"
BATCH = BATCH_DIR / "fortnite-first-review-batch-0006.json"
DECISIONS = BATCH_DIR / "fortnite-first-review-batch-0006-gpt56sol-decisions.json.gz"
BATCH7 = BATCH_DIR / "fortnite-first-review-batch-0007.json"
DECISIONS7 = BATCH_DIR / "fortnite-first-review-batch-0007-gpt56sol-decisions.json.gz"
BATCH8 = BATCH_DIR / "fortnite-first-review-batch-0008.json"
DECISIONS8 = BATCH_DIR / "fortnite-first-review-batch-0008-gpt56sol-decisions.json.gz"
BATCH9 = BATCH_DIR / "fortnite-first-review-batch-0009.json"
DECISIONS9 = BATCH_DIR / "fortnite-first-review-batch-0009-gpt56sol-decisions.json.gz"
BATCH10 = BATCH_DIR / "fortnite-first-review-batch-0010.json"
DECISIONS10 = BATCH_DIR / "fortnite-first-review-batch-0010-gpt56sol-decisions.json.gz"


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_fortnite_semantic_review_submission",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_batch_0006_compact_decisions_compile_to_valid_canonical_reviews() -> None:
    tool = load_tool()
    records, summary = tool.build_submission(BATCH, DECISIONS)

    assert len(records) == 25
    assert len({row["translation_pair_id"] for row in records}) == 25
    assert len({row["review_id"] for row in records}) == 25
    assert summary["submitted_reviews"] == 25
    assert summary["unique_pairs"] == 25
    assert summary["total_annotations"] == 100
    assert summary["exact_source_hashes"] == 25
    assert summary["exact_lego_hashes"] == 25
    assert summary["training_eligible"] == 0
    assert summary["workflow_run_id"] == 37151433717
    assert summary["workflow_artifact_id"] == 11284491078

    for review in records:
        assert review["reviewer"] == {
            "reviewer_type": "model",
            "reviewer_id": "openai_chatgpt_visual_review_batch6",
            "model_id": "GPT-5.6 Sol",
            "model_revision": "2026-10-03",
            "review_role": "reviewer",
        }
        assert review["review_status"] == "submitted"
        assert review["adjudicates_review_ids"] == []
        assert review["review_id"] == tool.canonical_review_id(review)
        assert tool.validate_record(review) == []
        assert tool.annotation_count(review) == 4
        assert review["evidence"]["claims_unobserved_surfaces"] is False
        direct = next(
            item
            for item in review["provenance"]
            if item.get("source") == "direct_visual_inspection_of_hash_verified_pair"
        )
        assert direct["source_image_sha256"] == review["evidence"]["source_image_sha256"]
        assert direct["lego_image_sha256"] == review["evidence"]["lego_image_sha256"]


def test_compact_decisions_reject_pair_set_drift(tmp_path: Path) -> None:
    tool = load_tool()
    decisions = tool.load_json(DECISIONS)
    decisions["records"] = decisions["records"][:-1]
    broken = tmp_path / "decisions.json"
    import json
    broken.write_text(json.dumps(decisions), encoding="utf-8")

    try:
        tool.build_submission(BATCH, broken)
    except ValueError as exc:
        assert "decision pair set mismatch" in str(exc)
    else:
        raise AssertionError("pair-set drift should fail compilation")


def test_batch_0007_compact_decisions_compile_to_valid_canonical_reviews() -> None:
    tool = load_tool()
    records, summary = tool.build_submission(BATCH7, DECISIONS7)

    assert len(records) == 25
    assert len({row["translation_pair_id"] for row in records}) == 25
    assert len({row["review_id"] for row in records}) == 25
    assert summary["submitted_reviews"] == 25
    assert summary["unique_pairs"] == 25
    assert summary["total_annotations"] == 100
    assert summary["exact_source_hashes"] == 25
    assert summary["exact_lego_hashes"] == 25
    assert summary["training_eligible"] == 0
    assert summary["workflow_run_id"] == 37154311505
    assert summary["workflow_artifact_id"] == 11284279940

    for review in records:
        assert review["reviewer"] == {
            "reviewer_type": "model",
            "reviewer_id": "openai_chatgpt_visual_review_batch7",
            "model_id": "GPT-5.6 Sol",
            "model_revision": "2026-10-03",
            "review_role": "reviewer",
        }
        assert review["review_status"] == "submitted"
        assert review["adjudicates_review_ids"] == []
        assert review["review_id"] == tool.canonical_review_id(review)
        assert tool.validate_record(review) == []
        assert tool.annotation_count(review) == 4
        assert review["evidence"]["claims_unobserved_surfaces"] is False
        direct = next(
            item
            for item in review["provenance"]
            if item.get("source") == "direct_visual_inspection_of_hash_verified_pair"
        )
        assert direct["source_image_sha256"] == review["evidence"]["source_image_sha256"]
        assert direct["lego_image_sha256"] == review["evidence"]["lego_image_sha256"]


def test_batch_0008_compact_decisions_compile_to_valid_canonical_reviews() -> None:
    tool = load_tool()
    records, summary = tool.build_submission(BATCH8, DECISIONS8)

    assert len(records) == 25
    assert len({row["translation_pair_id"] for row in records}) == 25
    assert len({row["review_id"] for row in records}) == 25
    assert summary["submitted_reviews"] == 25
    assert summary["unique_pairs"] == 25
    assert summary["total_annotations"] == 100
    assert summary["exact_source_hashes"] == 25
    assert summary["exact_lego_hashes"] == 25
    assert summary["training_eligible"] == 0
    assert summary["workflow_run_id"] == 37155139511
    assert summary["workflow_artifact_id"] == 11286060233

    for review in records:
        assert review["reviewer"] == {
            "reviewer_type": "model",
            "reviewer_id": "openai_chatgpt_visual_review_batch8",
            "model_id": "GPT-5.6 Sol",
            "model_revision": "2026-10-03",
            "review_role": "reviewer",
        }
        assert review["review_status"] == "submitted"
        assert review["adjudicates_review_ids"] == []
        assert review["review_id"] == tool.canonical_review_id(review)
        assert tool.validate_record(review) == []
        assert tool.annotation_count(review) == 4
        assert review["evidence"]["claims_unobserved_surfaces"] is False
        direct = next(
            item
            for item in review["provenance"]
            if item.get("source") == "direct_visual_inspection_of_hash_verified_pair"
        )
        assert direct["source_image_sha256"] == review["evidence"]["source_image_sha256"]
        assert direct["lego_image_sha256"] == review["evidence"]["lego_image_sha256"]


def test_batch_0009_compact_decisions_compile_to_valid_canonical_reviews() -> None:
    tool = load_tool()
    records, summary = tool.build_submission(BATCH9, DECISIONS9)

    assert len(records) == 25
    assert len({row["translation_pair_id"] for row in records}) == 25
    assert len({row["review_id"] for row in records}) == 25
    assert summary["submitted_reviews"] == 25
    assert summary["unique_pairs"] == 25
    assert summary["total_annotations"] == 100
    assert summary["exact_source_hashes"] == 25
    assert summary["exact_lego_hashes"] == 25
    assert summary["training_eligible"] == 0
    assert summary["workflow_run_id"] == 37169949760
    assert summary["workflow_artifact_id"] == 11290956141

    for review in records:
        assert review["reviewer"] == {
            "reviewer_type": "model",
            "reviewer_id": "openai_chatgpt_visual_review_batch9",
            "model_id": "GPT-5.6 Sol",
            "model_revision": "2026-10-03",
            "review_role": "reviewer",
        }
        assert review["review_status"] == "submitted"
        assert review["adjudicates_review_ids"] == []
        assert review["review_id"] == tool.canonical_review_id(review)
        assert tool.validate_record(review) == []
        assert tool.annotation_count(review) == 4
        assert review["evidence"]["claims_unobserved_surfaces"] is False
        direct = next(
            item
            for item in review["provenance"]
            if item.get("source") == "direct_visual_inspection_of_hash_verified_pair"
        )
        assert direct["source_image_sha256"] == review["evidence"]["source_image_sha256"]
        assert direct["lego_image_sha256"] == review["evidence"]["lego_image_sha256"]


def test_batch_0010_compact_decisions_compile_to_valid_canonical_reviews() -> None:
    tool = load_tool()
    records, summary = tool.build_submission(BATCH10, DECISIONS10)

    assert len(records) == 25
    assert len({row["translation_pair_id"] for row in records}) == 25
    assert len({row["review_id"] for row in records}) == 25
    assert summary["submitted_reviews"] == 25
    assert summary["unique_pairs"] == 25
    assert summary["total_annotations"] == 100
    assert summary["exact_source_hashes"] == 25
    assert summary["exact_lego_hashes"] == 25
    assert summary["training_eligible"] == 0
    assert summary["workflow_run_id"] == 37170592535
    assert summary["workflow_artifact_id"] == 11290094924

    for review in records:
        assert review["reviewer"] == {
            "reviewer_type": "model",
            "reviewer_id": "openai_chatgpt_visual_review_batch10",
            "model_id": "GPT-5.6 Sol",
            "model_revision": "2026-10-03",
            "review_role": "reviewer",
        }
        assert review["review_status"] == "submitted"
        assert review["adjudicates_review_ids"] == []
        assert review["review_id"] == tool.canonical_review_id(review)
        assert tool.validate_record(review) == []
        assert tool.annotation_count(review) == 4
        assert review["evidence"]["claims_unobserved_surfaces"] is False
        direct = next(
            item
            for item in review["provenance"]
            if item.get("source") == "direct_visual_inspection_of_hash_verified_pair"
        )
        assert direct["source_image_sha256"] == review["evidence"]["source_image_sha256"]
        assert direct["lego_image_sha256"] == review["evidence"]["lego_image_sha256"]
