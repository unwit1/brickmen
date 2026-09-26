#!/usr/bin/env python3
"""Exact-crosswalk user FigureRelease candidates against the HeroBloks catalog census.

Exact serial equality is catalog evidence for a release listing, not proof of manufacturer/factory
ownership. Name similarity is reported only as a consistency signal.
"""
from __future__ import annotations
import argparse,json,re,unicodedata
from collections import Counter,defaultdict
from pathlib import Path

VERSION="user-release-multicatalog-crosswalk/v2"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def code_norm(v):
    return re.sub(r"[^A-Z0-9]+","",str(v or "").upper())

def text_norm(v):
    s=unicodedata.normalize("NFKD",str(v or ""))
    s="".join(c for c in s if not unicodedata.combining(c)).casefold()
    s=re.sub(r"[^a-z0-9]+"," ",s)
    return " ".join(s.split())

def token_overlap(a,b):
    aa=set(text_norm(a).split());bb=set(text_norm(b).split())
    if not aa or not bb:return 0.0
    return round(len(aa&bb)/len(aa|bb),4)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--release-candidates",type=Path,required=True)
    ap.add_argument("--herobloks-catalog",type=Path,required=True)
    ap.add_argument("--historical-xinh-catalog",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    hb=defaultdict(list)
    for r in load_jsonl(args.herobloks_catalog):
        serial=r.get("serial_slug")
        key=code_norm(serial)
        if key:
            hb[key].append(r)

    historical=defaultdict(list)
    if args.historical_xinh_catalog and args.historical_xinh_catalog.exists():
        for r in load_jsonl(args.historical_xinh_catalog):
            key=code_norm(r.get("serial"))
            if key:
                historical[key].append(r)

    rows=[];bands=Counter();historical_bands=Counter()
    for rel in load_jsonl(args.release_candidates):
        code=rel.get("maker_product_code")
        key=code_norm(code)
        matches=hb.get(key,[])
        observed_names=rel.get("observed_names") or []
        compact=[]
        for m in matches:
            name=m.get("anchor_text") or m.get("name_slug")
            overlap=max([token_overlap(n,name) for n in observed_names] or [0.0])
            compact.append({
              "herobloks_id":m.get("herobloks_id"),
              "brand_slug":m.get("brand_slug"),
              "serial_slug":m.get("serial_slug"),
              "name_slug":m.get("name_slug"),
              "anchor_text":m.get("anchor_text"),
              "url":m.get("url"),
              "name_token_overlap_max":overlap,
            })
        if len(matches)==1:
            band="exact_unique_serial_match"
        elif len(matches)>1:
            band="exact_serial_collision"
        else:
            band="no_exact_serial_match"
        bands[band]+=1

        historical_matches=historical.get(key,[]) if band=="no_exact_serial_match" else []
        historical_compact=[]
        for m in historical_matches:
            hname=m.get("historical_name")
            overlap=max([token_overlap(n,hname) for n in observed_names] or [0.0]) if hname else 0.0
            historical_compact.append({
              "serial":m.get("serial"),
              "historical_name":hname,
              "name_status":m.get("name_status"),
              "source_url":m.get("source_url"),
              "source_updated_label":m.get("source_updated_label"),
              "name_token_overlap_max":overlap
            })
        if len(historical_matches)==1:
            historical_status="historical_exact_unique_serial_match"
        elif len(historical_matches)>1:
            historical_status="historical_exact_serial_collision"
        else:
            historical_status="no_historical_exact_serial_match"
        historical_bands[historical_status]+=1

        effective_status=(
          band if band!="no_exact_serial_match"
          else historical_status if historical_status!="no_historical_exact_serial_match"
          else "no_exact_serial_match_any_catalog"
        )
        rows.append({
          "figure_release_candidate_id":rel.get("figure_release_candidate_id"),
          "maker_product_code":code,
          "observed_names":observed_names,
          "observed_variants":rel.get("observed_variants") or [],
          "prefix_maker_candidates":rel.get("maker_candidates") or [],
          "herobloks_match_status":band,
          "herobloks_matches":compact,
          "historical_xinh_match_status":historical_status,
          "historical_xinh_matches":historical_compact,
          "effective_catalog_match_status":effective_status,
          "catalog_identity_consistency":(
            "name_supportive" if compact and max(x["name_token_overlap_max"] for x in compact)>=0.35
            else "serial_match_name_needs_review" if compact
            else "no_catalog_match"
          ),
          "promotion_policy":"A unique exact serial match verifies that the cited catalog records the serial/name association. Current HeroBloks evidence and historical DownTheBlocks evidence remain distinct. Canonical maker ownership, release chronology, collaboration, and character identity still require source-aware reconciliation.",
          "processor_version":VERSION
        })
    rows.sort(key=lambda x:(
      0 if x["herobloks_match_status"]=="exact_unique_serial_match" else
      1 if x["herobloks_match_status"]=="exact_serial_collision" else 2,
      x.get("maker_product_code") or ""
    ))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"user-release-multicatalog-crosswalk-summary/v2",
      "processor_version":VERSION,
      "release_candidates":len(rows),
      "match_status_counts":dict(bands),
      "historical_fallback_status_counts":dict(historical_bands),
      "historical_fallback_unique_matches":sum(
        r.get("historical_xinh_match_status")=="historical_exact_unique_serial_match" for r in rows
      ),
      "no_exact_match_any_catalog":sum(
        r.get("effective_catalog_match_status")=="no_exact_serial_match_any_catalog" for r in rows
      ),
      "unique_exact_match_rate":round(bands["exact_unique_serial_match"]/max(1,len(rows)),4),
      "unique_exact_matches_with_name_support":sum(
        r["herobloks_match_status"]=="exact_unique_serial_match" and r["catalog_identity_consistency"]=="name_supportive"
        for r in rows
      ),
      "unique_exact_matches_name_needs_review":sum(
        r["herobloks_match_status"]=="exact_unique_serial_match" and r["catalog_identity_consistency"]=="serial_match_name_needs_review"
        for r in rows
      ),
      "unmatched_prefix_counts":dict(Counter(
        (re.match(r"^[A-Za-z]+", str(r.get("maker_product_code") or "")) or ["" ])[0].upper()
        for r in rows if r["herobloks_match_status"]=="no_exact_serial_match"
      )),
      "unmatched_sample":[{
        "maker_product_code":r.get("maker_product_code"),
        "observed_names":r.get("observed_names"),
        "prefix_maker_candidates":r.get("prefix_maker_candidates")
      } for r in rows if r["herobloks_match_status"]=="no_exact_serial_match"][:100],
      "collision_sample":[{
        "maker_product_code":r.get("maker_product_code"),
        "observed_names":r.get("observed_names"),
        "matches":r.get("herobloks_matches")
      } for r in rows if r["herobloks_match_status"]=="exact_serial_collision"][:100],
      "status":"current_and_historical_exact_catalog_crosswalk_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
