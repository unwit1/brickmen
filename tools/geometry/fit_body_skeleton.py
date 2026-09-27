#!/usr/bin/env python3
"""Fit a Brickmen generation skeleton to reference landmarks.

This fitter solves *proportion parameters only*. It deliberately does not
derive or modify manufacturing-critical connector geometry.

Reference landmarks may be supplied as pixels inside a body bounding box or
already normalized in body-height units. Front/back fitting uses X/Z.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

from tools.geometry.generate_body_skeleton import compile_skeleton, load_spec


def load_reference(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        ref = json.load(fh)
    validate_reference(ref)
    return ref


def validate_reference(ref: Mapping[str, Any]) -> None:
    required = ["reference_id", "view", "evidence_class", "landmarks"]
    missing = [key for key in required if key not in ref]
    if missing:
        raise ValueError(f"Reference missing required keys: {missing}")

    mode = ref.get("landmark_coordinate_mode", "pixel")
    if mode == "pixel":
        if "body_bbox_px" not in ref:
            raise ValueError("Pixel references require body_bbox_px")
        bbox = ref["body_bbox_px"]
        if len(bbox) != 4 or bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
            raise ValueError("Invalid body_bbox_px")

    for name, obs in ref["landmarks"].items():
        position = obs.get("position")
        if not isinstance(position, list) or len(position) not in (2, 3):
            raise ValueError(f"Landmark {name} must have a 2D or 3D position")
        confidence = float(obs.get("confidence", 1.0))
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Landmark {name} confidence must be in [0, 1]")


def known_height_nominal(ref: Mapping[str, Any]) -> float | None:
    value = ref.get("known_height_mm")
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Mapping):
        if value.get("nominal") is not None:
            return float(value["nominal"])
        lo = value.get("min")
        hi = value.get("max")
        if lo is not None and hi is not None:
            return (float(lo) + float(hi)) / 2.0
    return None


def normalized_landmarks(ref: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Convert observations to body-height-normalized x/y/z coordinates.

    Pixel convention:
      - bbox = [left, top, right, bottom]
      - X zero is bbox horizontal center
      - Z zero is bbox bottom, increasing upward
      - Y is unavailable for ordinary 2D references

    A two-element pixel position is [x_px, y_px].
    """
    mode = ref.get("landmark_coordinate_mode", "pixel")
    out: Dict[str, Dict[str, Any]] = {}

    if mode == "normalized_body_height":
        for name, obs in ref["landmarks"].items():
            pos = [float(v) for v in obs["position"]]
            if len(pos) == 2:
                coords = {"x": pos[0], "z": pos[1]}
            else:
                coords = {"x": pos[0], "y": pos[1], "z": pos[2]}
            out[name] = {
                "coords": coords,
                "confidence": float(obs.get("confidence", 1.0)),
                "axes": obs.get("axes"),
            }
        return out

    left, top, right, bottom = [float(v) for v in ref["body_bbox_px"]]
    height = bottom - top
    center_x = (left + right) / 2.0

    for name, obs in ref["landmarks"].items():
        pos = [float(v) for v in obs["position"]]
        x_px, y_px = pos[0], pos[1]
        coords = {
            "x": (x_px - center_x) / height,
            "z": (bottom - y_px) / height,
        }
        out[name] = {
            "coords": coords,
            "confidence": float(obs.get("confidence", 1.0)),
            "axes": obs.get("axes"),
        }
    return out


def compiled_normalized_positions(
    spec: Mapping[str, Any], params: Mapping[str, float]
) -> Dict[str, Dict[str, float]]:
    compiled = compile_skeleton(
        spec, target_height_mm=1.0, parameter_overrides=params
    )
    return {
        node_id: {"x": p[0], "y": p[1], "z": p[2]}
        for node_id, p in compiled["nodes_mm"].items()
    }


def landmark_loss(
    spec: Mapping[str, Any],
    observations: Mapping[str, Mapping[str, Any]],
    params: Mapping[str, float],
) -> tuple[float, Dict[str, Any]]:
    model = compiled_normalized_positions(spec, params)
    weighted_sq = 0.0
    total_weight = 0.0
    residuals: Dict[str, Any] = {}

    for node_id, obs in observations.items():
        if node_id not in model:
            continue
        confidence = float(obs.get("confidence", 1.0))
        if confidence <= 0:
            continue
        target = obs["coords"]
        requested_axes = obs.get("axes")
        axes = requested_axes or [a for a in ("x", "y", "z") if a in target]
        per_axis = {}
        point_sq = 0.0
        axis_count = 0
        for axis in axes:
            if axis not in target:
                continue
            delta = model[node_id][axis] - float(target[axis])
            per_axis[axis] = delta
            point_sq += delta * delta
            axis_count += 1
        if not axis_count:
            continue
        point_mse = point_sq / axis_count
        weighted_sq += confidence * point_mse
        total_weight += confidence
        residuals[node_id] = {
            "axes": per_axis,
            "normalized_distance": math.sqrt(point_sq),
            "confidence": confidence,
        }

    if total_weight == 0:
        raise ValueError("No reference landmarks matched skeleton node IDs")

    loss = weighted_sq / total_weight
    return loss, residuals


def _candidate_values(
    definition: Mapping[str, Any],
    current: float,
    *,
    span_fraction: float,
    samples: int,
) -> list[float]:
    lo = float(definition.get("min", current))
    hi = float(definition.get("max", current))
    full_span = hi - lo
    half = max(full_span * span_fraction / 2.0, full_span / 1000.0)
    start = max(lo, current - half)
    end = min(hi, current + half)
    if samples <= 1 or end <= start:
        return [current]
    step = (end - start) / (samples - 1)
    values = [start + i * step for i in range(samples)]
    values.append(current)
    return sorted(set(round(v, 10) for v in values))


def _skeleton_parameter_names(spec: Mapping[str, Any]) -> list[str]:
    """Return parameters that actually alter skeleton node coordinates.

    Envelope-only parameters intentionally stay out of landmark fitting unless a
    caller explicitly requests them. This prevents visual mass controls from
    being mistaken for mechanical/proportion controls.
    """
    names: list[str] = []
    for rule in spec.get("parameter_rules", []):
        name = rule["parameter"]
        if name not in names:
            names.append(name)
    return names


def _validated_locked_parameters(
    definitions: Mapping[str, Mapping[str, Any]],
    values: Mapping[str, Any],
) -> Dict[str, float]:
    locked: Dict[str, float] = {}
    unknown = set(values) - set(definitions)
    if unknown:
        raise ValueError(f"Unknown locked skeleton parameters: {sorted(unknown)}")

    for name, raw in values.items():
        value = float(raw)
        definition = definitions[name]
        lo = definition.get("min")
        hi = definition.get("max")
        if lo is not None and value < float(lo):
            raise ValueError(f"Locked {name}={value} is below minimum {lo}")
        if hi is not None and value > float(hi):
            raise ValueError(f"Locked {name}={value} is above maximum {hi}")
        locked[name] = value
    return locked


def fit_skeleton(
    spec: Mapping[str, Any],
    reference: Mapping[str, Any],
    *,
    parameter_names: Sequence[str] | None = None,
    locked_parameters: Mapping[str, float] | None = None,
    passes: int = 6,
    samples_per_parameter: int = 13,
) -> Dict[str, Any]:
    observations = normalized_landmarks(reference)
    definitions = spec.get("parameters", {})

    reference_locks = reference.get("locked_parameters") or {}
    merged_locks = dict(reference_locks)
    if locked_parameters:
        merged_locks.update(locked_parameters)
    locked = _validated_locked_parameters(definitions, merged_locks)

    if parameter_names is None:
        parameter_names = (
            reference.get("fit_parameters") or _skeleton_parameter_names(spec)
        )
    parameter_names = [
        name
        for name in parameter_names
        if name in definitions and name not in locked
    ]

    params = {name: float(defn["default"]) for name, defn in definitions.items()}
    params.update(locked)
    initial_loss, initial_residuals = landmark_loss(
        spec, observations, params
    )

    history = []
    for pass_index in range(passes):
        span_fraction = 1.0 / (2 ** pass_index)
        improved_this_pass = False
        for name in parameter_names:
            best_value = params[name]
            best_loss, _ = landmark_loss(spec, observations, params)
            for value in _candidate_values(
                definitions[name],
                params[name],
                span_fraction=span_fraction,
                samples=samples_per_parameter,
            ):
                trial = dict(params)
                trial[name] = value
                trial_loss, _ = landmark_loss(spec, observations, trial)
                if trial_loss + 1e-12 < best_loss:
                    best_loss = trial_loss
                    best_value = value
            if best_value != params[name]:
                params[name] = best_value
                improved_this_pass = True
            history.append(
                {
                    "pass": pass_index,
                    "parameter": name,
                    "value": params[name],
                    "loss": best_loss,
                }
            )
        if not improved_this_pass and pass_index >= 2:
            break

    final_loss, final_residuals = landmark_loss(spec, observations, params)
    rmse = math.sqrt(final_loss)
    initial_rmse = math.sqrt(initial_loss)

    if rmse <= 0.025:
        fit_status = "strong_visual_fit"
    elif rmse <= 0.05:
        fit_status = "usable_visual_fit"
    elif rmse <= 0.08:
        fit_status = "weak_fit_review_required"
    else:
        fit_status = "architecture_or_landmarks_mismatch"

    target_height = known_height_nominal(reference)
    if target_height is None:
        target_height = float(spec["default_target_height_mm"])

    bound_hits = []
    for name in parameter_names:
        definition = definitions[name]
        lo = float(definition.get("min", params[name]))
        hi = float(definition.get("max", params[name]))
        tolerance = max((hi - lo) * 0.005, 1e-9)
        if abs(params[name] - lo) <= tolerance:
            bound_hits.append(
                {"parameter": name, "bound": "min", "value": params[name]}
            )
        elif abs(params[name] - hi) <= tolerance:
            bound_hits.append(
                {"parameter": name, "bound": "max", "value": params[name]}
            )

    diagnostic_flags = []
    if locked:
        diagnostic_flags.append("one_or_more_parameters_locked_to_reference_frame")
    if bound_hits:
        diagnostic_flags.append("one_or_more_parameters_hit_bounds")
    if (
        fit_status in {"weak_fit_review_required", "architecture_or_landmarks_mismatch"}
        and len(bound_hits) >= 2
    ):
        diagnostic_flags.append("skeleton_design_space_may_be_too_narrow")
    if reference.get("architecture_candidate_id") not in (
        None,
        spec["architecture_id"],
    ):
        diagnostic_flags.append("reference_architecture_differs_from_brickmen_target")

    return {
        "schema_version": "0.3",
        "reference_id": reference["reference_id"],
        "reference_architecture_candidate_id": reference.get(
            "architecture_candidate_id"
        ),
        "skeleton_id": spec["skeleton_id"],
        "architecture_id": spec["architecture_id"],
        "evidence_class": reference["evidence_class"],
        "target_height_mm": target_height,
        "fit_parameters": params,
        "locked_parameters": locked,
        "optimized_parameter_names": list(parameter_names),
        "initial_normalized_rmse": initial_rmse,
        "final_normalized_rmse": rmse,
        "fit_status": fit_status,
        "matched_landmark_count": len(final_residuals),
        "reference_landmark_count": len(observations),
        "bound_hits": bound_hits,
        "diagnostic_flags": diagnostic_flags,
        "residuals": final_residuals,
        "history": history,
        "production_geometry_authority": False,
        "warning": (
            "Reference fitting estimates proportions only. It does not validate "
            "or derive connector/joint manufacturing dimensions."
        ),
    }


def parse_params(values: Iterable[str]) -> list[str]:
    return [value.strip() for value in values if value.strip()]


def parse_param_values(values: Iterable[str]) -> Dict[str, float]:
    result: Dict[str, float] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Locked parameter must be name=value: {value}")
        name, raw = value.split("=", 1)
        result[name.strip()] = float(raw)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skeleton")
    parser.add_argument("reference")
    parser.add_argument(
        "--fit-param",
        action="append",
        default=[],
        help="Restrict optimization to this parameter; repeat as needed.",
    )
    parser.add_argument(
        "--lock-param",
        action="append",
        default=[],
        help=(
            "Lock a skeleton parameter to name=value while fitting; repeat as "
            "needed. Reference-file locked_parameters are applied first."
        ),
    )
    parser.add_argument("--passes", type=int, default=6)
    parser.add_argument("--samples", type=int, default=13)
    parser.add_argument("-o", "--output", default=None)
    args = parser.parse_args()

    spec = load_spec(args.skeleton)
    reference = load_reference(args.reference)
    fit = fit_skeleton(
        spec,
        reference,
        parameter_names=parse_params(args.fit_param) or None,
        locked_parameters=parse_param_values(args.lock_param) or None,
        passes=args.passes,
        samples_per_parameter=args.samples,
    )
    payload = json.dumps(fit, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
