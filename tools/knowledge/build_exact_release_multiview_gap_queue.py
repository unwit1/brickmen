#!/usr/bin/env python3
"""Build a conservative acquisition queue for missing exact-release multi-view evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VERSION = "exact-release-multiview-gap-queue/v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "exact-release-flat-art-reference-sets-v1.jsonl"
)
DEFAULT_OUTPUT = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "exact-release-multiview-gap-queue-v1.json"
)


def iter_jsonl(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def acquisition_targets(reference_set: dict[str, Any]) -> list[dict[str, Any]]:
    completeness = reference_set.get("completeness") or {}
    targets: list[dict[str, Any]] = []

    if completeness.get("has_torso_front") and not completeness.get("has_torso_rear"):
        targets.append(
            {
                "target": "torso_rear_evidence",
                "evidence_goal": "Acquire an exact-release rear torso view, even if the rear proves undecorated.",
                "priority_weight": 4,
                "content_inferred": False,
            }
        )

    if completeness.get("has_head_front") and not completeness.get("has_head_reverse"):
        targets.append(
            {
                "target": "head_rear_evidence",
                "evidence_goal": "Acquire an exact-release rear head view; do not assume a reverse print exists.",
                "priority_weight": 3,
                "content_inferred": False,
            }
        )

    if completeness.get("has_lower_body"):
        targets.append(
            {
                "target": "lower_body_rear_or_side_evidence",
                "evidence_goal": "Acquire exact-release rear or side lower-body evidence beyond the current front/unspecified flat-art view.",
                "priority_weight": 2,
                "content_inferred": False,
            }
        )

    # Flat art does not establish physical side appearance or three-dimensional fit.
    targets.extend(
        [
            {
                "target": "physical_left_side_view",
                "evidence_goal": "Acquire an exact-release physical left-side view for silhouette and cross-surface correspondence.",
                "priority_weight": 1,
                "content_inferred": False,
            },
            {
                "target": "physical_right_side_view",
                "evidence_goal": "Acquire an exact-release physical right-side view for silhouette and cross-surface correspondence.",
                "priority_weight": 1,
                "content_inferred": False,
            },
        ]
    )
    return targets


def build(reference_sets: list[dict[str, Any]]) -> dict[str, Any]:
    queue: list[dict[str, Any]] = []
    for row in reference_sets:
        targets = acquisition_targets(row)
        if not targets:
            continue
        completeness = row.get("completeness") or {}
        evidence_records = int(completeness.get("evidence_records") or 0)
        multi_surface_bonus = 2 if completeness.get("multi_surface") else 0
        exact_correspondence_bonus = min(
            len(row.get("same_component_cross_surface_correspondence") or []),
            2,
        )
        target_score = sum(int(item["priority_weight"]) for item in targets)
        score = target_score + multi_surface_bonus + exact_correspondence_bonus

        queue.append(
            {
                "reference_set_id": row["reference_set_id"],
                "sample_id": row["sample_id"],
                "subject": row.get("subject"),
                "identifiers": row.get("identifiers") or {},
                "priority_score": score,
                "existing_evidence_records": evidence_records,
                "existing_canonical_roles": list(
                    completeness.get("canonical_roles") or []
                ),
                "multi_surface": bool(completeness.get("multi_surface")),
                "same_component_cross_surface_correspondences": len(
                    row.get("same_component_cross_surface_correspondence") or []
                ),
                "targets": targets,
                "source_urls": sorted(
                    {
                        url
                        for item in row.get("surface_evidence") or []
                        for url in item.get("source_urls") or []
                        if isinstance(url, str) and url
                    }
                ),
            }
        )

    queue.sort(
        key=lambda item: (
            -int(item["priority_score"]),
            -int(item["existing_evidence_records"]),
            str(item["reference_set_id"]),
        )
    )

    target_counts: dict[str, int] = {}
    for item in queue:
        for target in item["targets"]:
            name = str(target["target"])
            target_counts[name] = target_counts.get(name, 0) + 1

    return {
        "schema": "exact-release-multiview-gap-queue/v1",
        "processor_version": VERSION,
        "source_reference_sets": len(reference_sets),
        "queued_reference_sets": len(queue),
        "target_counts": dict(sorted(target_counts.items())),
        "queue": queue,
        "policy": [
            "A missing view is an acquisition target, not evidence that unseen decoration or geometry exists.",
            "Exact release identity must be preserved when adding new media.",
            "Rear and side evidence must come from directly observed, provenance-retaining source material.",
            "Flat-art and physical-photo evidence remain distinct evidence classes.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    result = build(list(iter_jsonl(args.input)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "queue"},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
