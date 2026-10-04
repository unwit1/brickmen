#!/usr/bin/env python3
"""Build a provisional critic-evidence corpus from submitted Fortnite semantic reviews.

This corpus is intentionally non-canonical. It extracts only explicit reviewer
annotations describing transformations or losses (for example simplification,
omission, mould transfer, palette change, exaggeration, or uncertainty). It
never treats measurement heuristics as semantic evidence and never marks source
reviews or derived critic items as training-eligible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.knowledge.validate_fortnite_semantic_reviews import validate_record

VERSION = "fortnite-semantic-critic-evidence/v1"
SCHEMA = "fortnite-semantic-critic-evidence/v1"
DEFAULT_REVIEW_DIR = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "semantic-review-batches"
)
DEFAULT_OUTPUT = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "fortnite-semantic-critic-evidence-v1.jsonl"
)
DEFAULT_SUMMARY = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "fortnite-semantic-critic-evidence-v1-summary.json"
)

DECISION_CATEGORY = {
    "simplified": "detail_compression",
    "omitted": "feature_loss",
    "exaggerated": "feature_exaggeration",
    "moved_to_mould": "representation_transfer",
    "moved_to_accessory": "representation_transfer",
    "moved_to_cloth": "representation_transfer",
    "color_block_changed": "palette_or_block_change",
    "uncertain": "review_uncertainty",
}
REGION_ORDER = {
    "head": 0,
    "torso": 1,
    "lower_body": 2,
    "accessory_or_silhouette": 3,
}


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def critic_id(payload: dict[str, Any]) -> str:
    stable = {
        "translation_pair_id": payload["translation_pair_id"],
        "source_review_id": payload["source_review_id"],
        "region": payload["region"],
        "feature": payload["feature"],
        "decision": payload["decision"],
    }
    raw = json.dumps(stable, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "semcritic-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def iter_submitted_reviews(paths: Iterable[Path]):
    for path in sorted(paths):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("schema") != "fortnite-semantic-review/v1":
                continue
            errors = validate_record(row)
            if errors:
                raise ValueError(f"{path}:{line_no}: invalid semantic review: {errors}")
            if row.get("review_status") != "submitted":
                continue
            if row.get("reviewer", {}).get("review_role") != "reviewer":
                continue
            yield path, row


def build(review_dir: Path = DEFAULT_REVIEW_DIR) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = sorted(review_dir.glob("fortnite-first-review-batch-*-submitted.jsonl"))
    reviews = list(iter_submitted_reviews(paths))
    critics: list[dict[str, Any]] = []

    for path, review in reviews:
        regions = review.get("annotations", {}).get("regions", {})
        for region, annotations in regions.items():
            for annotation in annotations or []:
                decision = annotation.get("decision")
                category = DECISION_CATEGORY.get(str(decision))
                if category is None:
                    continue

                payload = {
                    "schema": SCHEMA,
                    "critic_id": None,
                    "translation_pair_id": review["translation_pair_id"],
                    "source_review_id": review["review_id"],
                    "source_review_file": _relative(path),
                    "reviewer": {
                        "reviewer_id": review.get("reviewer", {}).get("reviewer_id"),
                        "reviewer_type": review.get("reviewer", {}).get("reviewer_type"),
                        "model_id": review.get("reviewer", {}).get("model_id"),
                        "model_revision": review.get("reviewer", {}).get("model_revision"),
                    },
                    "evidence": {
                        "source_image_sha256": review["evidence"]["source_image_sha256"],
                        "lego_image_sha256": review["evidence"]["lego_image_sha256"],
                        "evidence_scope": review["evidence"]["evidence_scope"],
                        "claims_unobserved_surfaces": False,
                    },
                    "region": region,
                    "feature": annotation.get("feature"),
                    "decision": decision,
                    "critic_category": category,
                    "confidence": annotation.get("confidence"),
                    "evidence_basis": annotation.get("evidence_basis"),
                    "notes": annotation.get("notes"),
                    "evidence_status": "submitted_noncanonical",
                    "canonical_eligible": False,
                    "training_eligible": False,
                    "requires_independent_review_and_adjudication": True,
                    "processor_version": VERSION,
                }
                payload["critic_id"] = critic_id(payload)
                critics.append(payload)

    critics.sort(
        key=lambda row: (
            str(row["translation_pair_id"]),
            REGION_ORDER.get(str(row["region"]), 99),
            str(row["feature"]),
            str(row["critic_id"]),
        )
    )

    decisions = Counter(str(row["decision"]) for row in critics)
    categories = Counter(str(row["critic_category"]) for row in critics)
    regions = Counter(str(row["region"]) for row in critics)
    summary = {
        "schema": "fortnite-semantic-critic-evidence-summary/v1",
        "processor_version": VERSION,
        "source_review_files": len(paths),
        "submitted_reviews": len(reviews),
        "unique_translation_pairs": len({row["translation_pair_id"] for _, row in reviews}),
        "critic_evidence_items": len(critics),
        "unique_critic_pairs": len({row["translation_pair_id"] for row in critics}),
        "high_confidence_items": sum(
            isinstance(row.get("confidence"), (int, float)) and row["confidence"] >= 0.9
            for row in critics
        ),
        "decision_counts": dict(sorted(decisions.items())),
        "category_counts": dict(sorted(categories.items())),
        "region_counts": dict(sorted(regions.items())),
        "training_eligible_items": 0,
        "canonical_eligible_items": 0,
        "policy": [
            "Derived critic items preserve submitted-review status and are not canonical supervision.",
            "Only explicit semantic annotations are admitted; measurement signals are never copied into critic evidence.",
            "Preserved and not-applicable annotations are excluded because this corpus targets transformation, loss, and uncertainty.",
            "Independent second review and explicit adjudication remain required before any canonical promotion.",
        ],
    }
    return critics, summary


def write(
    review_dir: Path = DEFAULT_REVIEW_DIR,
    output: Path = DEFAULT_OUTPUT,
    summary_path: Path = DEFAULT_SUMMARY,
) -> dict[str, Any]:
    critics, summary = build(review_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in critics),
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()
    print(json.dumps(write(args.review_dir, args.output, args.summary), indent=2))


if __name__ == "__main__":
    main()
