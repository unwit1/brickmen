#!/usr/bin/env python3
"""Rank mask/headgear route candidates by component-evidence specificity."""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

VERSION="mask-headgear-route-ranking/v1"

STRONG={
  "transparent_dome_or_bubble_headgear",
  "costume_head_cover",
  "separate_mask_headgear",
  "modified_or_nonhuman_head",
}
MEDIUM={"cowl_plus_head","hood_plus_head","head_print_or_decorated_head_only","head_print_plus_headgear"}

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:yield json.loads(line)

def rank(rec):
    routes=set(rec.get("candidate_routes") or [])
    evidence=rec.get("evidence") or []
    explicit_mask=sum(e.get("kind")=="headgear_keyword" and "mask" in (e.get("matched_terms") or []) for e in evidence)
    modified=sum(e.get("kind")=="modified_head_keyword" for e in evidence)
    transparent=bool(routes&{"transparent_dome_or_bubble_headgear"})
    costume=bool(routes&{"costume_head_cover"})
    ambiguity=len(routes)
    if transparent or costume or explicit_mask or (modified and not rec.get("headgear_components")):
        confidence="high_component_route_candidate"
        score=100
    elif routes & MEDIUM:
        confidence="medium_component_route_candidate"
        score=60
    else:
        confidence="low_or_generic_headgear_candidate"
        score=25
    score += min(20,len(evidence)*2)
    score -= max(0,ambiguity-2)*5
    if "helmet_plus_head" in routes and not (routes & (STRONG|MEDIUM)):
        score-=20
    return max(0,score),confidence

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()
    rows=[];counts=Counter()
    for rec in load_jsonl(args.candidates):
        score,band=rank(rec);counts[band]+=1
        rows.append({
          **rec,
          "route_review_priority_score":score,
          "component_route_confidence_band":band,
          "source_translation_status":"not_yet_paired_to_source_appearance",
          "review_task":"Confirm the physical component route, then pair to the exact source appearance before assigning a source->LEGO translation label.",
          "processor_version":VERSION
        })
    rows.sort(key=lambda x:(-x["route_review_priority_score"],x.get("fig_num") or ""))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"mask-headgear-route-ranking-summary/v1",
      "processor_version":VERSION,
      "records":len(rows),
      "confidence_bands":dict(counts),
      "high_priority_records":sum(r["route_review_priority_score"]>=90 for r in rows),
      "status":"ranked_route_candidates_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
