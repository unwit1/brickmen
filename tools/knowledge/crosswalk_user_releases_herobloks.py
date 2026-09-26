#!/usr/bin/env python3
"""Exact-crosswalk user FigureRelease candidates against the HeroBloks catalog census.

Exact serial equality is catalog evidence for a release listing, not proof of manufacturer/factory
ownership. Name similarity is reported only as a consistency signal.
"""
from __future__ import annotations
import argparse,json,re,unicodedata
from collections import Counter,defaultdict
from pathlib import Path

VERSION="user-release-multicatalog-crosswalk/v3"

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
    ap.add_argument("--fallback-catalog",action="append",default=[],help="catalog_id=path; may be repeated")
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    ap.add_argument("--unresolved-output",type=Path)
    ap.add_argument("--collision-output",type=Path)
    ap.add_argument("--manual-verifications",type=Path)
    args=ap.parse_args()

    hb=defaultdict(list)
    for r in load_jsonl(args.herobloks_catalog):
        serial=r.get("serial_slug")
        key=code_norm(serial)
        if key:
            hb[key].append(r)

    fallback_catalogs={}
    if args.historical_xinh_catalog and args.historical_xinh_catalog.exists():
        fallback_catalogs["downtheblocks_xinh_g"]=args.historical_xinh_catalog
    for spec in args.fallback_catalog:
        if "=" not in spec:
            raise SystemExit(f"--fallback-catalog requires catalog_id=path, got {spec!r}")
        catalog_id,path_text=spec.split("=",1)
        path=Path(path_text)
        if path.exists():
            fallback_catalogs[catalog_id]=path

    historical_by_catalog={}
    for catalog_id,path in fallback_catalogs.items():
        index=defaultdict(list)
        for r in load_jsonl(path):
            key=code_norm(r.get("serial"))
            if key:index[key].append(r)
        historical_by_catalog[catalog_id]=index

    manual_index=defaultdict(list)
    if args.manual_verifications and args.manual_verifications.exists():
        manual_payload=json.loads(args.manual_verifications.read_text(encoding="utf-8"))
        for rec in manual_payload.get("records") or []:
            key=code_norm(rec.get("serial"))
            if key:
                manual_index[key].append(rec)

    rows=[];bands=Counter();historical_bands=Counter();fallback_catalog_hit_counts=Counter();manual_status_counts=Counter()
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

        historical_compact=[]
        historical_total=0
        historical_catalog_status={}
        if band=="no_exact_serial_match":
            for catalog_id,index in historical_by_catalog.items():
                cat_matches=index.get(key,[])
                historical_total+=len(cat_matches)
                if len(cat_matches)==1:
                    cat_status="exact_unique_serial_match"
                    fallback_catalog_hit_counts[catalog_id]+=1
                elif len(cat_matches)>1:
                    cat_status="exact_serial_collision"
                else:
                    cat_status="no_exact_serial_match"
                historical_catalog_status[catalog_id]=cat_status
                for m in cat_matches:
                    hname=m.get("historical_name")
                    overlap=max([token_overlap(n,hname) for n in observed_names] or [0.0]) if hname else 0.0
                    historical_compact.append({
                      "catalog_id":catalog_id,
                      "serial":m.get("serial"),
                      "historical_name":hname,
                      "historical_names":m.get("historical_names"),
                      "name_status":m.get("name_status"),
                      "source_url":m.get("source_url"),
                      "source_updated_label":m.get("source_updated_label"),
                      "name_token_overlap_max":overlap
                    })
        unique_catalog_matches=[cid for cid,status in historical_catalog_status.items() if status=="exact_unique_serial_match"]
        collision_catalog_matches=[cid for cid,status in historical_catalog_status.items() if status=="exact_serial_collision"]
        if collision_catalog_matches:
            historical_status="historical_exact_serial_collision"
        elif unique_catalog_matches:
            historical_status="historical_exact_unique_serial_match"
        else:
            historical_status="no_historical_exact_serial_match"
        historical_bands[historical_status]+=1

        manual_matches=manual_index.get(key,[]) if band=="no_exact_serial_match" and historical_status=="no_historical_exact_serial_match" else []
        if len(manual_matches)==1:
            manual_status="manual_exact_verified"
        elif len(manual_matches)>1:
            manual_status="manual_exact_collision"
        else:
            manual_status="no_manual_exact_verification"
        manual_status_counts[manual_status]+=1

        effective_status=(
          band if band!="no_exact_serial_match"
          else historical_status if historical_status!="no_historical_exact_serial_match"
          else manual_status if manual_status!="no_manual_exact_verification"
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
          "fallback_catalog_statuses":historical_catalog_status,
          "fallback_catalog_matches":historical_compact,
          "manual_verification_status":manual_status,
          "manual_verification_matches":manual_matches,
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
      "fallback_catalogs_loaded":sorted(fallback_catalogs),
      "fallback_catalog_unique_hit_counts":dict(fallback_catalog_hit_counts),
      "historical_fallback_unique_matches":sum(
        r.get("historical_xinh_match_status")=="historical_exact_unique_serial_match" for r in rows
      ),
      "manual_verification_status_counts":dict(manual_status_counts),
      "manual_exact_verifications":sum(r.get("manual_verification_status")=="manual_exact_verified" for r in rows),
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
      "effective_unmatched_prefix_counts":dict(Counter(
        (re.match(r"^[A-Za-z]+", str(r.get("maker_product_code") or "")) or ["" ])[0].upper()
        for r in rows if r.get("effective_catalog_match_status")=="no_exact_serial_match_any_catalog"
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
    if args.unresolved_output:
        args.unresolved_output.parent.mkdir(parents=True,exist_ok=True)
        with args.unresolved_output.open("w",encoding="utf-8") as f:
            for r in rows:
                if r.get("effective_catalog_match_status")=="no_exact_serial_match_any_catalog":
                    f.write(json.dumps(r,ensure_ascii=False)+"\n")
    if args.collision_output:
        args.collision_output.parent.mkdir(parents=True,exist_ok=True)
        with args.collision_output.open("w",encoding="utf-8") as f:
            for r in rows:
                if r.get("herobloks_match_status")=="exact_serial_collision" or r.get("historical_xinh_match_status")=="historical_exact_serial_collision":
                    f.write(json.dumps(r,ensure_ascii=False)+"\n")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
