#!/usr/bin/env python3
"""Create deterministic leakage-safe splits for the indexed LEGO face corpus.

All images with the same BrickLink head part ID stay in one split. This prevents
duplicate/alternate files for one decorated head from leaking into evaluation.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path

VERSION="lego-face-grouped-splits/v1"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def bucket(key):
    n=int(hashlib.sha256(str(key).encode()).hexdigest()[:8],16)%100
    if n<80:return "train"
    if n<90:return "validation"
    return "test"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--records",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()
    rows=list(load_jsonl(args.records))
    splits=Counter(); parts=defaultdict(set); labels=defaultdict(Counter)
    out=[]
    for r in rows:
        part=r.get("bricklink_head_part_id")
        group_key=part or r.get("sha256") or r.get("asset_id")
        split=bucket(group_key)
        splits[split]+=1
        if part:parts[split].add(part)
        for tag in r.get("semantic_descriptor_tokens") or []:labels[split][tag]+=1
        out.append({
          "asset_id":r.get("asset_id"),
          "bricklink_head_part_id":part,
          "split":split,
          "group_key":group_key,
          "grouping_policy":"all records sharing bricklink_head_part_id stay in one split",
          "source_sha256":r.get("sha256"),
          "semantic_descriptor_tokens":r.get("semantic_descriptor_tokens") or [],
          "processor_version":VERSION
        })
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in out:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    # verify no part appears in multiple splits
    seen={}
    leakage=[]
    for r in out:
        p=r.get("bricklink_head_part_id")
        if not p:continue
        prev=seen.setdefault(p,r["split"])
        if prev!=r["split"]:leakage.append(p)
    summary={
      "schema":"lego-face-grouped-split-summary/v1",
      "processor_version":VERSION,
      "records":len(out),
      "split_records":dict(splits),
      "unique_head_parts_by_split":{k:len(v) for k,v in parts.items()},
      "semantic_descriptor_counts_by_split":{k:dict(v.most_common()) for k,v in labels.items()},
      "head_part_leakage_count":len(set(leakage)),
      "split_rule":"sha256(head_part_id) mod 100: train 0-79, validation 80-89, test 90-99",
      "status":"ready" if not leakage else "invalid_leakage_detected"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
