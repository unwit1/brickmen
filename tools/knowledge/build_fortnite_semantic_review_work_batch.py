#!/usr/bin/env python3
"""Build deterministic, resumable Fortnite semantic-review work batches.

The source queue can contain thousands of ranked pairs. This tool selects a bounded
batch for first review, second review, or adjudication without changing queue order or
promoting measurement heuristics into labels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

VERSION = "fortnite-semantic-review-work-batch/v1"
MODES = {"first_review", "second_review", "adjudication"}


def iter_jsonl(paths: Iterable[Path]):
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def rank_key(record: dict[str, Any]) -> tuple[float, str]:
    try:
        score = float(record.get("review_priority_score") or 0.0)
    except (TypeError, ValueError):
        score = 0.0
    return (-score, str(record.get("translation_pair_id") or ""))


def review_template(
    queue_record: dict[str, Any],
    *,
    reviewer_id: str,
    reviewer_type: str,
    review_role: str,
) -> dict[str, Any]:
    return {
        "schema": "fortnite-semantic-review/v1",
        "review_id": None,
        "translation_pair_id": queue_record.get("translation_pair_id"),
        "reviewer": {
            "reviewer_type": reviewer_type,
            "reviewer_id": reviewer_id,
            "model_id": None,
            "model_revision": None,
            "review_role": review_role,
        },
        "evidence": {
            "source_image_url": queue_record.get("source_image_url"),
            "lego_image_url": queue_record.get("lego_image_url"),
            "source_image_sha256": None,
            "lego_image_sha256": None,
            "evidence_scope": "front_pair",
            "claims_unobserved_surfaces": False,
        },
        "annotations": {
            "regions": {
                "head": [],
                "torso": [],
                "lower_body": [],
                "accessory_or_silhouette": [],
            },
            "identity_critical_features": [],
            "mask_headgear_route": None,
            "expression_translation": None,
        },
        "limitations": [],
        "measurement_signal_refs": [
            {
                "signal": signal.get("signal"),
                "region": signal.get("region"),
                "value": signal.get("value"),
                "role": "review_prioritization_only",
            }
            for signal in (queue_record.get("measurement_signals") or [])
        ],
        "review_status": "draft",
        "adjudicates_review_ids": [],
        "created_at": None,
        "provenance": [
            {
                "source": "fortnite_semantic_review_queue",
                "processor_version": queue_record.get("processor_version"),
                "review_priority_score": queue_record.get("review_priority_score"),
            }
        ],
    }


def _reviewed_pair_ids(reviews: Iterable[dict[str, Any]]) -> set[str]:
    return {
        str(record["translation_pair_id"])
        for record in reviews
        if record.get("translation_pair_id")
        and record.get("review_status") in {"submitted", "adjudicated"}
    }


def _submitted_reviewer_ids_by_pair(
    reviews: Iterable[dict[str, Any]],
) -> dict[str, set[str]]:
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
    return by_pair


def _status_by_pair(
    adjudication_rows: Iterable[dict[str, Any]],
) -> dict[str, str]:
    return {
        str(row["translation_pair_id"]): str(row.get("status") or "")
        for row in adjudication_rows
        if row.get("translation_pair_id")
    }


def select(
    queue_records: Iterable[dict[str, Any]],
    *,
    mode: str,
    limit: int,
    offset: int = 0,
    min_priority_score: float = 0.0,
    existing_reviews: Iterable[dict[str, Any]] = (),
    adjudication_rows: Iterable[dict[str, Any]] = (),
    reviewer_id: str | None = None,
) -> list[dict[str, Any]]:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}")
    if limit <= 0:
        raise ValueError("limit must be positive")
    if offset < 0:
        raise ValueError("offset must be non-negative")

    existing_reviews = list(existing_reviews)
    reviewed_pairs = _reviewed_pair_ids(existing_reviews)
    submitted_reviewers_by_pair = _submitted_reviewer_ids_by_pair(existing_reviews)
    status_by_pair = _status_by_pair(adjudication_rows)
    normalized_reviewer_id = (
        reviewer_id.strip().casefold()
        if isinstance(reviewer_id, str) and reviewer_id.strip()
        else None
    )
    eligible: list[dict[str, Any]] = []

    for record in queue_records:
        pair_id = record.get("translation_pair_id")
        if not isinstance(pair_id, str) or not pair_id:
            continue
        try:
            score = float(record.get("review_priority_score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        if score < min_priority_score:
            continue

        if mode == "first_review":
            if pair_id in reviewed_pairs:
                continue
        elif mode == "second_review":
            if status_by_pair.get(pair_id) not in {
                "needs_second_review",
                "needs_independent_second_review",
            }:
                continue
            if (
                normalized_reviewer_id
                and normalized_reviewer_id != "unassigned"
                and normalized_reviewer_id
                in submitted_reviewers_by_pair.get(pair_id, set())
            ):
                continue
        elif mode == "adjudication":
            if status_by_pair.get(pair_id) not in {
                "needs_adjudication",
                "adjudicator_conflict",
                "invalid_adjudicator_references",
            }:
                continue

        eligible.append(record)

    eligible.sort(key=rank_key)
    return eligible[offset : offset + limit]


def build(
    queue_records: Iterable[dict[str, Any]],
    *,
    mode: str,
    limit: int,
    offset: int = 0,
    min_priority_score: float = 0.0,
    existing_reviews: Iterable[dict[str, Any]] = (),
    adjudication_rows: Iterable[dict[str, Any]] = (),
    reviewer_id: str = "unassigned",
    reviewer_type: str = "human",
) -> dict[str, Any]:
    if reviewer_type not in {"human", "model", "hybrid"}:
        raise ValueError("reviewer_type must be human, model, or hybrid")

    selected = select(
        queue_records,
        mode=mode,
        limit=limit,
        offset=offset,
        min_priority_score=min_priority_score,
        existing_reviews=existing_reviews,
        adjudication_rows=adjudication_rows,
        reviewer_id=reviewer_id,
    )
    review_role = "adjudicator" if mode == "adjudication" else "reviewer"
    items = [
        {
            "translation_pair_id": row.get("translation_pair_id"),
            "review_priority_score": row.get("review_priority_score"),
            "lego_image_resolution": row.get("lego_image_resolution"),
            "source_image_url": row.get("source_image_url"),
            "lego_image_url": row.get("lego_image_url"),
            "measurement_signals": row.get("measurement_signals") or [],
            "measurement_signal_policy": (
                "Signals only prioritize review and must not be copied into semantic "
                "labels without direct visual evidence."
            ),
            "review_template": review_template(
                row,
                reviewer_id=reviewer_id,
                reviewer_type=reviewer_type,
                review_role=review_role,
            ),
        }
        for row in selected
    ]

    pair_ids = [str(item["translation_pair_id"]) for item in items]
    digest_parts = [VERSION, mode]
    if mode == "second_review":
        digest_parts.append(reviewer_id.strip().casefold())
    digest = hashlib.sha256(
        ("|".join([*digest_parts, *pair_ids])).encode("utf-8")
    ).hexdigest()[:16]

    return {
        "schema": "fortnite-semantic-review-work-batch/v1",
        "processor_version": VERSION,
        "batch_id": f"fortnite-review-{mode}-{digest}",
        "mode": mode,
        "offset": offset,
        "limit": limit,
        "min_priority_score": min_priority_score,
        "selected_records": len(items),
        "reviewer_id": reviewer_id,
        "reviewer_type": reviewer_type,
        "items": items,
        "policy": [
            "Work batches are deterministic for the same queue, mode, filters, and offset.",
            "Measurement signals are prioritization hints only.",
            "Do not infer hidden or rear features from front-only evidence.",
            "First and second reviews remain non-canonical until explicit adjudication.",
            "Second-review work must be assigned to a reviewer identity distinct from prior submitted reviewers for the same pair.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--mode", choices=sorted(MODES), default="first_review")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--min-priority-score", type=float, default=6.0)
    parser.add_argument("--existing-reviews", type=Path, action="append", default=[])
    parser.add_argument("--adjudication-queue", type=Path)
    parser.add_argument("--reviewer-id", default="unassigned")
    parser.add_argument(
        "--reviewer-type",
        choices=["human", "model", "hybrid"],
        default="human",
    )
    args = parser.parse_args()

    existing_reviews = list(iter_jsonl(args.existing_reviews))
    adjudication_rows = (
        list(iter_jsonl([args.adjudication_queue]))
        if args.adjudication_queue
        else []
    )
    if args.mode in {"second_review", "adjudication"} and not adjudication_rows:
        raise SystemExit(
            "--adjudication-queue is required for second_review/adjudication modes"
        )
    if (
        args.mode == "second_review"
        and args.reviewer_id.strip().casefold() == "unassigned"
    ):
        raise SystemExit(
            "--reviewer-id must identify the independent reviewer for second_review mode"
        )

    result = build(
        iter_jsonl([args.queue]),
        mode=args.mode,
        limit=args.limit,
        offset=args.offset,
        min_priority_score=args.min_priority_score,
        existing_reviews=existing_reviews,
        adjudication_rows=adjudication_rows,
        reviewer_id=args.reviewer_id,
        reviewer_type=args.reviewer_type,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary = {
        key: value
        for key, value in result.items()
        if key != "items"
    }
    args.summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
