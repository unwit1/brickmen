#!/usr/bin/env python3
"""Compare a reviewed Particulate semantic mapping to Brickmen architecture."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.geometry.validate_body_generation_provider_geometry import (
    load_json,
    transform_point,
)


def _pair(a,b):
    return tuple(sorted((str(a),str(b))))


def _direction_transform(direction,matrix):
    x,y,z=map(float,direction)
    m=list(map(float,matrix))
    v=[
        m[0]*x+m[1]*y+m[2]*z,
        m[4]*x+m[5]*y+m[6]*z,
        m[8]*x+m[9]*y+m[10]*z,
    ]
    n=math.sqrt(sum(x*x for x in v))
    return [x/n for x in v] if n>1e-12 else None


def _axis_angle_deg(a,b):
    if a is None or b is None:
        return None
    na=math.sqrt(sum(float(x)*float(x) for x in a))
    nb=math.sqrt(sum(float(x)*float(x) for x in b))
    if na<=1e-12 or nb<=1e-12:
        return None
    dot=sum(float(a[i])*float(b[i]) for i in range(3))/(na*nb)
    dot=max(-1.0,min(1.0,abs(dot)))
    return math.degrees(math.acos(dot))


def _point_line_distance(point,line_point,line_dir):
    if point is None or line_point is None or line_dir is None:
        return None
    v=[float(point[i])-float(line_point[i]) for i in range(3)]
    cross=[
        v[1]*line_dir[2]-v[2]*line_dir[1],
        v[2]*line_dir[0]-v[0]*line_dir[2],
        v[0]*line_dir[1]-v[1]*line_dir[0],
    ]
    return math.sqrt(sum(x*x for x in cross))


def compare_particulate(
    conditioning: Mapping[str,Any],
    critic_report: Mapping[str,Any],
    mapping_proposal: Mapping[str,Any],
    candidate_index: int,
) -> dict[str,Any]:
    candidates=mapping_proposal.get("global_alignment_candidates",[])
    if candidate_index<0 or candidate_index>=len(candidates):
        raise ValueError("candidate_index outside mapping proposal")
    candidate=candidates[candidate_index]
    if not candidate.get("complete_required_visual_mapping"):
        raise ValueError("Selected critic mapping is incomplete")

    part_to_slot={
        int(a["particulate_part_id"]):str(a["slot_id"])
        for a in candidate["assignments"]
    }
    slot_to_part={slot:pid for pid,slot in part_to_slot.items()}
    transform=candidate["global_transform_particulate_to_brickmen_mm"]
    parts={int(p["part_id"]):p for p in critic_report.get("parts",[])}

    predicted_edges=[]
    for parent,child in critic_report.get("motion_hierarchy",[]):
        parent=int(parent); child=int(child)
        predicted_edges.append({
            "parent_part_id":parent,
            "child_part_id":child,
            "parent_slot":part_to_slot.get(parent),
            "child_slot":part_to_slot.get(child),
        })
    predicted_pairs={
        _pair(e["parent_slot"],e["child_slot"])
        for e in predicted_edges
        if e["parent_slot"] and e["child_slot"]
        and e["parent_slot"]!=e["child_slot"]
    }

    bindings=conditioning.get("component_plan",{}).get(
        "joint_component_bindings",[]
    )
    inter=[
        b for b in bindings
        if b.get("binding_status") in {
            "inter_component","optional_donor_or_adapter_interface"
        }
        and b.get("parent_slot")!=b.get("child_slot")
    ]
    expected_pairs={
        _pair(b["parent_slot"],b["child_slot"]) for b in inter
    }
    expected_by_pair={
        _pair(b["parent_slot"],b["child_slot"]):b for b in inter
    }
    joint_by_id={
        str(j["joint_id"]):j
        for j in conditioning.get("skeleton_control",{}).get("joints",[])
    }
    nodes=conditioning.get("skeleton_control",{}).get("nodes",{})

    observations=[]
    for edge in predicted_edges:
        if not edge["parent_slot"] or not edge["child_slot"]:
            continue
        pair=_pair(edge["parent_slot"],edge["child_slot"])
        binding=expected_by_pair.get(pair)
        child_part=parts.get(edge["child_part_id"],{})
        axis=child_part.get("revolute_axis_direction")
        axis_point=child_part.get("revolute_axis_point_in_prediction_frame")
        axis_mm=_direction_transform(axis,transform) if axis else None
        point_mm=(
            transform_point(axis_point,transform)
            if axis_point is not None else None
        )
        if binding:
            joint=joint_by_id.get(str(binding["joint_id"]),{})
            expected_axis=joint.get("axis")
            pivot_node=(
                joint.get("joint_id")
                if joint.get("joint_id") in nodes
                else joint.get("parent_node")
            )
            pivot=(
                nodes[pivot_node].get("position_mm_at_target_height")
                if pivot_node in nodes else None
            )
            expected_range=joint.get("range_deg")
        else:
            joint={}
            expected_axis=pivot=expected_range=None

        predicted_range=child_part.get("revolute_range_radians")
        predicted_range_deg=(
            [math.degrees(float(v)) for v in predicted_range]
            if predicted_range is not None else None
        )
        observations.append({
            "predicted_parent_part_id":edge["parent_part_id"],
            "predicted_child_part_id":edge["child_part_id"],
            "predicted_parent_slot":edge["parent_slot"],
            "predicted_child_slot":edge["child_slot"],
            "matches_expected_component_pair":binding is not None,
            "expected_joint_id":binding.get("joint_id") if binding else None,
            "expected_joint_type":joint.get("joint_type") if binding else None,
            "predicted_motion_class":child_part.get("motion_class"),
            "predicted_revolute_axis_direction_brickmen_frame":axis_mm,
            "predicted_revolute_axis_point_mm":point_mm,
            "expected_axis":expected_axis,
            "expected_pivot_mm":pivot,
            "axis_direction_error_deg_sign_invariant":_axis_angle_deg(
                axis_mm,expected_axis
            ),
            "axis_line_to_expected_pivot_distance_mm":_point_line_distance(
                pivot,point_mm,axis_mm
            ),
            "predicted_revolute_range_deg":predicted_range_deg,
            "expected_range_deg":expected_range,
            "range_span_error_deg":(
                abs(
                    (float(predicted_range_deg[1])-float(predicted_range_deg[0]))
                    -(float(expected_range[1])-float(expected_range[0]))
                )
                if predicted_range_deg is not None
                and expected_range is not None else None
            ),
        })

    within_combined=[
        b for b in bindings
        if b.get("binding_status")=="within_combined_component_slot"
    ]
    return {
        "schema_version":"0.1",
        "architecture_id":conditioning["architecture_id"],
        "critic_id":"particulate",
        "selected_candidate_index":candidate_index,
        "selected_mapping_score":candidate.get("total_score"),
        "part_to_slot_mapping":{
            str(pid):slot for pid,slot in sorted(part_to_slot.items())
        },
        "global_transform_particulate_to_brickmen_mm":transform,
        "graph_comparison":{
            "expected_inter_component_pairs":[list(p) for p in sorted(expected_pairs)],
            "predicted_mapped_pairs":[list(p) for p in sorted(predicted_pairs)],
            "matched_pairs":[list(p) for p in sorted(expected_pairs&predicted_pairs)],
            "missing_expected_pairs":[list(p) for p in sorted(expected_pairs-predicted_pairs)],
            "extra_predicted_pairs":[list(p) for p in sorted(predicted_pairs-expected_pairs)],
            "within_combined_slot_joints_not_expected_as_separate_parts":within_combined,
        },
        "joint_observations":observations,
        "authority":"auxiliary_learned_critic_comparison_noncanonical",
        "promotion_rule":(
            "Differences may create research/review findings, but Particulate "
            "predictions cannot automatically change Brickmen component graph, "
            "skeleton axes/ranges or validated mechanical interfaces."
        ),
        "production_geometry_authority":False,
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("critic_report")
    parser.add_argument("mapping_proposal")
    parser.add_argument("candidate_index",type=int)
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    result=compare_particulate(
        load_json(args.conditioning),
        load_json(args.critic_report),
        load_json(args.mapping_proposal),
        args.candidate_index,
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
