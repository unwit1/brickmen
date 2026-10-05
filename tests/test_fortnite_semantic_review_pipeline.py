from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_semantic_review_pipeline_end_to_end() -> None:
    batcher = load(
        "fortnite_review_batch",
        "tools/knowledge/build_fortnite_semantic_review_work_batch.py",
    )
    validator = load(
        "fortnite_review_validator",
        "tools/knowledge/validate_fortnite_semantic_reviews.py",
    )
    adjudicator = load(
        "fortnite_review_adjudication",
        "tools/knowledge/build_fortnite_semantic_adjudication_queue.py",
    )
    promoter = load(
        "fortnite_review_promotion",
        "tools/knowledge/promote_fortnite_semantic_supervision.py",
    )

    queue_record = {
        "translation_pair_id": "fortnitepair-integration",
        "source_image_url": "https://example.test/source.png",
        "lego_image_url": "https://example.test/lego.png",
        "lego_image_resolution": "direct_pair",
        "review_priority_score": 12,
        "measurement_signals": [
            {
                "signal": "palette_reduction",
                "region": "torso",
                "value": -2,
            }
        ],
        "processor_version": "fortnite-semantic-review-queue/v1",
    }

    work = batcher.build(
        [queue_record],
        mode="first_review",
        limit=1,
        reviewer_id="reviewer-a",
        reviewer_type="human",
    )
    template = work["items"][0]["review_template"]
    template["evidence"].update(source_image_sha256="a" * 64, lego_image_sha256="b" * 64)

    first = __import__("copy").deepcopy(template)
    first["reviewer"]["reviewer_id"] = "reviewer-a"
    first["review_status"] = "submitted"
    first["created_at"] = "2026-09-28T01:00:00Z"
    first["annotations"]["regions"]["torso"] = [
        {
            "feature": "fine torso energy texture",
            "decision": "simplified",
            "confidence": 0.9,
            "evidence_basis": "observed_in_both",
            "notes": None,
        }
    ]

    second = __import__("copy").deepcopy(template)
    second["reviewer"]["reviewer_id"] = "reviewer-b"
    second["review_status"] = "submitted"
    second["created_at"] = "2026-09-28T01:05:00Z"
    second["annotations"]["regions"]["torso"] = [
        {
            "feature": "fine torso energy texture",
            "decision": "preserved",
            "confidence": 0.65,
            "evidence_basis": "observed_in_both",
            "notes": "Reviewer interprets stylized print as preserving the motif.",
        }
    ]

    assert validator.validate_record(first) == []
    assert validator.validate_record(second) == []
    first = validator.normalize_record(first)
    second = validator.normalize_record(second)

    unresolved = adjudicator.build([first, second])
    assert unresolved["status_counts"] == {"needs_adjudication": 1}
    assert unresolved["training_eligible_pairs"] == 0

    final = __import__("copy").deepcopy(first)
    final["review_id"] = None
    final["reviewer"]["reviewer_id"] = "adjudicator-a"
    final["reviewer"]["review_role"] = "adjudicator"
    final["review_status"] = "adjudicated"
    final["created_at"] = "2026-09-28T01:10:00Z"
    final["adjudicates_review_ids"] = [
        first["review_id"],
        second["review_id"],
    ]
    final["annotations"]["regions"]["torso"][0]["confidence"] = 0.95

    assert validator.validate_record(final) == []
    final = validator.normalize_record(final)

    resolved = adjudicator.build([first, second, final])
    assert resolved["status_counts"] == {"adjudicated": 1}
    assert resolved["training_eligible_pairs"] == 1

    promoted = promoter.promote(
        [first, second, final],
        resolved["queue"],
    )
    assert promoted["promoted_records"] == 1
    supervision = promoted["supervision"][0]
    assert supervision["canonical_review_id"] == final["review_id"]
    assert supervision["promotion"]["training_eligible"] is True
    assert (
        supervision["annotations"]["regions"]["torso"][0]["decision"]
        == "simplified"
    )

    # Measurement heuristics can remain provenance/context, but never become labels by
    # passing through the empty review template automatically.
    assert template["annotations"]["regions"]["torso"] == []
    assert template["measurement_signal_refs"][0]["role"] == "review_prioritization_only"
