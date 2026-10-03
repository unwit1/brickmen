from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "prepare_fortnite_semantic_second_review.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "prepare_fortnite_semantic_second_review",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def queue_record(pair_id: str, score: float = 10.0) -> dict:
    return {
        "translation_pair_id": pair_id,
        "source_image_url": f"https://example.test/{pair_id}-source.png",
        "lego_image_url": f"https://example.test/{pair_id}-lego.png",
        "lego_image_resolution": "direct_pair",
        "review_priority_score": score,
        "measurement_signals": [],
        "processor_version": "fortnite-semantic-review-queue/v1",
    }


def review(
    review_id: str,
    pair_id: str,
    reviewer_id: str,
    *,
    feature: str = "SECRET-FIRST-REVIEW-FEATURE",
) -> dict:
    return {
        "schema": "fortnite-semantic-review/v1",
        "review_id": review_id,
        "translation_pair_id": pair_id,
        "reviewer": {
            "reviewer_type": "model",
            "reviewer_id": reviewer_id,
            "model_id": "model-a",
            "model_revision": "rev-a",
            "review_role": "reviewer",
        },
        "evidence": {
            "source_image_url": f"https://example.test/{pair_id}-source.png",
            "lego_image_url": f"https://example.test/{pair_id}-lego.png",
            "source_image_sha256": None,
            "lego_image_sha256": None,
            "evidence_scope": "front_pair",
            "claims_unobserved_surfaces": False,
        },
        "annotations": {
            "regions": {
                "head": [
                    {
                        "feature": feature,
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
            "identity_critical_features": [feature],
            "mask_headgear_route": None,
            "expression_translation": None,
        },
        "limitations": [],
        "measurement_signal_refs": [],
        "review_status": "submitted",
        "adjudicates_review_ids": [],
        "created_at": "2026-10-03T00:00:00Z",
        "provenance": [],
    }


def test_prepare_selects_pair_for_distinct_reviewer_without_leaking_annotations() -> None:
    tool = load_tool()
    result = tool.prepare(
        [queue_record("pair-a")],
        [review("r1", "pair-a", "reviewer-a")],
        reviewer_id="reviewer-b",
        reviewer_type="model",
    )

    assert result["selected_pair_ids"] == ["pair-a"]
    assert result["prior_submitted_reviewer_ids_by_selected_pair"] == {
        "pair-a": ["reviewer-a"]
    }
    batch_text = json.dumps(result["batch"])
    assert "SECRET-FIRST-REVIEW-FEATURE" not in batch_text
    assert result["batch"]["items"][0]["review_template"]["reviewer"]["reviewer_id"] == "reviewer-b"


def test_prepare_excludes_pair_if_assigned_reviewer_already_reviewed_it() -> None:
    tool = load_tool()
    result = tool.prepare(
        [queue_record("pair-a")],
        [review("r1", "pair-a", "reviewer-a")],
        reviewer_id="REVIEWER-A",
    )

    assert result["selected_records"] == 0
    assert result["selected_pair_ids"] == []


def test_prepare_handles_duplicate_same_reviewer_submissions_as_still_needing_independence() -> None:
    tool = load_tool()
    result = tool.prepare(
        [queue_record("pair-a")],
        [
            review("r1", "pair-a", "reviewer-a", feature="first"),
            review("r2", "pair-a", "reviewer-a", feature="second"),
        ],
        reviewer_id="reviewer-b",
    )

    assert result["candidate_status_counts"] == {
        "needs_independent_second_review": 1
    }
    assert result["selected_pair_ids"] == ["pair-a"]


def test_prepare_rejects_unassigned_reviewer() -> None:
    tool = load_tool()

    for reviewer_id in ("", "unassigned", " UNASSIGNED "):
        try:
            tool.prepare(
                [queue_record("pair-a")],
                [review("r1", "pair-a", "reviewer-a")],
                reviewer_id=reviewer_id,
            )
        except ValueError as exc:
            assert "genuinely independent reviewer" in str(exc)
        else:
            raise AssertionError("expected unassigned reviewer to be rejected")


def test_direct_script_execution_is_available() -> None:
    result = subprocess.run(
        [sys.executable, str(TOOL), "--help"],
        cwd=TOOL.parents[2],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "--existing-reviews" in result.stdout
    assert "--reviewer-id" in result.stdout
