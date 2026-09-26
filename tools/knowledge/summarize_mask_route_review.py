#!/usr/bin/env python3
"""Summarize the persisted ranked mask/headgear review queue into compact route-specific slices."""
from __future__ import annotations
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path

VERSION="mask-route-review-summary/v1"

def load_jsonl(path):
    with path.open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def compact(r):
    return {
      "fig_num":r.get("fig_num"),
      "name":r.get("name"),
      "score":r.get("route_review_priority_score"),
      "band":r.get("component_route_confidence_band"),
      "candidate_routes":r.get("candidate_routes"),
      "head_components":r.get("head_components"),
      "headgear_components":r.get("headgear_components"),
      "bodywear_components":r.get("bodywear_components"),
      "evidence":r.get("evidence"),
      "source_translation_status":r.get("source_translation_status")
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ranked",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    ap.add_argument("--review-output",type=Path,required=True)
    ap.add_argument("--per-route",type=int,default=20)
    args=ap.parse_args()
    rows=list(load_jsonl(args.ranked))
    by_route=defaultdict(list);route_counts=Counter();ambiguity=Counter()
    for r in rows:
        routes=r.get("candidate_routes") or []
        ambiguity[len(routes)]+=1
        for route in routes:
            route_counts[route]+=1
            by_route[route].append(r)
    selected=[]
    seen=set()
    route_summaries={}
    for route,items in sorted(by_route.items(),key=lambda kv:(-len(kv[1]),kv[0])):
        items=sorted(items,key=lambda r:(-(r.get("route_review_priority_score") or 0),r.get("fig_num") or ""))
        top=items[:args.per_route]
        route_summaries[route]=[compact(r) for r in top]
        for r in top:
            key=r.get("fig_num")
            if key not in seen:
                seen.add(key)
                selected.append({**compact(r),"review_focus_route":route})
    selected.sort(key=lambda r:(-(r.get("score") or 0),r.get("fig_num") or ""))
    args.review_output.parent.mkdir(parents=True,exist_ok=True)
    with args.review_output.open("w",encoding="utf-8") as f:
        for r in selected:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"mask-route-review-summary/v1",
      "processor_version":VERSION,
      "input_ranked_records":len(rows),
      "route_counts_in_top_queue":dict(route_counts.most_common()),
      "candidate_route_count_distribution":{str(k):v for k,v in sorted(ambiguity.items())},
      "route_top_examples":route_summaries,
      "unique_compact_review_records":len(selected),
      "policy":"This is a review slice of the already-ranked physical component-route candidates. It does not establish the source design route until paired to an exact source appearance.",
      "status":"compact_route_review_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k!="route_top_examples"},indent=2))
if __name__=="__main__":main()
