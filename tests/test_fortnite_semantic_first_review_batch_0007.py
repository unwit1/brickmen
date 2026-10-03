from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
BATCH_DIR = DATA / "semantic-review-batches"
BATCH = BATCH_DIR / "fortnite-first-review-batch-0007.json"
DECISIONS = BATCH_DIR / "fortnite-first-review-batch-0007-gpt56sol-decisions.json.gz"
REVIEWS = BATCH_DIR / "fortnite-first-review-batch-0007-gpt56sol-submitted.jsonl"
SUMMARY = BATCH_DIR / "fortnite-first-review-batch-0007-gpt56sol-summary.json"
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


def git_blob_sha1(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def load_reviews() -> list[dict]:
    return [
        json.loads(line)
        for line in REVIEWS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_batch_0007_compact_decision_evidence_is_byte_locked_and_readable() -> None:
    assert git_blob_sha1(DECISIONS) == "577f43c22a1d55a319f3b5c755d2123995ca92b9"
    with gzip.open(DECISIONS, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)

    assert payload["batch_id"] == "fortnite-review-first_review-ffb51cb7d7edc343"
    assert len(payload["records"]) == 25
    assert payload["workflow_run_id"] == 37152595877
    assert payload["workflow_artifact_id"] == 11284218022


def test_batch_0007_model_reviews_are_valid_hash_bound_submissions() -> None:
    validator = load_validator()
    batch = json.loads(BATCH.read_text(encoding="utf-8"))
    reviews = load_reviews()
    by_pair = {row["translation_pair_id"]: row for row in reviews}
    batch_by_pair = {row["translation_pair_id"]: row for row in batch["items"]}

    assert len(reviews) == 25
    assert len(by_pair) == 25
    assert len({row["review_id"] for row in reviews}) == 25
    assert set(by_pair) == set(batch_by_pair)

    for pair_id, review in by_pair.items():
        assert validator.validate_record(review) == []
        assert review["review_id"] == validator.canonical_review_id(review)
        assert review["review_status"] == "submitted"
        assert review["adjudicates_review_ids"] == []
        assert review["reviewer"] == {
            "reviewer_type": "model",
            "reviewer_id": "openai_chatgpt_visual_review_batch7",
            "model_id": "GPT-5.6 Sol",
            "model_revision": "2026-10-03",
            "review_role": "reviewer",
        }
        assert review["evidence"]["source_image_url"] == batch_by_pair[pair_id]["source_image_url"]
        assert review["evidence"]["lego_image_url"] == batch_by_pair[pair_id]["lego_image_url"]
        assert len(review["evidence"]["source_image_sha256"]) == 64
        assert len(review["evidence"]["lego_image_sha256"]) == 64
        assert review["evidence"]["claims_unobserved_surfaces"] is False
        direct = next(
            item
            for item in review["provenance"]
            if item.get("source") == "direct_visual_inspection_of_hash_verified_pair"
        )
        assert direct["source_image_sha256"] == review["evidence"]["source_image_sha256"]
        assert direct["lego_image_sha256"] == review["evidence"]["lego_image_sha256"]
        assert validator.annotation_count(review) == 4


def test_batch_0007_reviews_remain_noncanonical_until_independent_adjudication() -> None:
    reviews = load_reviews()
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    assert all(row["review_status"] == "submitted" for row in reviews)
    assert all(row["reviewer"]["review_role"] == "reviewer" for row in reviews)
    assert summary["submitted_reviews"] == 25
    assert summary["unique_pairs"] == 25
    assert summary["total_annotations"] == 100
    assert summary["training_eligible"] == 0
    assert summary["workflow_run_id"] == 37152595877
    assert summary["workflow_artifact_id"] == 11284218022
    assert "independent second review" in summary["policy"]
