#!/usr/bin/env python3
"""Build deterministic progress state for Fortnite semantic-review coverage."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.knowledge.validate_fortnite_semantic_reviews import annotation_count, validate_record
from tools.knowledge.fortnite_semantic_evidence import evidence_identity, require_shared_evidence, reviewer_principal

VERSION = "fortnite-semantic-review-progress/v2"
DEFAULT_BATCH_DIR = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "semantic-review-batches"
)
DEFAULT_PLAN = DEFAULT_BATCH_DIR / "fortnite-first-review-batch-plan.json"
DEFAULT_OUTPUT = DEFAULT_BATCH_DIR / "fortnite-semantic-review-progress.json"
REVIEW_GLOBS = ("*-submitted.jsonl", "*-adjudicated.jsonl")


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _iter_review_records(review_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    paths: set[Path] = set()
    for pattern in REVIEW_GLOBS:
        paths.update(review_dir.glob(pattern))

    for path in sorted(paths):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("schema") != "fortnite-semantic-review/v1":
                continue
            errors = validate_record(record)
            if errors:
                invalid.append(
                    {
                        "path": _relative(path),
                        "line": line_no,
                        "review_id": record.get("review_id"),
                        "translation_pair_id": record.get("translation_pair_id"),
                        "errors": errors,
                    }
                )
                continue
            records.append(record)
    return records, invalid


def _materialized_batch_pairs(plan: dict[str, Any]) -> tuple[dict[int, set[str]], set[str]]:
    pairs_by_batch: dict[int, set[str]] = {}
    all_pairs: set[str] = set()
    for batch in plan.get("batches", []):
        if not batch.get("materialized"):
            continue
        batch_path = ROOT / str(batch["path"])
        payload = json.loads(batch_path.read_text(encoding="utf-8"))
        pair_ids = {
            str(item["translation_pair_id"])
            for item in payload.get("items", [])
            if item.get("translation_pair_id")
        }
        expected = int(batch.get("selected_records") or 0)
        if len(pair_ids) != expected:
            raise ValueError(
                f"{batch_path}: expected {expected} unique pairs, found {len(pair_ids)}"
            )
        batch_index = int(batch["batch_index"])
        pairs_by_batch[batch_index] = pair_ids
        all_pairs.update(pair_ids)
    return pairs_by_batch, all_pairs


def build_progress(
    plan_path: Path = DEFAULT_PLAN,
    review_dir: Path = DEFAULT_BATCH_DIR,
) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    records, invalid = _iter_review_records(review_dir)
    if invalid:
        first = invalid[0]
        raise ValueError(
            "invalid semantic review record encountered: "
            f"{first['path']}:{first['line']} {first['errors']}"
        )

    pairs_by_batch, materialized_pairs = _materialized_batch_pairs(plan)

    submitted_records = [
        row
        for row in records
        if row.get("review_status") == "submitted"
        and row.get("reviewer", {}).get("review_role") == "reviewer"
    ]
    adjudicated_records = [
        row
        for row in records
        if row.get("review_status") == "adjudicated"
        and row.get("reviewer", {}).get("review_role") == "adjudicator"
    ]

    reviewers_by_pair: dict[str, set[str]] = defaultdict(set)
    reviews_by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    submitted_records_by_pair: dict[str, int] = defaultdict(int)
    for row in submitted_records:
        pair_id = str(row.get("translation_pair_id") or "")
        reviewer_id = reviewer_principal(row)
        if pair_id:
            reviews_by_pair[pair_id].append(row)
            submitted_records_by_pair[pair_id] += 1
            if reviewer_id:
                reviewers_by_pair[pair_id].add(reviewer_id)

    adjudicated_pair_ids = {
        str(row.get("translation_pair_id") or "")
        for row in adjudicated_records
        if row.get("translation_pair_id")
    }

    review_pairs = set(reviewers_by_pair)
    in_plan_review_pairs = review_pairs & materialized_pairs
    out_of_plan_review_pairs = sorted(review_pairs - materialized_pairs)
    distinct_reviewer_pair_ids = {
        pair_id
        for pair_id, reviewer_ids in reviewers_by_pair.items()
        if len(reviewer_ids) >= 2 and pair_id in materialized_pairs
    }
    independent_pair_ids: set[str] = set()
    evidence_blocked_pair_ids: set[str] = set()
    for pair_id in distinct_reviewer_pair_ids:
        try:
            require_shared_evidence(reviews_by_pair[pair_id])
        except ValueError:
            evidence_blocked_pair_ids.add(pair_id)
        else:
            independent_pair_ids.add(pair_id)
    exact_first_review_pairs = {
        pair_id for pair_id in in_plan_review_pairs
        if any(evidence_identity(row) is not None for row in reviews_by_pair[pair_id])
    }
    in_plan_adjudicated_pairs = adjudicated_pair_ids & materialized_pairs

    batch_progress: list[dict[str, Any]] = []
    for batch in plan.get("batches", []):
        batch_index = int(batch["batch_index"])
        expected_pairs = pairs_by_batch.get(batch_index, set())
        submitted_pairs = expected_pairs & review_pairs
        independent_pairs = expected_pairs & independent_pair_ids
        adjudicated_pairs = expected_pairs & in_plan_adjudicated_pairs
        selected_records = int(batch.get("selected_records") or 0)
        batch_progress.append(
            {
                "batch_index": batch_index,
                "batch_id": batch.get("batch_id"),
                "path": batch.get("path"),
                "materialized": bool(batch.get("materialized")),
                "selected_records": selected_records,
                "submitted_pairs": len(submitted_pairs),
                "remaining_first_review_pairs": (
                    selected_records - len(submitted_pairs)
                    if batch.get("materialized")
                    else selected_records
                ),
                "submitted_review_records": sum(
                    submitted_records_by_pair[pair_id] for pair_id in expected_pairs
                ),
                "independently_double_reviewed_pairs": len(independent_pairs),
                "adjudicated_pairs": len(adjudicated_pairs),
                "first_review_complete": bool(batch.get("materialized"))
                and len(submitted_pairs) == selected_records,
            }
        )

    complete_materialized = [
        row for row in batch_progress if row["materialized"] and row["first_review_complete"]
    ]
    next_materialized = next(
        (
            row
            for row in batch_progress
            if row["materialized"] and not row["first_review_complete"]
        ),
        None,
    )
    next_planned = next(
        (row for row in batch_progress if not row["materialized"]),
        None,
    )

    eligible_records = int(plan.get("eligible_records") or 0)
    submitted_first_review_pairs = len(in_plan_review_pairs)

    return {
        "schema": "fortnite-semantic-review-progress/v2",
        "processor_version": VERSION,
        "plan_path": _relative(plan_path),
        "plan_batch_count": int(plan.get("batch_count") or len(batch_progress)),
        "eligible_pairs": eligible_records,
        "materialized_batch_count": int(plan.get("materialized_batch_count") or 0),
        "complete_first_review_batch_count": len(complete_materialized),
        "submitted_reviewer_records": len(submitted_records),
        "submitted_first_review_pairs": submitted_first_review_pairs,
        "remaining_first_review_pairs": max(eligible_records - submitted_first_review_pairs, 0),
        "submitted_semantic_annotations": sum(
            annotation_count(row) for row in submitted_records
        ),
        "independently_double_reviewed_pairs": len(independent_pair_ids),
        "distinct_reviewer_pairs": len(distinct_reviewer_pair_ids),
        "double_review_evidence_blocked_pairs": len(evidence_blocked_pair_ids),
        "evidence_blocked_double_review_pair_ids": sorted(evidence_blocked_pair_ids),
        "first_review_pairs_with_exact_evidence": len(exact_first_review_pairs),
        "first_review_pairs_missing_exact_evidence": len(in_plan_review_pairs - exact_first_review_pairs),
        "adjudicated_pairs": len(in_plan_adjudicated_pairs),
        "review_pairs_outside_materialized_plan": out_of_plan_review_pairs,
        "invalid_review_records": 0,
        "next_materialized_incomplete_batch": (
            {
                key: next_materialized[key]
                for key in (
                    "batch_index",
                    "batch_id",
                    "path",
                    "selected_records",
                    "submitted_pairs",
                    "remaining_first_review_pairs",
                )
            }
            if next_materialized
            else None
        ),
        "next_planned_batch": (
            {
                key: next_planned[key]
                for key in ("batch_index", "batch_id", "path", "selected_records")
            }
            if next_planned
            else None
        ),
        "batch_progress": batch_progress,
        "policy": [
            "Progress is derived from the checked-in batch plan, materialized batch membership, and structurally valid review records.",
            "A pair counts as first-reviewed after at least one submitted reviewer-role record.",
            "Independent double review requires at least two normalized declared reviewer IDs and matching exact source/LEGO hashes and observed scope across the submitted reviews for the pair.",
            "Declared reviewer IDs do not prove that reviewers were genuinely independent; verify the review process separately.",
            "Adjudicated counts are descriptive only; canonical promotion must still pass the dedicated independence and promotion gates.",
            "Measurement signals never count as semantic review evidence.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_BATCH_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    result = build_progress(args.plan, args.review_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "batch_progress"},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
