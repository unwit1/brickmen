#!/usr/bin/env python3
"""Build an adjudication queue from validated Fortnite semantic reviews.

This tool preserves reviewer disagreement and never uses last-write-wins semantics.
Matching submitted reviews may become an agreement candidate, but they are not training
eligible until an explicit adjudicator record resolves the pair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.knowledge.fortnite_semantic_evidence import evidence_identity, require_shared_evidence

VERSION = "fortnite-semantic-adjudication-queue/v3"


def iter_jsonl(paths: Iterable[Path]):
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def semantic_payload(record: dict[str, Any]) -> dict[str, Any]:
    """Return only semantic content relevant to reviewer agreement."""
    annotations = record.get("annotations") or {}
    regions = annotations.get("regions") or {}
    normalized_regions: dict[str, list[dict[str, Any]]] = {}
    for region in sorted(regions):
        items = regions.get(region) or []
        normalized_regions[region] = sorted(
            (
                {
                    "feature": item.get("feature"),
                    "decision": item.get("decision"),
                    "confidence": item.get("confidence"),
                    "evidence_basis": item.get("evidence_basis"),
                    "notes": item.get("notes"),
                }
                for item in items
            ),
            key=lambda item: (
                str(item.get("feature") or "").casefold(),
                str(item.get("decision") or ""),
                str(item.get("evidence_basis") or ""),
                float(item.get("confidence") or 0.0),
                str(item.get("notes") or ""),
            ),
        )

    return {
        "regions": normalized_regions,
        "identity_critical_features": sorted(
            annotations.get("identity_critical_features") or [],
            key=str.casefold,
        ),
        "mask_headgear_route": annotations.get("mask_headgear_route"),
        "expression_translation": annotations.get("expression_translation"),
    }


def payload_hash(record: dict[str, Any]) -> str:
    raw = json.dumps(
        semantic_payload(record),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def reviewer_principal(record: dict[str, Any]) -> str:
    """Return the declared reviewer identity used for independence checks."""
    reviewer = record.get("reviewer") or {}
    return str(reviewer.get("reviewer_id") or "").strip().casefold()


def _review_stub(record: dict[str, Any]) -> dict[str, Any]:
    reviewer = record.get("reviewer") or {}
    return {
        "review_id": record.get("review_id"),
        "review_status": record.get("review_status"),
        "reviewer_id": reviewer.get("reviewer_id"),
        "reviewer_type": reviewer.get("reviewer_type"),
        "reviewer_principal": reviewer_principal(record),
        "review_role": reviewer.get("review_role"),
        "created_at": record.get("created_at"),
        "payload_hash": payload_hash(record),
    }


def classify_group(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        raise ValueError("cannot classify an empty review group")

    pair_ids = {record.get("translation_pair_id") for record in records}
    if len(pair_ids) != 1:
        raise ValueError("all records in a group must share translation_pair_id")
    pair_id = next(iter(pair_ids))

    submitted = [
        record for record in records if record.get("review_status") == "submitted"
    ]
    drafts = [record for record in records if record.get("review_status") == "draft"]
    adjudicated = [
        record for record in records if record.get("review_status") == "adjudicated"
    ]

    submitted_ids = {
        record.get("review_id")
        for record in submitted
        if isinstance(record.get("review_id"), str)
    }
    submitted_hashes = {payload_hash(record) for record in submitted}
    submitted_principals = {
        reviewer_principal(record) for record in submitted if reviewer_principal(record)
    }
    independent_submitted_review_count = len(submitted_principals)
    submitted_by_id = {
        record.get("review_id"): record
        for record in submitted
        if isinstance(record.get("review_id"), str)
    }

    adjudicator_ref_errors: list[dict[str, Any]] = []
    adjudicator_independence_errors: list[dict[str, Any]] = []
    for record in adjudicated:
        refs = record.get("adjudicates_review_ids") or []
        ref_ids = [ref for ref in refs if isinstance(ref, str)]
        missing = sorted(ref for ref in ref_ids if ref not in submitted_ids)
        if missing:
            adjudicator_ref_errors.append(
                {
                    "review_id": record.get("review_id"),
                    "missing_submitted_review_ids": missing,
                }
            )
            continue

        referenced_submitted = [submitted_by_id[ref] for ref in ref_ids]
        referenced_principals = {
            reviewer_principal(item)
            for item in referenced_submitted
            if reviewer_principal(item)
        }
        if len(referenced_principals) < 2:
            adjudicator_independence_errors.append(
                {
                    "review_id": record.get("review_id"),
                    "referenced_submitted_review_ids": sorted(ref_ids),
                    "independent_submitted_reviewer_count": len(referenced_principals),
                    "required_independent_submitted_reviewers": 2,
                }
            )

    adjudicated_hashes = {payload_hash(record) for record in adjudicated}

    bound_records = submitted + adjudicated
    evidence_missing = any(evidence_identity(record) is None for record in bound_records)
    evidence_variants = {evidence_identity(record) for record in bound_records if evidence_identity(record) is not None}
    if evidence_missing:
        status = "needs_exact_evidence"
        training_eligible = False
        selected_review_id = None
    elif len(evidence_variants) > 1:
        status = "evidence_conflict"
        training_eligible = False
        selected_review_id = None
    elif adjudicator_ref_errors:
        status = "invalid_adjudicator_references"
        training_eligible = False
        selected_review_id = None
    elif adjudicator_independence_errors:
        status = "invalid_adjudicator_independence"
        training_eligible = False
        selected_review_id = None
    elif len(adjudicated_hashes) > 1:
        status = "adjudicator_conflict"
        training_eligible = False
        selected_review_id = None
    elif len(adjudicated) >= 1:
        status = "adjudicated"
        training_eligible = True
        selected_review_id = sorted(
            str(record.get("review_id") or "") for record in adjudicated
        )[0]
    elif len(submitted) >= 2 and independent_submitted_review_count < 2:
        status = "needs_independent_second_review"
        training_eligible = False
        selected_review_id = None
    elif len(submitted) >= 2 and len(submitted_hashes) == 1:
        status = "agreement_candidate"
        training_eligible = False
        selected_review_id = None
    elif len(submitted) >= 2:
        status = "needs_adjudication"
        training_eligible = False
        selected_review_id = None
    elif len(submitted) == 1:
        status = "needs_second_review"
        training_eligible = False
        selected_review_id = None
    else:
        status = "draft_only"
        training_eligible = False
        selected_review_id = None

    return {
        "translation_pair_id": pair_id,
        "status": status,
        "training_eligible": training_eligible,
        "selected_review_id": selected_review_id,
        "submitted_review_count": len(submitted),
        "draft_review_count": len(drafts),
        "adjudicated_review_count": len(adjudicated),
        "evidence_snapshot_count": len(evidence_variants),
        "evidence_hashes_missing": evidence_missing,
        "submitted_payload_count": len(submitted_hashes),
        "independent_submitted_reviewer_count": independent_submitted_review_count,
        "adjudicated_payload_count": len(adjudicated_hashes),
        "adjudicator_reference_errors": adjudicator_ref_errors,
        "adjudicator_independence_errors": adjudicator_independence_errors,
        "reviews": sorted(
            (_review_stub(record) for record in records),
            key=lambda row: (
                str(row["created_at"] or ""),
                str(row["review_id"] or ""),
            ),
        ),
        "policy": (
            "Reviewer agreement is evidence, not canonical truth. Automatic training "
            "eligibility requires an explicit, non-conflicting adjudicated review."
        ),
        "processor_version": VERSION,
    }


def build(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        pair_id = record.get("translation_pair_id")
        if not isinstance(pair_id, str) or not pair_id:
            raise ValueError("all input records require translation_pair_id")
        by_pair[pair_id].append(record)

    queue = [
        classify_group(by_pair[pair_id])
        for pair_id in sorted(by_pair)
    ]
    status_counts = Counter(row["status"] for row in queue)

    return {
        "schema": "fortnite-semantic-adjudication-queue/v1",
        "processor_version": VERSION,
        "review_records": sum(len(records) for records in by_pair.values()),
        "translation_pairs": len(queue),
        "training_eligible_pairs": sum(row["training_eligible"] for row in queue),
        "status_counts": dict(status_counts),
        "queue": queue,
        "policy": [
            "Never use last-write-wins for semantic reviews.",
            "Matching submitted reviews remain agreement candidates and are not automatically canonical.",
            "A second submitted review must come from a distinct declared reviewer identity.",
            "Conflicting submitted reviews require adjudication.",
            "Adjudication requires references to at least two independent submitted reviewers.",
            "Conflicting adjudicator payloads block promotion.",
            "Adjudicator references must resolve to submitted reviews for the same translation pair.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    result = build(iter_jsonl(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as handle:
        for row in result["queue"]:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        key: value
        for key, value in result.items()
        if key != "queue"
    }
    args.summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
