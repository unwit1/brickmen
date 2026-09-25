#!/usr/bin/env python3
"""Build conservative mask/headgear route candidates from physical component inventories."""
from __future__ import annotations
import argparse,json,re
from collections import defaultdict,Counter
from pathlib import Path

VERSION="mask-headgear-candidate-corpus/v1"

MASK_WORDS=("mask","masked","balaclava","visor","goggles","face cover","breathing apparatus")
HEADGEAR_WORDS=("helmet","cowl","hood","mask","hat","headgear","headdress","dome","fishbowl","costume","hair")
MODIFIED_WORDS=("modified","alien","creature","wookiee","dragon","animal","skull","skeleton","monster","droid head","serpentine")
TRANSPARENT_WORDS=("dome","fishbowl","bubble")
COSTUME_WORDS=("costume","mascot")

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def contains(name,words):
    low=str(name or "").casefold()
    return [w for w in words if w in low]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--samples",type=Path,required=True)
    ap.add_argument("--components",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()
    samples={x.get("fig_num"):x for x in load_jsonl(args.samples) if x.get("fig_num")}
    comps=defaultdict(list)
    for c in load_jsonl(args.components):
        if c.get("fig_num"):comps[c["fig_num"]].append(c)
    rows=[]; routes=Counter()
    for fig_num,s in samples.items():
        cc=comps.get(fig_num,[])
        heads=[x for x in cc if x.get("component_role")=="head"]
        headgear=[x for x in cc if x.get("component_role")=="headgear"]
        head_mask=[(x,contains(x.get("part_name"),MASK_WORDS)) for x in heads]
        head_mask=[(x,w) for x,w in head_mask if w]
        hg_special=[]
        for x in headgear:
            words=contains(x.get("part_name"),HEADGEAR_WORDS)
            if words:hg_special.append((x,words))
        modified=[(x,contains(x.get("part_name"),MODIFIED_WORDS)) for x in heads]
        modified=[(x,w) for x,w in modified if w]
        if not (head_mask or hg_special or modified):continue
        evidence=[]
        candidate_routes=[]
        if head_mask and not headgear:
            candidate_routes.append("head_print_or_decorated_head_only")
        if head_mask and headgear:
            candidate_routes.append("head_print_plus_headgear")
        if hg_special:
            names=" ".join(str(x.get("part_name") or "") for x,_ in hg_special).casefold()
            if any(w in names for w in TRANSPARENT_WORDS):
                candidate_routes.append("transparent_dome_or_bubble_headgear")
            if any(w in names for w in COSTUME_WORDS):
                candidate_routes.append("costume_head_cover")
            if "cowl" in names:candidate_routes.append("cowl_plus_head")
            if "hood" in names:candidate_routes.append("hood_plus_head")
            if "helmet" in names:candidate_routes.append("helmet_plus_head")
            if "mask" in names:candidate_routes.append("separate_mask_headgear")
        if modified:candidate_routes.append("modified_or_nonhuman_head")
        candidate_routes=list(dict.fromkeys(candidate_routes))
        for x,w in head_mask:
            evidence.append({"kind":"head_mask_keyword","component_id":x.get("component_id"),"part_num":x.get("part_num"),"part_name":x.get("part_name"),"matched_terms":w})
        for x,w in hg_special:
            evidence.append({"kind":"headgear_keyword","component_id":x.get("component_id"),"part_num":x.get("part_num"),"part_name":x.get("part_name"),"matched_terms":w})
        for x,w in modified:
            evidence.append({"kind":"modified_head_keyword","component_id":x.get("component_id"),"part_num":x.get("part_num"),"part_name":x.get("part_name"),"matched_terms":w})
        for route in candidate_routes:routes[route]+=1
        rows.append({
          "fig_num":fig_num,"figure_name":s.get("name"),
          "candidate_routes":candidate_routes,
          "head_components":[{"part_num":x.get("part_num"),"part_name":x.get("part_name"),"print_of":x.get("print_of"),"image_url":x.get("image_url")} for x in heads],
          "headgear_components":[{"part_num":x.get("part_num"),"part_name":x.get("part_name"),"print_of":x.get("print_of"),"image_url":x.get("image_url")} for x in headgear],
          "evidence":evidence,
          "review_status":"candidate",
          "policy":"Keyword/component routing is candidate evidence only; source-design-to-LEGO route labels require reviewed identity/version context.",
          "processor_version":VERSION
        })
    rows.sort(key=lambda x:(-len(x["candidate_routes"]),x["fig_num"]))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"mask-headgear-candidate-corpus-summary/v1",
      "processor_version":VERSION,
      "physical_figures_indexed":len(samples),
      "candidate_figures":len(rows),
      "route_candidate_counts":dict(routes.most_common()),
      "status":"candidate_corpus_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
