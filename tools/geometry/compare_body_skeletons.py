#!/usr/bin/env python3
"""Compare one reference against multiple Brickmen generation skeletons.

This is a diagnostic comparator, not an architecture classifier. Shape fit,
height compatibility, and parameter saturation are reported separately so a
low 2D residual cannot silently override scale/topology evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from tools.geometry.fit_body_skeleton import (
    fit_skeleton,
    known_height_nominal,
    load_reference,
)
from tools.geometry.generate_body_skeleton import load_spec


def height_compatibility(
    reference_height_mm: float | None,
    design_range: list[float] | None,
    default_height_mm: float,
) -> dict[str, Any]:
    if reference_height_mm is None:
        return {
            "status": "unknown_reference_height",
            "reference_height_mm": None,
            "distance_to_range_mm": None,
            "relative_distance": None,
        }

    if not design_range:
        distance = abs(reference_height_mm - default_height_mm)
        return {
            "status": "default_only",
            "reference_height_mm": reference_height_mm,
            "distance_to_range_mm": distance,
            "relative_distance": distance / reference_height_mm,
        }

    lo, hi = [float(v) for v in design_range]
    if lo <= reference_height_mm <= hi:
        distance = 0.0
        status = "within_design_range"
    elif reference_height_mm < lo:
        distance = lo - reference_height_mm
        status = "below_design_range"
    else:
        distance = reference_height_mm - hi
        status = "above_design_range"

    return {
        "status": status,
        "reference_height_mm": reference_height_mm,
        "design_range_mm": [lo, hi],
        "distance_to_range_mm": distance,
        "relative_distance": distance / reference_height_mm,
    }


def compare_reference(
    reference_path: str | Path,
    skeleton_registry_path: str | Path,
) -> dict[str, Any]:
    reference_path = Path(reference_path)
    registry_path = Path(skeleton_registry_path)
    reference = load_reference(reference_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    ref_height = known_height_nominal(reference)

    candidates = []
    for entry in registry["skeletons"]:
        skeleton_path = registry_path.parent / entry["file"]
        spec = load_spec(skeleton_path)
        fit = fit_skeleton(spec, reference)
        scale = height_compatibility(
            ref_height,
            entry.get("design_height_range_mm"),
            float(entry["default_target_height_mm"]),
        )
        candidates.append(
            {
                "skeleton_id": entry["skeleton_id"],
                "architecture_id": entry["architecture_id"],
                "shape_rmse": fit["final_normalized_rmse"],
                "fit_status": fit["fit_status"],
                "bound_hit_count": len(fit.get("bound_hits", [])),
                "bound_hits": fit.get("bound_hits", []),
                "height_compatibility": scale,
                "diagnostic_flags": fit.get("diagnostic_flags", []),
            }
        )

    candidates.sort(
        key=lambda item: (
            item["height_compatibility"].get("distance_to_range_mm")
            if item["height_compatibility"].get("distance_to_range_mm")
            is not None
            else 0.0,
            item["shape_rmse"],
            item["bound_hit_count"],
        )
    )

    return {
        "schema_version": "0.1",
        "reference_id": reference["reference_id"],
        "reference_architecture_candidate_id": reference.get(
            "architecture_candidate_id"
        ),
        "known_height_mm": ref_height,
        "candidates": candidates,
        "interpretation_rule": (
            "Do not treat list order as architecture truth. Height compatibility, "
            "shape residual, topology evidence, source metadata, and physical "
            "evidence must be reconciled independently."
        ),
        "production_geometry_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("skeleton_registry")
    parser.add_argument("-o", "--output", default=None)
    args = parser.parse_args()

    result = compare_reference(args.reference, args.skeleton_registry)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
