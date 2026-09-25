#!/usr/bin/env python3
"""Crosswalk LEGO Pick a Brick element IDs to Rebrickable part/color/minifigure usage."""
from __future__ import annotations
import argparse,csv,gzip,json
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

VERSION="pab-rebrickable-crosswalk/v1"

def now_iso():return datetime.now(timezone.utc).isoformat()
def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:yield json.loads(line)
def open_csv(path):
    return gzip.open(path,"rt",encoding="utf-8-sig",newline="") if str(path).endswith(".gz") else open(path,"r",encoding="utf-8-sig",newline="")
def rows(path):
    with open_csv(path) as f:yield from csv.DictReader(f)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--pab",type=Path,required=True)
    ap.add_argument("--elements",type=Path,required=True)
    ap.add_argument("--parts",type=Path,required=True)
    ap.add_argument("--colors",type=Path,required=True)
    ap.add_argument("--components",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    element_map={str(r.get("element_id") or ""):r for r in rows(args.elements) if r.get("element_id")}
    parts={str(r.get("part_num") or ""):r for r in rows(args.parts) if r.get("part_num")}
    colors={str(r.get("id") or ""):r for r in rows(args.colors) if r.get("id")}
    usage=defaultdict(list)
    for c in load_jsonl(args.components):
        key=(str(c.get("part_num") or ""),str(c.get("color_id") or ""))
        usage[key].append(c)

    out=[]
    matched=0;used=0;printed=0;role_counts=Counter()
    for p in load_jsonl(args.pab):
        eid=str(p.get("element_id") or "")
        e=element_map.get(eid)
        rec={
          "element_id":eid,
          "design_id":str(p.get("design_id") or "") or None,
          "collapse_design_id":str(p.get("collapse_design_id") or "") or None,
          "lego_name":p.get("name"),
          "lego_image_url":p.get("image_url"),
          "availability":p.get("availability"),
          "delivery_channel":p.get("delivery_channel"),
          "price":p.get("price"),
          "color_hex":p.get("color_hex"),
          "locale":p.get("locale"),
          "retrieved_at":p.get("retrieved_at"),
          "rebrickable":None,
          "minifigure_usage":None,
          "processor_version":VERSION
        }
        if e:
            matched+=1
            part_num=str(e.get("part_num") or "")
            color_id=str(e.get("color_id") or "")
            pr=parts.get(part_num,{})
            cr=colors.get(color_id,{})
            comps=usage.get((part_num,color_id),[])
            roles=Counter(str(c.get("component_role") or "unknown") for c in comps)
            print_of=sorted({str(c.get("print_of")) for c in comps if c.get("print_of")})
            figs=sorted({str(c.get("fig_num")) for c in comps if c.get("fig_num")})
            if comps:used+=1
            if print_of:printed+=1
            role_counts.update(roles)
            rec["rebrickable"]={
              "part_num":part_num,
              "part_name":pr.get("name"),
              "part_category_id":pr.get("part_cat_id"),
              "color_id":color_id,
              "color_name":cr.get("name"),
              "color_rgb":cr.get("rgb"),
              "color_transparent":cr.get("is_trans"),
              "join_method":"exact_element_id"
            }
            rec["minifigure_usage"]={
              "component_record_count":len(comps),
              "figure_count":len(figs),
              "component_role_counts":dict(roles),
              "print_of_part_nums":print_of,
              "figure_id_examples":figs[:30],
              "used_in_minifigure_census":bool(comps)
            }
        out.append(rec)

    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in out:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"pab-rebrickable-crosswalk-summary/v1",
      "created_at":now_iso(),"processor_version":VERSION,
      "pab_elements":len(out),
      "exact_rebrickable_element_matches":matched,
      "unmatched_pab_elements":len(out)-matched,
      "matched_elements_used_in_minifigure_census":used,
      "matched_printed_minifigure_components":printed,
      "minifigure_component_role_observations":dict(role_counts.most_common()),
      "status":"exact_element_crosswalk_complete"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
