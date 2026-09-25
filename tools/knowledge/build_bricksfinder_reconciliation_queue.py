#!/usr/bin/env python3
"""Build reconciliation queues for BricksFinder's 2024 caption snapshot vs current census."""
from __future__ import annotations
import argparse,json,re
from collections import Counter
from pathlib import Path

VERSION="bricksfinder-reconciliation-queue/v1"

def load_shards(root):
    for path in sorted(Path(root).glob("records-part-*.jsonl")):
        with path.open("r",encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if line: yield json.loads(line)

def norm(v):
    s=re.sub(r"[^a-z0-9]+"," ",str(v or "").casefold())
    return " ".join(s.split())

def relation(old,new):
    a=norm(old); b=norm(new)
    if not b:return "missing_current_catalog_record"
    if a==b:return "same"
    if a in b or b in a:return "extends_or_shortens_name"
    ta=set(a.split());tb=set(b.split())
    overlap=len(ta&tb)/max(1,len(ta|tb))
    if overlap>=0.75:return "minor_name_normalization"
    if overlap>=0.45:return "moderate_name_drift"
    return "substantial_name_drift"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--records-dir",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()
    q=[];counts=Counter();total=0
    for r in load_shards(args.records_dir):
        total+=1
        if r.get("current_rebrickable_match") and r.get("short_caption_matches_current_name"):
            continue
        rel=relation(r.get("short_caption"),r.get("current_rebrickable_name"))
        counts[rel]+=1
        q.append({
          "fig_num":r.get("fig_num"),
          "dataset_row_index":r.get("dataset_row_index"),
          "historical_short_caption":r.get("short_caption"),
          "current_rebrickable_name":r.get("current_rebrickable_name"),
          "relation_candidate":rel,
          "caption":r.get("caption"),
          "part_nums":r.get("part_nums"),
          "image_reference":r.get("image_reference"),
          "current_catalog_image_url":r.get("current_catalog_image_url"),
          "current_rebrickable_match":r.get("current_rebrickable_match"),
          "review_priority":"high" if rel in {"missing_current_catalog_record","substantial_name_drift"} else "medium",
          "review_status":"pending",
          "policy":"Historical/current name differences may reflect renames, corrections, identifier reuse, or snapshot drift. Do not silently overwrite either source.",
          "processor_version":VERSION
        })
    q.sort(key=lambda x:(
      0 if x["review_priority"]=="high" else 1,
      x["relation_candidate"],x.get("fig_num") or ""
    ))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in q:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
      "schema":"bricksfinder-reconciliation-summary/v1",
      "processor_version":VERSION,
      "input_records":total,
      "queue_records":len(q),
      "relation_counts":dict(counts),
      "high_priority_records":sum(x["review_priority"]=="high" for x in q),
      "status":"reconciliation_queue_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
