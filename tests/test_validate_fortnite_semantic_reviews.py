from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "validate_fortnite_semantic_reviews.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "validate_fortnite_semantic_reviews",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def base_review() -> dict:
    return {
        "schema": "fortnite-semantic-review/v1",
        "translation_pair_id": "fortnitepair-test",
        "reviewer": {
            "reviewer_type": "human",
            "reviewer_id": "reviewer-a",
            "model_id": None,
            "model_revision": None,
            "review_role": "reviewer",
        },
        "evidence": {
            "source_image_url": "https://example.test/source.png",
            "lego_image_url": "https://example.test/lego.png",
            "source_image_sha256": None,
            "lego_image_sha256": None,
            "evidence_scope": "front_pair",
            "claims_unobserved_surfaces": False,
        },
        "annotations": {
            "regions": {
                "head": [
                    {
                        "feature": "eye shape",
                        "decision": "simplified",
                        "confidence": 0.9,
                        "evidence_basis": "observed_in_both",
                        "notes": None,
                    }
                ],
                "torso": [],
                "lower_body": [],
                "accessory_or_silhouette": [],
            },
            "identity_critical_features": ["eye shape"],
            "mask_headgear_route": None,
            "expression_translation": None,
        },
        "limitations": ["front-facing evidence only"],
        "measurement_signal_refs": [],
        "review_status": "submitted",
        "adjudicates_review_ids": [],
        "created_at": "2026-09-28T00:00:00Z",
        "provenance": ["test fixture"],
    }


def test_valid_submitted_review() -> None:
    tool = load_tool()
    review = base_review()

    assert tool.validate_record(review) == []
    normalized = tool.normalize_record(review)
    assert normalized["review_id"].startswith("semreview-")
    assert normalized["validator_version"] == tool.VERSION


def test_review_id_is_deterministic() -> None:
    tool = load_tool()
    review = base_review()

    assert tool.canonical_review_id(review) == tool.canonical_review_id(review)


def test_model_review_requires_model_identity_and_revision() -> None:
    tool = load_tool()
    review = base_review()
    review["reviewer"]["reviewer_type"] = "model"

    errors = tool.validate_record(review)
    assert "model/hybrid reviews require reviewer.model_id" in errors
    assert "model/hybrid reviews require reviewer.model_revision" in errors


def test_unobserved_surface_claims_are_rejected() -> None:
    tool = load_tool()
    review = base_review()
    review["evidence"]["claims_unobserved_surfaces"] = True

    assert (
        "evidence.claims_unobserved_surfaces must be false"
        in tool.validate_record(review)
    )


def test_adjudication_requires_explicit_adjudicator_and_review_refs() -> None:
    tool = load_tool()
    review = base_review()
    review["review_status"] = "adjudicated"

    errors = tool.validate_record(review)
    assert (
        "review_status=adjudicated requires reviewer.review_role=adjudicator"
        in errors
    )
    assert "adjudicated reviews must list adjudicates_review_ids" in errors

    review["reviewer"]["review_role"] = "adjudicator"
    review["adjudicates_review_ids"] = ["semreview-a", "semreview-b"]
    assert tool.validate_record(review) == []


def test_submitted_review_cannot_claim_adjudication_refs() -> None:
    tool = load_tool()
    review = base_review()
    review["adjudicates_review_ids"] = ["semreview-a"]

    assert (
        "non-adjudicated reviews must not claim adjudicates_review_ids"
        in tool.validate_record(review)
    )


def test_duplicate_feature_decision_is_rejected() -> None:
    tool = load_tool()
    review = base_review()
    duplicate = dict(review["annotations"]["regions"]["head"][0])
    review["annotations"]["regions"]["head"].append(duplicate)

    errors = tool.validate_record(review)
    assert any("duplicates feature/decision within region" in error for error in errors)


def test_submitted_review_requires_semantic_annotation() -> None:
    tool = load_tool()
    review = base_review()
    for region in review["annotations"]["regions"]:
        review["annotations"]["regions"][region] = []

    assert (
        "submitted/adjudicated reviews require at least one semantic annotation"
        in tool.validate_record(review)
    )
