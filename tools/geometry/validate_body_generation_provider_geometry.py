#!/usr/bin/env python3
"""Coarse geometry validation for mapped provider body components.

This gate operates only after an explicit provider->Brickmen-mm transform exists.

Checks:
- actual transformed mesh AABB;
- expected component-slot visual-envelope AABB;
- visual size/center plausibility;
- potential fixed mechanical keep-out overlap;
- potential overlap with OTHER component articulation sweeps.

Bounding boxes are intentionally coarse. A flagged overlap is a request for
exact triangle/collision/boolean analysis, not proof of invalid geometry.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.geometry.inspect_mesh_bounds import inspect_mesh_bounds


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _union_boxes(boxes: Sequence[Mapping[str, Sequence[float]]]) -> dict[str,list[float]]:
    if not boxes:
        raise ValueError("Cannot union empty box list")
    return {
        "min":[min(float(b["min"][i]) for b in boxes) for i in range(3)],
        "max":[max(float(b["max"][i]) for b in boxes) for i in range(3)],
    }


def _box_metrics(box: Mapping[str, Sequence[float]]) -> dict[str,list[float]]:
    mn=list(map(float,box["min"])); mx=list(map(float,box["max"]))
    return {
        "min":mn,
        "max":mx,
        "size":[mx[i]-mn[i] for i in range(3)],
        "center":[(mn[i]+mx[i])/2 for i in range(3)],
    }


def _envelope_box(
    conditioning: Mapping[str,Any],
    envelope: Mapping[str,Any],
) -> dict[str,list[float]]:
    size=list(map(float,envelope.get("size_mm_at_target_height") or [0,0,0]))
    shape=str(envelope.get("shape") or "")
    if envelope.get("a_mm_at_target_height") is not None:
        a=list(map(float,envelope["a_mm_at_target_height"]))
        b=list(map(float,envelope["b_mm_at_target_height"]))
        if shape=="capsule_between_nodes":
            half=[
                size[0]/2.0,
                size[1]/2.0,
                max(size[0],size[1])/2.0,
            ]
        else:
            half=[size[0]/2.0,size[1]/2.0,size[2]/2.0]
        return {
            "min":[min(a[i],b[i])-half[i] for i in range(3)],
            "max":[max(a[i],b[i])+half[i] for i in range(3)],
        }

    center_id=envelope.get("center_node")
    nodes=conditioning["skeleton_control"]["nodes"]
    if center_id not in nodes:
        raise ValueError(
            f"Envelope {envelope.get('envelope_id')} has no resolvable center"
        )
    center=list(map(float,nodes[center_id]["position_mm_at_target_height"]))
    half=[abs(v)/2.0 for v in size]
    return {
        "min":[center[i]-half[i] for i in range(3)],
        "max":[center[i]+half[i] for i in range(3)],
    }


def slot_target_box(
    conditioning: Mapping[str,Any],
    slot_id: str,
) -> dict[str,Any] | None:
    envs=[
        env for env in conditioning.get("visual_envelopes",[])
        if env.get("component_slot_id")==slot_id
    ]
    if not envs:
        return None
    boxes=[_envelope_box(conditioning,env) for env in envs]
    box=_box_metrics(_union_boxes(boxes))
    box["envelope_ids"]=[env["envelope_id"] for env in envs]
    return box


def transform_point(
    point: Sequence[float],
    matrix: Sequence[float],
) -> list[float]:
    if len(matrix)!=16:
        raise ValueError("Transform matrix must contain 16 row-major values")
    x,y,z=map(float,point)
    m=list(map(float,matrix))
    out=[
        m[0]*x+m[1]*y+m[2]*z+m[3],
        m[4]*x+m[5]*y+m[6]*z+m[7],
        m[8]*x+m[9]*y+m[10]*z+m[11],
    ]
    w=m[12]*x+m[13]*y+m[14]*z+m[15]
    if abs(w)>1e-12 and abs(w-1.0)>1e-12:
        out=[v/w for v in out]
    return out


def transform_box(
    box: Mapping[str,Sequence[float]],
    matrix: Sequence[float],
) -> dict[str,Any]:
    mn=list(map(float,box["min"])); mx=list(map(float,box["max"]))
    corners=[
        transform_point(p,matrix)
        for p in itertools.product(
            (mn[0],mx[0]),(mn[1],mx[1]),(mn[2],mx[2])
        )
    ]
    return _box_metrics({
        "min":[min(p[i] for p in corners) for i in range(3)],
        "max":[max(p[i] for p in corners) for i in range(3)],
    })


def boxes_intersect(
    a: Mapping[str,Sequence[float]],
    b: Mapping[str,Sequence[float]],
) -> bool:
    return all(
        float(a["min"][i]) <= float(b["max"][i])
        and float(a["max"][i]) >= float(b["min"][i])
        for i in range(3)
    )


def _mechanical_boxes(
    conditioning: Mapping[str,Any],
    slot_id: str,
) -> list[dict[str,Any]]:
    result=[]
    for constraint in conditioning.get("mechanical_constraints",[]):
        for placement in constraint.get("placements",[]):
            if slot_id not in placement.get("affected_component_slot_ids",[]):
                continue
            anchor=placement.get("anchor_mm_at_target_height")
            lo=placement.get("reference_keepout_local_min_mm")
            hi=placement.get("reference_keepout_local_max_mm")
            if anchor is None or lo is None or hi is None:
                continue
            result.append({
                "joint_profile_id":constraint.get("joint_profile_id"),
                "placement_id":placement.get("placement_id"),
                "authority_class":constraint.get("authority_class"),
                "boolean_subtraction_required_before_mechanical_validation":placement.get(
                    "boolean_subtraction_required_before_mechanical_validation",False
                ),
                "box":{
                    "min":[float(anchor[i])+float(lo[i]) for i in range(3)],
                    "max":[float(anchor[i])+float(hi[i]) for i in range(3)],
                },
            })
    return result


def _sweep_boxes_for_other_slots(
    conditioning: Mapping[str,Any],
    sweeps: Mapping[str,Any] | None,
    slot_id: str,
) -> list[dict[str,Any]]:
    if not sweeps:
        return []
    env_slot={
        env["envelope_id"]:env.get("component_slot_id")
        for env in conditioning.get("visual_envelopes",[])
    }
    result=[]
    for sweep in sweeps.get("joint_sweeps",[]):
        swept_slots={
            env_slot.get(item.get("envelope_id"))
            for item in sweep.get("visual_envelopes",[])
        }
        swept_slots.discard(None)
        if slot_id in swept_slots:
            continue
        box=sweep.get("combined_swept_aabb_mm")
        if box:
            result.append({
                "joint_id":sweep.get("joint_id"),
                "moving_component_slots":sorted(swept_slots),
                "box":box,
            })
    return result


def validate_provider_geometry(
    conditioning: Mapping[str,Any],
    output_mapping: Mapping[str,Any],
    *,
    sweeps: Mapping[str,Any] | None=None,
    relative_tolerance: float=0.30,
    absolute_tolerance_mm: float=2.0,
    minimum_size_fraction: float=0.25,
) -> dict[str,Any]:
    records=[]
    errors=[]
    exact_collision_review=False

    for component in output_mapping.get("components",[]):
        slot=str(component["slot_id"])
        matrix=component.get("transform_matrix_to_brickmen_mm")
        target=slot_target_box(conditioning,slot)
        base={
            "slot_id":slot,
            "path":component["path"],
            "transform_status":component.get("transform_status"),
            "visual_target":target,
        }

        if matrix is None:
            base.update({
                "status":"transform_required",
                "mesh_bounds_provider_frame":None,
                "mesh_bounds_brickmen_mm":None,
            })
            records.append(base)
            errors.append(f"{slot}:transform_required")
            continue

        try:
            raw=inspect_mesh_bounds(component["path"])
        except Exception as exc:
            base.update({
                "status":"mesh_inspection_failed",
                "inspection_error":str(exc),
            })
            records.append(base)
            errors.append(f"{slot}:mesh_inspection_failed")
            continue

        actual=transform_box(raw,matrix)
        base["mesh_bounds_provider_frame"]={
            key:raw[key] for key in ("min","max","size","center")
        }
        base["mesh_bounds_brickmen_mm"]=actual

        if target is None:
            base.update({
                "status":"no_visual_target_for_slot",
                "visual_conformance":None,
            })
        else:
            tol=[
                max(abs(float(target["size"][i]))*relative_tolerance,
                    absolute_tolerance_mm)
                for i in range(3)
            ]
            expanded={
                "min":[float(target["min"][i])-tol[i] for i in range(3)],
                "max":[float(target["max"][i])+tol[i] for i in range(3)],
            }
            within=all(
                float(actual["min"][i])>=expanded["min"][i]
                and float(actual["max"][i])<=expanded["max"][i]
                for i in range(3)
            )
            size_ratio=[
                (
                    float(actual["size"][i])/float(target["size"][i])
                    if abs(float(target["size"][i]))>1e-9 else None
                )
                for i in range(3)
            ]
            sufficiently_large=all(
                ratio is None or ratio>=minimum_size_fraction
                for ratio in size_ratio
            )
            center_offset=[
                float(actual["center"][i])-float(target["center"][i])
                for i in range(3)
            ]
            diagonal=math.sqrt(sum(float(v)*float(v) for v in target["size"]))
            normalized_center_offset=(
                math.sqrt(sum(v*v for v in center_offset))/diagonal
                if diagonal>1e-9 else None
            )
            plausible=within and sufficiently_large
            base["visual_conformance"]={
                "within_expanded_target_aabb":within,
                "sufficient_minimum_size":sufficiently_large,
                "plausible":plausible,
                "relative_tolerance":relative_tolerance,
                "absolute_tolerance_mm":absolute_tolerance_mm,
                "minimum_size_fraction":minimum_size_fraction,
                "size_ratio_actual_to_target":size_ratio,
                "center_offset_mm":center_offset,
                "normalized_center_offset":normalized_center_offset,
                "expanded_target_aabb_mm":expanded,
            }
            base["status"]=(
                "bbox_visual_target_plausible"
                if plausible
                else "bbox_visual_target_review_required"
            )
            if not plausible:
                errors.append(f"{slot}:visual_bbox_review_required")

        mechanical=[]
        for keepout in _mechanical_boxes(conditioning,slot):
            overlap=boxes_intersect(actual,keepout["box"])
            mechanical.append({
                **keepout,
                "bbox_intersection":overlap,
                "interpretation":(
                    "potential_overlap_requires_exact_mesh_boolean_or_collision_check"
                    if overlap else "no_bbox_overlap"
                ),
            })
            if overlap:
                exact_collision_review=True
        base["mechanical_keepout_checks"]=mechanical

        articulation=[]
        for sweep in _sweep_boxes_for_other_slots(
            conditioning,sweeps,slot
        ):
            overlap=boxes_intersect(actual,sweep["box"])
            articulation.append({
                **sweep,
                "bbox_intersection":overlap,
                "interpretation":(
                    "potential_overlap_requires_exact_pose_collision_check"
                    if overlap else "no_bbox_overlap"
                ),
            })
            if overlap:
                exact_collision_review=True
        base["other_component_articulation_sweep_checks"]=articulation
        records.append(base)

    complete=bool(records) and not any(
        r["status"] in {
            "transform_required",
            "mesh_inspection_failed",
            "bbox_visual_target_review_required",
        }
        for r in records
    )
    status=(
        "bbox_geometry_plausible_requires_exact_collision_validation"
        if complete
        else "geometry_review_required"
    )
    return {
        "schema_version":"0.1",
        "architecture_id":conditioning["architecture_id"],
        "provider_id":output_mapping.get("provider_id"),
        "provider_job_id":output_mapping.get("provider_job_id"),
        "components":records,
        "summary":{
            "status":status,
            "bbox_geometry_gate_passed":complete,
            "exact_collision_or_boolean_review_required":exact_collision_review,
            "errors":errors,
            "component_count":len(records),
        },
        "production_geometry_authority":False,
        "warning":(
            "AABB validation is intentionally coarse. Passing does not establish "
            "surface quality, exact collision clearance, fit, or manufacturing authority."
        ),
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("output_mapping")
    parser.add_argument("--sweeps",default=None)
    parser.add_argument("--relative-tolerance",type=float,default=.30)
    parser.add_argument("--absolute-tolerance-mm",type=float,default=2.0)
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    result=validate_provider_geometry(
        load_json(args.conditioning),
        load_json(args.output_mapping),
        sweeps=load_json(args.sweeps) if args.sweeps else None,
        relative_tolerance=args.relative_tolerance,
        absolute_tolerance_mm=args.absolute_tolerance_mm,
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0 if result["summary"]["bbox_geometry_gate_passed"] else 2


if __name__=="__main__":
    raise SystemExit(main())
