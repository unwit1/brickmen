from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
BATCH = DATA / "semantic-review-batches" / "fortnite-first-review-batch-0002.json"
REVIEWS = DATA / "semantic-review-batches" / "fortnite-first-review-batch-0002-gpt56sol-submitted.jsonl"
SUMMARY = DATA / "semantic-review-batches" / "fortnite-first-review-batch-0002-gpt56sol-summary.json"
VALIDATOR = ROOT / "tools" / "knowledge" / "validate_fortnite_semantic_reviews.py"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_fortnite_semantic_reviews",
        VALIDATOR,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_reviews() -> list[dict]:
    return [
        json.loads(line)
        for line in REVIEWS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_batch_0002_model_reviews_are_valid_hash_bound_submissions() -> None:
    validator = load_validator()
    batch = json.loads(BATCH.read_text(encoding="utf-8"))
    reviews = load_reviews()
    by_pair = {row["translation_pair_id"]: row for row in reviews}
    batch_by_pair = {row["translation_pair_id"]: row for row in batch["items"]}

    assert len(reviews) == 25
    assert len(by_pair) == 25
    assert set(by_pair) == set(batch_by_pair)

    for pair_id, review in by_pair.items():
        assert validator.validate_record(review) == []
        assert review["review_id"] == validator.canonical_review_id(review)
        assert review["review_status"] == "submitted"
        assert review["adjudicates_review_ids"] == []
        assert review["reviewer"] == {
            "reviewer_type": "model",
            "reviewer_id": "openai_chatgpt_visual_review_batch2",
            "model_id": "GPT-5.6 Sol",
            "model_revision": "2026-10-01",
            "review_role": "reviewer",
        }
        assert review["evidence"]["source_image_url"] == batch_by_pair[pair_id]["source_image_url"]
        assert review["evidence"]["lego_image_url"] == batch_by_pair[pair_id]["lego_image_url"]
        assert len(review["evidence"]["source_image_sha256"]) == 64
        assert len(review["evidence"]["lego_image_sha256"]) == 64
        assert review["evidence"]["claims_unobserved_surfaces"] is False
        assert validator.annotation_count(review) >= 3


def test_batch_0002_reviews_remain_noncanonical_until_adjudication() -> None:
    reviews = load_reviews()
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    assert all(row["review_status"] == "submitted" for row in reviews)
    assert all(row["reviewer"]["review_role"] == "reviewer" for row in reviews)
    assert summary["submitted_reviews"] == 25
    assert summary["unique_pairs"] == 25
    assert summary["total_annotations"] == 100
    assert summary["training_eligible"] == 0
    assert summary["workflow_run_id"] == 36888310826
    assert summary["workflow_artifact_id"] == 11174174737
