#!/usr/bin/env python3
"""Build compact durable review queues from HeroBloks brand-gap analysis."""
from __future__ import annotations
import argparse,json
from pathlib import Path

VERSION="herobloks-brand-review-queues/v1"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--analysis",type=Path,required=True)
    ap.add_argument("--stable-output",type=Path,required=True)
    ap.add_argument("--top-output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()
    payload=json.loads(args.analysis.read_text(encoding="utf-8"))
    rows=payload.get("all_brand_analysis") or []
    unmodeled=[x for x in rows if x.get("registry_status")=="unmodeled_brand_slug"]
    stable=[x for x in unmodeled if x.get("stable_prefix_candidate")]
    stable.sort(key=lambda x:(-x.get("review_priority_score",0),x.get("brand_slug","")))
    top=sorted(unmodeled,key=lambda x:(-x.get("review_priority_score",0),x.get("brand_slug","")))[:500]
    def compact(x):
        return {
          "brand_slug":x.get("brand_slug"),
          "figure_count":x.get("figure_count"),
          "dominant_prefix":x.get("dominant_prefix"),
          "dominant_prefix_count":x.get("dominant_prefix_count"),
          "dominant_prefix_fraction":x.get("dominant_prefix_fraction"),
          "stable_prefix_candidate":x.get("stable_prefix_candidate"),
          "serial_prefix_candidates":x.get("serial_prefix_candidates"),
          "review_priority_score":x.get("review_priority_score"),
          "registry_status":x.get("registry_status"),
          "review_status":"pending_identity_and_relationship_verification",
          "policy":"Catalog evidence only. Do not infer manufacturer ownership, factory identity, chronology, or collaboration from shared brand/prefix data."
        }
    args.stable_output.parent.mkdir(parents=True,exist_ok=True)
    with args.stable_output.open("w",encoding="utf-8") as f:
        for x in stable:f.write(json.dumps(compact(x),ensure_ascii=False)+"\n")
    with args.top_output.open("w",encoding="utf-8") as f:
        for x in top:f.write(json.dumps(compact(x),ensure_ascii=False)+"\n")
    summary={
      "schema":"herobloks-brand-review-queue-summary/v1",
      "processor_version":VERSION,
      "total_brand_records":len(rows),
      "unmodeled_brand_records":len(unmodeled),
      "stable_prefix_unmodeled_records":len(stable),
      "top_review_queue_records":len(top),
      "status":"compact_review_queues_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
