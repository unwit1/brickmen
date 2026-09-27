#!/usr/bin/env python3
"""Conservative continuous collision proof for rotating Brickmen components.

For a point rotating around a fixed axis, each world coordinate is:
    C + A*cos(theta) + B*sin(theta)

The tool evaluates endpoints plus every derivative root inside an angle interval,
giving exact coordinate extrema for that rotating point. Unioning the three
vertices therefore gives a conservative (coordinate-exact) swept AABB for a
rotating triangle over the interval.

Triangle pairs whose swept/static AABBs are disjoint are proven collision-free.
Ambiguous pairs are recursively subdivided. An interval can also be proven
acceptable when the entire possible overlap AABB is contained in an explicitly
validated allowed-contact region.

A pass is conservative: no unresolved interval and no disallowed sampled
intersection remain. A failure may be either a real sampled collision or an
unresolved near-contact interval that needs deeper/exact CCD.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.geometry.compile_body_articulation_sweeps import rotate_about_axis
from tools.geometry.validate_body_generation_provider_geometry import load_json
from tools.geometry.validate_body_generation_pose_collisions import (
    _aabb_overlap,
    _base_component_triangles,
    _build_static_index,
    _contact_joint_map,
    _moving_slots_for_joint,
    _triangle_aabb,
    _validated_regions_for_pair,
    triangle_intersection_witness,
)


def _unit(v: Sequence[float]) -> list[float]:
    n=math.sqrt(sum(float(x)*float(x) for x in v))
    if n<=1e-15:
        raise ValueError("rotation axis must be non-zero")
    return [float(x)/n for x in v]


def _cross(a,b):
    return [
        float(a[1])*float(b[2])-float(a[2])*float(b[1]),
        float(a[2])*float(b[0])-float(a[0])*float(b[2]),
        float(a[0])*float(b[1])-float(a[1])*float(b[0]),
    ]


def _dot(a,b):
    return sum(float(a[i])*float(b[i]) for i in range(3))


def _point_coordinate_coefficients(point,pivot,axis):
    u=_unit(axis)
    v=[float(point[i])-float(pivot[i]) for i in range(3)]
    dot=_dot(u,v)
    parallel=[u[i]*dot for i in range(3)]
    perp=[v[i]-parallel[i] for i in range(3)]
    cross=_cross(u,v)
    constant=[float(pivot[i])+parallel[i] for i in range(3)]
    return constant,perp,cross


def _critical_angles(lo: float,hi: float,a: float,b: float):
    if abs(a)<=1e-15 and abs(b)<=1e-15:
        return []
    base=math.atan2(b,a)
    start=math.ceil((lo-base)/math.pi)
    end=math.floor((hi-base)/math.pi)
    return [base+k*math.pi for k in range(start,end+1)]


def swept_point_bounds(
    point: Sequence[float],
    pivot: Sequence[float],
    axis: Sequence[float],
    lo_deg: float,
    hi_deg: float,
) -> dict[str,list[float]]:
    lo,hi=sorted((math.radians(float(lo_deg)),math.radians(float(hi_deg))))
    constant,a,b=_point_coordinate_coefficients(point,pivot,axis)
    mins=[]
    maxs=[]
    for i in range(3):
        angles=[lo,hi,*_critical_angles(lo,hi,a[i],b[i])]
        values=[
            constant[i]+a[i]*math.cos(theta)+b[i]*math.sin(theta)
            for theta in angles
        ]
        mins.append(min(values))
        maxs.append(max(values))
    return {"min":mins,"max":maxs}


def swept_triangle_bounds(
    triangle: Sequence[Sequence[float]],
    pivot: Sequence[float],
    axis: Sequence[float],
    lo_deg: float,
    hi_deg: float,
) -> dict[str,list[float]]:
    boxes=[
        swept_point_bounds(p,pivot,axis,lo_deg,hi_deg)
        for p in triangle
    ]
    return {
        "min":[min(box["min"][i] for box in boxes) for i in range(3)],
        "max":[max(box["max"][i] for box in boxes) for i in range(3)],
    }


def _intersection_box(a,b):
    if not _aabb_overlap(a,b):
        return None
    return {
        "min":[max(float(a["min"][i]),float(b["min"][i])) for i in range(3)],
        "max":[min(float(a["max"][i]),float(b["max"][i])) for i in range(3)],
    }


def _box_inside_region(box,region,eps=1e-8):
    if region.get("shape")!="aabb":
        return False
    mn=region.get("min_mm")
    mx=region.get("max_mm")
    if mn is None or mx is None:
        return False
    return all(
        float(box["min"][i])>=float(mn[i])-eps
        and float(box["max"][i])<=float(mx[i])+eps
        for i in range(3)
    )


def _point_inside_region(point,region,eps=1e-8):
    if region.get("shape")!="aabb":
        return False
    mn=region.get("min_mm")
    mx=region.get("max_mm")
    if mn is None or mx is None:
        return False
    return all(
        float(mn[i])-eps<=float(point[i])<=float(mx[i])+eps
        for i in range(3)
    )


def _rotated_triangle(triangle,pivot,axis,angle):
    return tuple(
        tuple(rotate_about_axis(p,pivot,axis,angle))
        for p in triangle
    )


def _interval_proof(
    moving_triangle,
    static_triangle,
    static_box,
    pivot,
    axis,
    lo,
    hi,
    regions,
    *,
    min_interval_deg,
    depth,
    max_depth,
):
    swept=swept_triangle_bounds(moving_triangle,pivot,axis,lo,hi)
    overlap=_intersection_box(swept,static_box)
    if overlap is None:
        return {
            "status":"proven_separated_by_swept_aabb",
            "nodes":1,
            "pruned_intervals":1,
            "allowed_intervals":0,
            "unresolved_intervals":[],
            "disallowed_collisions":[],
        }

    for region in regions:
        if _box_inside_region(overlap,region):
            return {
                "status":"proven_overlap_confined_to_validated_contact_region",
                "nodes":1,
                "pruned_intervals":0,
                "allowed_intervals":1,
                "unresolved_intervals":[],
                "disallowed_collisions":[],
                "allowed_contact_region_id":region.get("region_id"),
            }

    mid=(float(lo)+float(hi))/2.0
    sampled=[]
    for angle in (float(lo),mid,float(hi)):
        tri=_rotated_triangle(moving_triangle,pivot,axis,angle)
        witness=triangle_intersection_witness(tri,static_triangle)
        if witness is None:
            continue
        matched=next(
            (region for region in regions if _point_inside_region(witness,region)),
            None,
        )
        sampled.append({
            "angle_deg":angle,
            "witness_mm":witness,
            "allowed_contact_region_id":(
                matched.get("region_id") if matched else None
            ),
        })
        if matched is None:
            return {
                "status":"disallowed_collision_sampled",
                "nodes":1,
                "pruned_intervals":0,
                "allowed_intervals":0,
                "unresolved_intervals":[],
                "disallowed_collisions":[sampled[-1]],
            }

    width=abs(float(hi)-float(lo))
    if depth>=max_depth or width<=min_interval_deg:
        return {
            "status":"unresolved_near_contact_interval",
            "nodes":1,
            "pruned_intervals":0,
            "allowed_intervals":0,
            "unresolved_intervals":[{
                "lo_deg":float(lo),
                "hi_deg":float(hi),
                "width_deg":width,
                "possible_overlap_aabb_mm":overlap,
                "allowed_sampled_contacts":[
                    item for item in sampled
                    if item["allowed_contact_region_id"] is not None
                ],
            }],
            "disallowed_collisions":[],
        }

    left=_interval_proof(
        moving_triangle,static_triangle,static_box,pivot,axis,lo,mid,regions,
        min_interval_deg=min_interval_deg,depth=depth+1,max_depth=max_depth,
    )
    if left["disallowed_collisions"]:
        return left
    right=_interval_proof(
        moving_triangle,static_triangle,static_box,pivot,axis,mid,hi,regions,
        min_interval_deg=min_interval_deg,depth=depth+1,max_depth=max_depth,
    )
    return {
        "status":(
            "subintervals_proven"
            if not left["unresolved_intervals"]
            and not right["unresolved_intervals"]
            and not right["disallowed_collisions"]
            else "subinterval_review_required"
        ),
        "nodes":left["nodes"]+right["nodes"]+1,
        "pruned_intervals":left["pruned_intervals"]+right["pruned_intervals"],
        "allowed_intervals":left["allowed_intervals"]+right["allowed_intervals"],
        "unresolved_intervals":[
            *left["unresolved_intervals"],*right["unresolved_intervals"]
        ],
        "disallowed_collisions":[
            *left["disallowed_collisions"],*right["disallowed_collisions"]
        ],
    }


def _candidate_static_entries(static_index,swept_box):
    entries=static_index["entries"]
    mins=static_index["mins"]
    stop=bisect.bisect_right(mins,float(swept_box["max"][0])+1e-9)
    for entry in entries[:stop]:
        _,max_x,sbox,si,stri=entry
        if max_x < float(swept_box["min"][0])-1e-9:
            continue
        if _aabb_overlap(swept_box,sbox):
            yield si,stri,sbox


def validate_continuous_rotation_collisions(
    conditioning: Mapping[str,Any],
    output_mapping: Mapping[str,Any],
    *,
    contact_regions: Mapping[str,Any] | None=None,
    min_interval_deg: float=0.25,
    max_depth: int=14,
    max_candidate_triangle_pairs: int=200000,
) -> dict[str,Any]:
    components,load_errors=_base_component_triangles(output_mapping)
    nodes=conditioning["skeleton_control"]["nodes"]
    contact_map=_contact_joint_map(contact_regions)
    joint_results=[]
    total_unresolved=0
    total_collisions=0
    total_candidates=0
    incomplete=list(load_errors)

    for joint in conditioning["skeleton_control"].get("joints",[]):
        moving_slots=_moving_slots_for_joint(conditioning,joint)
        if not moving_slots:
            continue
        missing=[slot for slot in moving_slots if slot not in components]
        if missing:
            incomplete.append(
                f"{joint['joint_id']}:missing_moving_components:"+",".join(missing)
            )
            joint_results.append({
                "joint_id":joint["joint_id"],
                "status":"incomplete_missing_moving_components",
                "moving_slots":moving_slots,
            })
            continue

        pivot_node=(
            joint["joint_id"]
            if joint["joint_id"] in nodes
            else joint.get("parent_node")
        )
        if pivot_node not in nodes:
            incomplete.append(f"{joint['joint_id']}:missing_pivot_node")
            continue
        pivot=nodes[pivot_node]["position_mm_at_target_height"]
        axis=joint["axis"]
        lo,hi=map(float,joint["range_deg"])
        static_slots=sorted(set(components)-set(moving_slots))
        static_indices={
            slot:_build_static_index(components[slot])
            for slot in static_slots
        }
        pair_reports=[]
        joint_unresolved=0
        joint_collisions=0
        joint_candidates=0
        capped=False

        for moving_slot in moving_slots:
            for mi,mtri in enumerate(components[moving_slot]):
                full_swept=swept_triangle_bounds(mtri,pivot,axis,lo,hi)
                for static_slot in static_slots:
                    regions=_validated_regions_for_pair(
                        contact_map.get(str(joint["joint_id"])),
                        moving_slot,static_slot,
                    )
                    for si,stri,sbox in _candidate_static_entries(
                        static_indices[static_slot],full_swept
                    ):
                        joint_candidates+=1
                        total_candidates+=1
                        if joint_candidates>max_candidate_triangle_pairs:
                            capped=True
                            break
                        proof=_interval_proof(
                            mtri,stri,sbox,pivot,axis,lo,hi,regions,
                            min_interval_deg=min_interval_deg,
                            depth=0,max_depth=max_depth,
                        )
                        unresolved=len(proof["unresolved_intervals"])
                        collisions=len(proof["disallowed_collisions"])
                        joint_unresolved+=unresolved
                        joint_collisions+=collisions
                        if unresolved or collisions:
                            pair_reports.append({
                                "moving_slot":moving_slot,
                                "moving_triangle_index":mi,
                                "static_slot":static_slot,
                                "static_triangle_index":si,
                                "validated_contact_region_ids":[
                                    r.get("region_id") for r in regions
                                ],
                                "proof_status":proof["status"],
                                "proof_nodes":proof["nodes"],
                                "unresolved_intervals":proof["unresolved_intervals"][:20],
                                "disallowed_collisions":proof["disallowed_collisions"][:20],
                            })
                        if collisions:
                            # One proven disallowed collision is sufficient to fail
                            # this joint; continue other components only for context.
                            break
                    if capped:
                        break
                if capped:
                    break
            if capped:
                break

        if capped:
            incomplete.append(
                f"{joint['joint_id']}:candidate_pair_cap_exceeded:{max_candidate_triangle_pairs}"
            )
        total_unresolved+=joint_unresolved
        total_collisions+=joint_collisions
        joint_results.append({
            "joint_id":joint["joint_id"],
            "pivot_node":pivot_node,
            "axis":axis,
            "range_deg":[lo,hi],
            "moving_slots":moving_slots,
            "static_slots":static_slots,
            "candidate_triangle_pair_count":joint_candidates,
            "candidate_pair_cap_exceeded":capped,
            "unresolved_interval_count":joint_unresolved,
            "disallowed_collision_count":joint_collisions,
            "review_examples":pair_reports[:100],
            "status":(
                "continuous_rotation_collision_proven_safe_or_validated_contact_only"
                if not capped and joint_unresolved==0 and joint_collisions==0
                else "continuous_rotation_collision_review_required"
            ),
        })

    gate=(
        bool(joint_results)
        and not incomplete
        and total_unresolved==0
        and total_collisions==0
    )
    return {
        "schema_version":"0.1",
        "architecture_id":conditioning["architecture_id"],
        "provider_id":output_mapping.get("provider_id"),
        "provider_job_id":output_mapping.get("provider_job_id"),
        "min_interval_deg":min_interval_deg,
        "max_depth":max_depth,
        "joint_results":joint_results,
        "summary":{
            "status":(
                "continuous_rotation_collision_gate_passed"
                if gate else "continuous_rotation_collision_review_required"
            ),
            "continuous_rotation_collision_gate_passed":gate,
            "candidate_triangle_pair_count":total_candidates,
            "unresolved_interval_count":total_unresolved,
            "disallowed_collision_count":total_collisions,
            "incomplete_reasons":incomplete,
            "proof_method":"exact_rotational_vertex_coordinate_extrema_plus_recursive_swept_aabb_exclusion",
        },
        "production_geometry_authority":False,
        "warning":(
            "A pass is a conservative collision-exclusion proof for the declared "
            "single-axis joint rotations and supplied component meshes/contact regions. "
            "It does not validate mechanical fit, deformation, tolerance, or multi-joint "
            "simultaneous motion unless those configurations are separately modeled."
        ),
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("output_mapping")
    parser.add_argument("--contact-regions",default=None)
    parser.add_argument("--min-interval-deg",type=float,default=.25)
    parser.add_argument("--max-depth",type=int,default=14)
    parser.add_argument("--max-candidate-pairs",type=int,default=200000)
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    result=validate_continuous_rotation_collisions(
        load_json(args.conditioning),
        load_json(args.output_mapping),
        contact_regions=(
            load_json(args.contact_regions) if args.contact_regions else None
        ),
        min_interval_deg=args.min_interval_deg,
        max_depth=args.max_depth,
        max_candidate_triangle_pairs=args.max_candidate_pairs,
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0 if result["summary"]["continuous_rotation_collision_gate_passed"] else 2


if __name__=="__main__":
    raise SystemExit(main())
