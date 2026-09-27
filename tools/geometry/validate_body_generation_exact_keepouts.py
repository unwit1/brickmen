#!/usr/bin/env python3
"""Exact-ish triangle/solid validation of fixed mechanical keep-out boxes.

For each mapped component affected by a mechanical placement:
1. load actual mesh triangles;
2. apply explicit provider->Brickmen-mm transform;
3. test every relevant triangle against the keep-out AABB using SAT;
4. if no surface crosses the box and the mesh is closed, sample keep-out center
   and corners with ray-parity point-in-mesh checks to catch a keep-out fully
   buried inside solid material.

This validates geometric emptiness of the reference keep-out volume only.
It does not validate fit tolerance, torque, wear, material behavior, or the
hardware/socket interface itself.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.geometry.inspect_mesh_triangles import load_mesh_triangles
from tools.geometry.validate_body_generation_provider_geometry import (
    load_json,
    transform_point,
)


def _sub(a,b):
    return [float(a[i])-float(b[i]) for i in range(3)]


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


def triangle_intersects_aabb(
    triangle: Sequence[Sequence[float]],
    box: Mapping[str,Sequence[float]],
    *,
    eps: float=1e-9,
) -> bool:
    mn=list(map(float,box["min"])); mx=list(map(float,box["max"]))
    center=[(mn[i]+mx[i])/2 for i in range(3)]
    half=[(mx[i]-mn[i])/2 for i in range(3)]
    v=[_sub(p,center) for p in triangle]
    edges=[_sub(v[1],v[0]),_sub(v[2],v[1]),_sub(v[0],v[2])]
    basis=[[1,0,0],[0,1,0],[0,0,1]]
    axes=list(basis)
    normal=_cross(edges[0],edges[1])
    axes.append(normal)
    for edge in edges:
        for axis in basis:
            axes.append(_cross(edge,axis))

    for axis in axes:
        if _norm2(axis)<=eps*eps:
            continue
        projection=[_dot(p,axis) for p in v]
        radius=sum(half[i]*abs(float(axis[i])) for i in range(3))
        if min(projection)>radius+eps or max(projection)<-radius-eps:
            return False
    return True


def _vertex_key(point: Sequence[float], digits: int=7):
    return tuple(round(float(v),digits) for v in point)


def mesh_topology_summary(
    triangles: Sequence[Sequence[Sequence[float]]],
) -> dict[str,Any]:
    edges={}
    for tri in triangles:
        keys=[_vertex_key(p) for p in tri]
        for a,b in ((keys[0],keys[1]),(keys[1],keys[2]),(keys[2],keys[0])):
            edge=tuple(sorted((a,b)))
            edges[edge]=edges.get(edge,0)+1
    boundary=sum(1 for n in edges.values() if n==1)
    nonmanifold=sum(1 for n in edges.values() if n>2)
    return {
        "triangle_count":len(triangles),
        "unique_edge_count":len(edges),
        "boundary_edge_count":boundary,
        "nonmanifold_edge_count":nonmanifold,
        "closed_two_manifold_candidate":(
            bool(triangles) and boundary==0 and nonmanifold==0
            and all(n==2 for n in edges.values())
        ),
    }


RAY_DIR=[1.0,0.3713906763541037,0.529145221375667]


def _ray_triangle_t(
    origin: Sequence[float],
    direction: Sequence[float],
    triangle: Sequence[Sequence[float]],
    *,
    eps: float=1e-10,
) -> float | None:
    a,b,c=triangle
    e1=_sub(b,a); e2=_sub(c,a)
    h=_cross(direction,e2)
    det=_dot(e1,h)
    if abs(det)<=eps:
        return None
    inv=1.0/det
    s=_sub(origin,a)
    u=inv*_dot(s,h)
    if u<-eps or u>1+eps:
        return None
    q=_cross(s,e1)
    v=inv*_dot(direction,q)
    if v<-eps or u+v>1+eps:
        return None
    t=inv*_dot(e2,q)
    return t if t>eps else None


def point_inside_closed_mesh(
    point: Sequence[float],
    triangles: Sequence[Sequence[Sequence[float]]],
) -> bool:
    ts=[]
    for tri in triangles:
        t=_ray_triangle_t(point,RAY_DIR,tri)
        if t is not None:
            ts.append(t)
    # Shared-edge hits can be duplicated by adjacent triangles. Collapse nearly
    # identical ray distances before applying parity.
    unique=[]
    for t in sorted(ts):
        if not unique or abs(t-unique[-1])>1e-7:
            unique.append(t)
    return len(unique)%2==1


def _box_samples(box: Mapping[str,Sequence[float]]) -> list[list[float]]:
    mn=list(map(float,box["min"])); mx=list(map(float,box["max"]))
    center=[(mn[i]+mx[i])/2 for i in range(3)]
    corners=[
        list(p) for p in itertools.product(
            (mn[0],mx[0]),(mn[1],mx[1]),(mn[2],mx[2])
        )
    ]
    return [center,*corners]


def _triangle_box_prefilter(tri,box) -> bool:
    for i in range(3):
        if max(float(p[i]) for p in tri)<float(box["min"][i]):
            return False
        if min(float(p[i]) for p in tri)>float(box["max"][i]):
            return False
    return True


def _keepouts_for_slot(conditioning: Mapping[str,Any],slot: str):
    for constraint in conditioning.get("mechanical_constraints",[]):
        for placement in constraint.get("placements",[]):
            if slot not in placement.get("affected_component_slot_ids",[]):
                continue
            anchor=placement.get("anchor_mm_at_target_height")
            lo=placement.get("reference_keepout_local_min_mm")
            hi=placement.get("reference_keepout_local_max_mm")
            if anchor is None or lo is None or hi is None:
                continue
            yield {
                "joint_profile_id":constraint.get("joint_profile_id"),
                "authority_class":constraint.get("authority_class"),
                "placement_id":placement.get("placement_id"),
                "box_mm":{
                    "min":[float(anchor[i])+float(lo[i]) for i in range(3)],
                    "max":[float(anchor[i])+float(hi[i]) for i in range(3)],
                },
            }


def validate_exact_keepouts(
    conditioning: Mapping[str,Any],
    output_mapping: Mapping[str,Any],
) -> dict[str,Any]:
    component_results=[]
    all_pass=True
    relevant_count=0

    for component in output_mapping.get("components",[]):
        slot=str(component["slot_id"])
        keepouts=list(_keepouts_for_slot(conditioning,slot))
        if not keepouts:
            continue
        relevant_count+=1
        matrix=component.get("transform_matrix_to_brickmen_mm")
        if matrix is None:
            component_results.append({
                "slot_id":slot,
                "path":component["path"],
                "status":"transform_required",
                "keepouts":[],
            })
            all_pass=False
            continue
        try:
            source=load_mesh_triangles(component["path"])
        except Exception as exc:
            component_results.append({
                "slot_id":slot,
                "path":component["path"],
                "status":"triangle_extraction_failed",
                "error":str(exc),
                "keepouts":[],
            })
            all_pass=False
            continue
        transformed=[
            tuple(
                tuple(transform_point(p,matrix)) for p in tri
            )
            for tri in source
        ]
        topology=mesh_topology_summary(transformed)
        kresults=[]
        comp_pass=True
        for keepout in keepouts:
            box=keepout["box_mm"]
            surface_hits=0
            for tri in transformed:
                if not _triangle_box_prefilter(tri,box):
                    continue
                if triangle_intersects_aabb(tri,box):
                    surface_hits+=1
            inside_samples=[]
            if surface_hits==0 and topology["closed_two_manifold_candidate"]:
                for p in _box_samples(box):
                    if point_inside_closed_mesh(p,transformed):
                        inside_samples.append(p)
            if surface_hits:
                status="keepout_surface_intersection"
                empty=False
            elif topology["closed_two_manifold_candidate"] and inside_samples:
                status="keepout_inside_solid_material"
                empty=False
            elif topology["closed_two_manifold_candidate"]:
                status="keepout_geometrically_empty"
                empty=True
            else:
                status="inconclusive_open_or_nonmanifold_mesh"
                empty=False
            if not empty:
                comp_pass=False
            kresults.append({
                **keepout,
                "status":status,
                "geometrically_empty":empty,
                "surface_intersection_triangle_count":surface_hits,
                "inside_sample_count":len(inside_samples),
                "inside_samples_mm":inside_samples,
            })
        if not comp_pass:
            all_pass=False
        component_results.append({
            "slot_id":slot,
            "path":component["path"],
            "status":(
                "exact_keepout_pass"
                if comp_pass else "exact_keepout_review_required"
            ),
            "mesh_topology":topology,
            "keepouts":kresults,
        })

    if relevant_count==0:
        status="no_scoped_mechanical_keepouts_to_validate"
        gate=True
    elif all_pass:
        status="exact_reference_keepouts_geometrically_empty"
        gate=True
    else:
        status="exact_keepout_validation_failed_or_inconclusive"
        gate=False

    return {
        "schema_version":"0.1",
        "architecture_id":conditioning["architecture_id"],
        "provider_id":output_mapping.get("provider_id"),
        "provider_job_id":output_mapping.get("provider_job_id"),
        "components":component_results,
        "summary":{
            "status":status,
            "exact_keepout_gate_passed":gate,
            "scoped_component_count":relevant_count,
        },
        "production_geometry_authority":False,
        "warning":(
            "Passing proves only that the tested reference keep-out boxes are empty "
            "of the generated closed mesh under the supplied transform. It does not "
            "validate mating geometry, tolerance, torque, wear, or articulation."
        ),
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("output_mapping")
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    result=validate_exact_keepouts(
        load_json(args.conditioning),load_json(args.output_mapping)
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0 if result["summary"]["exact_keepout_gate_passed"] else 2


if __name__=="__main__":
    raise SystemExit(main())
