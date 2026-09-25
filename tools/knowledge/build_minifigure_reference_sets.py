#!/usr/bin/env python3
"""Assemble canonical ReferenceSets from normalized LEGO DerivedAssets.

Input JSONL:
Each record should contain at least:
  sample_id
  derived_asset_id
  source_reference_asset_id
Optional:
  authority
  medium
  view
  component_type
  width / height OR quality.width/quality.height
  quality metrics
  identity_confidence
  segmentation_confidence
  view_confidence

The tool selects the highest-scoring asset per evidence role and preserves ranked
alternates. It never deletes source/derived assets.
"""
from __future__ import annotations
import argparse,collections,hashlib,json
from datetime import datetime,timezone
from pathlib import Path

VERSION="minifigure-reference-set/v1"

AUTHORITY={
 "lego_primary":100,
 "rights_holder_primary":95,
 "developer_primary":95,
 "official_film_local_copy":90,
 "licensed_game_primary":90,
 "structured_catalog":80,
 "structured_catalog_secondary":72,
 "official_ecosystem_reference":70,
 "community_structured":62,
 "secondary_structured_vector":62,
 "secondary_research":45,
 "secondary_discovery":25
}

def now_iso():return datetime.now(timezone.utc).isoformat()

def score(r):
    q=r.get("quality") or {}
    authority=AUTHORITY.get(str(r.get("authority") or ""),50)
    identity=float(r.get("identity_confidence") or q.get("identity_confidence") or 0.7)
    view=float(r.get("view_confidence") or q.get("view_confidence") or 0.6)
    seg=float(r.get("segmentation_confidence") or q.get("segmentation_confidence") or 0.7)
    width=float(r.get("width") or q.get("width") or 0)
    height=float(r.get("height") or q.get("height") or 0)
    resolution=min(15.0,((width*height)**0.5)/100.0) if width and height else 4.0
    blur=q.get("blur_score")
    blur_penalty=10*float(blur) if blur is not None else 0
    occ=q.get("occlusion_score")
    occ_penalty=15*float(occ) if occ is not None else 0
    return authority + 20*identity + 10*view + 8*seg + resolution - blur_penalty - occ_penalty

def role(r):
    comp=str(r.get("component_type") or "").lower()
    view=str(r.get("view") or "unknown").lower()
    medium=str(r.get("medium") or "").lower()
    if "game_texture" in medium:return "game_texture"
    if "game_model" in medium:return "game_model_render"
    if "film" in medium:return "film_expression_states"
    if "pattern" in medium:return "structured_component_pattern"
    if "geometry" in medium:return "structured_geometry"
    if comp in {"head","face"}: return "head_reverse" if "rear" in view or "back" in view else "head_front"
    if comp=="torso": return "torso_rear" if "rear" in view or "back" in view else "torso_front"
    if comp in {"arm_left","left_arm"}:return "arm_left"
    if comp in {"arm_right","right_arm"}:return "arm_right"
    if comp in {"hips","leg","legs","hips_legs"}: return "hips_legs_rear" if "rear" in view or "back" in view else "hips_legs_front"
    if comp in {"helmet","mask","headgear","helmet_or_mask"}:
        return "mask_or_headgear_side" if "left" in view or "right" in view else "mask_or_headgear_front"
    if comp.startswith("accessory"):return "accessory_primary"
    mapping={
      "front":"full_front","rear":"full_rear","back":"full_rear",
      "left":"full_left","right":"full_right",
      "front_3q_left":"full_front_3q","front_3q_right":"full_front_3q"
    }
    return mapping.get(view,"other")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--alternates",type=int,default=5)
    args=ap.parse_args()
    by=collections.defaultdict(list)
    with args.input.open("r",encoding="utf-8") as f:
        for line in f:
            if not line.strip():continue
            r=json.loads(line)
            if r.get("sample_id") and r.get("derived_asset_id"):
                by[r["sample_id"]].append(r)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    count=0
    with args.output.open("w",encoding="utf-8") as out:
        for sample_id,records in sorted(by.items()):
            slots=collections.defaultdict(list)
            for r in records:
                slots[role(r)].append((score(r),r))
            resolved={}
            for k,items in slots.items():
                items.sort(key=lambda x:(x[0],str(x[1].get("derived_asset_id"))),reverse=True)
                resolved[k]={
                  "preferred_asset_id":items[0][1]["derived_asset_id"],
                  "preferred_score":round(items[0][0],3),
                  "alternate_asset_ids":[x[1]["derived_asset_id"] for x in items[1:1+args.alternates]]
                }
            required=["full_front","full_rear","full_left","full_right","head_front","torso_front","hips_legs_front"]
            completeness={k:k in resolved for k in required}
            rec={
              "reference_set_id":"refset-"+hashlib.sha256((sample_id+"|"+VERSION).encode()).hexdigest()[:24],
              "sample_id":sample_id,
              "slots":resolved,
              "completeness":completeness,
              "asset_count":len(records),
              "version":VERSION,
              "created_at":now_iso()
            }
            out.write(json.dumps(rec,ensure_ascii=False)+"\n");count+=1
    print(json.dumps({"reference_sets":count,"output":str(args.output),"version":VERSION},indent=2))
if __name__=="__main__":main()
