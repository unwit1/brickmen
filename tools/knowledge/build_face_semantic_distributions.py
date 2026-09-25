#!/usr/bin/env python3
"""Aggregate weak face semantics by era and theme from decorated-head metadata corpus."""
from __future__ import annotations
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path

VERSION="face-semantic-distributions/v1"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def era(y):
    if not y:return "unknown"
    y=int(y)
    if y<=1988:return "1978-1988"
    if y<=1998:return "1989-1998"
    if y<=2009:return "1999-2009"
    if y<=2019:return "2010-2019"
    return "2020-present"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--heads",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    groups=defaultdict(lambda:{
      "parts":0,"feature_counts":Counter(),"weak_expression_counts":Counter(),
      "alternate_expression_or_dual_side_candidates":0
    })
    total=0
    for r in load_jsonl(args.heads):
        total+=1
        themes=r.get("theme_names") or ["unknown"]
        years=[y for y in (r.get("observed_year_min"),r.get("observed_year_max")) if y]
        eras=sorted({era(y) for y in years}) or ["unknown"]
        keys=[("theme",t) for t in themes]+[("era",e) for e in eras]
        for kind,name in keys:
            g=groups[(kind,name)]
            g["parts"]+=1
            for t in r.get("catalog_semantic_tags") or []:g["feature_counts"][t]+=1
            for e in r.get("weak_expression_candidates") or []:g["weak_expression_counts"][e]+=1
            g["alternate_expression_or_dual_side_candidates"]+=bool(r.get("alternate_expression_or_dual_side_candidate"))

    rows=[]
    for (kind,name),g in groups.items():
        n=max(1,g["parts"])
        rows.append({
          "group_kind":kind,
          "group_name":name,
          "unique_decorated_head_parts":g["parts"],
          "feature_counts":dict(g["feature_counts"].most_common()),
          "feature_part_fractions":{k:round(v/n,4) for k,v in g["feature_counts"].most_common()},
          "weak_expression_counts":dict(g["weak_expression_counts"].most_common()),
          "weak_expression_part_fractions":{k:round(v/n,4) for k,v in g["weak_expression_counts"].most_common()},
          "alternate_expression_or_dual_side_candidates":g["alternate_expression_or_dual_side_candidates"],
          "alternate_expression_or_dual_side_fraction":round(g["alternate_expression_or_dual_side_candidates"]/n,4),
          "supervision_class":"weak_catalog_semantic_distribution",
          "policy":"Part-name descriptors are weak catalog semantics, not human-rated emotion labels. Theme membership may include ancestor themes and a part may contribute to multiple groups.",
          "processor_version":VERSION
        })
    rows.sort(key=lambda x:(x["group_kind"],-x["unique_decorated_head_parts"],x["group_name"]))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
      "schema":"face-semantic-distribution-summary/v1",
      "processor_version":VERSION,
      "decorated_head_records":total,
      "theme_groups":sum(r["group_kind"]=="theme" for r in rows),
      "era_groups":sum(r["group_kind"]=="era" for r in rows),
      "distribution_records":len(rows),
      "status":"weak_semantic_distributions_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
