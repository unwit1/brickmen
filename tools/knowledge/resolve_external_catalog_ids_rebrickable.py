#!/usr/bin/env python3
"""Resolve external minifigure catalog IDs against Rebrickable's bulk minifig catalog.

This is a cross-catalog identity-support layer. It does not assert that Rebrickable and
BrickLink are the same authority; it records exact identifier agreement and preserves
the user's original catalog provenance.
"""
from __future__ import annotations
import argparse,csv,gzip,json,re,unicodedata
from pathlib import Path

VERSION="external-catalog-rebrickable-crosswalk/v1"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def norm(v):
    s=unicodedata.normalize("NFKD",str(v or ""))
    s="".join(c for c in s if not unicodedata.combining(c)).casefold()
    s=re.sub(r"[^a-z0-9]+"," ",s)
    return " ".join(s.split())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--queue",type=Path,required=True)
    ap.add_argument("--rebrickable-minifigs",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    idx={}
    with gzip.open(args.rebrickable_minifigs,"rt",encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            key=str(row.get("fig_num") or "").strip().casefold()
            if key: idx[key]=row

    out=[]
    exact=0;supportive=0;name_conflict=0;missing=0
    for q in load_jsonl(args.queue):
        cid=str(q.get("catalog_id") or "").strip().casefold()
        row=idx.get(cid)
        if row:
            exact+=1
            user_name=q.get("name_or_note")
            rb_name=row.get("name")
            user_tokens=set(norm(user_name).split())
            rb_tokens=set(norm(rb_name).split())
            overlap=(len(user_tokens & rb_tokens)/len(user_tokens | rb_tokens)) if user_tokens and rb_tokens else None
            if overlap is not None and overlap >= 0.35: supportive+=1
            elif overlap is not None and overlap < 0.15: name_conflict+=1
            status="exact_rebrickable_fig_num_match"
            resolved={
              "rebrickable_fig_num":row.get("fig_num"),
              "rebrickable_name":rb_name,
              "rebrickable_num_parts":row.get("num_parts"),
              "rebrickable_img_url":row.get("img_url"),
              "name_token_overlap":round(overlap,4) if overlap is not None else None
            }
        else:
            missing+=1;status="no_rebrickable_fig_num_match";resolved={}
        out.append({
          **q,
          **resolved,
          "crosswalk_status":status,
          "promotion_policy":"Exact identifier agreement supports cross-catalog identity. Human-readable name disagreement must be reviewed before canonical Character/OutfitDesign promotion.",
          "processor_version":VERSION
        })

    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in out:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
      "schema":"external-catalog-rebrickable-crosswalk-summary/v1",
      "processor_version":VERSION,
      "queue_records":len(out),
      "exact_rebrickable_fig_num_matches":exact,
      "no_rebrickable_fig_num_matches":missing,
      "records_with_supportive_name_overlap":supportive,
      "records_with_strong_name_conflict_signal":name_conflict,
      "status":"external_catalog_crosswalk_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
