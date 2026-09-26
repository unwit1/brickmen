#!/usr/bin/env python3
"""Crosswalk actionable custom-design targets against known user release candidates.

The goal is to detect likely existing custom/bootleg representations that older tracker
rows may not have explicitly marked. Matching is conservative:
- exact normalized character name is required;
- exact/contained normalized variant agreement strengthens the match;
- name-only matches never automatically suppress a design target.
"""
from __future__ import annotations
import argparse,json,re,unicodedata
from collections import Counter,defaultdict
from pathlib import Path

VERSION="design-existing-release-crosswalk/v1"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:
                yield json.loads(line)

def norm(v):
    s=unicodedata.normalize("NFKD",str(v or ""))
    s="".join(c for c in s if not unicodedata.combining(c)).casefold()
    s=s.replace("&"," and ")
    s=re.sub(r"[^a-z0-9]+"," ",s)
    return " ".join(s.split())

def uniq(xs):
    return sorted({str(x).strip() for x in xs if x is not None and str(x).strip()})

def release_catalog_names(cross):
    vals=[]
    for m in cross.get("herobloks_matches") or []:
        vals.extend([m.get("anchor_text"),m.get("name_slug")])
    for m in cross.get("fallback_catalog_matches") or []:
        vals.extend([m.get("name"),m.get("anchor_text"),m.get("display_name")])
    for m in cross.get("manual_verification_matches") or []:
        vals.extend([m.get("name"),m.get("character"),m.get("display_name")])
    return uniq(vals)

def variant_support(target_variants, release_variants, catalog_names):
    tv=[norm(x) for x in target_variants if norm(x)]
    rv=[norm(x) for x in release_variants if norm(x)]
    cn=[norm(x) for x in catalog_names if norm(x)]
    if not tv:
        return "target_has_no_variant"
    for t in tv:
        if t in rv:
            return "exact_variant"
    for t in tv:
        if any(t and (t in r or r in t) for r in rv if r):
            return "variant_contains"
    for t in tv:
        if any(t and t in c for c in cn):
            return "catalog_name_contains_variant"
    return "variant_unresolved"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--backlog",type=Path,required=True)
    ap.add_argument("--releases",type=Path,required=True)
    ap.add_argument("--crosswalk",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    release_by_id={r.get("figure_release_candidate_id"):r for r in load_jsonl(args.releases)}
    cross_by_id={r.get("figure_release_candidate_id"):r for r in load_jsonl(args.crosswalk)}

    name_index=defaultdict(list)
    for rid,rel in release_by_id.items():
        for name in rel.get("observed_names") or []:
            n=norm(name)
            if n:
                name_index[n].append(rid)

    rows=[];status_counts=Counter()
    for target in load_jsonl(args.backlog):
        if target.get("gap_mode")!="custom_design_candidate":
            continue
        target_names=target.get("names") or []
        candidate_ids=[]
        for name in target_names:
            candidate_ids.extend(name_index.get(norm(name),[]))
        candidate_ids=uniq(candidate_ids)

        matches=[]
        for rid in candidate_ids:
            rel=release_by_id.get(rid) or {}
            cross=cross_by_id.get(rid) or {}
            catalog_names=release_catalog_names(cross)
            vs=variant_support(
                target.get("variants") or [],
                rel.get("observed_variants") or [],
                catalog_names,
            )
            catalog_status=cross.get("effective_catalog_match_status") or cross.get("herobloks_match_status")
            if vs in {"exact_variant","variant_contains","catalog_name_contains_variant"}:
                status="likely_existing_representation"
            elif vs=="target_has_no_variant" and catalog_status and "match" in str(catalog_status) and "no_exact" not in str(catalog_status):
                status="existing_name_level_representation"
            else:
                status="name_match_variant_unresolved"
            matches.append({
                "figure_release_candidate_id":rid,
                "maker_product_code":rel.get("maker_product_code"),
                "maker_candidates":rel.get("maker_candidates") or [],
                "release_observed_names":rel.get("observed_names") or [],
                "release_observed_variants":rel.get("observed_variants") or [],
                "catalog_names":catalog_names,
                "catalog_match_status":catalog_status,
                "variant_support":vs,
                "representation_status":status,
            })

        if not matches:
            overall="no_exact_name_release_candidate"
        elif any(m["representation_status"]=="likely_existing_representation" for m in matches):
            overall="likely_existing_representation"
        elif any(m["representation_status"]=="existing_name_level_representation" for m in matches):
            overall="existing_name_level_representation"
        else:
            overall="name_match_variant_unresolved"

        status_counts[overall]+=1
        rows.append({
            "custom_design_candidate_id":target.get("custom_design_candidate_id"),
            "strict_group_key":target.get("strict_group_key"),
            "names":target_names,
            "identities":target.get("identities") or [],
            "variants":target.get("variants") or [],
            "franchise_family":target.get("franchise_family"),
            "priority_score":target.get("priority_score"),
            "release_candidate_count":len(matches),
            "representation_status":overall,
            "release_matches":matches,
            "review_status":"pending" if overall!="no_exact_name_release_candidate" else "no_match_found",
            "policy":"Exact normalized character-name matches are candidate evidence only. A design target is only likely represented when variant evidence also agrees; name-only matches remain review candidates.",
            "processor_version":VERSION,
        })

    rows.sort(key=lambda x:(
        0 if x["representation_status"]=="likely_existing_representation" else
        1 if x["representation_status"]=="existing_name_level_representation" else
        2 if x["representation_status"]=="name_match_variant_unresolved" else 3,
        -(x.get("priority_score") or 0),
        x.get("custom_design_candidate_id") or ""
    ))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row,ensure_ascii=False)+"\n")

    summary={
        "schema":"design-existing-release-crosswalk-summary/v1",
        "processor_version":VERSION,
        "custom_design_candidates_checked":len(rows),
        "status_counts":dict(status_counts),
        "likely_existing_representation_records":status_counts["likely_existing_representation"],
        "existing_name_level_representation_records":status_counts["existing_name_level_representation"],
        "name_match_variant_unresolved_records":status_counts["name_match_variant_unresolved"],
        "no_exact_name_release_candidate_records":status_counts["no_exact_name_release_candidate"],
        "status":"design_existing_release_crosswalk_ready",
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
