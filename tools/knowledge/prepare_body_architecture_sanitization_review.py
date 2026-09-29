#!/usr/bin/env python3
"""Prepare a local architecture-sanitization review bundle in one command.

The command regenerates deterministic derivatives from verified source URLs, writes
those derivative PNGs only to the requested local output directory, verifies every
generated hash against the canonical metadata-only candidate manifest, and builds the
hash-verifying browser reviewer. It never changes repository approval state.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_body_architecture_sanitization_review_ui as review_ui  # noqa: E402
import generate_body_architecture_sanitization_candidates as generator  # noqa: E402

VERSION = "body-architecture-sanitization-review-prep/v1"
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
DEFAULT_QUEUE = DATA / "body-architecture-benchmark-sanitization-queue.json"
DEFAULT_TRANSFORMS = DATA / "body-architecture-benchmark-sanitization-transforms.json"
DEFAULT_CANDIDATES = DATA / "body-architecture-benchmark-sanitization-candidates.json"

REVIEWED_HOSTS = {
    "img.bricklink.com",
    "kongbricks.com",
    "kongbricks.myshopify.com",
    "cdn.shopify.com",
    "static.herobloks.com",
}


def verify_generated_against_canonical(
    generated: dict[str, Any],
    canonical: dict[str, Any],
) -> dict[str, Any]:
    generated_by_id = {
        row["source_record_id"]: row
        for row in generated.get("records", [])
    }
    canonical_by_id = {
        row["source_record_id"]: row
        for row in canonical.get("records", [])
    }
    if set(generated_by_id) != set(canonical_by_id):
        raise ValueError(
            "generated candidate set differs from canonical candidate set"
        )

    fields = (
        "source_file_sha256",
        "source_dimensions",
        "operations",
        "output_dimensions",
        "sanitized_pixel_sha256",
        "sanitized_png_sha256",
    )
    for record_id in sorted(canonical_by_id):
        observed = generated_by_id[record_id]
        expected = canonical_by_id[record_id]
        for field in fields:
            if observed.get(field) != expected.get(field):
                raise ValueError(
                    f"candidate drift for {record_id}: {field}"
                )

    generated_blockers = {
        row["source_record_id"]: row.get("status")
        for row in generated.get("blockers", [])
    }
    canonical_blockers = {
        row["source_record_id"]: row.get("status")
        for row in canonical.get("blockers", [])
    }
    if generated_blockers != canonical_blockers:
        raise ValueError("segmentation blocker set differs from canonical manifest")

    if generated.get("errors"):
        raise ValueError("generated review bundle contains candidate errors")

    return {
        "verified_candidates": len(generated_by_id),
        "verified_blockers": len(generated_blockers),
        "candidate_hash_drift": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--transforms", type=Path, default=DEFAULT_TRANSFORMS)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--allow-host", action="append", default=[])
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--delay-seconds", type=float, default=0.20)
    args = parser.parse_args()

    allowed_hosts = {
        str(host).strip().lower()
        for host in args.allow_host
        if str(host).strip()
    } or set(REVIEWED_HOSTS)

    out = args.output_dir.resolve()
    derivatives = out / "derivatives"
    report_path = out / "generated-candidate-report.json"
    reviewer_path = out / "review.html"
    out.mkdir(parents=True, exist_ok=True)

    generated = generator.build(
        args.queue,
        args.transforms,
        allowed_hosts=allowed_hosts,
        timeout_seconds=args.timeout_seconds,
        delay_seconds=args.delay_seconds,
        write_derivatives_dir=derivatives,
    )
    canonical = json.loads(args.candidates.read_text(encoding="utf-8"))
    verification = verify_generated_against_canonical(generated, canonical)

    report_path.write_text(
        json.dumps(generated, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    queue_doc = json.loads(args.queue.read_text(encoding="utf-8"))
    payload = review_ui.build_payload(generated, queue_doc)
    reviewer_path.write_text(
        review_ui.build_review_html(payload),
        encoding="utf-8",
    )

    summary = {
        "schema": "body-architecture-sanitization-review-prep/v1",
        "processor_version": VERSION,
        **verification,
        "derivative_directory": str(derivatives),
        "candidate_report": str(report_path),
        "reviewer_html": str(reviewer_path),
        "next_steps": [
            "Open review.html in a browser.",
            "Use Load derivatives and select all PNGs from the derivatives directory.",
            "Visually review each exact hash-verified candidate.",
            "Export JSONL review metadata.",
            "Validate exported reviews with validate_body_architecture_sanitized_asset_reviews.py before rebuilding the model-input manifest.",
        ],
        "policy": (
            "Derivative image bytes remain in the selected local output directory. "
            "This command does not commit, upload, or approve them."
        ),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
