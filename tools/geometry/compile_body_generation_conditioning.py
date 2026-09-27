#!/usr/bin/env python3
"""Compile fitted Brickmen body evidence into provider-neutral generation controls.

This is the deterministic handoff between reference fitting and learned/agentic
shell generation. It deliberately keeps three layers separate:

1. skeleton/proportion controls;
2. visual body-envelope controls;
3. mechanical interface / keep-out constraints.

The compiler never upgrades reference CAD or validation-pending joint profiles
into production geometry authority.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.geometry.fit_body_envelope_profile import fit_envelope_profile
from tools.geometry.fit_body_skeleton import fit_skeleton, load_reference
from tools.geometry.generate_body_skeleton import compile_skeleton, load_spec


PRODUCTION_INTERFACE_STATUSES = {"production_approved"}
PROTOTYPE_INTERFACE_STATUSES = {"validated_prototype"}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def skeleton_parameter_names(spec: Mapping[str, Any]) -> list[str]:
    result: list[str] = []
    for rule in spec.get("parameter_rules", []):
        name = str(rule["parameter"])
        if name not in result:
            result.append(name)
    return result


def envelope_parameter_names(spec: Mapping[str, Any]) -> list[str]:
    result: list[str] = []
    for envelope in spec.get("envelopes", []):
        for name in envelope.get("size_modifiers", {}).values():
            name = str(name)
            if name not in result:
                result.append(name)
    return result


def _node_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {
        node["id"]: {
            key: node.get(key)
            for key in ("role", "semantic_side", "functional")
            if key in node
        }
        for node in spec.get("nodes", [])
    }


def _envelopes(
    normalized: Mapping[str, Any],
    physical: Mapping[str, Any],
) -> list[dict[str, Any]]:
    mm_by_id = {item["id"]: item for item in physical.get("envelopes", [])}
    result = []
    for item in normalized.get("envelopes", []):
        mm = mm_by_id.get(item["id"], {})
        result.append(
            {
                "envelope_id": item["id"],
                "shape": item.get("shape"),
                "center_node": item.get("center_node"),
                "size_normalized_body_height": item.get("size_mm"),
                "size_mm_at_target_height": mm.get("size_mm"),
                "visual_only": True,
            }
        )
    return result


def compile_joint_constraint(
    profile: Mapping[str, Any],
    *,
    target_height_mm: float,
) -> dict[str, Any]:
    manufacturing_status = str(
        profile.get("manufacturing_status", profile.get("status", "unknown"))
    )
    if manufacturing_status in PRODUCTION_INTERFACE_STATUSES:
        authority = "production_approved_deterministic_interface"
        manufacturing_authority = True
    elif manufacturing_status in PROTOTYPE_INTERFACE_STATUSES:
        authority = "validated_prototype_not_production"
        manufacturing_authority = False
    else:
        authority = "reference_only_not_manufacturing_authority"
        manufacturing_authority = False

    shell_interface = profile.get("shell_interface", {})
    bbox_mm = shell_interface.get("reference_keepout_bbox_mm")
    bbox_norm = None
    if bbox_mm:
        bbox_norm = [float(value) / target_height_mm for value in bbox_mm]

    return {
        "joint_profile_id": profile.get("joint_profile_id"),
        "primitive_type": profile.get("primitive_type"),
        "parent_component_role": profile.get("parent_component_role"),
        "child_component_role": profile.get("child_component_role"),
        "degrees_of_freedom": profile.get("degrees_of_freedom"),
        "axes": profile.get("axes"),
        "manufacturing_status": manufacturing_status,
        "authority_class": authority,
        "manufacturing_authority": manufacturing_authority,
        "hardware_bom": profile.get("hardware_bom", []),
        "reference_keepout_bbox_mm": bbox_mm,
        "reference_keepout_normalized_at_target_height": bbox_norm,
        "keepout_status": shell_interface.get("keepout_status"),
        "required_validation": profile.get("required_validation", []),
        "hard_rules": profile.get("hard_rules", []),
        "warning": (
            "Normalized keep-out size is a conditioning convenience only. Fixed "
            "commodity hardware dimensions remain in millimeters and must never "
            "scale with the character body."
        ) if bbox_mm else None,
    }


def compile_conditioning(
    spec: Mapping[str, Any],
    *,
    skeleton_fit: Mapping[str, Any] | None = None,
    envelope_fit: Mapping[str, Any] | None = None,
    joint_profiles: Sequence[Mapping[str, Any]] = (),
    target_height_mm: float | None = None,
) -> dict[str, Any]:
    target_height = float(
        target_height_mm
        if target_height_mm is not None
        else spec["default_target_height_mm"]
    )
    if target_height <= 0:
        raise ValueError("target_height_mm must be positive")

    parameters = {
        name: float(definition["default"])
        for name, definition in spec.get("parameters", {}).items()
    }
    locked_parameters: dict[str, float] = {}

    if skeleton_fit:
        for name, value in skeleton_fit.get("fit_parameters", {}).items():
            if name in parameters:
                parameters[name] = float(value)
        locked_parameters = {
            name: float(value)
            for name, value in skeleton_fit.get("locked_parameters", {}).items()
        }

    if envelope_fit:
        for name, value in envelope_fit.get("parameter_overrides", {}).items():
            if name not in parameters:
                raise ValueError(f"Envelope fit references unknown parameter {name}")
            parameters[name] = float(value)

    normalized = compile_skeleton(
        spec,
        target_height_mm=1.0,
        parameter_overrides=parameters,
    )
    physical = compile_skeleton(
        spec,
        target_height_mm=target_height,
        parameter_overrides=parameters,
    )

    skeleton_names = skeleton_parameter_names(spec)
    envelope_names = envelope_parameter_names(spec)
    mechanical_shape = {
        name: parameters[name] for name in skeleton_names if name in parameters
    }
    visual_envelope = {
        name: parameters[name] for name in envelope_names if name in parameters
    }
    other = {
        name: value
        for name, value in parameters.items()
        if name not in set(skeleton_names) | set(envelope_names)
    }

    joint_constraints = [
        compile_joint_constraint(profile, target_height_mm=target_height)
        for profile in joint_profiles
    ]

    generation_contract = spec.get("generation_contract", {})
    shell_editable = list(generation_contract.get("shell_editable_regions", []))
    locked_regions = list(generation_contract.get("locked_regions", []))

    constraints = [
        "Treat skeleton landmarks as proportion/alignment controls, not printable connector geometry.",
        "Treat visual envelopes as editable shell targets independent from joint spacing.",
        "Do not allow generated geometry to overwrite deterministic or reserved mechanical interface regions.",
    ]
    if locked_regions:
        constraints.append(
            "Preserve locked architecture regions: " + ", ".join(locked_regions) + "."
        )
    for constraint in joint_constraints:
        profile_id = constraint.get("joint_profile_id") or "unnamed_joint_profile"
        if constraint["authority_class"] == "reference_only_not_manufacturing_authority":
            constraints.append(
                f"{profile_id} is reference-only: preserve its hardware/keep-out intent "
                "but do not infer socket tolerances, friction, or production mating geometry."
            )
        elif constraint["authority_class"] == "validated_prototype_not_production":
            constraints.append(
                f"{profile_id} is validated only as a prototype; do not silently "
                "promote it to production geometry."
            )
        else:
            constraints.append(
                f"{profile_id} is a production-approved deterministic interface; "
                "generated shell geometry must preserve it exactly."
            )

    node_meta = _node_metadata(spec)
    skeleton_nodes = {
        node_id: {
            "position_normalized_body_height": normalized["nodes_mm"][node_id],
            "position_mm_at_target_height": physical["nodes_mm"][node_id],
            **node_meta.get(node_id, {}),
        }
        for node_id in normalized["nodes_mm"]
    }

    return {
        "schema_version": "0.1",
        "architecture_id": spec["architecture_id"],
        "skeleton_id": spec["skeleton_id"],
        "target_height_mm": target_height,
        "source_fits": {
            "skeleton_reference_id": (
                skeleton_fit.get("reference_id") if skeleton_fit else None
            ),
            "skeleton_reference_height_mm": (
                skeleton_fit.get("target_height_mm") if skeleton_fit else None
            ),
            "skeleton_fit_status": (
                skeleton_fit.get("fit_status") if skeleton_fit else None
            ),
            "envelope_reference_id": (
                envelope_fit.get("reference_id") if envelope_fit else None
            ),
            "envelope_bound_hits": (
                envelope_fit.get("bound_hits", []) if envelope_fit else []
            ),
        },
        "parameter_layers": {
            "mechanical_shape_and_landmarks": mechanical_shape,
            "visual_envelope": visual_envelope,
            "other": other,
            "locked_parameters": locked_parameters,
            "rule": (
                "Mechanical-shape parameters move skeleton landmarks; visual-envelope "
                "parameters resize shell targets. One layer must not silently substitute "
                "for the other."
            ),
        },
        "skeleton_control": {
            "coordinate_system": spec.get("coordinate_system"),
            "nodes": skeleton_nodes,
            "bones": normalized.get("bones", []),
            "joints": normalized.get("joints", []),
            "production_geometry_authority": False,
        },
        "visual_envelopes": _envelopes(normalized, physical),
        "component_plan": {
            "shell_editable_regions": shell_editable,
            "locked_regions": locked_regions,
            "default_lower_body_mode": generation_contract.get(
                "default_lower_body_mode"
            ),
        },
        "mechanical_constraints": joint_constraints,
        "conditioning_channels": {
            "skeleton_landmarks": "skeleton_control.nodes",
            "skeleton_links": "skeleton_control.bones",
            "visual_mass_boxes_or_capsules": "visual_envelopes",
            "component_editability": "component_plan",
            "mechanical_keepouts_and_hardware": "mechanical_constraints",
        },
        "generation_constraints": constraints,
        "production_geometry_authority": False,
        "warning": (
            "This payload conditions visual/part-aware generation. It is not a "
            "manufacturing drawing. Only separately validated deterministic interface "
            "records may authorize fit-critical production geometry."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skeleton")
    parser.add_argument("--skeleton-reference", default=None)
    parser.add_argument("--envelope-reference", default=None)
    parser.add_argument("--joint-profile", action="append", default=[])
    parser.add_argument("--target-height-mm", type=float, default=None)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()

    spec = load_spec(args.skeleton)

    skeleton_fit = None
    if args.skeleton_reference:
        skeleton_reference = load_reference(args.skeleton_reference)
        skeleton_fit = fit_skeleton(spec, skeleton_reference)

    envelope_fit = None
    if args.envelope_reference:
        envelope_reference = load_reference(args.envelope_reference)
        envelope_fit = fit_envelope_profile(spec, envelope_reference)

    joint_profiles = [load_json(path) for path in args.joint_profile]
    result = compile_conditioning(
        spec,
        skeleton_fit=skeleton_fit,
        envelope_fit=envelope_fit,
        joint_profiles=joint_profiles,
        target_height_mm=args.target_height_mm,
    )
    Path(args.output).write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
