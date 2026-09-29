#!/usr/bin/env python3
"""Report FigureArchitecture evaluation coverage and rank remaining gaps.

Coverage is counted only from evaluation cohorts that have explicit architecture
targets. Umbrella/source-label-only records remain visible as ontology work rather than
being mistaken for benchmark-ready classes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
DEFAULT_REGISTRY = DATA / "figure-architecture-registry.json"
DEFAULT_BASE = DATA / "body-architecture-recognition-benchmark-cases.json"
DEFAULT_CHALLENGE = DATA / "body-architecture-recognition-challenge-cases-v3.json"
DEFAULT_CONTRAST = DATA / "body-architecture-same-character-contrast-v1.json"
DEFAULT_OUTPUT = DATA / "body-architecture-recognition-coverage-gaps.json"
VERSION = "body-architecture-coverage-gaps/v2"

NON_CLASS_STATUSES = (
    "umbrella",
    "source_label",
    "construction_style_not_single",
    "construction_method_umbrella",
    "unresolved",
)

HIGH_VALUE_OFFICIAL = (
    "canonical_existing",
    "architecture_family",
    "catalog_identified",
    "adjacent_official_architecture",
    "official_architecture_family",
    "official_architecture_variant",
    "official_character_specific_architecture",
    "historical_reference_architecture",
    "strong_catalog_evidence",
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def target_ids(manifest: dict[str, Any]) -> set[str]:
    return {
        row["expected"]["architecture_id"]
        for row in manifest.get("cases", [])
        if (row.get("expected") or {}).get("architecture_id")
    }


def contrast_ids(doc: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for pair in doc.get("pairs", []):
        for side in ("left", "right"):
            value = (pair.get(side) or {}).get("architecture_id")
            if value:
                result.add(value)
    return result


def classify_gap(row: dict[str, Any]) -> tuple[str, str]:
    status = str(row.get("status") or "").lower()

    if any(marker in status for marker in NON_CLASS_STATUSES):
        return (
            "ontology_resolution",
            "P2",
        )

    if any(marker in status for marker in HIGH_VALUE_OFFICIAL):
        return (
            "official_evaluation_gap",
            "P0",
        )

    if status.startswith("commercial_architecture"):
        return (
            "custom_evaluation_gap",
            "P1",
        )

    if "strong" in status and "candidate" in status:
        return (
            "evidence_resolution_then_evaluation",
            "P1",
        )

    return (
        "research_gap",
        "P2",
    )


def build(
    registry_path: Path = DEFAULT_REGISTRY,
    base_path: Path = DEFAULT_BASE,
    challenge_path: Path = DEFAULT_CHALLENGE,
    contrast_path: Path = DEFAULT_CONTRAST,
) -> dict[str, Any]:
    registry = load(registry_path)
    base = load(base_path)
    challenge = load(challenge_path)
    contrast = load(contrast_path)

    sources = {
        "base_benchmark": sorted(target_ids(base)),
        "challenge_v3": sorted(target_ids(challenge)),
        "same_character_contrast": sorted(contrast_ids(contrast)),
    }
    covered = set().union(*(set(values) for values in sources.values()))

    coverage_rows = []
    gap_rows = []
    for row in registry.get("architectures", []):
        architecture_id = row["architecture_id"]
        is_covered = architecture_id in covered
        item = {
            "architecture_id": architecture_id,
            "canonical_name": row.get("canonical_name"),
            "status": row.get("status"),
            "scale_class": row.get("scale_class"),
            "covered": is_covered,
            "coverage_sources": [
                name
                for name, values in sources.items()
                if architecture_id in values
            ],
        }
        coverage_rows.append(item)

        if not is_covered:
            gap_type, priority = classify_gap(row)
            gap_rows.append(
                {
                    **item,
                    "gap_type": gap_type,
                    "priority": priority,
                    "representative_characters": row.get(
                        "representative_characters"
                    )
                    or [],
                    "representative_release_ids": row.get(
                        "representative_release_ids"
                    )
                    or [],
                    "representative_part_ids": row.get(
                        "representative_part_ids"
                    )
                    or [],
                    "sources": row.get("sources") or [],
                }
            )

    gap_rows.sort(
        key=lambda row: (
            {"P0": 0, "P1": 1, "P2": 2}[row["priority"]],
            row["gap_type"],
            row["architecture_id"],
        )
    )

    return {
        "schema_version": "0.1",
        "created": "2026-09-29",
        "status": "coverage_gap_inventory",
        "processor_version": VERSION,
        "policy": [
            "Evaluation coverage is architecture-target coverage, not source-count coverage.",
            "Challenge-v3 and same-character contrast assets are evaluation-only.",
            "Umbrella, source-label-only and unresolved families are ontology work, not closed-set benchmark classes.",
            "Prioritize concrete official untested architectures before adding redundant examples of already-covered families.",
        ],
        "inputs": {
            "registry": registry_path.relative_to(ROOT).as_posix(),
            "base_benchmark": base_path.relative_to(ROOT).as_posix(),
            "challenge": challenge_path.relative_to(ROOT).as_posix(),
            "same_character_contrast": contrast_path.relative_to(ROOT).as_posix(),
        },
        "summary": {
            "registry_architectures": len(coverage_rows),
            "covered_architectures": sum(row["covered"] for row in coverage_rows),
            "uncovered_architectures": len(gap_rows),
            "coverage_fraction": (
                round(
                    sum(row["covered"] for row in coverage_rows)
                    / len(coverage_rows),
                    6,
                )
                if coverage_rows
                else 0.0
            ),
            "p0_official_gaps": sum(
                row["priority"] == "P0" for row in gap_rows
            ),
            "p1_gaps": sum(
                row["priority"] == "P1" for row in gap_rows
            ),
            "p2_gaps": sum(
                row["priority"] == "P2" for row in gap_rows
            ),
        },
        "coverage_sources": sources,
        "coverage": coverage_rows,
        "gaps": gap_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--challenge", type=Path, default=DEFAULT_CHALLENGE)
    parser.add_argument("--contrast", type=Path, default=DEFAULT_CONTRAST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    result = build(
        args.registry,
        args.base,
        args.challenge,
        args.contrast,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
