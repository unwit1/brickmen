#!/usr/bin/env python3
"""Build a resolved official-wishlist layer from source rows plus BrickLink metadata."""
from __future__ import annotations
import argparse,json
from pathlib import Path

VERSION="official-wishlist-resolution/v1"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--wishlist",type=Path,required=True)
    ap.add_argument("--bricklink-metadata",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    meta={str(x.get("catalog_id") or "").casefold():x for x in load_jsonl(args.bricklink_metadata)}
    rows=[];resolved=0;name_only=0;named_mismatch=0
    for src in load_jsonl(args.wishlist):
        bid=str(src.get("bricklink_minifigure_id") or "").strip()
        m=meta.get(bid.casefold()) if bid else None
        if bid and m and m.get("bricklink_catalog_name"):
            resolved+=1
            overlap=m.get("user_name_catalog_token_overlap")
            review=None
            if src.get("name_or_note") and overlap is not None and float(overlap)<0.15:
                review="user_name_vs_catalog_name_semantic_review"
                named_mismatch+=1
            row={
              **src,
              "resolved_catalog_namespace":"bricklink_minifigure",
              "resolved_catalog_id":bid.lower(),
              "resolved_catalog_name":m.get("bricklink_catalog_name"),
              "resolved_year_start":m.get("years_released_start"),
              "resolved_year_end":m.get("years_released_end"),
              "catalog_page_sha256":m.get("page_sha256"),
              "catalog_retrieved_at":m.get("retrieved_at"),
              "resolution_status":"official_wishlist_id_resolved",
              "semantic_review_flag":review,
              "resolution_policy":"BrickLink ID and public catalog metadata are authoritative for the catalog target. User shorthand/notes are preserved separately and never overwritten."
            }
        else:
            name_only+=1
            row={
              **src,
              "resolved_catalog_namespace":None,
              "resolved_catalog_id":None,
              "resolved_catalog_name":None,
              "resolution_status":"official_wishlist_name_only_unresolved",
              "semantic_review_flag":"catalog_identity_needed",
              "resolution_policy":"Name-only wishlist targets remain unresolved until an exact official catalog identity is verified."
            }
        row["processor_version"]=VERSION
        rows.append(row)

    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
      "schema":"official-wishlist-resolution-summary/v1",
      "processor_version":VERSION,
      "source_records":len(rows),
      "id_backed_records_resolved":resolved,
      "name_only_records_unresolved":name_only,
      "id_backed_records_with_semantic_name_review":named_mismatch,
      "status":"official_wishlist_resolution_layer_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
