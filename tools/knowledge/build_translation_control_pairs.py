#!/usr/bin/env python3
"""Build deterministic positive/negative controls from source-to-LEGO identity pairs."""
from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION="translation-control-pairs/v1"

def now_iso(): return datetime.now(timezone.utc).isoformat()

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def first_image(images):
    for x in images or []:
        if isinstance(x,str) and x: return x
    return None

def cid(kind,a,b):
    raw=f"{kind}|{a}|{b}".encode()
    return "control-"+hashlib.sha256(raw).hexdigest()[:24]

def compact(pair):
    src=pair.get("source") or {}
    lego=pair.get("lego") or {}
    meta=src.get("metadata") or {}
    series=(meta.get("series") or {}).get("value") if isinstance(meta.get("series"),dict) else None
    setv=(meta.get("set") or {}).get("value") if isinstance(meta.get("set"),dict) else None
    return {
        "pair_id":pair.get("translation_pair_id"),
        "source_id":src.get("id"),
        "source_name":src.get("name"),
        "source_image_url":first_image([u for u in src.get("images",[]) if "/cosmetics/br/" in u] or src.get("images")),
        "lego_id":lego.get("id"),
        "lego_image_url":first_image(lego.get("images")),
        "series":series,
        "set":setv,
    }

def record(kind,src,tgt,difficulty,group_basis=None):
    return {
        "control_id":cid(kind,src["pair_id"],tgt["pair_id"]),
        "control_type":kind,
        "source_pair_id":src["pair_id"],
        "target_pair_id":tgt["pair_id"],
        "source_identity_id":src["source_id"],
        "source_identity_name":src["source_name"],
        "lego_identity_id":tgt["lego_id"],
        "source_image_url":src["source_image_url"],
        "lego_image_url":tgt["lego_image_url"],
        "group_basis":group_basis,
        "difficulty":difficulty,
        "expected_identity_match":kind=="positive_identity",
        "generated_by":VERSION,
        "generation_seed":"stable_sorted_rotation",
        "provenance":[src["pair_id"],tgt["pair_id"]],
        "review_status":"deterministic_control",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--pairs",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    pairs=sorted((compact(x) for x in load_jsonl(args.pairs)), key=lambda x:x["pair_id"] or "")
    usable=[p for p in pairs if p["source_id"] and p["lego_id"]]
    rows=[]

    for p in usable:
        rows.append(record("positive_identity",p,p,"positive"))

    if len(usable)>1:
        for i,p in enumerate(usable):
            q=usable[(i+1)%len(usable)]
            if q["source_id"]==p["source_id"]:
                q=usable[(i+2)%len(usable)]
            rows.append(record("negative_wrong_identity_global",p,q,"easy_negative"))

    grouped=defaultdict(list)
    for p in usable:
        key=("set",p["set"]) if p["set"] else (("series",p["series"]) if p["series"] else None)
        if key: grouped[key].append(p)
    hard=0
    for key,group in grouped.items():
        group=sorted(group,key=lambda x:x["pair_id"])
        if len(group)<2: continue
        for i,p in enumerate(group):
            q=group[(i+1)%len(group)]
            if q["source_id"]==p["source_id"]: continue
            rows.append(record(
                "negative_wrong_identity_hard_group",p,q,"hard_negative",
                {"field":key[0],"value":key[1]}
            ))
            hard+=1

    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows: f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
        "schema":"translation-control-pair-summary/v1",
        "created_at":now_iso(),
        "processor_version":VERSION,
        "input_pairs":len(pairs),
        "usable_pairs":len(usable),
        "positive_controls":sum(r["control_type"]=="positive_identity" for r in rows),
        "global_wrong_identity_negatives":sum(r["control_type"]=="negative_wrong_identity_global" for r in rows),
        "hard_group_wrong_identity_negatives":hard,
        "total_controls":len(rows),
        "group_count":len(grouped),
        "status":"deterministic_controls_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
