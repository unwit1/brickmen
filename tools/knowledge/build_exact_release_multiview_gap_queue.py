#!/usr/bin/env python3
"""Build a conservative acquisition queue for missing exact-release multi-view evidence."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

VERSION = "exact-release-multiview-gap-queue/v2"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "exact-release-flat-art-reference-sets-v1.jsonl"
)
DEFAULT_REVIEWED_CANDIDATES = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "exact-release-multiview-source-candidates-v1.json"
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


def acquisition_targets(
    reference_set: dict[str, Any],
    satisfied_targets: set[str] | None = None,
) -> list[dict[str, Any]]:
    satisfied_targets = satisfied_targets or set()
    completeness = reference_set.get("completeness") or {}
    targets: list[dict[str, Any]] = []

    if (
        completeness.get("has_torso_front")
        and not completeness.get("has_torso_rear")
        and "torso_rear_evidence" not in satisfied_targets
    ):
        targets.append(
            {
                "target": "torso_rear_evidence",
                "evidence_goal": "Acquire an exact-release rear torso view, even if the rear proves undecorated.",
                "priority_weight": 4,
                "content_inferred": False,
            }
        )

    if (
        completeness.get("has_head_front")
        and not completeness.get("has_head_reverse")
        and "head_rear_evidence" not in satisfied_targets
    ):
        targets.append(
            {
                "target": "head_rear_evidence",
                "evidence_goal": "Acquire an exact-release rear head view; do not assume a reverse print exists.",
                "priority_weight": 3,
                "content_inferred": False,
            }
        )

    if (
        completeness.get("has_lower_body")
        and "lower_body_rear_or_side_evidence" not in satisfied_targets
    ):
        targets.append(
            {
                "target": "lower_body_rear_or_side_evidence",
                "evidence_goal": "Acquire exact-release rear or side lower-body evidence beyond the current front/unspecified flat-art view.",
                "priority_weight": 2,
                "content_inferred": False,
            }
        )

    # Flat art does not establish physical side appearance or three-dimensional fit.
    for target, goal in (
        (
            "physical_left_side_view",
            "Acquire an exact-release physical left-side view for silhouette and cross-surface correspondence.",
        ),
        (
            "physical_right_side_view",
            "Acquire an exact-release physical right-side view for silhouette and cross-surface correspondence.",
        ),
    ):
        if target not in satisfied_targets:
            targets.append(
                {
                    "target": target,
                    "evidence_goal": goal,
                    "priority_weight": 1,
                    "content_inferred": False,
                }
            )
    return targets


def reviewed_evidence_index(
    candidates: list[dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"satisfied_targets": set(), "evidence": []}
    )
    for candidate in candidates or []:
        if candidate.get("byte_verified") is not True:
            continue
        if candidate.get("canonical_eligible") is not False:
            raise ValueError("reviewed candidate evidence must remain canonical-ineligible")
        if candidate.get("training_eligible") is not False:
            raise ValueError("reviewed candidate evidence must remain training-ineligible")

        exact_sha = candidate.get("exact_image_sha256")
        review = candidate.get("visual_review") or {}
        if review.get("status") != "verified_rear_view":
            continue
        if review.get("image_sha256") != exact_sha:
            raise ValueError(
                f"{candidate.get('candidate_id')}: visual review hash does not match exact_image_sha256"
            )
        satisfied = review.get("satisfies_targets") or []
        if not isinstance(satisfied, list):
            raise ValueError("visual_review.satisfies_targets must be a list")

        ref_id = str(candidate.get("reference_set_id") or "")
        if not ref_id:
            raise ValueError("reviewed candidate missing reference_set_id")
        for target in satisfied:
            if not isinstance(target, str) or not target:
                raise ValueError("reviewed satisfied target must be a non-empty string")
            index[ref_id]["satisfied_targets"].add(target)
        index[ref_id]["evidence"].append(
            {
                "candidate_id": candidate.get("candidate_id"),
                "image_sha256": exact_sha,
                "source_provider": review.get("source_provider"),
                "observed_view": review.get("observed_view"),
                "status": review.get("status"),
                "satisfies_targets": sorted(set(satisfied)),
            }
        )
    return index


def build(
    reference_sets: list[dict[str, Any]],
    reviewed_candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    evidence_index = reviewed_evidence_index(reviewed_candidates)
    queue: list[dict[str, Any]] = []
    completed_reference_sets: list[str] = []

    for row in reference_sets:
        ref_id = str(row["reference_set_id"])
        reviewed = evidence_index.get(
            ref_id,
            {"satisfied_targets": set(), "evidence": []},
        )
        satisfied_targets = set(reviewed["satisfied_targets"])
        targets = acquisition_targets(row, satisfied_targets)
        if not targets:
            completed_reference_sets.append(ref_id)
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
                "reference_set_id": ref_id,
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
                "satisfied_targets_from_reviewed_evidence": sorted(satisfied_targets),
                "reviewed_evidence": list(reviewed["evidence"]),
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

    reviewed_satisfied_counts: dict[str, int] = {}
    for item in evidence_index.values():
        for target in item["satisfied_targets"]:
            reviewed_satisfied_counts[target] = reviewed_satisfied_counts.get(target, 0) + 1

    return {
        "schema": "exact-release-multiview-gap-queue/v1",
        "processor_version": VERSION,
        "source_reference_sets": len(reference_sets),
        "reviewed_candidate_records": len(reviewed_candidates or []),
        "reviewed_reference_sets": len(evidence_index),
        "reviewed_satisfied_target_counts": dict(sorted(reviewed_satisfied_counts.items())),
        "queued_reference_sets": len(queue),
        "completed_reference_sets": sorted(completed_reference_sets),
        "target_counts": dict(sorted(target_counts.items())),
        "queue": queue,
        "policy": [
            "A missing view is an acquisition target, not evidence that unseen decoration or geometry exists.",
            "Exact release identity must be preserved when adding new media.",
            "Rear and side evidence must come from directly observed, provenance-retaining source material.",
            "Only byte-verified, hash-bound visual-review records may suppress an acquisition target.",
            "A verified rear photograph may satisfy a rear torso or lower-body evidence target while leaving an obscured rear-head target open.",
            "Flat-art and physical-photo evidence remain distinct evidence classes.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--reviewed-candidates",
        type=Path,
        default=DEFAULT_REVIEWED_CANDIDATES,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    candidates_doc = json.loads(args.reviewed_candidates.read_text(encoding="utf-8"))
    result = build(
        list(iter_jsonl(args.input)),
        list(candidates_doc.get("candidates") or []),
    )
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
