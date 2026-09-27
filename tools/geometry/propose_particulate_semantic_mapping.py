#!/usr/bin/env python3
"""Propose Particulate inferred-part -> Brickmen component-slot mappings.

This reuses the same global AABB-registration/assignment cost model as primary
provider part mapping, but operates on Particulate part bounds embedded in the
normalized critic report.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any, Mapping

from tools.geometry.propose_body_provider_output_mapping import (
    _assign,
    _diag,
    _matrix,
    _metrics,
    _pair_cost,
    _proper_rotation_sign,
    _shape_log_rmse,
    _uniform_scale,
    _union,
)
from tools.geometry.validate_body_generation_provider_geometry import (
    load_json,
    slot_target_box,
    transform_box,
)


def propose_particulate_mapping(
    conditioning: Mapping[str,Any],
    critic_report: Mapping[str,Any],
    *,
    candidate_limit: int=12,
    near_best_score_delta: float=.02,
) -> dict[str,Any]:
    if critic_report.get("critic_id")!="particulate":
        raise ValueError("Expected a normalized Particulate critic report")

    slots=[
        dict(item)
        for item in conditioning.get("component_plan",{}).get(
            "generated_component_slots",[]
        )
        if item.get("required",True)
    ]
    targets=[]
    missing_visual=[]
    for item in slots:
        slot=str(item["slot_id"])
        box=slot_target_box(conditioning,slot)
        if box is None:
            missing_visual.append(slot)
        else:
            targets.append((slot,box))
    if not targets:
        raise ValueError("No required Brickmen slots expose visual target boxes")

    components=[]
    missing_bounds=[]
    for part in critic_report.get("parts",[]):
        box=part.get("predicted_part_bounds")
        if box is None:
            missing_bounds.append(int(part["part_id"]))
            continue
        components.append({
            "part_id":int(part["part_id"]),
            "provider_bounds":box,
        })
    if not components:
        raise ValueError(
            "Particulate report has no per-part bounds; ingest with --pred-obj"
        )

    provider_union=_metrics(_union([
        c["provider_bounds"] for c in components
    ]))
    target_union=_metrics(_union([box for _,box in targets]))
    global_diag=max(_diag(target_union["size"]),1e-9)

    candidates=[]
    for perm in itertools.permutations(range(3)):
        permuted=[provider_union["size"][perm[i]] for i in range(3)]
        scale=_uniform_scale(permuted,target_union["size"])
        if scale<=0:
            continue
        for signs in itertools.product((-1,1),repeat=3):
            if not _proper_rotation_sign(perm,signs):
                continue
            matrix=_matrix(
                perm,signs,scale,
                provider_union["center"],target_union["center"]
            )
            transformed=[
                transform_box(c["provider_bounds"],matrix)
                for c in components
            ]
            costs=[
                [_pair_cost(box,target,global_diag) for _,target in targets]
                for box in transformed
            ]
            assignment_cost,pairs,_=_assign(costs)
            assignments=[]
            used_parts=set(); used_slots=set()
            for pi,si in pairs:
                slot,target=targets[si]
                used_parts.add(pi); used_slots.add(slot)
                assignments.append({
                    "particulate_part_id":components[pi]["part_id"],
                    "slot_id":slot,
                    "pair_cost":costs[pi][si],
                    "transformed_aabb_mm":transformed[pi],
                    "target_aabb_mm":target,
                })
            assignments.sort(key=lambda x:x["slot_id"])
            union_shape=_shape_log_rmse(
                [scale*v for v in permuted],target_union["size"]
            )
            avg=assignment_cost/max(len(pairs),1)
            candidates.append({
                "total_score":union_shape+avg,
                "union_shape_log_rmse":union_shape,
                "average_assignment_cost":avg,
                "axis_permutation_target_from_particulate":list(perm),
                "axis_signs":list(signs),
                "uniform_scale_particulate_units_to_mm":scale,
                "global_transform_particulate_to_brickmen_mm":matrix,
                "assignments":assignments,
                "missing_slots":sorted(set(slot for slot,_ in targets)-used_slots),
                "unassigned_particulate_part_ids":[
                    components[i]["part_id"]
                    for i in range(len(components))
                    if i not in used_parts
                ],
                "complete_required_visual_mapping":(
                    not missing_visual
                    and not missing_bounds
                    and len(assignments)==len(slots)
                ),
            })
    candidates.sort(key=lambda x:(
        x["total_score"],
        x["axis_permutation_target_from_particulate"],
        x["axis_signs"],
    ))
    if not candidates:
        raise ValueError("Could not construct Particulate mapping candidates")

    best=float(candidates[0]["total_score"])
    near=[
        c for c in candidates
        if float(c["total_score"])<=best+near_best_score_delta
    ]
    mapping_variants={
        tuple(sorted(
            (int(a["particulate_part_id"]),str(a["slot_id"]))
            for a in c["assignments"]
        ))
        for c in near
    }
    return {
        "schema_version":"0.1",
        "critic_id":"particulate",
        "architecture_id":conditioning["architecture_id"],
        "source_critic_report":critic_report.get("source_npz"),
        "part_count":critic_report.get("part_count"),
        "required_slots":slots,
        "missing_visual_target_slots":missing_visual,
        "parts_missing_bounds":missing_bounds,
        "global_alignment_candidates":candidates[:candidate_limit],
        "ambiguity":{
            "near_best_score_delta":near_best_score_delta,
            "near_best_candidate_count":len(near),
            "distinct_near_best_mapping_count":len(mapping_variants),
            "explanation":(
                "Particulate part IDs are anonymous critic labels. Symmetric "
                "left/right decompositions frequently remain geometrically ambiguous."
            ),
        },
        "automatic_promotion_allowed":False,
        "recommended_action":(
            "review one critic mapping candidate before interpreting predicted "
            "hierarchy/axes against Brickmen semantics"
        ),
        "production_geometry_authority":False,
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("critic_report")
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    result=propose_particulate_mapping(
        load_json(args.conditioning),load_json(args.critic_report)
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
