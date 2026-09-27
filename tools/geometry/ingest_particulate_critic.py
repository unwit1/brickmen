#!/usr/bin/env python3
"""Normalize Particulate pred.npz/pred.obj into Brickmen critic evidence."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from tools.geometry.read_numeric_npz import read_npz


EXPECTED_KEYS={
    "face_part_ids",
    "motion_hierarchy",
    "is_part_revolute",
    "is_part_prismatic",
    "revolute_plucker",
    "revolute_range",
    "prismatic_axis",
    "prismatic_range",
}


def _values(arrays,key):
    if key not in arrays:
        raise ValueError(f"Particulate NPZ missing required array {key}")
    return arrays[key]["values"]


def _axis_point(plucker):
    direction=[float(v) for v in plucker[:3]]
    moment=[float(v) for v in plucker[3:6]]
    n=math.sqrt(sum(v*v for v in direction))
    if n<=1e-12:
        return None,None
    axis=[v/n for v in direction]
    point=[
        moment[1]*axis[2]-moment[2]*axis[1],
        moment[2]*axis[0]-moment[0]*axis[2],
        moment[0]*axis[1]-moment[1]*axis[0],
    ]
    return axis,point


def _obj_part_bounds(path: str | Path,face_part_ids):
    p=Path(path)
    vertices=[]
    faces=[]
    for raw in p.read_text(encoding="utf-8",errors="replace").splitlines():
        line=raw.strip()
        if line.startswith("v "):
            f=line.split()
            vertices.append(tuple(map(float,f[1:4])))
        elif line.startswith("f "):
            refs=line.split()[1:]
            idx=[]
            for ref in refs:
                raw_i=int(ref.split("/")[0])
                idx.append(raw_i-1 if raw_i>0 else len(vertices)+raw_i)
            faces.append(idx)
    if len(faces)!=len(face_part_ids):
        return {
            "status":"face_count_mismatch",
            "obj_face_count":len(faces),
            "face_part_id_count":len(face_part_ids),
            "part_bounds":{},
        }
    by_part={}
    for face,part_id in zip(faces,face_part_ids):
        points=[vertices[i] for i in face]
        bucket=by_part.setdefault(int(part_id),[])
        bucket.extend(points)
    bounds={}
    for part_id,points in by_part.items():
        mn=[min(p[i] for p in points) for i in range(3)]
        mx=[max(p[i] for p in points) for i in range(3)]
        bounds[str(part_id)]={
            "min":mn,
            "max":mx,
            "size":[mx[i]-mn[i] for i in range(3)],
            "center":[(mn[i]+mx[i])/2 for i in range(3)],
        }
    return {
        "status":"ok",
        "obj_face_count":len(faces),
        "face_part_id_count":len(face_part_ids),
        "part_bounds":bounds,
    }


def ingest_particulate(
    npz_path: str | Path,
    *,
    pred_obj: str | Path | None=None,
) -> dict[str,Any]:
    arrays=read_npz(npz_path)
    missing=sorted(EXPECTED_KEYS-set(arrays))
    if missing:
        raise ValueError("Particulate NPZ missing keys: "+", ".join(missing))

    face_ids=[int(v) for v in _values(arrays,"face_part_ids")]
    hierarchy=[
        [int(row[0]),int(row[1])]
        for row in _values(arrays,"motion_hierarchy")
    ]
    revolute=[bool(v) for v in _values(arrays,"is_part_revolute")]
    prismatic=[bool(v) for v in _values(arrays,"is_part_prismatic")]
    pluckers=_values(arrays,"revolute_plucker")
    rev_ranges=_values(arrays,"revolute_range")
    pris_axes=_values(arrays,"prismatic_axis")
    pris_ranges=_values(arrays,"prismatic_range")
    counts={
        len(revolute),len(prismatic),len(pluckers),len(rev_ranges),
        len(pris_axes),len(pris_ranges)
    }
    if len(counts)!=1:
        raise ValueError("Particulate part-level arrays have inconsistent lengths")
    part_count=counts.pop()
    bounds_result=(
        _obj_part_bounds(pred_obj,face_ids)
        if pred_obj is not None else None
    )

    parts=[]
    for i in range(part_count):
        axis,point=_axis_point(pluckers[i])
        parts.append({
            "part_id":i,
            "face_count":sum(1 for v in face_ids if v==i),
            "is_revolute":revolute[i],
            "is_prismatic":prismatic[i],
            "motion_class":(
                "revolute_and_prismatic"
                if revolute[i] and prismatic[i]
                else "revolute" if revolute[i]
                else "prismatic" if prismatic[i]
                else "fixed_or_unclassified"
            ),
            "revolute_plucker":pluckers[i],
            "revolute_axis_direction":axis,
            "revolute_axis_point_in_prediction_frame":point,
            "revolute_range_radians":rev_ranges[i],
            "prismatic_axis_direction":pris_axes[i],
            "prismatic_range_prediction_units":pris_ranges[i],
            "predicted_part_bounds":(
                bounds_result["part_bounds"].get(str(i))
                if bounds_result and bounds_result.get("status")=="ok"
                else None
            ),
        })

    return {
        "schema_version":"0.1",
        "critic_id":"particulate",
        "source_npz":str(npz_path),
        "source_pred_obj":str(pred_obj) if pred_obj is not None else None,
        "part_count":part_count,
        "face_count":len(face_ids),
        "parts":parts,
        "motion_hierarchy":hierarchy,
        "root_candidate_part_ids":sorted(
            set(range(part_count))-{child for _,child in hierarchy}
        ),
        "obj_part_bounds_ingestion":bounds_result,
        "coordinate_frame":"particulate_prediction_frame_requires_registration_before_brickmen_axis_comparison",
        "angle_units":"radians",
        "prismatic_range_units":"particulate_prediction_frame_units",
        "semantic_slot_mapping_status":"not_resolved",
        "authority":"auxiliary_learned_articulation_evidence_only",
        "production_geometry_authority":False,
        "warning":(
            "Particulate predictions are critic evidence. Part IDs, hierarchy, motion "
            "classes, axes and ranges cannot overwrite Brickmen skeleton/joint/interface "
            "records without semantic mapping, frame registration and independent validation."
        ),
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("pred_npz")
    parser.add_argument("--pred-obj",default=None)
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    result=ingest_particulate(args.pred_npz,pred_obj=args.pred_obj)
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
