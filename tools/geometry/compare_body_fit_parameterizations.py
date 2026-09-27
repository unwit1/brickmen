#!/usr/bin/env python3
"""Compare current seed body fits with an identifiability-approved expansion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.geometry.fit_body_skeleton import fit_skeleton, load_reference
from tools.geometry.generate_body_skeleton import load_spec


SAFE_EXPANSION = (
    "neck_head_offset_scale",
    "thigh_length_scale",
    "shin_length_scale",
)


def safe_expanded_parameters(
    spec: Mapping[str, Any],
    reference: Mapping[str, Any],
) -> list[str]:
    names = [
        name
        for name in reference.get("fit_parameters", [])
        if name in spec.get("parameters", {})
    ]
    for name in SAFE_EXPANSION:
        if name in spec.get("parameters", {}) and name not in names:
            names.append(name)
    return names


def fit_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "optimized_parameter_names": result["optimized_parameter_names"],
        "initial_normalized_rmse": result["initial_normalized_rmse"],
        "final_normalized_rmse": result["final_normalized_rmse"],
        "fit_status": result["fit_status"],
        "bound_hits": result["bound_hits"],
        "diagnostic_flags": result["diagnostic_flags"],
        "fit_parameters": {
            name: result["fit_parameters"][name]
            for name in result["optimized_parameter_names"]
        },
        "matched_landmark_count": result["matched_landmark_count"],
    }


def compare_reference(
    spec: Mapping[str, Any],
    reference: Mapping[str, Any],
) -> dict[str, Any]:
    current_names = [
        name
        for name in reference.get("fit_parameters", [])
        if name in spec.get("parameters", {})
    ]
    expanded_names = safe_expanded_parameters(spec, reference)
    current = fit_skeleton(spec, reference, parameter_names=current_names)
    expanded = fit_skeleton(spec, reference, parameter_names=expanded_names)
    current_rmse = float(current["final_normalized_rmse"])
    expanded_rmse = float(expanded["final_normalized_rmse"])
    improvement = current_rmse - expanded_rmse
    relative = improvement / current_rmse if current_rmse > 0 else 0.0
    return {
        "reference_id": reference["reference_id"],
        "skeleton_id": spec["skeleton_id"],
        "current": fit_summary(current),
        "safe_expanded_v1": fit_summary(expanded),
        "rmse_improvement_absolute": improvement,
        "rmse_improvement_fraction": relative,
        "expanded_not_worse": expanded_rmse <= current_rmse + 1e-12,
        "production_geometry_authority": False,
    }


def compare_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent
    records = []
    for entry in manifest["references"]:
        reference = load_reference((base / entry["reference"]).resolve())
        spec = load_spec((base / entry["skeleton"]).resolve())
        result = compare_reference(spec, reference)
        result["reference_file"] = entry["reference"]
        result["role"] = entry.get("role")
        records.append(result)

    return {
        "schema_version": "0.1",
        "status": "seed_fit_parameterization_comparison",
        "source_manifest": str(manifest_path),
        "expanded_parameter_policy": {
            "retain_current": True,
            "add": list(SAFE_EXPANSION),
            "excluded_due_to_identifiability": [
                "lower_torso_length_scale",
                "upper_torso_length_scale",
            ],
        },
        "records": records,
        "production_geometry_authority": False,
        "warning": (
            "Lower RMSE on manually estimated seed landmarks is evidence for review, "
            "not automatic permission to change architecture or production geometry."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()
    payload = compare_manifest(args.manifest)
    Path(args.output).write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
