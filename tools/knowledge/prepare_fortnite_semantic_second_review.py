#!/usr/bin/env python3
"""Prepare a blind, identity-safe Fortnite semantic second-review work batch.

This composes the existing adjudication queue and work-batch builders so an operator
does not have to manually wire them together. Prior semantic annotations are used only
to determine review state and reviewer identity; they are never copied into the
second-review batch.
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

from tools.knowledge.build_fortnite_semantic_adjudication_queue import (
    build as build_adjudication_queue,
)
from tools.knowledge.build_fortnite_semantic_review_work_batch import (
    build as build_work_batch,
    iter_jsonl,
)

VERSION = "fortnite-semantic-second-review-preparation/v1"


def _reviewer_principals_by_pair(
    reviews: Iterable[dict[str, Any]],
) -> dict[str, list[str]]:
    by_pair: dict[str, set[str]] = {}
    for record in reviews:
        if record.get("review_status") != "submitted":
            continue
        pair_id = record.get("translation_pair_id")
        reviewer = record.get("reviewer") or {}
        reviewer_id = reviewer.get("reviewer_id")
        if not isinstance(pair_id, str) or not pair_id:
            continue
        if not isinstance(reviewer_id, str) or not reviewer_id.strip():
            continue
        by_pair.setdefault(pair_id, set()).add(reviewer_id.strip().casefold())
    return {
        pair_id: sorted(principals)
        for pair_id, principals in sorted(by_pair.items())
    }


def prepare(
    queue_records: Iterable[dict[str, Any]],
    existing_reviews: Iterable[dict[str, Any]],
    *,
    reviewer_id: str,
    reviewer_type: str = "human",
    limit: int = 25,
    offset: int = 0,
    min_priority_score: float = 6.0,
) -> dict[str, Any]:
    reviewer_id = reviewer_id.strip()
    if not reviewer_id or reviewer_id.casefold() == "unassigned":
        raise ValueError("reviewer_id must identify a genuinely independent reviewer")

    reviews = list(existing_reviews)
    adjudication = build_adjudication_queue(reviews)
    batch = build_work_batch(
        queue_records,
        mode="second_review",
        limit=limit,
        offset=offset,
        min_priority_score=min_priority_score,
        existing_reviews=reviews,
        adjudication_rows=adjudication["queue"],
        reviewer_id=reviewer_id,
        reviewer_type=reviewer_type,
    )
    prior_reviewers = _reviewer_principals_by_pair(reviews)
    selected_pair_ids = [
        str(item["translation_pair_id"])
        for item in batch["items"]
        if item.get("translation_pair_id")
    ]

    return {
        "schema": "fortnite-semantic-second-review-preparation/v1",
        "processor_version": VERSION,
        "reviewer_id": reviewer_id,
        "reviewer_type": reviewer_type,
        "selected_records": batch["selected_records"],
        "selected_pair_ids": selected_pair_ids,
        "candidate_status_counts": adjudication["status_counts"],
        "prior_submitted_reviewer_ids_by_selected_pair": {
            pair_id: prior_reviewers.get(pair_id, [])
            for pair_id in selected_pair_ids
        },
        "batch": batch,
        "policy": [
            "Second-review batches are built from the ranked source/LEGO queue, not from first-review annotations.",
            "Prior reviews are consulted only for workflow status and reviewer-identity exclusion.",
            "The assigned reviewer must be distinct from every prior submitted reviewer for a selected pair.",
            "Second reviews remain non-canonical until explicit adjudication.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--existing-reviews", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument(
        "--reviewer-type",
        choices=["human", "model", "hybrid"],
        default="human",
    )
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--min-priority-score", type=float, default=6.0)
    args = parser.parse_args()

    result = prepare(
        iter_jsonl([args.queue]),
        iter_jsonl(args.existing_reviews),
        reviewer_id=args.reviewer_id,
        reviewer_type=args.reviewer_type,
        limit=args.limit,
        offset=args.offset,
        min_priority_score=args.min_priority_score,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result["batch"], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary = {key: value for key, value in result.items() if key != "batch"}
    args.summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
