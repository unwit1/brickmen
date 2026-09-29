#!/usr/bin/env python3
"""Compile the architecture benchmark model-input gate.

This manifest separates provenance/evaluation cases from bytes models may actually see.
Raw source images are admitted only when the visual-sanitization queue explicitly
approved them. Sanitized derivatives are admitted only when hash-pinned review records
unanimously approve that exact candidate. Anything pending, rejected, revised,
conflicting, stale, or segmentation-required remains blocked.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

VERSION = "body-architecture-model-input-manifest/v1"
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
DEFAULT_QUEUE = DATA / "body-architecture-benchmark-sanitization-queue.json"
DEFAULT_CANDIDATES = DATA / "body-architecture-benchmark-sanitization-candidates.json"
DEFAULT_OUTPUT = DATA / "body-architecture-benchmark-model-input-manifest.json"

CHECKS = (
    "identity_preserved",
    "primary_figure_complete",
    "forbidden_text_absent",
    "task_confounders_absent",
    "architecture_evidence_preserved",
    "no_material_transform_artifacts",
)


def iter_jsonl(paths: Iterable[Path]):
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def _review_is_exact_valid_approval(
    review: dict[str, Any],
    candidate: dict[str, Any],
) -> bool:
    if review.get("decision") != "approved":
        return False
    if review.get("model_input_allowed") is not True:
        return False
    for key in (
        "source_file_sha256",
        "sanitized_pixel_sha256",
        "sanitized_png_sha256",
    ):
        if review.get(key) != candidate.get(key):
            return False
    checks = review.get("checks") or {}
    return all(checks.get(key) is True for key in CHECKS)


def _merge_candidate_docs(
    candidate_doc: dict[str, Any],
    supplemental_candidate_docs: Iterable[dict[str, Any]] = (),
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    candidate_by_id = {
        row["source_record_id"]: row
        for row in candidate_doc.get("records", [])
    }
    blocker_by_id = {
        row["source_record_id"]: row
        for row in candidate_doc.get("blockers", [])
    }

    for doc in supplemental_candidate_docs:
        for row in doc.get("records", []):
            record_id = row["source_record_id"]
            existing = candidate_by_id.get(record_id)
            if existing is not None:
                same_hashes = all(
                    existing.get(key) == row.get(key)
                    for key in (
                        "source_file_sha256",
                        "sanitized_pixel_sha256",
                        "sanitized_png_sha256",
                    )
                )
                if not same_hashes:
                    raise ValueError(
                        "supplemental candidate conflicts with existing "
                        f"candidate: {record_id}"
                    )
            candidate_by_id[record_id] = row
            blocker_by_id.pop(record_id, None)

        for row in doc.get("blockers", []):
            record_id = row["source_record_id"]
            if record_id not in candidate_by_id:
                blocker_by_id[record_id] = row

    return candidate_by_id, blocker_by_id


def build(
    queue_doc: dict[str, Any],
    candidate_doc: dict[str, Any],
    reviews: Iterable[dict[str, Any]] = (),
    supplemental_candidate_docs: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    queue_by_id = {
        row["source_record_id"]: row
        for row in queue_doc.get("queue", [])
    }
    candidate_by_id, blocker_by_id = _merge_candidate_docs(
        candidate_doc,
        supplemental_candidate_docs,
    )
    reviews_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for review in reviews:
        record_id = review.get("source_record_id")
        if isinstance(record_id, str) and record_id:
            reviews_by_id[record_id].append(review)

    entries: list[dict[str, Any]] = []
    for record_id, row in sorted(queue_by_id.items()):
        source = row["source"]

        if row.get("status") == "approved_raw_model_input":
            entries.append(
                {
                    "source_record_id": record_id,
                    "case_id": row["case_id"],
                    "split": row["split"],
                    "scoring_track": row["scoring_track"],
                    "status": "approved_raw",
                    "model_input_allowed": True,
                    "asset_kind": "verified_raw_reference",
                    "asset_sha256": source["source_file_sha256"],
                    "source_file_sha256": source["source_file_sha256"],
                    "expected_local_asset": None,
                    "approval_review_ids": [],
                    "blocked_reason": None,
                }
            )
            continue

        candidate = candidate_by_id.get(record_id)
        blocker = blocker_by_id.get(record_id)
        relevant = reviews_by_id.get(record_id, [])

        if candidate is None:
            queue_status = row.get("status")
            if blocker is not None:
                reason = "requires_segmentation_or_manual_cleanup"
            elif queue_status == "blocked_pending_visual_sanitization_review":
                reason = "pending_visual_sanitization_review"
            elif queue_status == "review_stale_source_hash_changed":
                reason = "stale_visual_sanitization_review"
            elif queue_status == "sanitization_required":
                reason = "missing_sanitization_candidate"
            else:
                reason = "missing_sanitization_candidate"
            entries.append(
                {
                    "source_record_id": record_id,
                    "case_id": row["case_id"],
                    "split": row["split"],
                    "scoring_track": row["scoring_track"],
                    "status": "blocked",
                    "model_input_allowed": False,
                    "asset_kind": None,
                    "asset_sha256": None,
                    "source_file_sha256": source["source_file_sha256"],
                    "expected_local_asset": None,
                    "approval_review_ids": [],
                    "blocked_reason": reason,
                }
            )
            continue

        decisions = {
            str(review.get("decision") or "")
            for review in relevant
            if review.get("source_file_sha256")
            == candidate.get("source_file_sha256")
            and review.get("sanitized_png_sha256")
            == candidate.get("sanitized_png_sha256")
            and review.get("sanitized_pixel_sha256")
            == candidate.get("sanitized_pixel_sha256")
        }
        approvals = [
            review
            for review in relevant
            if _review_is_exact_valid_approval(review, candidate)
        ]

        if approvals and decisions == {"approved"}:
            entries.append(
                {
                    "source_record_id": record_id,
                    "case_id": row["case_id"],
                    "split": row["split"],
                    "scoring_track": row["scoring_track"],
                    "status": "approved_sanitized",
                    "model_input_allowed": True,
                    "asset_kind": "sanitized_derivative",
                    "asset_sha256": candidate["sanitized_png_sha256"],
                    "sanitized_pixel_sha256": candidate[
                        "sanitized_pixel_sha256"
                    ],
                    "source_file_sha256": candidate["source_file_sha256"],
                    "expected_local_asset": (
                        f"{record_id}--"
                        f"{candidate['sanitized_pixel_sha256'][:16]}.png"
                    ),
                    "approval_review_ids": sorted(
                        str(review.get("review_id") or "")
                        for review in approvals
                    ),
                    "blocked_reason": None,
                }
            )
        else:
            if not relevant:
                reason = "pending_visual_review"
            elif len(decisions) > 1:
                reason = "conflicting_reviews"
            elif decisions == {"rejected"}:
                reason = "candidate_rejected"
            elif decisions == {"revise"}:
                reason = "candidate_revision_required"
            elif approvals:
                reason = "review_state_not_unanimous"
            else:
                reason = "no_valid_exact_approval"
            entries.append(
                {
                    "source_record_id": record_id,
                    "case_id": row["case_id"],
                    "split": row["split"],
                    "scoring_track": row["scoring_track"],
                    "status": "blocked",
                    "model_input_allowed": False,
                    "asset_kind": "sanitized_derivative_candidate",
                    "asset_sha256": candidate["sanitized_png_sha256"],
                    "sanitized_pixel_sha256": candidate[
                        "sanitized_pixel_sha256"
                    ],
                    "source_file_sha256": candidate["source_file_sha256"],
                    "expected_local_asset": (
                        f"{record_id}--"
                        f"{candidate['sanitized_pixel_sha256'][:16]}.png"
                    ),
                    "approval_review_ids": [],
                    "blocked_reason": reason,
                }
            )

    return {
        "schema_version": "0.1",
        "processor_version": VERSION,
        "status": "gated_model_input_manifest",
        "policy": (
            "Only visually approved raw references or exact hash-pinned approved "
            "sanitized derivatives are model inputs. Provenance/audit identifiers "
            "remain metadata and must not be exposed as model features."
        ),
        "summary": {
            "total_cases": len(entries),
            "model_input_allowed_cases": sum(
                row["model_input_allowed"] for row in entries
            ),
            "approved_raw_cases": sum(
                row["status"] == "approved_raw" for row in entries
            ),
            "approved_sanitized_cases": sum(
                row["status"] == "approved_sanitized" for row in entries
            ),
            "blocked_cases": sum(
                not row["model_input_allowed"] for row in entries
            ),
        },
        "entries": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--reviews", type=Path, action="append", default=[])
    parser.add_argument(
        "--supplemental-candidates",
        type=Path,
        action="append",
        default=[],
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    queue_doc = json.loads(args.queue.read_text(encoding="utf-8"))
    candidate_doc = json.loads(args.candidates.read_text(encoding="utf-8"))
    supplemental_docs = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in args.supplemental_candidates
    ]
    result = build(
        queue_doc,
        candidate_doc,
        iter_jsonl(args.reviews),
        supplemental_docs,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
