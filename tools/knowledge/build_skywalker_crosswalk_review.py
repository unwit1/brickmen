#!/usr/bin/env python3
"""Build grouped review queues for Skywalker digital->physical candidates."""
from __future__ import annotations
import argparse,json,re
from collections import Counter,defaultdict
from pathlib import Path

VERSION="skywalker-crosswalk-review/v1"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:yield json.loads(line)

def base_key(key):
    s=str(key or "")
    # Filename census has already removed LSW_ProfileIcons prefixes.
    first=s.split("_",1)[0]
    return re.sub(r"[^A-Za-z0-9]+","",first) or s

def priority(row):
    band=row.get("confidence_band")
    top=float(row.get("top_score") or 0)
    margin=float(row.get("top_margin") or 0)
    if band=="strong_candidate": base=100
    elif band=="review_candidate": base=65
    else: base=25
    return round(base+top*10+margin*20,2)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--groups-output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()
    rows=[];groups=defaultdict(list);bands=Counter()
    for r in load_jsonl(args.candidates):
        r=dict(r)
        r["base_character_key"]=base_key(r.get("character_variant_key"))
        r["review_priority_score"]=priority(r)
        r["review_status"]="pending_independent_version_confirmation"
        r["promotion_rule"]="Promote to physical equivalence only when character, outfit/version and physical release evidence agree. Otherwise retain as digital-only or unresolved."
        r["processor_version"]=VERSION
        bands[r.get("confidence_band")]+=1
        rows.append(r);groups[r["base_character_key"]].append(r)
    rows.sort(key=lambda x:(-x["review_priority_score"],x.get("character_variant_key") or ""))
    group_rows=[]
    for key,items in groups.items():
        keys=sorted({x.get("character_variant_key") for x in items})
        b=Counter(x.get("confidence_band") for x in items)
        physical=Counter()
        for x in items:
            for c in x.get("top_candidates") or []:
                if c.get("fig_num"):physical[c["fig_num"]]+=1
        group_rows.append({
          "base_character_key":key,
          "digital_variant_count":len(items),
          "digital_variant_keys":keys,
          "confidence_bands":dict(b),
          "most_common_physical_candidates":[{"fig_num":k,"appearances":v} for k,v in physical.most_common(10)],
          "has_multiple_digital_variants":len(items)>1,
          "review_priority_score":max(x["review_priority_score"] for x in items)+(5 if len(items)>1 else 0),
          "review_status":"pending",
          "processor_version":VERSION
        })
    group_rows.sort(key=lambda x:(-x["review_priority_score"],x["base_character_key"]))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    with args.groups_output.open("w",encoding="utf-8") as f:
        for r in group_rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"skywalker-crosswalk-review-summary/v1",
      "processor_version":VERSION,
      "records":len(rows),
      "base_character_groups":len(group_rows),
      "multi_variant_groups":sum(g["has_multiple_digital_variants"] for g in group_rows),
      "confidence_bands":dict(bands),
      "status":"grouped_review_queue_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
