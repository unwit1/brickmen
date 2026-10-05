#!/usr/bin/env python3
"""Promote explicitly adjudicated Fortnite semantic reviews into canonical supervision.

The promotion gate is intentionally narrow. Agreement candidates, drafts, unresolved
conflicts, and submitted reviews are never promoted automatically.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.knowledge.fortnite_semantic_evidence import evidence_identity, require_shared_evidence

VERSION = "fortnite-semantic-supervision-promotion/v3"


def iter_jsonl(paths: Iterable[Path]):
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def index_reviews(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        review_id = record.get("review_id")
        if not isinstance(review_id, str) or not review_id:
            raise ValueError("validated review is missing review_id")
        if review_id in by_id:
            raise ValueError(f"duplicate review_id: {review_id}")
        by_id[review_id] = record
    return by_id


def reviewer_principal(record: dict[str, Any]) -> str:
    reviewer = record.get("reviewer") or {}
    return str(reviewer.get("reviewer_id") or "").strip().casefold()


def promote(
    reviews: Iterable[dict[str, Any]],
    adjudication_rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    review_by_id = index_reviews(reviews)
    supervision: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for row in adjudication_rows:
        pair_id = row.get("translation_pair_id")
        status = row.get("status")
        selected_review_id = row.get("selected_review_id")
        eligible = row.get("training_eligible") is True

        if status != "adjudicated" or not eligible or not selected_review_id:
            skipped.append(
                {
                    "translation_pair_id": pair_id,
                    "status": status,
                    "reason": "not_explicitly_adjudicated",
                }
            )
            continue

        review = review_by_id.get(selected_review_id)
        if review is None:
            raise ValueError(
                f"selected adjudicated review {selected_review_id!r} is missing"
            )
        if review.get("translation_pair_id") != pair_id:
            raise ValueError(
                f"selected review {selected_review_id!r} belongs to another pair"
            )
        if review.get("review_status") != "adjudicated":
            raise ValueError(
                f"selected review {selected_review_id!r} is not adjudicated"
            )
        reviewer = review.get("reviewer") or {}
        if reviewer.get("review_role") != "adjudicator":
            raise ValueError(
                f"selected review {selected_review_id!r} is not from an adjudicator"
            )
        adjudicates = review.get("adjudicates_review_ids") or []
        if not adjudicates:
            raise ValueError(
                f"selected review {selected_review_id!r} has no adjudicated review refs"
            )

        referenced_submitted: list[dict[str, Any]] = []
        for referenced_id in adjudicates:
            referenced = review_by_id.get(referenced_id)
            if referenced is None:
                raise ValueError(
                    f"selected review {selected_review_id!r} references missing submitted review "
                    f"{referenced_id!r}"
                )
            if referenced.get("translation_pair_id") != pair_id:
                raise ValueError(
                    f"adjudicated review reference {referenced_id!r} belongs to another pair"
                )
            if referenced.get("review_status") != "submitted":
                raise ValueError(
                    f"adjudicated review reference {referenced_id!r} is not submitted"
                )
            referenced_submitted.append(referenced)

        independent_principals = {
            reviewer_principal(record)
            for record in referenced_submitted
            if reviewer_principal(record)
        }
        if len(independent_principals) < 2:
            raise ValueError(
                f"selected review {selected_review_id!r} requires at least two independent "
                "submitted reviewers"
            )

        require_shared_evidence([review, *referenced_submitted])

        supervision.append(
            {
                "schema": "fortnite-semantic-supervision/v1",
                "translation_pair_id": pair_id,
                "canonical_review_id": selected_review_id,
                "annotations": review.get("annotations"),
                "evidence": review.get("evidence"),
                "limitations": review.get("limitations") or [],
                "adjudicates_review_ids": adjudicates,
                "adjudicator": {
                    "reviewer_id": reviewer.get("reviewer_id"),
                    "reviewer_type": reviewer.get("reviewer_type"),
                    "model_id": reviewer.get("model_id"),
                    "model_revision": reviewer.get("model_revision"),
                },
                "created_at": review.get("created_at"),
                "provenance": review.get("provenance") or [],
                "promotion": {
                    "training_eligible": True,
                    "source_status": "adjudicated",
                    "independent_submitted_reviewer_count": len(independent_principals),
                    "processor_version": VERSION,
                },
            }
        )

    supervision.sort(key=lambda row: str(row["translation_pair_id"]))
    skipped.sort(
        key=lambda row: (
            str(row.get("translation_pair_id") or ""),
            str(row.get("status") or ""),
        )
    )

    return {
        "schema": "fortnite-semantic-supervision-promotion/v1",
        "processor_version": VERSION,
        "promoted_records": len(supervision),
        "skipped_pairs": len(skipped),
        "supervision": supervision,
        "skipped": skipped,
        "policy": (
            "Only explicit adjudicated queue rows backed by at least two independent "
            "submitted reviewers may be promoted. Reviewer agreement without adjudication "
            "and all unresolved conflicts remain non-canonical."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviews", type=Path, action="append", required=True)
    parser.add_argument("--adjudication-queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    result = promote(
        iter_jsonl(args.reviews),
        iter_jsonl([args.adjudication_queue]),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as handle:
        for row in result["supervision"]:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        key: value
        for key, value in result.items()
        if key not in {"supervision", "skipped"}
    }
    summary["skipped_status_counts"] = {}
    for row in result["skipped"]:
        status = str(row.get("status") or "unknown")
        summary["skipped_status_counts"][status] = (
            summary["skipped_status_counts"].get(status, 0) + 1
        )
    args.summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
