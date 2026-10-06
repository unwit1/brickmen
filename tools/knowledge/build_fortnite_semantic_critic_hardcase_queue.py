#!/usr/bin/env python3
"""Rank provisional Fortnite semantic critic evidence into hard-case evaluation work.

The queue is for evaluation prioritization only. It does not promote submitted
reviews, infer hidden surfaces, or make any derived item training-eligible.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VERSION = "fortnite-semantic-critic-hardcase-queue/v2"
DEFAULT_INPUT = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "fortnite-semantic-critic-evidence-v1.jsonl"
)
DEFAULT_OUTPUT = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "fortnite-semantic-critic-hardcase-queue-v1.json"
)

DECISION_WEIGHT = {
    "uncertain": 6,
    "omitted": 5,
    "color_block_changed": 4,
    "exaggerated": 4,
    "moved_to_accessory": 3,
    "moved_to_cloth": 3,
    "moved_to_mould": 2,
    "simplified": 1,
}


def iter_jsonl(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def build(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    source_files: dict[str, set[str]] = defaultdict(set)
    seen: dict[str, dict[str, Any]] = {}
    duplicate_count = 0
    for row in rows:
        if row.get("schema") != "fortnite-semantic-critic-evidence/v1":
            continue
        if row.get("canonical_eligible") is not False:
            raise ValueError("critic evidence must remain canonical-ineligible")
        if row.get("training_eligible") is not False:
            raise ValueError("critic evidence must remain training-ineligible")
        pair_id = str(row.get("translation_pair_id") or "")
        if not pair_id:
            raise ValueError("critic evidence missing translation_pair_id")
        critic_id = row.get("critic_id")
        if not isinstance(critic_id, str) or not critic_id.strip():
            raise ValueError("critic evidence missing critic_id")
        source_files[pair_id].add(str(row["source_review_file"]))
        payload = {key: value for key, value in row.items() if key != "source_review_file"}
        if critic_id in seen:
            if payload != seen[critic_id]:
                raise ValueError(f"conflicting duplicate critic_id: {critic_id}")
            duplicate_count += 1
            continue
        seen[critic_id] = payload
        by_pair[pair_id].append(row)

    queue: list[dict[str, Any]] = []
    for pair_id, items in sorted(by_pair.items()):
        decisions = Counter(str(item.get("decision")) for item in items)
        categories = sorted({str(item.get("critic_category")) for item in items})
        regions = sorted({str(item.get("region")) for item in items})
        source_only_count = sum(item.get("evidence_basis") == "source_only" for item in items)
        uncertain_count = decisions.get("uncertain", 0)
        # An unpaired uncertain feature is unresolved evidence, not an observed
        # translation failure. Retain it for acquisition without score inflation.
        unpaired_uncertainty = [item for item in items if item.get("decision") == "uncertain"
                                and item.get("evidence_basis") != "observed_in_both"]
        priority_items = [item for item in items if not (item.get("decision") == "uncertain"
                           and item.get("evidence_basis") != "observed_in_both")]
        priority_categories = {str(item.get("critic_category")) for item in priority_items}
        priority_regions = {str(item.get("region")) for item in priority_items}
        lower_confidence_priority_count = sum(
            isinstance(item.get("confidence"), (int, float))
            and float(item["confidence"]) < 0.9
            for item in priority_items
        )
        base_score = sum(
            DECISION_WEIGHT.get(str(item.get("decision")), 0)
            for item in priority_items
        )
        lower_confidence_count = sum(isinstance(item.get("confidence"), (int, float))
                                     and float(item["confidence"]) < 0.9 for item in items)
        category_diversity_bonus = max(len(priority_categories) - 1, 0) * 2
        region_diversity_bonus = max(len(priority_regions) - 1, 0)
        source_only_bonus = sum(item.get("evidence_basis") == "source_only" for item in priority_items) * 2
        uncertainty_bonus = sum(item.get("decision") == "uncertain" for item in priority_items) * 3
        lower_confidence_bonus = lower_confidence_priority_count

        score = (
            base_score
            + category_diversity_bonus
            + region_diversity_bonus
            + source_only_bonus
            + uncertainty_bonus
            + lower_confidence_bonus
        )

        source_review_ids = sorted({str(item["source_review_id"]) for item in items})
        source_review_files = sorted(source_files[pair_id])
        source_hashes = sorted(
            {str(item["evidence"]["source_image_sha256"]) for item in items}
        )
        lego_hashes = sorted(
            {str(item["evidence"]["lego_image_sha256"]) for item in items}
        )

        queue.append(
            {
                "translation_pair_id": pair_id,
                "hardcase_score": score,
                "critic_item_count": len(items),
                "category_count": len(categories),
                "region_count": len(regions),
                "source_only_item_count": source_only_count,
                "uncertain_item_count": uncertain_count,
                "unpaired_uncertainty_item_count": len(unpaired_uncertainty),
                "translation_priority_item_count": len(priority_items),
                "unpaired_uncertainty_critic_ids": sorted(item["critic_id"] for item in unpaired_uncertainty),
                "source_only_omitted_item_count": sum(item.get("decision") == "omitted" and item.get("evidence_basis") == "source_only" for item in items),
                "lower_confidence_item_count": lower_confidence_count,
                "lower_confidence_priority_item_count": lower_confidence_priority_count,
                "decision_counts": dict(sorted(decisions.items())),
                "critic_categories": categories,
                "regions": regions,
                "source_review_ids": source_review_ids,
                "source_review_files": source_review_files,
                "source_image_sha256": source_hashes,
                "lego_image_sha256": lego_hashes,
                "evaluation_status": "provisional_submitted_review_evidence",
                "canonical_eligible": False,
                "training_eligible": False,
                "requires_independent_review_and_adjudication": True,
            }
        )

    queue.sort(
        key=lambda row: (
            -int(row["hardcase_score"]),
            -int(row["translation_priority_item_count"]),
            str(row["translation_pair_id"]),
        )
    )

    for rank, row in enumerate(queue, 1):
        row["rank"] = rank

    score_values = [int(row["hardcase_score"]) for row in queue]
    summary = {
        "schema": "fortnite-semantic-critic-hardcase-queue/v1",
        "processor_version": VERSION,
        "source_critic_items": len(rows),
        "unique_critic_items": len(seen),
        "duplicate_critic_items_ignored": duplicate_count,
        "unpaired_uncertainty_items": sum(row["unpaired_uncertainty_item_count"] for row in queue),
        "queued_pairs": len(queue),
        "max_hardcase_score": max(score_values, default=0),
        "min_hardcase_score": min(score_values, default=0),
        "pairs_with_source_only_loss": sum(
            int(row["source_only_omitted_item_count"]) > 0 for row in queue
        ),
        "pairs_with_source_only_evidence": sum(int(row["source_only_item_count"]) > 0 for row in queue),
        "pairs_with_uncertainty": sum(
            int(row["uncertain_item_count"]) > 0 for row in queue
        ),
        "pairs_with_multiple_categories": sum(
            int(row["category_count"]) > 1 for row in queue
        ),
        "pairs_with_multiple_regions": sum(
            int(row["region_count"]) > 1 for row in queue
        ),
        "scoring": {
            "decision_weight": DECISION_WEIGHT,
            "category_diversity_bonus_per_extra_category": 2,
            "region_diversity_bonus_per_extra_region": 1,
            "source_only_bonus_per_item": 2,
            "uncertainty_bonus_per_item": 3,
            "lower_confidence_bonus_per_item": 1,
            "unpaired_uncertainty_contribution": 0,
            "diversity_and_tie_break_inputs": "translation_priority_items_only",
        },
        "policy": [
            "The score is a deterministic evaluation-priority heuristic, not a quality label.",
            "Only explicit submitted-review critic evidence contributes to the queue.",
            "Measurement signals and unobserved surfaces do not contribute to scoring.",
            "Uncertain annotations without observed_in_both evidence remain acquisition/review gaps and contribute no translation-priority score or tie-break bonus.",
            "Identical critic IDs count once; conflicting duplicate IDs fail. All source-file links are retained.",
            "Source-only loss counts only explicit omitted decisions, not source-only uncertainty.",
            "Every queue item remains canonical-ineligible and training-ineligible.",
            "Independent second review and explicit adjudication remain required before canonical promotion.",
        ],
        "queue": queue,
    }
    return summary


def write(input_path: Path = DEFAULT_INPUT, output_path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    result = build(list(iter_jsonl(input_path)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = write(args.input, args.output)
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "queue"},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
