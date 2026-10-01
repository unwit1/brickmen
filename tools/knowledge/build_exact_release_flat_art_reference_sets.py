#!/usr/bin/env python3
"""Build exact-release flat-art ReferenceSets from reviewed crosswalk evidence.

This compiler is intentionally conservative:
- only one-to-one BrickLink + Rebrickable release records are admitted;
- every input record must already be reviewed/verified;
- explicit front/back surface labels are preserved;
- generic surface labels are normalized only when the asset name identifies the
  visible face/front convention;
- same-component cross-surface links never claim pixel alignment or hidden views.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

VERSION = "exact-release-flat-art-reference-sets/v1"
SOURCE_FILE = "knowledge/libraries/lego-minifigure-customs/data/flat-art-verified-crosswalk-2026-09-25.json"


def canonical_role(record: dict[str, Any]) -> str:
    surface = str(record.get("surface") or "").lower()
    stem = str(record.get("relative_stem") or "").lower()
    if surface == "head_back":
        return "head_reverse"
    if surface == "head_front":
        return "head_front"
    if surface == "head":
        return "head_front" if "face" in stem else "head_unspecified"
    if surface == "torso_back":
        return "torso_rear"
    if surface == "torso_front":
        return "torso_front"
    if surface == "torso":
        return "torso_rear" if "torso back" in stem else "torso_front"
    if surface in {"hips_and_legs", "legs", "leg"}:
        return "hips_legs_front_or_unspecified"
    if surface == "dress_skirt":
        return "lower_body_front_or_unspecified"
    if surface == "modified_head":
        return "head_shape_or_pattern"
    if surface == "modified_head_eyes_subregion":
        return "head_eyes_subregion"
    if surface == "modified_head_ears_subregion":
        return "head_ears_subregion"
    if surface == "shield":
        return "accessory_primary"
    return f"surface:{surface or 'unknown'}"


def component_key(record: dict[str, Any]) -> str | None:
    evidence = record.get("evidence") or {}
    value = evidence.get("bricklink_component")
    if isinstance(value, str) and value:
        return f"bricklink:{value}"
    value = evidence.get("rebrickable_component")
    if isinstance(value, str) and value:
        return f"rebrickable:{value}"
    return None


def eligible(record: dict[str, Any]) -> bool:
    evidence = record.get("evidence") or {}
    return (
        isinstance(evidence.get("bricklink_figure"), str)
        and bool(evidence.get("bricklink_figure"))
        and isinstance(evidence.get("rebrickable_figure"), str)
        and bool(evidence.get("rebrickable_figure"))
        and str(record.get("verification_status") or "").startswith("verified")
    )


def build(doc: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_records = list(doc.get("records") or [])
    admitted = [record for record in source_records if eligible(record)]
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in admitted:
        evidence = record["evidence"]
        groups[
            (evidence["bricklink_figure"], evidence["rebrickable_figure"])
        ].append(record)

    reference_sets: list[dict[str, Any]] = []
    for (bricklink, rebrickable), records in sorted(groups.items()):
        records.sort(key=lambda row: str(row.get("crosswalk_id") or ""))
        subjects = sorted(
            {str(row["subject"]) for row in records if row.get("subject")}
        )
        if len(subjects) != 1:
            raise ValueError(
                f"exact-release group has conflicting subjects: "
                f"{bricklink}/{rebrickable}: {subjects}"
            )
        years = sorted(
            {
                int(row["version_year"])
                for row in records
                if row.get("version_year") is not None
            }
        )
        surface_evidence = []
        for row in records:
            evidence = row.get("evidence") or {}
            surface_evidence.append(
                {
                    "crosswalk_id": row.get("crosswalk_id"),
                    "surface": row.get("surface"),
                    "canonical_role": canonical_role(row),
                    "relative_stem": row.get("relative_stem"),
                    "verification_status": row.get("verification_status"),
                    "bricklink_component": evidence.get("bricklink_component"),
                    "rebrickable_component": evidence.get(
                        "rebrickable_component"
                    ),
                    "ldraw_part": evidence.get("ldraw_part"),
                    "svg_sha256": row.get("svg_sha256"),
                    "png_sha256": row.get("png_sha256"),
                    "source_urls": evidence.get("source_urls")
                    or (
                        [evidence["source_url"]]
                        if evidence.get("source_url")
                        else []
                    ),
                }
            )

        by_component: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in records:
            key = component_key(row)
            if key:
                by_component[key].append(row)

        correspondences = []
        for component, component_records in sorted(by_component.items()):
            roles = sorted(
                {canonical_role(row) for row in component_records}
            )
            if len(roles) < 2:
                continue
            correspondences.append(
                {
                    "correspondence_id": (
                        f"xref-flatart-{bricklink}-"
                        f"{component.replace(':', '-')}-"
                        + "--".join(roles)
                    ),
                    "component_id": component,
                    "canonical_roles": roles,
                    "crosswalk_ids": sorted(
                        str(row.get("crosswalk_id") or "")
                        for row in component_records
                    ),
                    "relationship": "same_decorated_component_multi_surface",
                    "alignment_inferred": False,
                }
            )

        roles = sorted(
            {item["canonical_role"] for item in surface_evidence}
        )
        explicit_surfaces = {
            str(row.get("surface") or "") for row in records
        }
        reference_sets.append(
            {
                "reference_set_id": (
                    f"refset-flatart-{bricklink}-{rebrickable}"
                ),
                "sample_id": f"physicalrelease::bricklink::{bricklink}",
                "subject": subjects[0],
                "version_years": years,
                "identifiers": {
                    "bricklink_minifigure_id": bricklink,
                    "rebrickable_fig_num": rebrickable,
                },
                "evidence_class": "reviewed_structured_flat_art",
                "exact_release_identity": True,
                "surface_evidence": surface_evidence,
                "same_component_cross_surface_correspondence": (
                    correspondences
                ),
                "completeness": {
                    "evidence_records": len(surface_evidence),
                    "distinct_canonical_roles": len(roles),
                    "canonical_roles": roles,
                    "multi_surface": len(roles) >= 2,
                    "has_head_front": "head_front" in roles,
                    "has_head_reverse": "head_reverse" in roles,
                    "has_torso_front": "torso_front" in roles,
                    "has_torso_rear": "torso_rear" in roles,
                    "has_explicit_torso_front_rear": (
                        "torso_front" in explicit_surfaces
                        and "torso_back" in explicit_surfaces
                    ),
                    "has_lower_body": any(
                        role
                        in {
                            "hips_legs_front_or_unspecified",
                            "lower_body_front_or_unspecified",
                        }
                        for role in roles
                    ),
                },
                "policy": {
                    "hidden_surface_inference": False,
                    "geometry_equivalence_inferred": False,
                    "note": (
                        "Surface links mean the evidence records are independently "
                        "verified to the same exact physical release. They do not "
                        "imply pixel alignment, hidden-view content, or mechanical "
                        "equivalence."
                    ),
                },
                "processor_version": VERSION,
            }
        )

    summary = {
        "schema": "exact-release-flat-art-reference-set-summary/v1",
        "processor_version": VERSION,
        "source_file": SOURCE_FILE,
        "source_records": len(source_records),
        "exact_single_release_records": len(admitted),
        "excluded_records": len(source_records) - len(admitted),
        "reference_sets": len(reference_sets),
        "multi_surface_reference_sets": sum(
            row["completeness"]["multi_surface"]
            for row in reference_sets
        ),
        "explicit_torso_front_rear_reference_sets": sum(
            row["completeness"]["has_explicit_torso_front_rear"]
            for row in reference_sets
        ),
        "same_component_cross_surface_correspondences": sum(
            len(row["same_component_cross_surface_correspondence"])
            for row in reference_sets
        ),
        "policy": (
            "Only independently reviewed records with one explicit BrickLink "
            "minifigure ID and one explicit Rebrickable figure ID are admitted. "
            "Missing surfaces remain missing."
        ),
    }
    return reference_sets, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    doc = json.loads(args.input.read_text(encoding="utf-8"))
    reference_sets, summary = build(doc)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in reference_sets:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
