#!/usr/bin/env python3
"""Run current and expanded identifiability diagnostics for seed body references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.geometry.analyze_body_fit_identifiability import analyze_identifiability
from tools.geometry.fit_body_skeleton import load_reference
from tools.geometry.generate_body_skeleton import load_spec


def _existing(spec: dict[str, Any], names: list[str]) -> list[str]:
    definitions = spec.get("parameters", {})
    return [name for name in names if name in definitions]


def candidate_sets(spec: dict[str, Any], reference: dict[str, Any]) -> dict[str, list[str]]:
    current = _existing(spec, list(reference.get("fit_parameters") or []))

    safe_expanded = list(current)
    for name in ("neck_head_offset_scale", "thigh_length_scale", "shin_length_scale"):
        if name in spec.get("parameters", {}) and name not in safe_expanded:
            safe_expanded.append(name)

    segmented_torso = [
        name for name in current if name != "torso_height_scale"
    ]
    for name in (
        "lower_torso_length_scale",
        "upper_torso_length_scale",
        "neck_head_offset_scale",
        "thigh_length_scale",
        "shin_length_scale",
    ):
        if name in spec.get("parameters", {}) and name not in segmented_torso:
            segmented_torso.append(name)

    return {
        "current": current,
        "safe_expanded_v1": safe_expanded,
        "segmented_torso_experiment": segmented_torso,
    }


def analyze_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent
    records = []

    for entry in manifest["references"]:
        reference_path = (base / entry["reference"]).resolve()
        skeleton_path = (base / entry["skeleton"]).resolve()
        reference = load_reference(reference_path)
        spec = load_spec(skeleton_path)
        analyses = {}
        for set_name, names in candidate_sets(spec, reference).items():
            analyses[set_name] = analyze_identifiability(
                spec, reference, parameter_names=names
            )
        records.append(
            {
                "reference_id": reference["reference_id"],
                "reference_file": entry["reference"],
                "skeleton_id": spec["skeleton_id"],
                "role": entry.get("role"),
                "analyses": analyses,
            }
        )

    conclusions = []
    for record in records:
        safe = record["analyses"]["safe_expanded_v1"]
        segmented = record["analyses"]["segmented_torso_experiment"]
        conclusions.append(
            {
                "reference_id": record["reference_id"],
                "safe_expanded_status": safe["status"],
                "safe_expanded_rank": safe["jacobian_rank"],
                "safe_expanded_parameter_count": safe["parameter_count"],
                "segmented_torso_status": segmented["status"],
                "segmented_torso_rank": segmented["jacobian_rank"],
                "segmented_torso_parameter_count": segmented["parameter_count"],
                "segmented_torso_confounded_pairs": segmented["confounded_pairs"],
            }
        )

    return {
        "schema_version": "0.1",
        "status": "local_landmark_identifiability_diagnostic",
        "source_manifest": str(manifest_path),
        "records": records,
        "conclusions": conclusions,
        "rules": [
            "Do not add a fine-grained fit parameter merely because it lowers RMSE.",
            "Prefer candidate parameter sets whose local Jacobian is full column rank for the observed landmark axes.",
            "A rank-deficient parameterization requires more landmarks, parameter locking, or a simpler model.",
            "Identifiability does not establish architecture or production geometry authority.",
        ],
        "production_geometry_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()
    result = analyze_manifest(args.manifest)
    Path(args.output).write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
