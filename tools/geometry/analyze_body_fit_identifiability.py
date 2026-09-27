#!/usr/bin/env python3
"""Diagnose whether body-skeleton parameters are identifiable from a reference.

The analyzer numerically differentiates matched landmark coordinates with
respect to candidate skeleton parameters. It reports:
- zero/weakly observed parameters;
- pairwise near-collinearity (confounding);
- Jacobian rank;
- observation/parameter dimensionality.

This is a model-selection diagnostic, not a fitter and not mechanical
metrology. It prevents adding fine-grained parameters that the current
landmarks cannot actually distinguish.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.geometry.fit_body_skeleton import load_reference, normalized_landmarks
from tools.geometry.generate_body_skeleton import compile_skeleton, load_spec


def _skeleton_parameter_names(spec: Mapping[str, Any]) -> list[str]:
    result: list[str] = []
    for rule in spec.get("parameter_rules", []):
        name = str(rule["parameter"])
        if name not in result:
            result.append(name)
    return result


def _observation_axes(
    spec: Mapping[str, Any],
    reference: Mapping[str, Any],
) -> list[tuple[str, str]]:
    observations = normalized_landmarks(reference)
    model = compile_skeleton(spec, target_height_mm=1.0)["nodes_mm"]
    labels: list[tuple[str, str]] = []
    for node_id, obs in observations.items():
        if node_id not in model:
            continue
        target = obs["coords"]
        axes = obs.get("axes") or [
            axis for axis in ("x", "y", "z") if axis in target
        ]
        for axis in axes:
            if axis in target:
                labels.append((node_id, axis))
    return labels


def _vector(
    compiled: Mapping[str, Any],
    labels: Sequence[tuple[str, str]],
) -> list[float]:
    axis_index = {"x": 0, "y": 1, "z": 2}
    return [
        float(compiled["nodes_mm"][node_id][axis_index[axis]])
        for node_id, axis in labels
    ]


def _parameter_step(
    definition: Mapping[str, Any],
    value: float,
    *,
    fraction: float,
) -> float:
    lo = float(definition.get("min", value))
    hi = float(definition.get("max", value))
    span = hi - lo
    if span <= 0:
        return 0.0
    return max(span * fraction, 1e-6)


def _derivative_column(
    spec: Mapping[str, Any],
    labels: Sequence[tuple[str, str]],
    params: Mapping[str, float],
    name: str,
    *,
    fraction: float,
) -> list[float]:
    definition = spec["parameters"][name]
    base = float(params[name])
    lo = float(definition.get("min", base))
    hi = float(definition.get("max", base))
    step = _parameter_step(definition, base, fraction=fraction)
    if step <= 0:
        return [0.0] * len(labels)

    low = max(lo, base - step)
    high = min(hi, base + step)
    if high <= low:
        return [0.0] * len(labels)

    low_params = dict(params)
    high_params = dict(params)
    low_params[name] = low
    high_params[name] = high
    low_vec = _vector(
        compile_skeleton(spec, target_height_mm=1.0, parameter_overrides=low_params),
        labels,
    )
    high_vec = _vector(
        compile_skeleton(spec, target_height_mm=1.0, parameter_overrides=high_params),
        labels,
    )
    denominator = high - low
    return [(b - a) / denominator for a, b in zip(low_vec, high_vec)]


def _norm(values: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in values))


def _cosine(a: Sequence[float], b: Sequence[float]) -> float | None:
    na = _norm(a)
    nb = _norm(b)
    if na <= 1e-15 or nb <= 1e-15:
        return None
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


def matrix_rank(rows: list[list[float]], tolerance: float = 1e-8) -> int:
    """Small dependency-free Gaussian-elimination rank."""
    if not rows or not rows[0]:
        return 0
    a = [list(map(float, row)) for row in rows]
    m = len(a)
    n = len(a[0])
    rank = 0
    col = 0
    while rank < m and col < n:
        pivot = max(range(rank, m), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) <= tolerance:
            col += 1
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        pivot_value = a[rank][col]
        a[rank] = [value / pivot_value for value in a[rank]]
        for r in range(m):
            if r == rank:
                continue
            factor = a[r][col]
            if abs(factor) <= tolerance:
                continue
            a[r] = [
                a[r][c] - factor * a[rank][c]
                for c in range(n)
            ]
        rank += 1
        col += 1
    return rank


def analyze_identifiability(
    spec: Mapping[str, Any],
    reference: Mapping[str, Any],
    *,
    parameter_names: Sequence[str] | None = None,
    parameter_values: Mapping[str, float] | None = None,
    derivative_fraction: float = 0.01,
    zero_norm_threshold: float = 1e-8,
    confounded_cosine_threshold: float = 0.995,
) -> dict[str, Any]:
    labels = _observation_axes(spec, reference)
    if not labels:
        raise ValueError("No reference landmark axes match skeleton nodes")

    definitions = spec.get("parameters", {})
    if parameter_names is None:
        parameter_names = (
            reference.get("fit_parameters") or _skeleton_parameter_names(spec)
        )
    parameter_names = [name for name in parameter_names if name in definitions]
    if not parameter_names:
        raise ValueError("No candidate parameters exist in the skeleton")

    params = {
        name: float(definition["default"])
        for name, definition in definitions.items()
    }
    if parameter_values:
        for name, value in parameter_values.items():
            if name in params:
                params[name] = float(value)

    columns: dict[str, list[float]] = {
        name: _derivative_column(
            spec,
            labels,
            params,
            name,
            fraction=derivative_fraction,
        )
        for name in parameter_names
    }
    norms = {name: _norm(column) for name, column in columns.items()}
    unobserved = sorted(
        name for name, value in norms.items() if value <= zero_norm_threshold
    )

    pairwise = []
    confounded_pairs = []
    for i, left in enumerate(parameter_names):
        for right in parameter_names[i + 1 :]:
            cosine = _cosine(columns[left], columns[right])
            item = {
                "parameter_a": left,
                "parameter_b": right,
                "cosine": cosine,
                "absolute_cosine": abs(cosine) if cosine is not None else None,
            }
            pairwise.append(item)
            if (
                cosine is not None
                and abs(cosine) >= confounded_cosine_threshold
            ):
                confounded_pairs.append(item)

    # Jacobian rows are observations, columns are parameters.
    jacobian_rows = [
        [columns[name][row] for name in parameter_names]
        for row in range(len(labels))
    ]
    rank = matrix_rank(jacobian_rows)

    if rank == len(parameter_names) and not unobserved:
        status = "locally_identifiable"
    elif rank == 0:
        status = "unidentifiable"
    else:
        status = "partially_identifiable"

    return {
        "schema_version": "0.1",
        "reference_id": reference["reference_id"],
        "skeleton_id": spec["skeleton_id"],
        "candidate_parameters": list(parameter_names),
        "observation_axes": [
            {"node_id": node_id, "axis": axis} for node_id, axis in labels
        ],
        "observation_dimension": len(labels),
        "parameter_count": len(parameter_names),
        "jacobian_rank": rank,
        "identifiable_dimension_count": rank,
        "status": status,
        "sensitivity_norms": norms,
        "unobserved_parameters": unobserved,
        "confounded_pairs": confounded_pairs,
        "pairwise_cosines": pairwise,
        "diagnostic_rules": {
            "zero_norm_threshold": zero_norm_threshold,
            "confounded_cosine_threshold": confounded_cosine_threshold,
            "derivative_fraction_of_parameter_range": derivative_fraction,
        },
        "production_geometry_authority": False,
        "warning": (
            "Local sensitivity/identifiability only. A full-rank landmark fit does "
            "not prove architecture identity or manufacturing geometry."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skeleton")
    parser.add_argument("reference")
    parser.add_argument("--param", action="append", default=[])
    parser.add_argument("--derivative-fraction", type=float, default=0.01)
    parser.add_argument("-o", "--output", default=None)
    args = parser.parse_args()

    spec = load_spec(args.skeleton)
    reference = load_reference(args.reference)
    result = analyze_identifiability(
        spec,
        reference,
        parameter_names=args.param or None,
        derivative_fraction=args.derivative_fraction,
    )
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
