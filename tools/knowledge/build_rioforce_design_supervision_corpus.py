#!/usr/bin/env python3
"""Build a durable supervision-role corpus from the classified rioforce texture index."""
from __future__ import annotations
import argparse,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

VERSION="rioforce-design-supervision-corpus/v1"

def now_iso(): return datetime.now(timezone.utc).isoformat()

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

ROLE={
 "minifigure_surface_map":"component_surface_supervision",
 "motif_primitive":"motif_and_symbol_supervision",
 "non_minifigure_component_art":"non_minifigure_decoration_supervision",
 "unscoped_design_or_pattern":"generic_design_pattern_supervision",
 "legacy_unclassified":"review_required",
}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--index",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    rows=[];classes=Counter();roles=Counter();surfaces=Counter()
    for r in load_jsonl(args.index):
        cls=r.get("asset_class") or "legacy_unclassified"
        sup=ROLE.get(cls,"review_required")
        classes[cls]+=1;roles[sup]+=1
        if r.get("surface_role_hint"): surfaces[r["surface_role_hint"]]+=1
        rows.append({
          "asset_group_id":r.get("asset_group_id"),
          "relative_stem":r.get("relative_stem"),
          "category":r.get("category"),
          "asset_class":cls,
          "surface_role_hint":r.get("surface_role_hint"),
          "supervision_role":sup,
          "files":r.get("files"),
          "authority":r.get("authority"),
          "license":r.get("license"),
          "attribution":r.get("attribution"),
          "training_rights_status":"allowed_by_specific_permission",
          "component_exact_promotion_allowed":cls=="minifigure_surface_map",
          "policy":(
             "Exact component promotion requires independent catalog/component verification."
             if cls=="minifigure_surface_map"
             else "Use as design/motif/non-minifigure supervision; do not assign an exact minifigure component without independent evidence."
          ),
          "processor_version":VERSION
        })

    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"rioforce-design-supervision-summary/v1",
      "created_at":now_iso(),
      "processor_version":VERSION,
      "records":len(rows),
      "asset_class_counts":dict(classes),
      "supervision_role_counts":dict(roles),
      "surface_role_counts":dict(surfaces),
      "component_exact_promotion_eligible":sum(r["component_exact_promotion_allowed"] for r in rows),
      "status":"classified_supervision_corpus_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
