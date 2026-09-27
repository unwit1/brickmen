#!/usr/bin/env python3
"""Fit visual body-envelope parameters without moving skeletal joint centers.

Horizontal measurements are view-aware:
- front/back: width maps to body X;
- left/right: depth maps to body Y.

Vertical silhouette spans can map to visual envelope Z, currently including
head height. Three-quarter views remain diagnostic unless an explicit binding
is supplied.

Outer shoulder/hip silhouette spans stay unmapped until a dedicated visual
primitive exists; they are never silently reinterpreted as joint spacing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from tools.geometry.fit_body_skeleton import load_reference
from tools.geometry.generate_body_skeleton import load_spec

FRONT_BACK_BINDINGS = {
    "head_width": ("head", "x"),
    "chest_outer_width": ("torso", "x"),
    "waist_outer_width": ("abdomen", "x"),
}

SIDE_BINDINGS = {
    "head_depth": ("head", "y"),
    "chest_outer_depth": ("torso", "y"),
    "waist_outer_depth": ("abdomen", "y"),
}

VERTICAL_BINDINGS = {
    "head_height": ("head", "z"),
}

AXIS_INDEX = {"x": 0, "y": 1, "z": 2}


def default_bindings_for_view(view: str) -> dict[str, tuple[str, str]]:
    if view in {"front", "back"}:
        bindings = dict(FRONT_BACK_BINDINGS)
    elif view in {"left", "right"}:
        bindings = dict(SIDE_BINDINGS)
    elif view == "multi_view":
        bindings = {**FRONT_BACK_BINDINGS, **SIDE_BINDINGS}
    else:
        bindings = {}
    bindings.update(VERTICAL_BINDINGS)
    return bindings


def normalized_visual_measurements(
    reference: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    bbox = reference.get("body_bbox_px")
    horizontal = reference.get("silhouette_pairs_px", {})
    vertical = reference.get("silhouette_vertical_pairs_px", {})
    direct = reference.get("envelope_measurements_normalized", {})
    if not horizontal and not vertical and not direct:
        raise ValueError("Reference has no visual envelope observations")

    height = None
    if horizontal or vertical:
        if not bbox:
            raise ValueError("Pixel envelope observations require body_bbox_px")
        left, top, right, bottom = [float(v) for v in bbox]
        height = bottom - top
        if height <= 0:
            raise ValueError("Invalid body_bbox_px")

    out: dict[str, dict[str, Any]] = {}
    for name, pair in horizontal.items():
        span = float(pair["right_x"]) - float(pair["left_x"])
        assert height is not None
        out[name] = {
            "value": span / height,
            "span_px": span,
            "orientation": "horizontal",
            "confidence": float(pair.get("confidence", 1.0)),
            "semantic": pair.get("semantic"),
            "notes": pair.get("notes"),
        }

    for name, pair in vertical.items():
        span = float(pair["bottom_y"]) - float(pair["top_y"])
        assert height is not None
        out[name] = {
            "value": span / height,
            "span_px": span,
            "orientation": "vertical",
            "confidence": float(pair.get("confidence", 1.0)),
            "semantic": pair.get("semantic"),
            "notes": pair.get("notes"),
        }
    for name, observation in direct.items():
        value = float(observation["value"])
        if value < 0:
            raise ValueError(f"Normalized envelope measurement {name} is negative")
        out[name] = {
            "value": value,
            "orientation": "normalized_direct",
            "confidence": float(observation.get("confidence", 1.0)),
            "semantic": observation.get("semantic"),
            "notes": observation.get("notes"),
            "source": observation.get("source"),
            "binding": (
                str(observation["envelope_id"]),
                str(observation["axis"]),
            ),
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
    resolved_bindings = (
        dict(bindings)
        if bindings is not None
        else default_bindings_for_view(str(reference.get("view", "unknown")))
    )
    observations = normalized_visual_measurements(reference)
    envelopes = _envelope_map(spec)
    definitions = spec.get("parameters", {})

    overrides: dict[str, float] = {}
    measurements: dict[str, Any] = {}
    unmapped: dict[str, Any] = {}
    bound_hits: list[str] = []

    for measurement_name, observation in observations.items():
        binding = observation.get("binding") or resolved_bindings.get(measurement_name)
        if not binding:
            unmapped[measurement_name] = {
                **observation,
                "reason": (
                    f"no default visual-envelope binding for view "
                    f"{reference.get('view', 'unknown')!r}"
                ),
            }
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
            "orientation": observation["orientation"],
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
        "lower_torso_length_scale",
        "upper_torso_length_scale",
        "neck_head_offset_scale",
        "thigh_length_scale",
        "shin_length_scale",
    }
    mechanical_changes = sorted(mechanical_names.intersection(overrides))

    return {
        "schema_version": "0.3",
        "reference_id": reference["reference_id"],
        "view": reference.get("view"),
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
