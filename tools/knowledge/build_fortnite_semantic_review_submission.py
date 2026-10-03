#!/usr/bin/env python3
"""Compile compact Fortnite semantic-review decisions into canonical submissions."""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.knowledge.validate_fortnite_semantic_reviews import (
    ALLOWED_REGIONS,
    canonical_review_id,
    annotation_count,
    validate_record,
)

VERSION = "fortnite-semantic-review-submission-builder/v1"
DECISION_SCHEMA = "fortnite-semantic-review-decision-batch/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REGION_ORDER = ("head", "torso", "lower_body", "accessory_or_silhouette")


def load_json(path: Path) -> dict[str, Any]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def _decode_annotations(compact: list[Any]) -> dict[str, list[dict[str, Any]]]:
    regions = {region: [] for region in REGION_ORDER}
    for index, row in enumerate(compact):
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError(f"annotation {index} must be a six-item list")
        region, feature, decision, confidence, basis, notes = row
        if region not in ALLOWED_REGIONS:
            raise ValueError(f"annotation {index} has unknown region {region!r}")
        regions[str(region)].append(
            {
                "feature": feature,
                "decision": decision,
                "confidence": confidence,
                "evidence_basis": basis,
                "notes": notes,
            }
        )
    return regions


def build_submission(
    batch_path: Path,
    decisions_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    decisions = load_json(decisions_path)

    if decisions.get("schema") != DECISION_SCHEMA:
        raise ValueError(f"decisions schema must be {DECISION_SCHEMA}")
    if decisions.get("batch_id") != batch.get("batch_id"):
        raise ValueError("decision batch_id does not match materialized batch")

    reviewer = decisions.get("reviewer")
    if not isinstance(reviewer, dict) or reviewer.get("review_role") != "reviewer":
        raise ValueError("decision batch reviewer must have review_role=reviewer")
    created_at = decisions.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        raise ValueError("decision batch requires created_at")

    compact_records = decisions.get("records")
    if not isinstance(compact_records, list):
        raise ValueError("decision batch records must be a list")
    by_pair: dict[str, dict[str, Any]] = {}
    for row in compact_records:
        pair_id = str(row.get("id") or "")
        if not pair_id or pair_id in by_pair:
            raise ValueError(f"duplicate or missing decision pair id: {pair_id!r}")
        for key in ("sh", "lh"):
            value = row.get(key)
            if not isinstance(value, str) or not HEX64.fullmatch(value):
                raise ValueError(f"{pair_id}: {key} must be a lowercase SHA-256")
        by_pair[pair_id] = row

    batch_items = batch.get("items") or []
    expected_pairs = [str(item.get("translation_pair_id") or "") for item in batch_items]
    if len(expected_pairs) != len(set(expected_pairs)):
        raise ValueError("materialized batch contains duplicate translation_pair_id values")
    if set(expected_pairs) != set(by_pair):
        missing = sorted(set(expected_pairs) - set(by_pair))
        extra = sorted(set(by_pair) - set(expected_pairs))
        raise ValueError(f"decision pair set mismatch: missing={missing} extra={extra}")

    records: list[dict[str, Any]] = []
    for item in batch_items:
        pair_id = str(item["translation_pair_id"])
        compact = by_pair[pair_id]
        regions = _decode_annotations(compact.get("a") or [])
        record = {
            "schema": "fortnite-semantic-review/v1",
            "review_id": None,
            "translation_pair_id": pair_id,
            "reviewer": reviewer,
            "evidence": {
                "source_image_url": item["source_image_url"],
                "lego_image_url": item["lego_image_url"],
                "source_image_sha256": compact["sh"],
                "lego_image_sha256": compact["lh"],
                "evidence_scope": "front_pair",
                "claims_unobserved_surfaces": False,
            },
            "annotations": {
                "regions": regions,
                "identity_critical_features": compact.get("i") or [],
                "mask_headgear_route": compact.get("m"),
                "expression_translation": compact.get("e"),
            },
            "limitations": compact.get("l") or [],
            "measurement_signal_refs": (
                item.get("review_template", {}).get("measurement_signal_refs") or []
            ),
            "review_status": "submitted",
            "adjudicates_review_ids": [],
            "created_at": created_at,
            "provenance": [
                {
                    "source": "github_actions_review_bundle",
                    "workflow_run_id": decisions.get("workflow_run_id"),
                    "artifact_id": decisions.get("workflow_artifact_id"),
                    "batch_id": batch.get("batch_id"),
                },
                {
                    "source": "direct_visual_inspection_of_hash_verified_pair",
                    "source_image_sha256": compact["sh"],
                    "lego_image_sha256": compact["lh"],
                },
            ],
        }
        record["review_id"] = canonical_review_id(record)
        errors = validate_record(record)
        if errors:
            raise ValueError(f"{pair_id}: invalid compiled review: {errors}")
        records.append(record)

    review_ids = [row["review_id"] for row in records]
    if len(review_ids) != len(set(review_ids)):
        raise ValueError("compiled reviews produced duplicate canonical review IDs")

    summary = {
        "schema": "fortnite-semantic-review-batch-summary/v1",
        "batch_id": batch.get("batch_id"),
        "review_file": None,
        "reviewer_id": reviewer.get("reviewer_id"),
        "model_id": reviewer.get("model_id"),
        "model_revision": reviewer.get("model_revision"),
        "submitted_reviews": len(records),
        "unique_pairs": len({row["translation_pair_id"] for row in records}),
        "total_annotations": sum(annotation_count(row) for row in records),
        "exact_source_hashes": len({row["evidence"]["source_image_sha256"] for row in records}),
        "exact_lego_hashes": len({row["evidence"]["lego_image_sha256"] for row in records}),
        "training_eligible": 0,
        "workflow_run_id": decisions.get("workflow_run_id"),
        "workflow_artifact_id": decisions.get("workflow_artifact_id"),
        "policy": (
            "Submitted model reviews are evidence only. They require a genuinely "
            "independent second review and explicit adjudication before canonical "
            "supervision promotion."
        ),
    }
    return records, summary


def write_submission(
    batch_path: Path,
    decisions_path: Path,
    output_path: Path,
    summary_path: Path,
) -> dict[str, Any]:
    records, summary = build_submission(batch_path, decisions_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
        encoding="utf-8",
    )
    summary["review_file"] = output_path.name
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    result = write_submission(args.batch, args.decisions, args.output, args.summary)
    print(json.dumps({"processor_version": VERSION, **result}, indent=2))


if __name__ == "__main__":
    main()
