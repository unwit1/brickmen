#!/usr/bin/env python3
"""Fit visual body-envelope parameters without moving skeletal joint centers.

This fitter consumes silhouette observations from the reference-landmark files.
It intentionally maps only measurements with an explicit envelope semantic:
  head_width -> head envelope X
  chest_outer_width -> torso envelope X
  waist_outer_width -> abdomen envelope X

Outer shoulder width and hip outer width remain diagnostics unless the target
skeleton explicitly defines compatible visual-envelope primitives for them.
They must never be silently reinterpreted as mechanical joint spacing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from tools.geometry.fit_body_skeleton import load_reference
from tools.geometry.generate_body_skeleton import load_spec

DEFAULT_BINDINGS = {
    "head_width": ("head", "x"),
    "chest_outer_width": ("torso", "x"),
    "waist_outer_width": ("abdomen", "x"),
}

AXIS_INDEX = {"x": 0, "y": 1, "z": 2}


def normalized_visual_widths(reference: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    bbox = reference.get("body_bbox_px")
    pairs = reference.get("silhouette_pairs_px", {})
    if not bbox:
        raise ValueError("BodyEnvelopeProfile fitting requires body_bbox_px")
    if not pairs:
        raise ValueError("Reference has no silhouette_pairs_px")

    left, top, right, bottom = [float(v) for v in bbox]
    height = bottom - top
    if height <= 0:
        raise ValueError("Invalid body_bbox_px")

    out: dict[str, dict[str, Any]] = {}
    for name, pair in pairs.items():
        width = float(pair["right_x"]) - float(pair["left_x"])
        out[name] = {
            "value": width / height,
            "confidence": float(pair.get("confidence", 1.0)),
            "semantic": pair.get("semantic"),
            "notes": pair.get("notes"),
        }
    return out


def _envelope_map(spec: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {item["id"]: item for item in spec.get("envelopes", [])}


def fit_envelope_profile(
    spec: Mapping[str, Any],
    reference: Mapping[str, Any],
    *,
    bindings: Mapping[str, tuple[str, str]] | None = None,
) -> dict[str, Any]:
    bindings = dict(bindings or DEFAULT_BINDINGS)
    observations = normalized_visual_widths(reference)
    envelopes = _envelope_map(spec)
    definitions = spec.get("parameters", {})

    overrides: dict[str, float] = {}
    measurements: dict[str, Any] = {}
    unmapped: dict[str, Any] = {}
    bound_hits: list[str] = []

    for measurement_name, observation in observations.items():
        binding = bindings.get(measurement_name)
        if not binding:
            unmapped[measurement_name] = observation
            continue

        envelope_id, axis_name = binding
        envelope = envelopes.get(envelope_id)
        if not envelope:
            unmapped[measurement_name] = {
                **observation,
                "reason": f"target skeleton has no {envelope_id!r} envelope",
            }
            continue

        modifier = envelope.get("size_modifiers", {}).get(axis_name)
        if not modifier or modifier not in definitions:
            unmapped[measurement_name] = {
                **observation,
                "reason": (
                    f"{envelope_id}.{axis_name} has no independent envelope parameter"
                ),
            }
            continue

        axis = AXIS_INDEX[axis_name]
        base_size = float(envelope["size_norm"][axis])
        if base_size <= 0:
            raise ValueError(f"Envelope {envelope_id} has nonpositive base size")

        raw_scale = float(observation["value"]) / base_size
        definition = definitions[modifier]
        lo = float(definition.get("min", raw_scale))
        hi = float(definition.get("max", raw_scale))
        fitted_scale = min(max(raw_scale, lo), hi)
        if fitted_scale != raw_scale:
            bound_hits.append(modifier)

        fitted_value = base_size * fitted_scale
        overrides[modifier] = fitted_scale
        measurements[measurement_name] = {
            "envelope_id": envelope_id,
            "axis": axis_name,
            "parameter": modifier,
            "observed_normalized": float(observation["value"]),
            "base_normalized": base_size,
            "raw_scale": raw_scale,
            "fitted_scale": fitted_scale,
            "fitted_normalized": fitted_value,
            "residual_normalized": fitted_value - float(observation["value"]),
            "confidence": float(observation["confidence"]),
            "bound_hit": fitted_scale != raw_scale,
        }

    mechanical_names = {
        "shoulder_width_scale",
        "arm_length_scale",
        "torso_height_scale",
        "lower_body_height_scale",
        "stance_width_scale",
    }
    mechanical_changes = sorted(mechanical_names.intersection(overrides))

    return {
        "schema_version": "0.1",
        "reference_id": reference["reference_id"],
        "skeleton_id": spec["skeleton_id"],
        "architecture_id": spec["architecture_id"],
        "parameter_overrides": overrides,
        "measurements": measurements,
        "unmapped_measurements": unmapped,
        "bound_hits": sorted(set(bound_hits)),
        "mechanical_parameter_changes": mechanical_changes,
        "production_geometry_authority": False,
        "warning": (
            "Envelope fitting controls visual mass only. It must not move or validate "
            "mechanical joint centers, connector geometry, or manufacturing tolerances."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skeleton")
    parser.add_argument("reference")
    parser.add_argument("-o", "--output", default=None)
    args = parser.parse_args()

    spec = load_spec(args.skeleton)
    reference = load_reference(args.reference)
    result = fit_envelope_profile(spec, reference)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
