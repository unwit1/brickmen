#!/usr/bin/env python3
"""Compile conservative visual articulation-sweep volumes from conditioning.

These sweeps help visual-shell generation and collision review. They are
intentionally conservative and are NOT physical clearance or tolerance models.
Fixed-mm mechanical keep-outs are attached separately and retain their own
authority state.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _norm(v: Sequence[float]) -> float:
    return math.sqrt(sum(float(x) * float(x) for x in v))


def _unit(v: Sequence[float]) -> list[float]:
    n = _norm(v)
    if n <= 1e-12:
        raise ValueError("Articulation axis must be non-zero")
    return [float(x) / n for x in v]


def rotate_about_axis(
    point: Sequence[float],
    pivot: Sequence[float],
    axis: Sequence[float],
    angle_deg: float,
) -> list[float]:
    """Rodrigues rotation of a point around an axis through pivot."""
    u = _unit(axis)
    theta = math.radians(angle_deg)
    c, s = math.cos(theta), math.sin(theta)
    v = [float(point[i]) - float(pivot[i]) for i in range(3)]
    cross = [
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    ]
    dot = sum(u[i] * v[i] for i in range(3))
    out = [
        v[i] * c + cross[i] * s + u[i] * dot * (1.0 - c)
        for i in range(3)
    ]
    return [float(pivot[i]) + out[i] for i in range(3)]


def _angles(range_deg: Sequence[float], samples: int) -> list[float]:
    lo, hi = map(float, range_deg)
    if samples < 2 or abs(hi - lo) <= 1e-12:
        return [lo]
    return [lo + (hi - lo) * i / (samples - 1) for i in range(samples)]


def _envelope_radius(envelope: Mapping[str, Any], *, normalized: bool) -> float:
    key = (
        "size_normalized_body_height"
        if normalized
        else "size_mm_at_target_height"
    )
    size = envelope.get(key) or [0, 0, 0]
    values = [abs(float(v)) for v in size]
    shape = envelope.get("shape")
    if "between_nodes" in str(shape):
        # Cross-section is encoded in the first two dimensions. Use the larger
        # half-width as a conservative isotropic expansion around the swept link.
        return max(values[:2] or [0.0]) / 2.0
    return math.sqrt(sum((v / 2.0) ** 2 for v in values))


def _aabb(points: Sequence[Sequence[float]], radius: float) -> dict[str, list[float]]:
    mins = [min(float(p[i]) for p in points) - radius for i in range(3)]
    maxs = [max(float(p[i]) for p in points) + radius for i in range(3)]
    return {"min": mins, "max": maxs}


def _volume(aabb: Mapping[str, Sequence[float]]) -> float:
    return math.prod(
        max(0.0, float(aabb["max"][i]) - float(aabb["min"][i]))
        for i in range(3)
    )


def _mechanical_placements(
    conditioning: Mapping[str, Any], anchor_node: str
) -> list[dict[str, Any]]:
    out = []
    for constraint in conditioning.get("mechanical_constraints", []):
        for placement in constraint.get("placements", []):
            if placement.get("anchor_node") == anchor_node:
                out.append(
                    {
                        "joint_profile_id": constraint.get("joint_profile_id"),
                        "authority_class": constraint.get("authority_class"),
                        "manufacturing_authority": constraint.get(
                            "manufacturing_authority", False
                        ),
                        "placement": placement,
                    }
                )
    return out


def compile_articulation_sweeps(
    conditioning: Mapping[str, Any],
    *,
    samples_per_joint: int = 73,
) -> dict[str, Any]:
    nodes = conditioning["skeleton_control"]["nodes"]
    envelopes = {
        item["envelope_id"]: item for item in conditioning["visual_envelopes"]
    }
    joints = conditioning["skeleton_control"]["joints"]
    target_height = float(conditioning["target_height_mm"])

    results = []
    for joint in joints:
        envelope_ids = list(joint.get("visual_envelope_ids") or [])
        if not envelope_ids:
            continue
        joint_id = joint["joint_id"]
        pivot_node = joint_id if joint_id in nodes else joint.get("parent_node")
        if pivot_node not in nodes:
            continue

        pivot_norm = nodes[pivot_node]["position_normalized_body_height"]
        pivot_mm = nodes[pivot_node]["position_mm_at_target_height"]
        axis = joint["axis"]
        angle_samples = _angles(joint["range_deg"], samples_per_joint)
        per_envelope = []

        for envelope_id in envelope_ids:
            if envelope_id not in envelopes:
                continue
            envelope = envelopes[envelope_id]
            norm_points = []
            mm_points = []

            if envelope.get("b_normalized_body_height") is not None:
                moving_norm = envelope["b_normalized_body_height"]
                moving_mm = envelope["b_mm_at_target_height"]
            else:
                center_node = envelope.get("center_node")
                if center_node not in nodes:
                    continue
                moving_norm = nodes[center_node]["position_normalized_body_height"]
                moving_mm = nodes[center_node]["position_mm_at_target_height"]

            for angle in angle_samples:
                norm_points.append(
                    rotate_about_axis(moving_norm, pivot_norm, axis, angle)
                )
                mm_points.append(
                    rotate_about_axis(moving_mm, pivot_mm, axis, angle)
                )

            # Include pivot for linked/capsule-like envelopes so the conservative
            # box covers the whole link rather than only the moving endpoint arc.
            if "between_nodes" in str(envelope.get("shape")):
                norm_points.append(list(pivot_norm))
                mm_points.append(list(pivot_mm))

            radius_norm = _envelope_radius(envelope, normalized=True)
            radius_mm = _envelope_radius(envelope, normalized=False)
            norm_box = _aabb(norm_points, radius_norm)
            mm_box = _aabb(mm_points, radius_mm)
            per_envelope.append(
                {
                    "envelope_id": envelope_id,
                    "shape": envelope.get("shape"),
                    "samples": len(angle_samples),
                    "range_deg": list(map(float, joint["range_deg"])),
                    "radius_approximation_normalized": radius_norm,
                    "radius_approximation_mm": radius_mm,
                    "swept_aabb_normalized_body_height": norm_box,
                    "swept_aabb_mm": mm_box,
                    "swept_aabb_volume_normalized": _volume(norm_box),
                    "swept_aabb_volume_mm3": _volume(mm_box),
                    "approximation":"conservative_endpoint_arc_plus_isotropic_envelope_radius",
                }
            )

        if not per_envelope:
            continue

        all_norm_min = [
            min(e["swept_aabb_normalized_body_height"]["min"][i] for e in per_envelope)
            for i in range(3)
        ]
        all_norm_max = [
            max(e["swept_aabb_normalized_body_height"]["max"][i] for e in per_envelope)
            for i in range(3)
        ]
        all_mm_min = [
            min(e["swept_aabb_mm"]["min"][i] for e in per_envelope)
            for i in range(3)
        ]
        all_mm_max = [
            max(e["swept_aabb_mm"]["max"][i] for e in per_envelope)
            for i in range(3)
        ]

        results.append(
            {
                "joint_id": joint_id,
                "pivot_node": pivot_node,
                "pivot_normalized_body_height": pivot_norm,
                "pivot_mm_at_target_height": pivot_mm,
                "axis": axis,
                "range_deg": joint["range_deg"],
                "visual_envelopes": per_envelope,
                "combined_swept_aabb_normalized_body_height":{
                    "min":all_norm_min,"max":all_norm_max
                },
                "combined_swept_aabb_mm":{"min":all_mm_min,"max":all_mm_max},
                "mechanical_placements_at_pivot": _mechanical_placements(
                    conditioning, pivot_node
                ),
                "authority_class":"visual_articulation_sweep_nonproduction",
            }
        )

    return {
        "schema_version":"0.1",
        "architecture_id":conditioning["architecture_id"],
        "target_height_mm":target_height,
        "conditioning_reference":conditioning.get("source_fits", {}),
        "samples_per_joint":samples_per_joint,
        "joint_sweeps":results,
        "generation_rule":(
            "Generated visual shell should not occupy conservative articulation "
            "sweep volumes unless the architecture explicitly permits overlap or "
            "a later exact collision analysis replaces this approximation."
        ),
        "production_geometry_authority":False,
        "warning":(
            "Sweeps are conservative visual/collision-conditioning approximations. "
            "They do not establish physical clearance, tolerance, torque, wear, "
            "or production articulation limits."
        ),
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("-o","--output",required=True)
    parser.add_argument("--samples",type=int,default=73)
    args=parser.parse_args()
    result=compile_articulation_sweeps(
        load_json(args.conditioning), samples_per_joint=args.samples
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
