from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "build_fortnite_semantic_adjudication_queue.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_fortnite_semantic_adjudication_queue",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def review(
    review_id: str,
    *,
    pair_id: str = "fortnitepair-test",
    status: str = "submitted",
    decision: str = "simplified",
    reviewer_id: str | None = None,
    role: str = "reviewer",
    adjudicates: list[str] | None = None,
) -> dict:
    return {
        "schema": "fortnite-semantic-review/v1",
        "review_id": review_id,
        "translation_pair_id": pair_id,
        "reviewer": {
            "reviewer_type": "human",
            "reviewer_id": reviewer_id or review_id,
            "model_id": None,
            "model_revision": None,
            "review_role": role,
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
                        "decision": decision,
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
        "limitations": [],
        "measurement_signal_refs": [],
        "review_status": status,
        "adjudicates_review_ids": adjudicates or [],
        "created_at": "2026-09-28T00:00:00Z",
        "provenance": [],
    }


def test_single_submitted_review_needs_second_review() -> None:
    tool = load_tool()
    result = tool.classify_group([review("r1")])

    assert result["status"] == "needs_second_review"
    assert result["training_eligible"] is False


def test_matching_submitted_reviews_are_not_auto_promoted() -> None:
    tool = load_tool()
    result = tool.classify_group([review("r1"), review("r2")])

    assert result["status"] == "agreement_candidate"
    assert result["submitted_payload_count"] == 1
    assert result["training_eligible"] is False
    assert result["selected_review_id"] is None


def test_duplicate_submissions_from_same_reviewer_do_not_count_as_independent() -> None:
    tool = load_tool()
    result = tool.classify_group(
        [
            review("r1", reviewer_id="same-reviewer"),
            review("r2", reviewer_id="same-reviewer"),
        ]
    )

    assert result["status"] == "needs_independent_second_review"
    assert result["independent_submitted_reviewer_count"] == 1
    assert result["training_eligible"] is False


def test_adjudication_requires_two_independent_submitted_reviewers() -> None:
    tool = load_tool()
    submitted = [
        review("r1", reviewer_id="same-reviewer"),
        review("r2", reviewer_id="same-reviewer"),
    ]
    adjudicator = review(
        "a1",
        status="adjudicated",
        role="adjudicator",
        adjudicates=["r1", "r2"],
    )

    result = tool.classify_group([*submitted, adjudicator])

    assert result["status"] == "invalid_adjudicator_independence"
    assert result["training_eligible"] is False
    assert result["adjudicator_independence_errors"] == [
        {
            "review_id": "a1",
            "referenced_submitted_review_ids": ["r1", "r2"],
            "independent_submitted_reviewer_count": 1,
            "required_independent_submitted_reviewers": 2,
        }
    ]


def test_conflicting_submitted_reviews_require_adjudication() -> None:
    tool = load_tool()
    result = tool.classify_group(
        [
            review("r1", decision="simplified"),
            review("r2", decision="preserved"),
        ]
    )

    assert result["status"] == "needs_adjudication"
    assert result["submitted_payload_count"] == 2
    assert result["training_eligible"] is False
    assert {row["review_id"] for row in result["reviews"]} == {"r1", "r2"}


def test_explicit_adjudication_enables_training() -> None:
    tool = load_tool()
    submitted = [
        review("r1", decision="simplified"),
        review("r2", decision="preserved"),
    ]
    adjudicator = review(
        "a1",
        status="adjudicated",
        decision="simplified",
        role="adjudicator",
        adjudicates=["r1", "r2"],
    )

    result = tool.classify_group([*submitted, adjudicator])

    assert result["status"] == "adjudicated"
    assert result["training_eligible"] is True
    assert result["selected_review_id"] == "a1"


def test_missing_adjudicated_review_reference_blocks_promotion() -> None:
    tool = load_tool()
    adjudicator = review(
        "a1",
        status="adjudicated",
        role="adjudicator",
        adjudicates=["r1", "missing-review"],
    )

    result = tool.classify_group([review("r1"), adjudicator])

    assert result["status"] == "invalid_adjudicator_references"
    assert result["training_eligible"] is False
    assert result["adjudicator_reference_errors"] == [
        {
            "review_id": "a1",
            "missing_submitted_review_ids": ["missing-review"],
        }
    ]


def test_conflicting_adjudicators_block_promotion() -> None:
    tool = load_tool()
    submitted = [
        review("r1", decision="simplified"),
        review("r2", decision="preserved"),
    ]
    a1 = review(
        "a1",
        status="adjudicated",
        decision="simplified",
        role="adjudicator",
        adjudicates=["r1", "r2"],
    )
    a2 = review(
        "a2",
        status="adjudicated",
        decision="preserved",
        role="adjudicator",
        adjudicates=["r1", "r2"],
    )

    result = tool.classify_group([*submitted, a1, a2])

    assert result["status"] == "adjudicator_conflict"
    assert result["training_eligible"] is False
    assert result["adjudicated_payload_count"] == 2


def test_build_reports_pair_level_status_counts() -> None:
    tool = load_tool()
    records = [
        review("r1", pair_id="pair-a"),
        review("r2", pair_id="pair-a"),
        review("r3", pair_id="pair-b", decision="preserved"),
        review("r4", pair_id="pair-b", decision="simplified"),
    ]

    result = tool.build(records)

    assert result["translation_pairs"] == 2
    assert result["review_records"] == 4
    assert result["training_eligible_pairs"] == 0
    assert result["status_counts"] == {
        "agreement_candidate": 1,
        "needs_adjudication": 1,
    }
