#!/usr/bin/env python3
"""Propose semantic Brickmen slot mapping for anonymous provider part meshes.

The proposal uses a *single global rigid-axis/uniform-scale registration* for the
whole generated part bundle, then solves a minimum-cost one-to-one assignment
between transformed provider part AABBs and Brickmen component-slot envelope
AABBs.

It does not trust provider output order or filenames.

The result is a review proposal. Left/right and front/back symmetries often
produce equally plausible global registrations, so automatic promotion is
intentionally conservative.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.geometry.inspect_mesh_bounds import inspect_mesh_bounds
from tools.geometry.validate_body_generation_provider_geometry import (
    load_json,
    slot_target_box,
    transform_box,
)


def _union(boxes: Sequence[Mapping[str,Sequence[float]]]):
    if not boxes:
        raise ValueError("Cannot union an empty box set")
    return {
        "min":[min(float(b["min"][i]) for b in boxes) for i in range(3)],
        "max":[max(float(b["max"][i]) for b in boxes) for i in range(3)],
    }


def _metrics(box):
    mn=list(map(float,box["min"])); mx=list(map(float,box["max"]))
    return {
        "min":mn,"max":mx,
        "size":[mx[i]-mn[i] for i in range(3)],
        "center":[(mn[i]+mx[i])/2.0 for i in range(3)],
    }


def _diag(size):
    return math.sqrt(sum(float(v)*float(v) for v in size))


def _permutation_parity(perm):
    inv=sum(
        1 for i in range(len(perm)) for j in range(i+1,len(perm))
        if perm[i]>perm[j]
    )
    return -1 if inv%2 else 1


def _proper_rotation_sign(perm,signs):
    value=_permutation_parity(perm)
    for sign in signs:
        value*=int(sign)
    return value==1


def _uniform_scale(source_size,target_size):
    denom=sum(float(v)*float(v) for v in source_size)
    if denom<=1e-15:
        raise ValueError("Provider part union has zero total extent")
    return sum(
        float(source_size[i])*float(target_size[i])
        for i in range(3)
    )/denom


def _matrix(perm,signs,scale,source_center,target_center):
    rows=[]
    for i in range(3):
        row=[0.0,0.0,0.0,0.0]
        row[int(perm[i])]=float(scale)*float(signs[i])
        row[3]=float(target_center[i])-sum(
            row[j]*float(source_center[j]) for j in range(3)
        )
        rows.extend(row)
    rows.extend([0.0,0.0,0.0,1.0])
    return rows


def _shape_log_rmse(actual,target):
    terms=[]
    for a,t in zip(actual,target):
        a=max(abs(float(a)),1e-9)
        t=max(abs(float(t)),1e-9)
        terms.append(math.log(a/t)**2)
    return math.sqrt(sum(terms)/len(terms))


def _intersection_volume(a,b):
    lengths=[
        max(
            0.0,
            min(float(a["max"][i]),float(b["max"][i]))
            - max(float(a["min"][i]),float(b["min"][i])),
        )
        for i in range(3)
    ]
    return lengths[0]*lengths[1]*lengths[2]


def _volume(box):
    return math.prod(
        max(0.0,float(box["max"][i])-float(box["min"][i]))
        for i in range(3)
    )


def _iou(a,b):
    inter=_intersection_volume(a,b)
    union=_volume(a)+_volume(b)-inter
    return inter/union if union>1e-15 else 0.0


def _pair_cost(actual,target,global_diag):
    actual=_metrics(actual)
    target=_metrics(target)
    shape=_shape_log_rmse(actual["size"],target["size"])
    center=math.sqrt(sum(
        (float(actual["center"][i])-float(target["center"][i]))**2
        for i in range(3)
    ))/max(float(global_diag),1e-9)
    overlap_penalty=1.0-_iou(actual,target)
    return {
        "total":shape+2.0*center+0.5*overlap_penalty,
        "shape_log_rmse":shape,
        "normalized_center_distance":center,
        "aabb_iou":1.0-overlap_penalty,
    }


def _assign(costs):
    """Assign min(n_parts,n_slots) one-to-one pairs using bitmask DP."""
    n=len(costs)
    m=len(costs[0]) if n else 0
    k=min(n,m)
    # mask -> (cost, [(part_idx, slot_idx), ...])
    dp={0:(0.0,[])}
    for part_idx in range(n):
        nxt=dict(dp)  # skipping this provider part is permitted.
        for mask,(cost,pairs) in dp.items():
            if mask.bit_count()>=k:
                continue
            for slot_idx in range(m):
                bit=1<<slot_idx
                if mask&bit:
                    continue
                new_mask=mask|bit
                new_cost=cost+float(costs[part_idx][slot_idx]["total"])
                previous=nxt.get(new_mask)
                if previous is None or new_cost<previous[0]:
                    nxt[new_mask]=(
                        new_cost,
                        [*pairs,(part_idx,slot_idx)],
                    )
        dp=nxt
    candidates=[
        (cost,pairs,mask)
        for mask,(cost,pairs) in dp.items()
        if mask.bit_count()==k and len(pairs)==k
    ]
    if not candidates:
        return 0.0,[],0
    return min(candidates,key=lambda x:x[0])


def _required_slots(conditioning,provider_job):
    if provider_job:
        return [
            dict(item)
            for item in provider_job.get("component_slots",{}).get("required",[])
        ]
    return [
        dict(item)
        for item in conditioning.get("component_plan",{}).get(
            "generated_component_slots",[]
        )
        if item.get("required",True)
    ]


def _component_paths(provider_run):
    classification=provider_run.get("output_classification") or {}
    paths=list(classification.get("component_candidates") or [])
    if paths:
        return paths
    # Fallback deliberately excludes obvious aggregate/non-mesh artifacts.
    return [
        str(path) for path in provider_run.get("discovered_outputs",[])
        if Path(path).suffix.lower() in {".obj",".glb",".gltf",".ply",".stl"}
    ]


def propose_output_mapping(
    conditioning: Mapping[str,Any],
    provider_run: Mapping[str,Any],
    *,
    provider_job: Mapping[str,Any] | None=None,
    candidate_limit: int=12,
    near_best_score_delta: float=.02,
) -> dict[str,Any]:
    provider_id=provider_run.get("provider_id")
    if provider_job:
        if provider_job.get("provider_id")!=provider_id:
            raise ValueError("Provider job/run IDs do not match")
        if provider_job.get("pipeline_stage")=="post_generation_critic":
            raise ValueError(
                "Post-generation critic outputs are not primary component-mapping candidates"
            )
        if provider_job.get("requires_component_slot_mapping") is False:
            raise ValueError("Provider job explicitly disables component-slot mapping")

    required_slots=_required_slots(conditioning,provider_job)
    slot_ids=[str(item["slot_id"]) for item in required_slots]
    targets=[]
    missing_visual=[]
    for slot in slot_ids:
        target=slot_target_box(conditioning,slot)
        if target is None:
            missing_visual.append(slot)
        else:
            targets.append((slot,target))
    if not targets:
        raise ValueError("No required component slots have visual target envelopes")

    raw_paths=_component_paths(provider_run)
    components=[]
    invalid=[]
    for path in raw_paths:
        try:
            bounds=inspect_mesh_bounds(path)
        except Exception as exc:
            invalid.append({"path":str(path),"error":str(exc)})
            continue
        if _diag(bounds["size"])<=1e-10:
            invalid.append({
                "path":str(path),
                "error":"zero_or_negligible_mesh_extent",
            })
            continue
        components.append({
            "path":str(path),
            "provider_bounds":{
                key:bounds[key] for key in ("min","max","size","center","format")
            },
        })
    if not components:
        raise ValueError("Provider run exposes no readable nondegenerate component meshes")

    provider_union=_metrics(_union([
        c["provider_bounds"] for c in components
    ]))
    target_union=_metrics(_union([
        target for _,target in targets
    ]))
    global_diag=max(_diag(target_union["size"]),1e-9)

    candidates=[]
    for perm in itertools.permutations(range(3)):
        permuted=[
            provider_union["size"][perm[i]] for i in range(3)
        ]
        scale=_uniform_scale(permuted,target_union["size"])
        if scale<=0:
            continue
        for signs in itertools.product((-1,1),repeat=3):
            if not _proper_rotation_sign(perm,signs):
                continue
            matrix=_matrix(
                perm,signs,scale,
                provider_union["center"],target_union["center"],
            )
            transformed=[
                transform_box(c["provider_bounds"],matrix)
                for c in components
            ]
            costs=[
                [
                    _pair_cost(box,target,global_diag)
                    for _,target in targets
                ]
                for box in transformed
            ]
            assignment_cost,pairs,mask=_assign(costs)
            assignments=[]
            assigned_parts=set()
            assigned_slots=set()
            for part_idx,slot_idx in pairs:
                slot,target=targets[slot_idx]
                assigned_parts.add(part_idx)
                assigned_slots.add(slot)
                assignments.append({
                    "provider_part_path":components[part_idx]["path"],
                    "slot_id":slot,
                    "pair_cost":costs[part_idx][slot_idx],
                    "transformed_aabb_mm":transformed[part_idx],
                    "target_aabb_mm":target,
                })
            assignments.sort(key=lambda x:x["slot_id"])
            union_shape=_shape_log_rmse(
                [scale*v for v in permuted],
                target_union["size"],
            )
            avg_assignment=(
                assignment_cost/max(len(pairs),1)
            )
            missing_slots=sorted(set(slot for slot,_ in targets)-assigned_slots)
            unassigned=[
                components[i]["path"]
                for i in range(len(components))
                if i not in assigned_parts
            ]
            total=union_shape+avg_assignment
            candidates.append({
                "total_score":total,
                "union_shape_log_rmse":union_shape,
                "average_assignment_cost":avg_assignment,
                "axis_permutation_target_from_provider":list(perm),
                "axis_signs":list(signs),
                "uniform_scale_provider_units_to_mm":scale,
                "global_transform_matrix_to_brickmen_mm":matrix,
                "assignments":assignments,
                "missing_visual_target_slots":missing_visual,
                "missing_geometrically_mappable_slots":missing_slots,
                "unassigned_provider_parts":unassigned,
                "complete_visual_slot_assignment":(
                    not missing_visual
                    and not missing_slots
                    and len(assignments)==len(slot_ids)
                ),
            })

    candidates.sort(key=lambda x:(
        x["total_score"],
        x["axis_permutation_target_from_provider"],
        x["axis_signs"],
    ))
    if not candidates:
        raise ValueError("No global alignment/mapping candidates could be constructed")

    best=float(candidates[0]["total_score"])
    near=[
        item for item in candidates
        if float(item["total_score"])<=best+near_best_score_delta
    ]
    second=(
        float(candidates[1]["total_score"])
        if len(candidates)>1 else None
    )
    best_margin=(second-best) if second is not None else None
    exact_same_assignment={
        tuple(
            sorted(
                (a["provider_part_path"],a["slot_id"])
                for a in item["assignments"]
            )
        )
        for item in near
    }
    sign_ambiguity=len(near)>1
    mapping_ambiguity=len(exact_same_assignment)>1

    # Deliberately conservative. Geometry-only auto-promotion requires a unique
    # near-best mapping/orientation and a substantial score margin. Symmetric
    # left/right figures will normally fail this condition and require review.
    auto=bool(
        candidates[0]["complete_visual_slot_assignment"]
        and len(near)==1
        and best_margin is not None
        and best_margin>=0.10
        and best<=0.75
    )

    return {
        "schema_version":"0.1",
        "architecture_id":conditioning["architecture_id"],
        "provider_id":provider_id,
        "provider_job_id":provider_run.get("provider_job_id"),
        "component_candidates":components,
        "invalid_or_degenerate_outputs":invalid,
        "required_slots":required_slots,
        "visual_target_slot_ids":[slot for slot,_ in targets],
        "missing_visual_target_slots":missing_visual,
        "provider_union_bounds":provider_union,
        "target_union_bounds_mm":target_union,
        "global_alignment_candidates":candidates[:candidate_limit],
        "ambiguity":{
            "near_best_score_delta":near_best_score_delta,
            "near_best_candidate_count":len(near),
            "distinct_near_best_mapping_count":len(exact_same_assignment),
            "orientation_or_sign_ambiguous":sign_ambiguity,
            "semantic_mapping_ambiguous":mapping_ambiguity,
            "best_to_second_score_margin":best_margin,
            "explanation":(
                "Geometry can usually recover scale/axis placement and coarse semantic "
                "roles, but symmetric left/right parts may remain equally plausible. "
                "Provider part ordering is never treated as semantic evidence."
            ),
        },
        "automatic_promotion_allowed":auto,
        "recommended_action":(
            "review the highest-ranked global mapping against Brickmen structural guides; "
            "then explicitly promote one candidate into the provider-output mapping"
        ),
        "production_geometry_authority":False,
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("provider_run")
    parser.add_argument("--provider-job",default=None)
    parser.add_argument("--limit",type=int,default=12)
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    result=propose_output_mapping(
        load_json(args.conditioning),
        load_json(args.provider_run),
        provider_job=(
            load_json(args.provider_job) if args.provider_job else None
        ),
        candidate_limit=args.limit,
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
