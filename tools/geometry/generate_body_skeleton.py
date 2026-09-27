#!/usr/bin/env python3
"""Compile Brickmen normalized body skeletons into world-space coordinates.

This tool intentionally handles generation/alignment skeletons only.
It does not create production connector geometry. Production joints must be
instantiated from validated JointCartridge / ConnectorProfile records.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

AXIS_INDEX = {"x": 0, "y": 1, "z": 2}


def load_spec(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        spec = json.load(fh)
    validate_spec(spec)
    return spec


def validate_spec(spec: Mapping[str, Any]) -> None:
    required = [
        "skeleton_id",
        "architecture_id",
        "default_target_height_mm",
        "nodes",
        "bones",
        "joints",
    ]
    missing = [key for key in required if key not in spec]
    if missing:
        raise ValueError(f"Skeleton spec missing required keys: {missing}")

    node_ids = [node["id"] for node in spec["nodes"]]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("Skeleton contains duplicate node IDs")
    node_set = set(node_ids)

    for node in spec["nodes"]:
        pos = node.get("position_norm")
        if not isinstance(pos, list) or len(pos) != 3:
            raise ValueError(f"Node {node.get('id')} needs a 3-vector position_norm")

    for bone in spec["bones"]:
        if bone["a"] not in node_set or bone["b"] not in node_set:
            raise ValueError(f"Bone {bone.get('id')} references an unknown node")

    for joint in spec["joints"]:
        if joint["parent_node"] not in node_set or joint["child_node"] not in node_set:
            raise ValueError(f"Joint {joint.get('joint_id')} references an unknown node")

    for rule in spec.get("parameter_rules", []):
        if rule["parameter"] not in spec.get("parameters", {}):
            raise ValueError(f"Rule references unknown parameter {rule['parameter']}")
        unknown = set(rule.get("nodes", [])) - node_set
        if unknown:
            raise ValueError(f"Rule references unknown nodes: {sorted(unknown)}")
        anchor = rule.get("anchor_node")
        if anchor and anchor not in node_set:
            raise ValueError(f"Rule references unknown anchor node {anchor}")
        endpoint = rule.get("endpoint_node")
        if endpoint and endpoint not in node_set:
            raise ValueError(f"Rule references unknown endpoint node {endpoint}")
        unknown_descendants = set(rule.get("descendant_nodes", [])) - node_set
        if unknown_descendants:
            raise ValueError(
                f"Rule references unknown descendant nodes: {sorted(unknown_descendants)}"
            )


def resolve_parameters(
    spec: Mapping[str, Any], overrides: Mapping[str, float] | None = None
) -> Dict[str, float]:
    overrides = overrides or {}
    unknown = set(overrides) - set(spec.get("parameters", {}))
    if unknown:
        raise ValueError(f"Unknown skeleton parameters: {sorted(unknown)}")

    values: Dict[str, float] = {}
    for name, definition in spec.get("parameters", {}).items():
        value = float(overrides.get(name, definition["default"]))
        min_value = definition.get("min")
        max_value = definition.get("max")
        if min_value is not None and value < float(min_value):
            raise ValueError(f"{name}={value} is below minimum {min_value}")
        if max_value is not None and value > float(max_value):
            raise ValueError(f"{name}={value} is above maximum {max_value}")
        values[name] = value
    return values


def _node_map(spec: Mapping[str, Any]) -> Dict[str, list[float]]:
    return {
        node["id"]: [float(v) for v in node["position_norm"]]
        for node in spec["nodes"]
    }


def _apply_rule(
    positions: Dict[str, list[float]], rule: Mapping[str, Any], value: float
) -> None:
    mode = rule["mode"]
    anchor = positions[rule.get("anchor_node", "root")]
    nodes = rule.get("nodes", [])

    if mode == "scale_axis_about_anchor":
        axis = AXIS_INDEX[rule["axis"]]
        for node_id in nodes:
            p = positions[node_id]
            p[axis] = anchor[axis] + (p[axis] - anchor[axis]) * value
        return

    if mode == "scale_vector_about_anchor":
        axes = [AXIS_INDEX[a] for a in rule.get("axes", ["x", "y", "z"])]
        for node_id in nodes:
            p = positions[node_id]
            for axis in axes:
                p[axis] = anchor[axis] + (p[axis] - anchor[axis]) * value
        return

    if mode == "offset_axis":
        axis = AXIS_INDEX[rule["axis"]]
        coefficient = float(rule.get("coefficient", 1.0))
        default = float(rule.get("default", 1.0))
        delta = coefficient * (value - default)
        for node_id in nodes:
            positions[node_id][axis] += delta
        return

    if mode == "move_endpoint_with_descendants":
        endpoint_id = rule["endpoint_node"]
        endpoint = positions[endpoint_id]
        axes = [AXIS_INDEX[a] for a in rule.get("axes", ["x", "y", "z"])]
        delta = [0.0, 0.0, 0.0]
        for axis in axes:
            delta[axis] = (endpoint[axis] - anchor[axis]) * (value - 1.0)

        targets = [endpoint_id, *rule.get("descendant_nodes", [])]
        seen = set()
        for node_id in targets:
            if node_id in seen:
                continue
            seen.add(node_id)
            for axis in axes:
                positions[node_id][axis] += delta[axis]
        return

    raise ValueError(f"Unsupported parameter rule mode: {mode}")


def compile_skeleton(
    spec: Mapping[str, Any],
    *,
    target_height_mm: float | None = None,
    parameter_overrides: Mapping[str, float] | None = None,
) -> Dict[str, Any]:
    validate_spec(spec)
    target_height_mm = float(
        target_height_mm
        if target_height_mm is not None
        else spec["default_target_height_mm"]
    )
    if target_height_mm <= 0:
        raise ValueError("target_height_mm must be positive")

    parameters = resolve_parameters(spec, parameter_overrides)
    positions = _node_map(spec)

    for rule in spec.get("parameter_rules", []):
        _apply_rule(positions, rule, parameters[rule["parameter"]])

    nodes_mm = {
        node_id: [round(v * target_height_mm, 6) for v in position]
        for node_id, position in positions.items()
    }

    envelopes = []
    for envelope in spec.get("envelopes", []):
        item = copy.deepcopy(envelope)
        size = [float(v) for v in item.get("size_norm", [0, 0, 0])]
        for axis_name, parameter_name in item.get("size_modifiers", {}).items():
            axis = AXIS_INDEX[axis_name]
            size[axis] *= parameters[parameter_name]
        item["size_mm"] = [round(v * target_height_mm, 6) for v in size]
        a_node = item.get("a_node")
        b_node = item.get("b_node")
        if a_node and b_node:
            if a_node not in nodes_mm or b_node not in nodes_mm:
                raise ValueError(
                    f"Envelope {item.get('id')} references unknown endpoint nodes"
                )
            a_mm = nodes_mm[a_node]
            b_mm = nodes_mm[b_node]
            item["a_mm"] = list(a_mm)
            item["b_mm"] = list(b_mm)
            item["derived_length_mm"] = round(
                sum((b_mm[i] - a_mm[i]) ** 2 for i in range(3)) ** 0.5,
                6,
            )
        item.pop("size_norm", None)
        envelopes.append(item)

    return {
        "schema_version": "0.1",
        "compiled_from": spec["skeleton_id"],
        "architecture_id": spec["architecture_id"],
        "source_status": spec.get("status"),
        "target_height_mm": target_height_mm,
        "parameters": parameters,
        "nodes_mm": nodes_mm,
        "bones": copy.deepcopy(spec["bones"]),
        "joints": copy.deepcopy(spec["joints"]),
        "envelopes": envelopes,
        "generation_contract": copy.deepcopy(spec.get("generation_contract", {})),
        "production_warning": (
            "Generation/alignment skeleton only. Joint centers and interface geometry "
            "must be reconciled with validated JointCartridge/ConnectorProfile data "
            "before manufacturing."
        ),
    }


def skeleton_to_obj(compiled: Mapping[str, Any]) -> str:
    """Return a simple OBJ containing vertices and line segments for the skeleton."""
    nodes = list(compiled["nodes_mm"].items())
    index = {node_id: i + 1 for i, (node_id, _) in enumerate(nodes)}
    lines = [
        f"# Brickmen skeleton: {compiled['compiled_from']}",
        f"# Architecture: {compiled['architecture_id']}",
        "# Units: mm",
    ]
    for node_id, position in nodes:
        lines.append(f"# node {node_id}")
        lines.append(f"v {position[0]:.6f} {position[1]:.6f} {position[2]:.6f}")
    for bone in compiled["bones"]:
        lines.append(f"l {index[bone['a']]} {index[bone['b']]}")
    return "\n".join(lines) + "\n"


def parse_param_overrides(values: Iterable[str]) -> Dict[str, float]:
    result: Dict[str, float] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Parameter override must be name=value: {value}")
        name, raw = value.split("=", 1)
        result[name] = float(raw)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", help="Path to a Brickmen skeleton JSON spec")
    parser.add_argument("--height-mm", type=float, default=None)
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Parameter override name=value; repeat as needed",
    )
    parser.add_argument("--format", choices=["json", "obj"], default="json")
    parser.add_argument("-o", "--output", default=None)
    args = parser.parse_args()

    spec = load_spec(args.spec)
    compiled = compile_skeleton(
        spec,
        target_height_mm=args.height_mm,
        parameter_overrides=parse_param_overrides(args.param),
    )

    if args.format == "json":
        payload = json.dumps(compiled, indent=2) + "\n"
    else:
        payload = skeleton_to_obj(compiled)

    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
