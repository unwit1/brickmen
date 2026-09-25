#!/usr/bin/env python3
"""Build catalog-backed compatible-brand/code candidates from HeroBloks brand census."""
from __future__ import annotations
import argparse,json,re,unicodedata
from pathlib import Path

VERSION="compatible-brand-catalog-candidates/v1"

def slug(v):
    s=unicodedata.normalize("NFKD",str(v or "")).casefold().replace("&"," and ")
    return re.sub(r"[^a-z0-9]+","-",s).strip("-")

def known_map(crosswalk):
    out={}
    for fam in crosswalk.get("families") or []:
        name=fam.get("brand")
        for value in [name]+list(fam.get("aliases") or []):
            if value:out[slug(value)]=name
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--brand-census",type=Path,required=True)
    ap.add_argument("--crosswalk",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()
    census=json.loads(args.brand_census.read_text(encoding="utf-8"))
    cw=json.loads(args.crosswalk.read_text(encoding="utf-8"))
    known=known_map(cw)
    rows=[]
    for b in census.get("brand_records") or []:
        if not b.get("stable_prefix_candidate"):continue
        bs=b.get("brand_slug") or ""
        if bs in {"lego","unknown","unknown-custom"}:continue
        rows.append({
          "brand_slug":bs,
          "canonical_registry_match":known.get(slug(bs)),
          "figure_count":b.get("figure_count"),
          "dominant_prefix":b.get("dominant_prefix"),
          "dominant_prefix_count":b.get("dominant_prefix_count"),
          "dominant_prefix_fraction":b.get("dominant_prefix_fraction"),
          "all_observed_prefix_candidates":b.get("serial_prefix_candidates"),
          "catalog_evidence_status":"stable_prefix_candidate",
          "relationship_status":"unresolved_unless_independently_verified",
          "source":"HeroBloks complete figure list census",
          "source_url":"https://www.herobloks.com/list",
          "source_sha256":census.get("source_sha256"),
          "review_status":"known_registry_prefix_update" if known.get(slug(bs)) else "new_brand_candidate",
          "policy":"This record proves catalog usage association only. It does not prove manufacturer ownership, factory identity, alias equivalence, or chronology.",
          "processor_version":VERSION
        })
    rows.sort(key=lambda x:(x["review_status"]!="new_brand_candidate",-int(x["figure_count"] or 0),x["brand_slug"]))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"compatible-brand-catalog-candidate-summary/v1",
      "processor_version":VERSION,
      "stable_prefix_candidates":len(rows),
      "new_brand_candidates":sum(r["review_status"]=="new_brand_candidate" for r in rows),
      "known_registry_prefix_updates":sum(r["review_status"]=="known_registry_prefix_update" for r in rows),
      "status":"catalog_backed_brand_code_candidates_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
