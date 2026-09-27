#!/usr/bin/env python3
"""Pose-sampled triangle collision validation for generated Brickmen components.

This validator:
- transforms provider meshes into the Brickmen-mm frame;
- samples each articulated joint across its declared range;
- moves every visual-envelope component slot associated with that joint;
- tests those moving meshes against all static mapped components;
- suppresses a collision ONLY when its witness point lies inside an explicitly
  validated joint-local allowed-contact region for that component pair.

This is discrete pose sampling, not continuous collision detection. Passing
samples does not prove that no collision occurs between samples.
"""

from __future__ import annotations

import argparse
import bisect
import itertools
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.geometry.compile_body_articulation_sweeps import rotate_about_axis
from tools.geometry.inspect_mesh_triangles import load_mesh_triangles
from tools.geometry.validate_body_generation_provider_geometry import (
    load_json,
    transform_point,
)


VALID_CONTACT_STATUSES={"validated_prototype","production_approved"}


def _sub(a,b):
    return [float(a[i])-float(b[i]) for i in range(3)]


def _add(a,b):
    return [float(a[i])+float(b[i]) for i in range(3)]


def _scale(a,s):
    return [float(v)*float(s) for v in a]


def _dot(a,b):
    return sum(float(a[i])*float(b[i]) for i in range(3))


def _cross(a,b):
    return [
        float(a[1])*float(b[2])-float(a[2])*float(b[1]),
        float(a[2])*float(b[0])-float(a[0])*float(b[2]),
        float(a[0])*float(b[1])-float(a[1])*float(b[0]),
    ]


def _norm2(a):
    return _dot(a,a)


def _triangle_aabb(tri):
    return {
        "min":[min(float(p[i]) for p in tri) for i in range(3)],
        "max":[max(float(p[i]) for p in tri) for i in range(3)],
    }


def _aabb_overlap(a,b,eps=1e-9):
    return all(
        float(a["min"][i]) <= float(b["max"][i])+eps
        and float(a["max"][i])+eps >= float(b["min"][i])
        for i in range(3)
    )


def _segment_triangle_hit(
    p0: Sequence[float],
    p1: Sequence[float],
    tri: Sequence[Sequence[float]],
    *,
    eps: float=1e-9,
) -> list[float] | None:
    """Möller-Trumbore segment/triangle hit, excluding coplanar case."""
    a,b,c=tri
    direction=_sub(p1,p0)
    e1=_sub(b,a)
    e2=_sub(c,a)
    h=_cross(direction,e2)
    det=_dot(e1,h)
    if abs(det)<=eps:
        return None
    inv=1.0/det
    s=_sub(p0,a)
    u=inv*_dot(s,h)
    if u < -eps or u > 1.0+eps:
        return None
    q=_cross(s,e1)
    v=inv*_dot(direction,q)
    if v < -eps or u+v > 1.0+eps:
        return None
    t=inv*_dot(e2,q)
    if t < -eps or t > 1.0+eps:
        return None
    return _add(p0,_scale(direction,t))


def _project2(point,drop_axis):
    return tuple(float(point[i]) for i in range(3) if i!=drop_axis)


def _orient2(a,b,c):
    return (
        (float(b[0])-float(a[0]))*(float(c[1])-float(a[1]))
        -(float(b[1])-float(a[1]))*(float(c[0])-float(a[0]))
    )


def _point_in_triangle2(p,tri,eps=1e-9):
    a,b,c=tri
    o1=_orient2(a,b,p)
    o2=_orient2(b,c,p)
    o3=_orient2(c,a,p)
    has_neg=(o1 < -eps) or (o2 < -eps) or (o3 < -eps)
    has_pos=(o1 > eps) or (o2 > eps) or (o3 > eps)
    return not (has_neg and has_pos)


def _segment_intersection2(a,b,c,d,eps=1e-9):
    """Return t along AB for a 2D segment intersection when determinable."""
    r=(float(b[0])-float(a[0]),float(b[1])-float(a[1]))
    s=(float(d[0])-float(c[0]),float(d[1])-float(c[1]))
    denom=r[0]*s[1]-r[1]*s[0]
    ca=(float(c[0])-float(a[0]),float(c[1])-float(a[1]))
    if abs(denom)<=eps:
        return None
    t=(ca[0]*s[1]-ca[1]*s[0])/denom
    u=(ca[0]*r[1]-ca[1]*r[0])/denom
    if -eps<=t<=1.0+eps and -eps<=u<=1.0+eps:
        return max(0.0,min(1.0,t))
    return None


def triangle_intersection_witness(
    tri_a: Sequence[Sequence[float]],
    tri_b: Sequence[Sequence[float]],
    *,
    eps: float=1e-9,
) -> list[float] | None:
    if not _aabb_overlap(_triangle_aabb(tri_a),_triangle_aabb(tri_b),eps):
        return None

    edges=((0,1),(1,2),(2,0))
    for i,j in edges:
        hit=_segment_triangle_hit(tri_a[i],tri_a[j],tri_b,eps=eps)
        if hit is not None:
            return hit
    for i,j in edges:
        hit=_segment_triangle_hit(tri_b[i],tri_b[j],tri_a,eps=eps)
        if hit is not None:
            return hit

    # Coplanar overlap/containment.
    na=_cross(_sub(tri_a[1],tri_a[0]),_sub(tri_a[2],tri_a[0]))
    nb=_cross(_sub(tri_b[1],tri_b[0]),_sub(tri_b[2],tri_b[0]))
    if _norm2(na)<=eps*eps or _norm2(nb)<=eps*eps:
        return None
    parallel=_norm2(_cross(na,nb)) <= eps*eps*_norm2(na)*_norm2(nb)
    plane_distance=abs(_dot(na,_sub(tri_b[0],tri_a[0])))
    if not parallel or plane_distance > eps*math.sqrt(_norm2(na)):
        return None

    drop=max(range(3),key=lambda i:abs(float(na[i])))
    a2=[_project2(p,drop) for p in tri_a]
    b2=[_project2(p,drop) for p in tri_b]
    for i,p in enumerate(a2):
        if _point_in_triangle2(p,b2,eps):
            return list(map(float,tri_a[i]))
    for i,p in enumerate(b2):
        if _point_in_triangle2(p,a2,eps):
            return list(map(float,tri_b[i]))
    for ai,aj in edges:
        for bi,bj in edges:
            t=_segment_intersection2(a2[ai],a2[aj],b2[bi],b2[bj],eps)
            if t is not None:
                return _add(
                    tri_a[ai],
                    _scale(_sub(tri_a[aj],tri_a[ai]),t),
                )
    return None


def _build_static_index(triangles):
    entries=[]
    for i,tri in enumerate(triangles):
        box=_triangle_aabb(tri)
        entries.append((float(box["min"][0]),float(box["max"][0]),box,i,tri))
    entries.sort(key=lambda x:x[0])
    return {
        "entries":entries,
        "mins":[e[0] for e in entries],
    }


def _collision_witnesses(
    moving,
    static_index,
    *,
    max_hits=250,
):
    entries=static_index["entries"]
    mins=static_index["mins"]
    hits=[]
    tested_pairs=0
    for mi,mtri in enumerate(moving):
        mbox=_triangle_aabb(mtri)
        stop=bisect.bisect_right(mins,float(mbox["max"][0])+1e-9)
        for entry in entries[:stop]:
            _,max_x,sbox,si,stri=entry
            if max_x < float(mbox["min"][0])-1e-9:
                continue
            if not _aabb_overlap(mbox,sbox):
                continue
            tested_pairs+=1
            witness=triangle_intersection_witness(mtri,stri)
            if witness is not None:
                hits.append({
                    "moving_triangle_index":mi,
                    "static_triangle_index":si,
                    "witness_mm":witness,
                })
                if len(hits)>=max_hits:
                    return hits,tested_pairs,True
    return hits,tested_pairs,False


def _angles(range_deg,samples):
    lo,hi=map(float,range_deg)
    if samples<=1 or abs(hi-lo)<=1e-12:
        return [lo]
    values=[lo+(hi-lo)*i/(samples-1) for i in range(samples)]
    if lo < 0 < hi and not any(abs(v)<=1e-9 for v in values):
        values.append(0.0)
        values.sort()
    return values


def _pair_key(a,b):
    return tuple(sorted((str(a),str(b))))


def _contact_joint_map(contact_regions):
    if not contact_regions:
        return {}
    return {
        str(item["joint_id"]):item
        for item in contact_regions.get("joints",[])
    }


def _validated_regions_for_pair(contact_joint,a,b):
    if not contact_joint:
        return []
    target=_pair_key(a,b)
    declared={
        _pair_key(pair[0],pair[1])
        for pair in contact_joint.get("component_pairs",[])
        if isinstance(pair,list) and len(pair)==2
    }
    if target not in declared:
        return []
    return [
        region for region in contact_joint.get("allowed_contact_regions_mm",[])
        if region.get("status") in VALID_CONTACT_STATUSES
        and region.get("shape")=="aabb"
    ]


def _point_in_region(point,region,eps=1e-8):
    if region.get("shape")!="aabb":
        return False
    mn=region.get("min_mm")
    mx=region.get("max_mm")
    if mn is None or mx is None:
        return False
    return all(
        float(mn[i])-eps <= float(point[i]) <= float(mx[i])+eps
        for i in range(3)
    )


def _moving_slots_for_joint(conditioning,joint):
    envelope_slot={
        env["envelope_id"]:env.get("component_slot_id")
        for env in conditioning.get("visual_envelopes",[])
    }
    return sorted({
        envelope_slot.get(eid)
        for eid in joint.get("visual_envelope_ids",[])
        if envelope_slot.get(eid)
    })


def _base_component_triangles(output_mapping):
    result={}
    errors=[]
    for component in output_mapping.get("components",[]):
        slot=str(component["slot_id"])
        matrix=component.get("transform_matrix_to_brickmen_mm")
        if matrix is None:
            errors.append(f"{slot}:missing_transform")
            continue
        try:
            triangles=load_mesh_triangles(component["path"])
        except Exception as exc:
            errors.append(f"{slot}:triangle_extraction_failed:{exc}")
            continue
        result[slot]=[
            tuple(tuple(transform_point(p,matrix)) for p in tri)
            for tri in triangles
        ]
    return result,errors


def validate_pose_collisions(
    conditioning: Mapping[str,Any],
    output_mapping: Mapping[str,Any],
    *,
    contact_regions: Mapping[str,Any] | None=None,
    samples_per_joint: int=9,
    max_collision_examples_per_pair: int=250,
) -> dict[str,Any]:
    components,load_errors=_base_component_triangles(output_mapping)
    nodes=conditioning["skeleton_control"]["nodes"]
    contact_map=_contact_joint_map(contact_regions)
    joint_results=[]
    global_disallowed=0
    global_allowed=0
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
                "missing_slots":missing,
                "poses":[],
            })
            continue

        static_slots=sorted(set(components)-set(moving_slots))
        pivot_node=(
            joint["joint_id"]
            if joint["joint_id"] in nodes
            else joint.get("parent_node")
        )
        if pivot_node not in nodes:
            incomplete.append(f"{joint['joint_id']}:missing_pivot_node")
            joint_results.append({
                "joint_id":joint["joint_id"],
                "status":"incomplete_missing_pivot",
                "moving_slots":moving_slots,
                "poses":[],
            })
            continue
        pivot=nodes[pivot_node]["position_mm_at_target_height"]
        axis=joint["axis"]
        static_indices={
            slot:_build_static_index(components[slot])
            for slot in static_slots
        }
        poses=[]
        joint_disallowed=0
        joint_allowed=0

        for angle in _angles(joint["range_deg"],samples_per_joint):
            moved_by_slot={
                slot:[
                    tuple(
                        rotate_about_axis(p,pivot,axis,angle)
                        for p in tri
                    )
                    for tri in components[slot]
                ]
                for slot in moving_slots
            }
            pose_collisions=[]
            for moving_slot in moving_slots:
                for static_slot in static_slots:
                    hits,tested,truncated=_collision_witnesses(
                        moved_by_slot[moving_slot],
                        static_indices[static_slot],
                        max_hits=max_collision_examples_per_pair,
                    )
                    if not hits:
                        continue
                    regions=_validated_regions_for_pair(
                        contact_map.get(str(joint["joint_id"])),
                        moving_slot,
                        static_slot,
                    )
                    allowed=[]
                    disallowed=[]
                    for hit in hits:
                        matched=next(
                            (
                                region for region in regions
                                if _point_in_region(hit["witness_mm"],region)
                            ),
                            None,
                        )
                        record={
                            **hit,
                            "allowed_contact":matched is not None,
                            "allowed_contact_region_id":(
                                matched.get("region_id") if matched else None
                            ),
                        }
                        (allowed if matched else disallowed).append(record)
                    joint_allowed+=len(allowed)
                    joint_disallowed+=len(disallowed)
                    pose_collisions.append({
                        "moving_slot":moving_slot,
                        "static_slot":static_slot,
                        "triangle_pairs_broadphase_tested":tested,
                        "collision_examples_truncated":truncated,
                        "validated_contact_region_ids":[
                            r.get("region_id") for r in regions
                        ],
                        "allowed_collision_count":len(allowed),
                        "disallowed_collision_count":len(disallowed),
                        "allowed_collision_examples":allowed[:20],
                        "disallowed_collision_examples":disallowed[:20],
                    })
            poses.append({
                "angle_deg":angle,
                "collision_pairs":pose_collisions,
                "allowed_collision_count":sum(
                    p["allowed_collision_count"] for p in pose_collisions
                ),
                "disallowed_collision_count":sum(
                    p["disallowed_collision_count"] for p in pose_collisions
                ),
            })

        global_allowed+=joint_allowed
        global_disallowed+=joint_disallowed
        joint_results.append({
            "joint_id":joint["joint_id"],
            "pivot_node":pivot_node,
            "axis":axis,
            "range_deg":joint["range_deg"],
            "moving_slots":moving_slots,
            "static_slots":static_slots,
            "sample_count":len(poses),
            "poses":poses,
            "allowed_collision_count":joint_allowed,
            "disallowed_collision_count":joint_disallowed,
            "status":(
                "sampled_poses_collision_free_or_validated_contact_only"
                if joint_disallowed==0
                else "disallowed_collision_detected"
            ),
        })

    gate=not incomplete and global_disallowed==0 and bool(joint_results)
    return {
        "schema_version":"0.1",
        "architecture_id":conditioning["architecture_id"],
        "provider_id":output_mapping.get("provider_id"),
        "provider_job_id":output_mapping.get("provider_job_id"),
        "samples_per_joint_requested":samples_per_joint,
        "joint_results":joint_results,
        "summary":{
            "status":(
                "sampled_pose_collision_gate_passed"
                if gate else "sampled_pose_collision_review_required"
            ),
            "sampled_pose_collision_gate_passed":gate,
            "allowed_collision_count":global_allowed,
            "disallowed_collision_count":global_disallowed,
            "incomplete_reasons":incomplete,
            "continuous_collision_detection_performed":False,
        },
        "production_geometry_authority":False,
        "warning":(
            "Passing checks only sampled joint poses. It is not continuous collision "
            "detection and does not prove collision-free motion between samples. "
            "Only explicitly validated joint-local contact regions can suppress a "
            "sampled triangle collision."
        ),
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("output_mapping")
    parser.add_argument("--contact-regions",default=None)
    parser.add_argument("--samples",type=int,default=9)
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    result=validate_pose_collisions(
        load_json(args.conditioning),
        load_json(args.output_mapping),
        contact_regions=(
            load_json(args.contact_regions) if args.contact_regions else None
        ),
        samples_per_joint=args.samples,
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0 if result["summary"]["sampled_pose_collision_gate_passed"] else 2


if __name__=="__main__":
    raise SystemExit(main())
