#!/usr/bin/env python3
"""Validate source-image sanitization reviews for architecture benchmarks.

Source review is distinct from derivative approval. This validator pins each review to
the exact byte-verified source hash in a sanitization queue and fails closed when the
source changes or an approval contains leakage/confounders.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

VERSION = "body-architecture-source-sanitization-review-validator/v1"
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
DEFAULT_QUEUE = DATA / "body-architecture-benchmark-sanitization-queue.json"
DEFAULT_REVIEWS = DATA / "body-architecture-benchmark-sanitization-reviews.json"

STATUSES = {"approved_raw", "sanitization_required"}
PRIMARY_VIEWS = {
    "front",
    "front_3q",
    "side",
    "rear",
    "multi_view_composite",
    "uncertain",
}
ACTIONS = {
    "none",
    "tight_figure_crop",
    "mask_regions",
    "segment_primary_figure",
    "replace_source",
    "manual_composite_cleanup",
}
REVIEWER_TYPES = {"human", "model", "hybrid"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def queue_sources(queue_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in queue_doc.get("queue", []):
        record_id = row.get("source_record_id")
        if not isinstance(record_id, str) or not record_id:
            raise ValueError("sanitization queue row missing source_record_id")
        if record_id in result:
            raise ValueError(f"duplicate queue source_record_id: {record_id}")
        source = row.get("source")
        if not isinstance(source, dict):
            raise ValueError(f"queue row missing source object: {record_id}")
        result[record_id] = source
    return result


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, str) and item.strip()
        for item in value
    )


def validate_reviewer(reviewer: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(reviewer, dict):
        return ["reviewer must be an object"]

    reviewer_id = reviewer.get("reviewer_id")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        errors.append("reviewer.reviewer_id must be a non-empty string")

    reviewer_type = reviewer.get("reviewer_type")
    if reviewer_type not in REVIEWER_TYPES:
        errors.append(
            f"reviewer.reviewer_type must be one of {sorted(REVIEWER_TYPES)}"
        )
    if reviewer_type in {"model", "hybrid"}:
        model_family = reviewer.get("model_family") or reviewer.get("model_id")
        if not isinstance(model_family, str) or not model_family.strip():
            errors.append(
                "model/hybrid review requires reviewer.model_family or model_id"
            )

    method = reviewer.get("review_method")
    if not isinstance(method, str) or not method.strip():
        errors.append("reviewer.review_method must be a non-empty string")
    return errors


def validate_review(
    review: dict[str, Any],
    source_by_record: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    record_id = review.get("source_record_id")
    if not isinstance(record_id, str) or not record_id.strip():
        errors.append("source_record_id must be a non-empty string")
        source = None
    else:
        source = source_by_record.get(record_id)
        if source is None:
            errors.append("source_record_id does not exist in sanitization queue")

    source_id = review.get("source_id")
    if not isinstance(source_id, str) or not source_id.strip():
        errors.append("source_id must be a non-empty string")

    source_hash = review.get("source_file_sha256")
    if not isinstance(source_hash, str) or HEX64.fullmatch(source_hash) is None:
        errors.append("source_file_sha256 must be a lowercase SHA-256 hex digest")

    if source is not None:
        if source_id != source.get("source_id"):
            errors.append("source_id does not match sanitization queue")
        if source_hash != source.get("source_file_sha256"):
            errors.append("source_file_sha256 does not match sanitization queue")

    status = review.get("status")
    if status not in STATUSES:
        errors.append(f"status must be one of {sorted(STATUSES)}")

    identity = review.get("identity_match")
    if identity not in {True, False, "uncertain"}:
        errors.append("identity_match must be true, false, or 'uncertain'")

    primary_view = review.get("primary_view")
    if primary_view not in PRIMARY_VIEWS:
        errors.append(
            f"primary_view must be one of {sorted(PRIMARY_VIEWS)}"
        )

    complete = review.get("primary_figure_complete")
    if complete not in {True, False, "uncertain"}:
        errors.append(
            "primary_figure_complete must be true, false, or 'uncertain'"
        )

    leakage = review.get("visible_text_leakage")
    if not _string_list(leakage):
        errors.append(
            "visible_text_leakage must be a list of non-empty strings"
        )
        leakage = []

    confounders = review.get("visual_confounders")
    if not _string_list(confounders):
        errors.append(
            "visual_confounders must be a list of non-empty strings"
        )
        confounders = []

    action = review.get("sanitization_action")
    if action not in ACTIONS:
        errors.append(
            f"sanitization_action must be one of {sorted(ACTIONS)}"
        )

    raw_allowed = review.get("raw_model_input_allowed")
    if raw_allowed not in {True, False}:
        errors.append("raw_model_input_allowed must be true or false")

    confidence = review.get("review_confidence")
    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError):
        errors.append("review_confidence must be numeric in [0, 1]")
    else:
        if not 0 <= confidence_value <= 1:
            errors.append("review_confidence must be in [0, 1]")

    notes = review.get("notes")
    if not _string_list(notes):
        errors.append("notes must be a list of non-empty strings")

    if status == "approved_raw":
        if identity is not True:
            errors.append("approved_raw requires identity_match=true")
        if complete is not True:
            errors.append(
                "approved_raw requires primary_figure_complete=true"
            )
        if leakage:
            errors.append(
                "approved_raw requires visible_text_leakage to be empty"
            )
        if confounders:
            errors.append(
                "approved_raw requires visual_confounders to be empty"
            )
        if action != "none":
            errors.append("approved_raw requires sanitization_action=none")
        if raw_allowed is not True:
            errors.append(
                "approved_raw requires raw_model_input_allowed=true"
            )

    if status == "sanitization_required":
        if raw_allowed is not False:
            errors.append(
                "sanitization_required requires raw_model_input_allowed=false"
            )
        if action == "none":
            errors.append(
                "sanitization_required requires a non-none sanitization_action"
            )
        if identity is False and action != "replace_source":
            errors.append(
                "identity_match=false requires sanitization_action=replace_source"
            )

    return errors


def validate_review_set(
    review_doc: dict[str, Any],
    queue_doc: dict[str, Any],
) -> dict[str, Any]:
    source_by_record = queue_sources(queue_doc)
    errors: list[dict[str, Any]] = []

    reviews = review_doc.get("reviews")
    if not isinstance(reviews, list):
        return {
            "valid": False,
            "errors": errors + [
                {"scope": "document", "error": "reviews must be a list"}
            ],
            "review_count": 0,
            "approved_raw": 0,
            "sanitization_required": 0,
            "queue_cases": len(source_by_record),
            "unreviewed_queue_cases": sorted(source_by_record),
            "reviewed_unknown_cases": [],
        }

    # An initialized-but-empty review set is a valid incomplete state. Reviewer
    # provenance becomes mandatory as soon as the first review is recorded.
    if reviews:
        for error in validate_reviewer(review_doc.get("reviewer")):
            errors.append({"scope": "reviewer", "error": error})

    seen: set[str] = set()
    approved = 0
    sanitize = 0
    for index, review in enumerate(reviews):
        if not isinstance(review, dict):
            errors.append(
                {
                    "scope": f"reviews[{index}]",
                    "error": "review must be an object",
                }
            )
            continue
        record_id = review.get("source_record_id")
        if isinstance(record_id, str):
            if record_id in seen:
                errors.append(
                    {
                        "scope": record_id,
                        "error": "duplicate source_record_id review",
                    }
                )
            seen.add(record_id)
        for error in validate_review(review, source_by_record):
            errors.append(
                {
                    "scope": record_id or f"reviews[{index}]",
                    "error": error,
                }
            )
        if review.get("status") == "approved_raw":
            approved += 1
        elif review.get("status") == "sanitization_required":
            sanitize += 1

    queue_ids = set(source_by_record)
    reviewed_ids = {
        review.get("source_record_id")
        for review in reviews
        if isinstance(review, dict)
        and isinstance(review.get("source_record_id"), str)
    }
    return {
        "valid": not errors,
        "errors": errors,
        "review_count": len(reviews),
        "approved_raw": approved,
        "sanitization_required": sanitize,
        "queue_cases": len(queue_ids),
        "unreviewed_queue_cases": sorted(queue_ids - reviewed_ids),
        "reviewed_unknown_cases": sorted(reviewed_ids - queue_ids),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--reviews", type=Path, default=DEFAULT_REVIEWS)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Fail if any queue case lacks a review.",
    )
    parser.add_argument(
        "--allow-invalid",
        action="store_true",
        help="Write the report and exit successfully even if validation fails.",
    )
    args = parser.parse_args()

    result = validate_review_set(
        load_json(args.reviews),
        load_json(args.queue),
    )
    result["schema"] = (
        "body-architecture-source-sanitization-review-validation/v1"
    )
    result["validator_version"] = VERSION
    result["queue"] = str(args.queue)
    result["reviews"] = str(args.reviews)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))

    incomplete = bool(result["unreviewed_queue_cases"])
    if (not result["valid"] or (args.require_complete and incomplete)) and not args.allow_invalid:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
