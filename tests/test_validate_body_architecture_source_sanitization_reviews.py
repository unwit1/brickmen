from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = (
    ROOT
    / "tools"
    / "knowledge"
    / "validate_body_architecture_source_sanitization_reviews.py"
)
DATA = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "validate_body_architecture_source_sanitization_reviews",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_source_sanitization_reviews_validate_complete() -> None:
    tool = load_tool()
    result = tool.validate_review_set(
        tool.load_json(
            DATA / "body-architecture-benchmark-sanitization-reviews.json"
        ),
        tool.load_json(
            DATA / "body-architecture-benchmark-sanitization-queue.json"
        ),
    )

    assert result["valid"] is True
    assert result["review_count"] == 27
    assert result["approved_raw"] == 4
    assert result["sanitization_required"] == 23
    assert result["queue_cases"] == 27
    assert result["unreviewed_queue_cases"] == []
    assert result["reviewed_unknown_cases"] == []


def test_challenge_empty_review_set_is_valid_but_incomplete() -> None:
    tool = load_tool()
    result = tool.validate_review_set(
        tool.load_json(
            DATA
            / "body-architecture-recognition-challenge-sanitization-reviews-v1.json"
        ),
        tool.load_json(
            DATA
            / "body-architecture-recognition-challenge-sanitization-queue-v1.json"
        ),
    )

    assert result["valid"] is True
    assert result["review_count"] == 0
    assert result["queue_cases"] == 8
    assert len(result["unreviewed_queue_cases"]) == 8


def test_approved_raw_fails_closed_on_leakage() -> None:
    tool = load_tool()
    source_hash = "a" * 64
    queue = {
        "queue": [
            {
                "source_record_id": "test",
                "source": {
                    "source_id": "source-test",
                    "source_file_sha256": source_hash,
                },
            }
        ]
    }
    reviews = {
        "reviewer": {
            "reviewer_id": "reviewer-a",
            "reviewer_type": "human",
            "review_method": "visual",
        },
        "reviews": [
            {
                "source_record_id": "test",
                "source_id": "source-test",
                "source_file_sha256": source_hash,
                "status": "approved_raw",
                "identity_match": True,
                "primary_view": "front",
                "primary_figure_complete": True,
                "visible_text_leakage": ["release_or_sku_code"],
                "visual_confounders": [],
                "sanitization_action": "none",
                "raw_model_input_allowed": True,
                "review_confidence": 0.9,
                "notes": ["test"],
            }
        ],
    }

    result = tool.validate_review_set(reviews, queue)

    assert result["valid"] is False
    assert any(
        "approved_raw requires visible_text_leakage to be empty"
        in row["error"]
        for row in result["errors"]
    )


def test_changed_source_hash_invalidates_review() -> None:
    tool = load_tool()
    queue = {
        "queue": [
            {
                "source_record_id": "test",
                "source": {
                    "source_id": "source-test",
                    "source_file_sha256": "a" * 64,
                },
            }
        ]
    }
    reviews = {
        "reviewer": {
            "reviewer_id": "reviewer-a",
            "reviewer_type": "human",
            "review_method": "visual",
        },
        "reviews": [
            {
                "source_record_id": "test",
                "source_id": "source-test",
                "source_file_sha256": "b" * 64,
                "status": "sanitization_required",
                "identity_match": True,
                "primary_view": "front",
                "primary_figure_complete": True,
                "visible_text_leakage": ["maker_or_brand_logo"],
                "visual_confounders": [],
                "sanitization_action": "tight_figure_crop",
                "raw_model_input_allowed": False,
                "review_confidence": 0.9,
                "notes": ["test"],
            }
        ],
    }

    result = tool.validate_review_set(reviews, queue)

    assert result["valid"] is False
    assert any(
        "source_file_sha256 does not match sanitization queue"
        in row["error"]
        for row in result["errors"]
    )


def test_sanitization_required_cannot_authorize_raw_input() -> None:
    tool = load_tool()
    source_hash = "a" * 64
    queue = {
        "queue": [
            {
                "source_record_id": "test",
                "source": {
                    "source_id": "source-test",
                    "source_file_sha256": source_hash,
                },
            }
        ]
    }
    review = {
        "source_record_id": "test",
        "source_id": "source-test",
        "source_file_sha256": source_hash,
        "status": "sanitization_required",
        "identity_match": True,
        "primary_view": "front",
        "primary_figure_complete": True,
        "visible_text_leakage": ["character_name_or_alias_text"],
        "visual_confounders": [],
        "sanitization_action": "tight_figure_crop",
        "raw_model_input_allowed": True,
        "review_confidence": 0.9,
        "notes": ["test"],
    }

    errors = tool.validate_review(review, tool.queue_sources(queue))
    assert (
        "sanitization_required requires raw_model_input_allowed=false"
        in errors
    )


def test_nonempty_review_set_requires_reviewer_provenance() -> None:
    tool = load_tool()
    source_hash = "a" * 64
    queue = {
        "queue": [
            {
                "source_record_id": "test",
                "source": {
                    "source_id": "source-test",
                    "source_file_sha256": source_hash,
                },
            }
        ]
    }
    reviews = {
        "reviewer": None,
        "reviews": [
            {
                "source_record_id": "test",
                "source_id": "source-test",
                "source_file_sha256": source_hash,
                "status": "sanitization_required",
                "identity_match": True,
                "primary_view": "front",
                "primary_figure_complete": True,
                "visible_text_leakage": ["character_name_or_alias_text"],
                "visual_confounders": [],
                "sanitization_action": "tight_figure_crop",
                "raw_model_input_allowed": False,
                "review_confidence": 0.9,
                "notes": ["test"],
            }
        ],
    }

    result = tool.validate_review_set(reviews, queue)
    assert result["valid"] is False
    assert any(
        row["scope"] == "reviewer"
        and "reviewer must be an object" in row["error"]
        for row in result["errors"]
    )
