#!/usr/bin/env python3
"""Validate and normalize Fortnite -> LEGO semantic review records.

The validator intentionally separates review evidence from canonical supervision:
- measurement heuristics cannot become labels;
- submitted reviews remain evidence;
- only explicit adjudicator records may carry review_status=adjudicated;
- invalid records are never silently promoted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

VERSION = "fortnite-semantic-review-validator/v1"
SCHEMA = "fortnite-semantic-review/v1"

ALLOWED_REGIONS = {
    "head",
    "torso",
    "lower_body",
    "accessory_or_silhouette",
}
ALLOWED_DECISIONS = {
    "preserved",
    "simplified",
    "omitted",
    "exaggerated",
    "moved_to_mould",
    "moved_to_accessory",
    "moved_to_cloth",
    "color_block_changed",
    "not_applicable",
    "uncertain",
}
ALLOWED_EVIDENCE_BASIS = {
    "observed_in_both",
    "source_only",
    "lego_only",
    "multi_view",
    "metadata_only",
    "uncertain",
}
ALLOWED_EVIDENCE_SCOPE = {
    "front_pair",
    "wide_pair",
    "front_and_wide",
    "multi_view",
    "mixed",
    "unknown",
}
ALLOWED_REVIEWER_TYPES = {"human", "model", "hybrid"}
ALLOWED_REVIEW_ROLES = {"reviewer", "adjudicator"}
ALLOWED_REVIEW_STATUS = {"draft", "submitted", "adjudicated"}
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def iter_jsonl(paths: Iterable[Path]):
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                yield path, line_no, json.loads(line)


def canonical_review_id(record: dict[str, Any]) -> str:
    payload = {
        "translation_pair_id": record.get("translation_pair_id"),
        "reviewer": record.get("reviewer"),
        "evidence": record.get("evidence"),
        "annotations": record.get("annotations"),
        "created_at": record.get("created_at"),
    }
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "semreview-" + hashlib.sha256(raw).hexdigest()[:24]


def _is_https(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("https://")


def _valid_hash(value: Any) -> bool:
    return value is None or (isinstance(value, str) and HEX64.fullmatch(value) is not None)


def annotation_count(record: dict[str, Any]) -> int:
    annotations = record.get("annotations") or {}
    regions = annotations.get("regions") or {}
    return sum(len(items) for items in regions.values() if isinstance(items, list))


def validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if record.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA!r}")

    pair_id = record.get("translation_pair_id")
    if not isinstance(pair_id, str) or not pair_id.strip():
        errors.append("translation_pair_id must be a non-empty string")

    reviewer = record.get("reviewer")
    if not isinstance(reviewer, dict):
        errors.append("reviewer must be an object")
        reviewer = {}

    reviewer_type = reviewer.get("reviewer_type")
    if reviewer_type not in ALLOWED_REVIEWER_TYPES:
        errors.append(f"reviewer.reviewer_type must be one of {sorted(ALLOWED_REVIEWER_TYPES)}")

    reviewer_id = reviewer.get("reviewer_id")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        errors.append("reviewer.reviewer_id must be a non-empty string")

    review_role = reviewer.get("review_role")
    if review_role not in ALLOWED_REVIEW_ROLES:
        errors.append(f"reviewer.review_role must be one of {sorted(ALLOWED_REVIEW_ROLES)}")

    if reviewer_type in {"model", "hybrid"}:
        if not isinstance(reviewer.get("model_id"), str) or not reviewer.get("model_id"):
            errors.append("model/hybrid reviews require reviewer.model_id")
        if not isinstance(reviewer.get("model_revision"), str) or not reviewer.get("model_revision"):
            errors.append("model/hybrid reviews require reviewer.model_revision")

    evidence = record.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("evidence must be an object")
        evidence = {}

    for key in ("source_image_url", "lego_image_url"):
        if not _is_https(evidence.get(key)):
            errors.append(f"evidence.{key} must be an https URL")

    for key in ("source_image_sha256", "lego_image_sha256"):
        if not _valid_hash(evidence.get(key)):
            errors.append(f"evidence.{key} must be null or a 64-character SHA-256 hex digest")

    scope = evidence.get("evidence_scope")
    if scope not in ALLOWED_EVIDENCE_SCOPE:
        errors.append(f"evidence.evidence_scope must be one of {sorted(ALLOWED_EVIDENCE_SCOPE)}")

    if evidence.get("claims_unobserved_surfaces") is not False:
        errors.append("evidence.claims_unobserved_surfaces must be false")

    annotations = record.get("annotations")
    if not isinstance(annotations, dict):
        errors.append("annotations must be an object")
        annotations = {}

    regions = annotations.get("regions")
    if not isinstance(regions, dict):
        errors.append("annotations.regions must be an object")
        regions = {}

    unknown_regions = set(regions) - ALLOWED_REGIONS
    if unknown_regions:
        errors.append(f"unknown annotation regions: {sorted(unknown_regions)}")

    for region, items in regions.items():
        if region not in ALLOWED_REGIONS:
            continue
        if not isinstance(items, list):
            errors.append(f"annotations.regions.{region} must be a list")
            continue
        seen: set[tuple[str, str]] = set()
        for index, item in enumerate(items):
            prefix = f"annotations.regions.{region}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            feature = item.get("feature")
            if not isinstance(feature, str) or not feature.strip():
                errors.append(f"{prefix}.feature must be a non-empty string")
            decision = item.get("decision")
            if decision not in ALLOWED_DECISIONS:
                errors.append(f"{prefix}.decision must be one of {sorted(ALLOWED_DECISIONS)}")
            confidence = item.get("confidence")
            try:
                confidence_value = float(confidence)
            except (TypeError, ValueError):
                errors.append(f"{prefix}.confidence must be numeric in [0, 1]")
            else:
                if not 0.0 <= confidence_value <= 1.0:
                    errors.append(f"{prefix}.confidence must be in [0, 1]")
            basis = item.get("evidence_basis")
            if basis not in ALLOWED_EVIDENCE_BASIS:
                errors.append(f"{prefix}.evidence_basis must be one of {sorted(ALLOWED_EVIDENCE_BASIS)}")
            if isinstance(feature, str) and isinstance(decision, str):
                key = (feature.strip().casefold(), decision)
                if key in seen:
                    errors.append(f"{prefix} duplicates feature/decision within region")
                seen.add(key)

    identity = annotations.get("identity_critical_features", [])
    if not isinstance(identity, list) or any(
        not isinstance(item, str) or not item.strip() for item in identity
    ):
        errors.append("annotations.identity_critical_features must be a list of non-empty strings")

    limitations = record.get("limitations", [])
    if not isinstance(limitations, list) or any(
        not isinstance(item, str) or not item.strip() for item in limitations
    ):
        errors.append("limitations must be a list of non-empty strings")

    signal_refs = record.get("measurement_signal_refs", [])
    if not isinstance(signal_refs, list):
        errors.append("measurement_signal_refs must be a list")

    status = record.get("review_status")
    if status not in ALLOWED_REVIEW_STATUS:
        errors.append(f"review_status must be one of {sorted(ALLOWED_REVIEW_STATUS)}")

    if status in {"submitted", "adjudicated"}:
        created_at = record.get("created_at")
        if not isinstance(created_at, str) or not created_at.strip():
            errors.append("submitted/adjudicated reviews require created_at")
        if annotation_count(record) == 0:
            errors.append("submitted/adjudicated reviews require at least one semantic annotation")

    adjudicates = record.get("adjudicates_review_ids", [])
    if not isinstance(adjudicates, list) or any(
        not isinstance(item, str) or not item.strip() for item in adjudicates
    ):
        errors.append("adjudicates_review_ids must be a list of non-empty review IDs")

    if status == "adjudicated":
        if review_role != "adjudicator":
            errors.append("review_status=adjudicated requires reviewer.review_role=adjudicator")
        if not adjudicates:
            errors.append("adjudicated reviews must list adjudicates_review_ids")
    elif adjudicates:
        errors.append("non-adjudicated reviews must not claim adjudicates_review_ids")

    return errors


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    if not normalized.get("review_id"):
        normalized["review_id"] = canonical_review_id(normalized)
    normalized["validator_version"] = VERSION
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--invalid-output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument(
        "--allow-invalid",
        action="store_true",
        help="Write valid records and return success even when invalid records are present.",
    )
    args = parser.parse_args()

    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()

    for path, line_no, record in iter_jsonl(args.input):
        errors = validate_record(record)
        if errors:
            invalid.append(
                {
                    "input_path": str(path),
                    "line_no": line_no,
                    "translation_pair_id": record.get("translation_pair_id"),
                    "review_id": record.get("review_id"),
                    "errors": errors,
                    "record": record,
                }
            )
            continue
        normalized = normalize_record(record)
        valid.append(normalized)
        status_counts[str(normalized.get("review_status"))] += 1

    valid.sort(
        key=lambda row: (
            str(row.get("translation_pair_id") or ""),
            str(row.get("created_at") or ""),
            str(row.get("review_id") or ""),
        )
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.invalid_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as handle:
        for record in valid:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    with args.invalid_output.open("w", encoding="utf-8") as handle:
        for record in invalid:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "schema": "fortnite-semantic-review-validation-summary/v1",
        "validator_version": VERSION,
        "input_records": len(valid) + len(invalid),
        "valid_records": len(valid),
        "invalid_records": len(invalid),
        "review_status_counts": dict(status_counts),
        "training_eligible_adjudicated_records": status_counts.get("adjudicated", 0),
        "policy": (
            "Structural validity is not semantic truth. Only explicit adjudicated "
            "records are eligible for automatic canonical supervision promotion."
        ),
    }
    args.summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))

    if invalid and not args.allow_invalid:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
