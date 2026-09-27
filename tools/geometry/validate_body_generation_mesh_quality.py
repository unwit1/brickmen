#!/usr/bin/env python3
"""Topology/printability-preflight audit for mapped generated body meshes."""

from __future__ import annotations

import argparse
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


def _cross(a,b):
    return [
        float(a[1])*float(b[2])-float(a[2])*float(b[1]),
        float(a[2])*float(b[0])-float(a[0])*float(b[2]),
        float(a[0])*float(b[1])-float(a[1])*float(b[0]),
    ]


def _dot(a,b):
    return sum(float(a[i])*float(b[i]) for i in range(3))


def _key(p,digits=7):
    return tuple(round(float(v),digits) for v in p)


def _area2(tri):
    return math.sqrt(_dot(_cross(_sub(tri[1],tri[0]),_sub(tri[2],tri[0])),
                          _cross(_sub(tri[1],tri[0]),_sub(tri[2],tri[0]))))


def _canonical_triangle(tri):
    keys=sorted(_key(p) for p in tri)
    return tuple(keys)


def _face_components(face_edges):
    edge_faces={}
    for fi,edges in enumerate(face_edges):
        for edge in edges:
            edge_faces.setdefault(edge,[]).append(fi)
    adj=[set() for _ in face_edges]
    for faces in edge_faces.values():
        for a in faces:
            adj[a].update(b for b in faces if b!=a)
    count=0
    seen=set()
    for start in range(len(face_edges)):
        if start in seen: continue
        count+=1
        stack=[start]; seen.add(start)
        while stack:
            cur=stack.pop()
            for nxt in adj[cur]:
                if nxt not in seen:
                    seen.add(nxt); stack.append(nxt)
    return count


def audit_triangles(
    triangles: Sequence[Sequence[Sequence[float]]],
    *,
    degenerate_area2_threshold: float=1e-10,
) -> dict[str,Any]:
    edge_counts={}
    edge_directions={}
    face_edges=[]
    vertices=set()
    duplicate_count=0
    seen_faces=set()
    degenerate=0
    signed_volume6=0.0

    for tri in triangles:
        keys=[_key(p) for p in tri]
        vertices.update(keys)
        canon=_canonical_triangle(tri)
        if canon in seen_faces:
            duplicate_count+=1
        seen_faces.add(canon)
        if _area2(tri)<=degenerate_area2_threshold:
            degenerate+=1
        signed_volume6+=_dot(tri[0],_cross(tri[1],tri[2]))
        edges=[]
        for a,b in ((keys[0],keys[1]),(keys[1],keys[2]),(keys[2],keys[0])):
            undirected=tuple(sorted((a,b)))
            edges.append(undirected)
            edge_counts[undirected]=edge_counts.get(undirected,0)+1
            # Direction sign relative to sorted key.
            direction=1 if (a,b)==undirected else -1
            edge_directions.setdefault(undirected,[]).append(direction)
        face_edges.append(edges)

    boundary=sum(1 for n in edge_counts.values() if n==1)
    nonmanifold=sum(1 for n in edge_counts.values() if n>2)
    winding_conflicts=0
    for edge,directions in edge_directions.items():
        if len(directions)==2 and directions[0]==directions[1]:
            winding_conflicts+=1

    components=_face_components(face_edges) if face_edges else 0
    chi=len(vertices)-len(edge_counts)+len(triangles)
    closed=(
        bool(triangles)
        and boundary==0
        and nonmanifold==0
        and all(n==2 for n in edge_counts.values())
    )
    return {
        "triangle_count":len(triangles),
        "unique_vertex_count":len(vertices),
        "unique_edge_count":len(edge_counts),
        "connected_face_component_count":components,
        "boundary_edge_count":boundary,
        "nonmanifold_edge_count":nonmanifold,
        "winding_conflict_edge_count":winding_conflicts,
        "duplicate_triangle_count":duplicate_count,
        "degenerate_triangle_count":degenerate,
        "euler_characteristic":chi,
        "closed_two_manifold_candidate":closed,
        "signed_volume":signed_volume6/6.0,
        "absolute_volume":abs(signed_volume6/6.0),
    }


def validate_mesh_quality(
    output_mapping: Mapping[str,Any],
    *,
    require_single_component: bool=True,
) -> dict[str,Any]:
    results=[]
    all_pass=True

    for component in output_mapping.get("components",[]):
        slot=component["slot_id"]
        matrix=component.get("transform_matrix_to_brickmen_mm")
        try:
            source=load_mesh_triangles(component["path"])
        except Exception as exc:
            results.append({
                "slot_id":slot,"path":component["path"],
                "status":"triangle_extraction_failed","error":str(exc)
            })
            all_pass=False
            continue

        source_audit=audit_triangles(source)
        if matrix is not None:
            triangles=[
                tuple(tuple(transform_point(p,matrix)) for p in tri)
                for tri in source
            ]
            audit=audit_triangles(triangles)
            units="brickmen_mm"
            volume_units="mm3"
        else:
            audit=source_audit
            units="provider_units"
            volume_units="provider_units3"

        errors=[]
        if audit["boundary_edge_count"]>0:
            errors.append("open_boundary_edges")
        if audit["nonmanifold_edge_count"]>0:
            errors.append("nonmanifold_edges")
        if audit["winding_conflict_edge_count"]>0:
            errors.append("inconsistent_winding")
        if audit["duplicate_triangle_count"]>0:
            errors.append("duplicate_triangles")
        if audit["degenerate_triangle_count"]>0:
            errors.append("degenerate_triangles")
        if require_single_component and audit["connected_face_component_count"]!=1:
            errors.append("multiple_or_zero_disconnected_face_components")
        if audit["absolute_volume"]<=1e-12:
            errors.append("zero_or_negligible_signed_volume")

        passed=not errors
        if not passed:
            all_pass=False
        results.append({
            "slot_id":slot,
            "path":component["path"],
            "transform_status":component.get("transform_status"),
            "audit_frame":units,
            "volume_units":volume_units,
            "audit":audit,
            "source_provider_frame_audit":source_audit,
            "errors":errors,
            "status":"mesh_topology_preflight_pass" if passed else "mesh_repair_required",
        })

    status=(
        "all_mapped_components_pass_topology_preflight"
        if results and all_pass
        else "mesh_repair_or_review_required"
    )
    return {
        "schema_version":"0.1",
        "provider_id":output_mapping.get("provider_id"),
        "provider_job_id":output_mapping.get("provider_job_id"),
        "components":results,
        "summary":{
            "status":status,
            "mesh_quality_gate_passed":bool(results) and all_pass,
            "component_count":len(results),
            "require_single_component":require_single_component,
        },
        "production_geometry_authority":False,
        "warning":(
            "Topology preflight does not validate self-intersection, wall thickness, "
            "overhang, process compensation, strength, or physical interface performance."
        ),
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("output_mapping")
    parser.add_argument("--allow-disconnected",action="store_true")
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    result=validate_mesh_quality(
        load_json(args.output_mapping),
        require_single_component=not args.allow_disconnected,
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0 if result["summary"]["mesh_quality_gate_passed"] else 2


if __name__=="__main__":
    raise SystemExit(main())
