#!/usr/bin/env python3
"""Create leakage-safe grouped train/validation/test assignments for LEGO corpus records.

This tool never random-splits individual images. All records sharing the selected group
identity are assigned to the same split using a stable SHA-256 hash.

Recommended normal split:
  --group-field outfit_design_id

Hard benchmarks:
  --group-field character_id
  --group-field theme
  --group-field mask_family

If the requested group field is missing, records fall back to sample_id and are flagged.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path

VERSION="minifigure-grouped-split/v1"

def bucket(group,train,val):
    n=int(hashlib.sha256(group.encode()).hexdigest()[:16],16)/(16**16)
    if n<train:return "train"
    if n<train+val:return "validation"
    return "test"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--group-field",default="outfit_design_id")
    ap.add_argument("--train",type=float,default=0.80)
    ap.add_argument("--validation",type=float,default=0.10)
    args=ap.parse_args()
    if not (0<args.train<1 and 0<=args.validation<1 and args.train+args.validation<1):
        raise SystemExit("Invalid split fractions")
    counts=Counter(); fallback=0
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.input.open("r",encoding="utf-8") as src,args.output.open("w",encoding="utf-8") as dst:
        for line in src:
            if not line.strip():continue
            r=json.loads(line)
            group=r.get(args.group_field)
            used_fallback=False
            if not group:
                group=r.get("sample_id") or r.get("derived_asset_id")
                used_fallback=True;fallback+=1
            if not group:continue
            split=bucket(str(group),args.train,args.validation)
            counts[split]+=1
            dst.write(json.dumps({
              "record_id":r.get("derived_asset_id") or r.get("sample_id"),
              "group_field":args.group_field,
              "group_id":group,
              "used_fallback":used_fallback,
              "split":split,
              "split_version":VERSION
            },ensure_ascii=False)+"\n")
    print(json.dumps({"counts":dict(counts),"fallback_records":fallback,"group_field":args.group_field,"version":VERSION,"output":str(args.output)},indent=2))
if __name__=="__main__":main()
