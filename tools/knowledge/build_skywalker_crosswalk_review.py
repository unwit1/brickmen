#!/usr/bin/env python3
"""Build grouped review queues for Skywalker digital->physical candidates."""
from __future__ import annotations
import argparse,json,re
from collections import Counter,defaultdict
from pathlib import Path
from skywalker_identity_keys import parse_identity_key

VERSION="skywalker-crosswalk-review/v3"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:yield json.loads(line)

def base_key(key):
    parsed=parse_identity_key(key)
    base=parsed["base_character_key"]
    return re.sub(r"[^A-Za-z0-9]+","",base) or str(key or "")

def exact_character_identity(row):
    candidates=row.get("top_candidates") or []
    if not candidates:return False
    top=candidates[0]
    ev=top.get("evidence") or {}
    return (
        float(top.get("score") or 0) >= 0.999
        and float(ev.get("key_token_coverage") or 0) >= 0.999
        and float(ev.get("jaccard") or 0) >= 0.999
        and str(ev.get("key_normalized") or "").strip()
        and str(ev.get("key_normalized") or "").strip()==str(ev.get("catalog_normalized") or "").strip()
    )

def physical_years(row):
    candidates=row.get("top_candidates") or []
    if not candidates:return []
    years=set()
    for occ in candidates[0].get("set_occurrences") or []:
        try:years.add(int(occ.get("year")))
        except (TypeError,ValueError):pass
    return sorted(years)

def temporal_relation(row,game_launch_year):
    years=physical_years(row)
    if not years:return "unknown"
    first=years[0]
    if first<game_launch_year:return "physical_predates_game"
    if first>game_launch_year:return "physical_postdates_game"
    return "same_calendar_year_timing_unresolved"

def triage(row,game_launch_year):
    exact=exact_character_identity(row)
    relation=temporal_relation(row,game_launch_year)
    return {
      "character_identity_status":"exact_catalog_name_match" if exact else "candidate_identity_review_required",
      "physical_release_years":physical_years(row),
      "temporal_relation_to_game_launch":relation,
      "physical_equivalence_status":"not_established_requires_version_or_visual_confirmation",
      "triage_note":(
        "Exact normalized character identity is established, but exact digital-to-physical decoration equivalence is intentionally not auto-promoted."
        if exact else
        "Character identity itself still requires review before any physical counterpart inference."
      ),
    }

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
    ap.add_argument("--game-launch-year",type=int,default=2022,
                    help="Reference year for conservative physical-vs-digital temporal triage; default is The Skywalker Saga launch year.")
    args=ap.parse_args()
    rows=[];groups=defaultdict(list);bands=Counter();triage_counts=Counter();temporal_counts=Counter()
    for r in load_jsonl(args.candidates):
        r=dict(r)
        r["base_character_key"]=base_key(r.get("character_variant_key"))
        r["review_priority_score"]=priority(r)
        r.update(triage(r,args.game_launch_year))
        triage_counts[r["character_identity_status"]]+=1
        temporal_counts[r["temporal_relation_to_game_launch"]]+=1
        r["review_status"]=(
            "character_identity_confirmed_version_pending"
            if r["character_identity_status"]=="exact_catalog_name_match"
            else "pending_independent_version_confirmation"
        )
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
          "exact_character_identity_matches":sum(x.get("character_identity_status")=="exact_catalog_name_match" for x in items),
          "temporal_relations":dict(Counter(x.get("temporal_relation_to_game_launch") for x in items)),
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
      "character_identity_status_counts":dict(triage_counts),
      "temporal_relation_counts":dict(temporal_counts),
      "game_launch_reference_year":args.game_launch_year,
      "automatic_physical_equivalence_promotions":0,
      "status":"grouped_review_queue_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
