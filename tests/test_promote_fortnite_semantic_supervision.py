from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "promote_fortnite_semantic_supervision.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "promote_fortnite_semantic_supervision",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def review(
    review_id: str,
    *,
    pair_id: str = "pair-a",
    status: str = "submitted",
    role: str = "reviewer",
    reviewer_id: str | None = None,
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
            "source_image_sha256": "a" * 64,
            "lego_image_sha256": "b" * 64,
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
                ]
            },
            "identity_critical_features": ["eye shape"],
            "mask_headgear_route": None,
            "expression_translation": None,
        },
        "limitations": ["front only"],
        "review_status": status,
        "adjudicates_review_ids": adjudicates or [],
        "created_at": "2026-09-28T00:00:00Z",
        "provenance": ["test"],
    }


def queue_row(
    *,
    pair_id: str = "pair-a",
    status: str = "adjudicated",
    eligible: bool = True,
    selected: str | None = "a1",
) -> dict:
    return {
        "translation_pair_id": pair_id,
        "status": status,
        "training_eligible": eligible,
        "selected_review_id": selected,
    }


def test_explicit_adjudicated_review_is_promoted() -> None:
    tool = load_tool()
    submitted = [review("r1"), review("r2")]
    adjudicated = review(
        "a1",
        status="adjudicated",
        role="adjudicator",
        adjudicates=["r1", "r2"],
    )

    result = tool.promote([*submitted, adjudicated], [queue_row()])

    assert result["promoted_records"] == 1
    assert result["skipped_pairs"] == 0
    promoted = result["supervision"][0]
    assert promoted["translation_pair_id"] == "pair-a"
    assert promoted["canonical_review_id"] == "a1"
    assert promoted["promotion"]["training_eligible"] is True
    assert promoted["promotion"]["independent_submitted_reviewer_count"] == 2
    assert promoted["adjudicates_review_ids"] == ["r1", "r2"]


def test_adjudicated_review_with_same_reviewer_twice_is_rejected() -> None:
    tool = load_tool()
    submitted = [
        review("r1", reviewer_id="same-reviewer"),
        review("r2", reviewer_id="same-reviewer"),
    ]
    adjudicated = review(
        "a1",
        status="adjudicated",
        role="adjudicator",
        adjudicates=["r1", "r2"],
    )

    try:
        tool.promote([*submitted, adjudicated], [queue_row()])
    except ValueError as exc:
        assert "at least two independent submitted reviewers" in str(exc)
    else:
        raise AssertionError("expected same-reviewer submissions to be rejected")


def test_agreement_candidate_is_not_promoted() -> None:
    tool = load_tool()
    result = tool.promote(
        [review("r1"), review("r2")],
        [
            queue_row(
                status="agreement_candidate",
                eligible=False,
                selected=None,
            )
        ],
    )

    assert result["promoted_records"] == 0
    assert result["skipped_pairs"] == 1
    assert result["skipped"][0]["reason"] == "not_explicitly_adjudicated"


def test_conflict_is_not_promoted_even_if_review_exists() -> None:
    tool = load_tool()
    adjudicated = review(
        "a1",
        status="adjudicated",
        role="adjudicator",
        adjudicates=["r1"],
    )
    result = tool.promote(
        [review("r1"), adjudicated],
        [
            queue_row(
                status="adjudicator_conflict",
                eligible=False,
                selected=None,
            )
        ],
    )

    assert result["promoted_records"] == 0
    assert result["skipped_pairs"] == 1


def test_missing_selected_review_is_rejected() -> None:
    tool = load_tool()

    try:
        tool.promote([review("r1")], [queue_row(selected="missing")])
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected missing adjudicated review to be rejected")


def test_selected_review_must_belong_to_same_pair() -> None:
    tool = load_tool()
    adjudicated = review(
        "a1",
        pair_id="pair-b",
        status="adjudicated",
        role="adjudicator",
        adjudicates=["r1"],
    )

    try:
        tool.promote(
            [review("r1", pair_id="pair-a"), adjudicated],
            [queue_row(pair_id="pair-a", selected="a1")],
        )
    except ValueError as exc:
        assert "another pair" in str(exc)
    else:
        raise AssertionError("expected cross-pair selected review to be rejected")


def test_selected_review_must_be_adjudicated_and_from_adjudicator() -> None:
    tool = load_tool()

    try:
        tool.promote([review("a1")], [queue_row()])
    except ValueError as exc:
        assert "not adjudicated" in str(exc)
    else:
        raise AssertionError("expected submitted review to be rejected")

    bad_role = review(
        "a1",
        status="adjudicated",
        role="reviewer",
        adjudicates=["r1"],
    )
    try:
        tool.promote([review("r1"), bad_role], [queue_row()])
    except ValueError as exc:
        assert "not from an adjudicator" in str(exc)
    else:
        raise AssertionError("expected non-adjudicator review to be rejected")


def test_duplicate_review_ids_are_rejected() -> None:
    tool = load_tool()

    try:
        tool.promote([review("r1"), review("r1")], [])
    except ValueError as exc:
        assert "duplicate review_id" in str(exc)
    else:
        raise AssertionError("expected duplicate review IDs to be rejected")


def test_forged_eligible_queue_cannot_bypass_exact_evidence_matching():
    import pytest
    tool = load_tool()
    records = [review("r1"), review("r2"), review("a1", status="adjudicated", role="adjudicator", adjudicates=["r1", "r2"])]
    records[1]["evidence"]["lego_image_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="different exact evidence"):
        tool.promote(records, [queue_row()])
    records[1]["evidence"]["lego_image_sha256"] = None
    with pytest.raises(ValueError, match="require exact"):
        tool.promote(records, [queue_row()])
