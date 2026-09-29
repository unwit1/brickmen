#!/usr/bin/env python3
"""Validate hash-pinned visual reviews of sanitized architecture benchmark assets.

A generated crop/mask is only a candidate. Approval is valid only when:
- source SHA matches the candidate's verified source SHA;
- pixel and PNG hashes match the exact generated derivative;
- all required visual checks are explicitly true;
- reviewer provenance is complete.

Rejected/revise records are retained as evidence but never authorize model input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

VERSION = "body-architecture-sanitized-asset-review-validator/v1"
SCHEMA = "body-architecture-sanitized-asset-review/v1"
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
DEFAULT_CANDIDATES = DATA / "body-architecture-benchmark-sanitization-candidates.json"

DECISIONS = {"approved", "rejected", "revise"}
REVIEWER_TYPES = {"human", "model", "hybrid"}
CHECKS = (
    "identity_preserved",
    "primary_figure_complete",
    "forbidden_text_absent",
    "task_confounders_absent",
    "architecture_evidence_preserved",
    "no_material_transform_artifacts",
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def load_candidates(path: Path = DEFAULT_CANDIDATES) -> dict[str, dict[str, Any]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {
        row["source_record_id"]: row
        for row in doc.get("records", [])
    }


def iter_jsonl(paths: Iterable[Path]):
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if line.strip():
                    yield path, line_no, json.loads(line)


def review_id(record: dict[str, Any]) -> str:
    payload = {
        "source_record_id": record.get("source_record_id"),
        "source_file_sha256": record.get("source_file_sha256"),
        "sanitized_pixel_sha256": record.get("sanitized_pixel_sha256"),
        "sanitized_png_sha256": record.get("sanitized_png_sha256"),
        "decision": record.get("decision"),
        "checks": record.get("checks"),
        "reviewer": record.get("reviewer"),
        "reviewed_at": record.get("reviewed_at"),
    }
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sanreview-" + hashlib.sha256(raw).hexdigest()[:24]


def _hash(value: Any) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def validate_record(
    record: dict[str, Any],
    candidates: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []

    if record.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA!r}")

    record_id = record.get("source_record_id")
    if not isinstance(record_id, str) or not record_id:
        errors.append("source_record_id must be a non-empty string")
        candidate = None
    else:
        candidate = candidates.get(record_id)
        if candidate is None:
            errors.append("source_record_id is not a generated sanitization candidate")

    for key in (
        "source_file_sha256",
        "sanitized_pixel_sha256",
        "sanitized_png_sha256",
    ):
        if not _hash(record.get(key)):
            errors.append(f"{key} must be a lowercase 64-character SHA-256 hex digest")

    if candidate is not None:
        expected = {
            "source_file_sha256": candidate.get("source_file_sha256"),
            "sanitized_pixel_sha256": candidate.get("sanitized_pixel_sha256"),
            "sanitized_png_sha256": candidate.get("sanitized_png_sha256"),
        }
        for key, value in expected.items():
            if record.get(key) != value:
                errors.append(f"{key} does not match the generated candidate")

    decision = record.get("decision")
    if decision not in DECISIONS:
        errors.append(f"decision must be one of {sorted(DECISIONS)}")

    checks = record.get("checks")
    if not isinstance(checks, dict):
        errors.append("checks must be an object")
        checks = {}
    unknown_checks = set(checks) - set(CHECKS)
    if unknown_checks:
        errors.append(f"unknown checks: {sorted(unknown_checks)}")
    for key in CHECKS:
        if checks.get(key) not in {True, False}:
            errors.append(f"checks.{key} must be true or false")

    if decision == "approved":
        failed = [key for key in CHECKS if checks.get(key) is not True]
        if failed:
            errors.append(
                "approved review requires all checks true: " + ", ".join(failed)
            )

    reviewer = record.get("reviewer")
    if not isinstance(reviewer, dict):
        errors.append("reviewer must be an object")
        reviewer = {}
    reviewer_id = reviewer.get("reviewer_id")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        errors.append("reviewer.reviewer_id must be a non-empty string")
    reviewer_type = reviewer.get("reviewer_type")
    if reviewer_type not in REVIEWER_TYPES:
        errors.append(
            f"reviewer.reviewer_type must be one of {sorted(REVIEWER_TYPES)}"
        )
    if reviewer_type in {"model", "hybrid"}:
        if not isinstance(reviewer.get("model_id"), str) or not reviewer.get("model_id"):
            errors.append("model/hybrid review requires reviewer.model_id")
        if (
            not isinstance(reviewer.get("model_revision"), str)
            or not reviewer.get("model_revision")
        ):
            errors.append("model/hybrid review requires reviewer.model_revision")

    confidence = record.get("review_confidence")
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        errors.append("review_confidence must be numeric in [0, 1]")
    else:
        if not 0 <= confidence <= 1:
            errors.append("review_confidence must be in [0, 1]")

    notes = record.get("notes")
    if not isinstance(notes, list) or any(
        not isinstance(note, str) or not note.strip()
        for note in notes
    ):
        errors.append("notes must be a list of non-empty strings")

    if decision in {"rejected", "revise"} and not notes:
        errors.append("rejected/revise review requires explanatory notes")

    reviewed_at = record.get("reviewed_at")
    if not isinstance(reviewed_at, str) or not reviewed_at.strip():
        errors.append("reviewed_at must be a non-empty timestamp string")

    return errors


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized["review_id"] = normalized.get("review_id") or review_id(normalized)
    normalized["validator_version"] = VERSION
    normalized["model_input_allowed"] = normalized.get("decision") == "approved"
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--invalid-output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--allow-invalid", action="store_true")
    args = parser.parse_args()

    candidates = load_candidates(args.candidates)
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []

    for path, line_no, record in iter_jsonl(args.input):
        errors = validate_record(record, candidates)
        if errors:
            invalid.append(
                {
                    "input_path": str(path),
                    "line_no": line_no,
                    "source_record_id": record.get("source_record_id"),
                    "review_id": record.get("review_id"),
                    "errors": errors,
                    "record": record,
                }
            )
        else:
            valid.append(normalize_record(record))

    valid.sort(
        key=lambda row: (
            str(row.get("source_record_id") or ""),
            str(row.get("reviewed_at") or ""),
            str(row.get("review_id") or ""),
        )
    )

    for path in (args.output, args.invalid_output, args.summary):
        path.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as handle:
        for row in valid:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with args.invalid_output.open("w", encoding="utf-8") as handle:
        for row in invalid:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "schema": "body-architecture-sanitized-asset-review-validation/v1",
        "validator_version": VERSION,
        "candidate_records": len(candidates),
        "input_records": len(valid) + len(invalid),
        "valid_records": len(valid),
        "invalid_records": len(invalid),
        "approved_records": sum(row["decision"] == "approved" for row in valid),
        "rejected_records": sum(row["decision"] == "rejected" for row in valid),
        "revise_records": sum(row["decision"] == "revise" for row in valid),
        "policy": (
            "Validation binds approval to exact source and derivative hashes. "
            "Only valid approved records authorize model input."
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
