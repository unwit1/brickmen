#!/usr/bin/env python3
"""Propose provider->Brickmen-mm alignment candidates from component bounds.

The estimator searches orientation-preserving signed axis permutations, solves
one uniform scale, and centers the transformed provider bounding box on the
target Brickmen component-slot box.

Bounding boxes cannot resolve many sign/front-back ambiguities. Therefore this
tool produces ranked *candidates* and never promotes a transform automatically
when equally plausible orientations remain.
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


def _permutation_parity(perm: Sequence[int]) -> int:
    inversions=0
    for i in range(len(perm)):
        for j in range(i+1,len(perm)):
            if perm[i]>perm[j]:
                inversions+=1
    return -1 if inversions%2 else 1


def _det_sign(perm: Sequence[int], signs: Sequence[int]) -> int:
    sign=_permutation_parity(perm)
    for value in signs:
        sign*=int(value)
    return sign


def _scale_least_squares(source: Sequence[float], target: Sequence[float]) -> float:
    denom=sum(float(x)*float(x) for x in source)
    if denom<=1e-15:
        raise ValueError("Provider bounding box has zero total size")
    return sum(float(source[i])*float(target[i]) for i in range(3))/denom


def _shape_error(
    transformed_size: Sequence[float],
    target_size: Sequence[float],
) -> float:
    terms=[]
    for actual,target in zip(transformed_size,target_size):
        actual=float(actual); target=float(target)
        if actual<=1e-12 or target<=1e-12:
            continue
        terms.append(math.log(actual/target)**2)
    return math.sqrt(sum(terms)/len(terms)) if terms else float("inf")


def _matrix(
    perm: Sequence[int],
    signs: Sequence[int],
    scale: float,
    source_center: Sequence[float],
    target_center: Sequence[float],
) -> list[float]:
    # target[i] = scale*sign[i]*source[perm[i]] + translation[i]
    rows=[]
    for i in range(3):
        row=[0.0,0.0,0.0,0.0]
        row[perm[i]]=scale*float(signs[i])
        row[3]=float(target_center[i])-sum(
            row[j]*float(source_center[j]) for j in range(3)
        )
        rows.extend(row)
    rows.extend([0.0,0.0,0.0,1.0])
    return rows


def propose_alignment_candidates(
    conditioning: Mapping[str,Any],
    mesh_path: str | Path,
    slot_id: str,
    *,
    candidate_limit: int=12,
    dimension_error_tolerance: float=1e-9,
) -> dict[str,Any]:
    target=slot_target_box(conditioning,slot_id)
    if target is None:
        raise ValueError(f"No visual target envelopes exist for slot {slot_id}")
    provider=inspect_mesh_bounds(mesh_path)
    source_size=list(map(float,provider["size"]))
    source_center=list(map(float,provider["center"]))
    target_size=list(map(float,target["size"]))
    target_center=list(map(float,target["center"]))

    candidates=[]
    for perm in itertools.permutations(range(3)):
        permuted=[source_size[perm[i]] for i in range(3)]
        scale=_scale_least_squares(permuted,target_size)
        if scale<=0:
            continue
        transformed_size=[scale*v for v in permuted]
        error=_shape_error(transformed_size,target_size)
        for signs in itertools.product((-1,1),repeat=3):
            # Restrict to proper rotations + uniform positive scale. Reflection
            # proposals can be added explicitly later when source semantics justify it.
            if _det_sign(perm,signs)!=1:
                continue
            matrix=_matrix(
                perm,signs,scale,source_center,target_center
            )
            transformed=transform_box(provider,matrix)
            candidates.append({
                "axis_permutation_target_from_provider":list(perm),
                "axis_signs":list(signs),
                "uniform_scale_provider_units_to_mm":scale,
                "shape_log_rmse":error,
                "transform_matrix_to_brickmen_mm":matrix,
                "transformed_box_mm":transformed,
                "determinant_sign":1,
            })

    candidates.sort(key=lambda x:(
        x["shape_log_rmse"],
        x["axis_permutation_target_from_provider"],
        x["axis_signs"],
    ))
    if not candidates:
        raise ValueError("No alignment candidates could be constructed")

    best_error=float(candidates[0]["shape_log_rmse"])
    equivalent=[
        c for c in candidates
        if abs(float(c["shape_log_rmse"])-best_error)<=dimension_error_tolerance
    ]
    best_perm=equivalent[0]["axis_permutation_target_from_provider"]
    same_perm=[
        c for c in equivalent
        if c["axis_permutation_target_from_provider"]==best_perm
    ]

    distinct_perms={
        tuple(c["axis_permutation_target_from_provider"]) for c in equivalent
    }
    automatic=(
        len(equivalent)==1
        and best_error<=0.08
    )

    return {
        "schema_version":"0.1",
        "slot_id":slot_id,
        "mesh_path":str(mesh_path),
        "target_box_mm":target,
        "provider_box":{
            key:provider[key] for key in (
                "min","max","size","center","format","units","coordinate_frame"
            )
        },
        "candidates":candidates[:candidate_limit],
        "best_shape_log_rmse":best_error,
        "equally_best_candidate_count":len(equivalent),
        "equally_best_axis_permutation_count":len(distinct_perms),
        "same_best_axis_permutation_orientation_count":len(same_perm),
        "ambiguity":{
            "axis_permutation_ambiguous":len(distinct_perms)>1,
            "sign_or_front_back_ambiguous":len(same_perm)>1,
            "explanation":(
                "Bounding-box dimensions cannot by themselves resolve all axis signs "
                "or front/back orientation, especially for symmetric components."
            ),
        },
        "automatic_promotion_allowed":automatic,
        "recommended_action":(
            "review against structural guide or use semantic/feature alignment before "
            "copying a candidate transform into the provider output mapping"
        ),
        "production_geometry_authority":False,
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("mesh")
    parser.add_argument("slot_id")
    parser.add_argument("--limit",type=int,default=12)
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    result=propose_alignment_candidates(
        load_json(args.conditioning),
        args.mesh,
        args.slot_id,
        candidate_limit=args.limit,
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
