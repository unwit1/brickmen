#!/usr/bin/env python3
"""Build a ranked custom-design backlog from conservative collection/design gap candidates.

Only explicit missing targets and wishlist targets are actionable by default.
Unknown/maybe states remain review-only and are never silently promoted.
"""
from __future__ import annotations
import argparse,json,re
from collections import Counter,defaultdict
from pathlib import Path

VERSION="custom-design-backlog/v1"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def uniq(values):
    return sorted({str(v).strip() for v in values if v is not None and str(v).strip()})

def first_nonempty(records, *keys):
    for key in keys:
        vals=uniq(r.get(key) for r in records)
        if vals:return vals
    return []

def source_family(rec):
    title=(rec.get("source_title") or "").casefold()
    tab=(rec.get("source_tab") or "").casefold()
    category=(rec.get("category") or "").casefold()
    collection=(rec.get("collection") or "").casefold()
    blob=" ".join([title,tab,category,collection])
    if "star wars" in blob:return "Star Wars"
    if "dragon ball" in blob:return "Dragon Ball"
    if "one piece" in blob:return "One Piece"
    if "invincible" in blob:return "Invincible"
    if "x-men" in blob or "x men" in blob:return "X-Men"
    if "marvel" in blob or "avengers" in blob or "spider" in blob:return "Marvel"
    if "dc" in blob or any(x in blob for x in ("batman","superman","justice league","titans","doom patrol","aquaman")):return "DC"
    if "anime" in blob:return "Anime"
    if "gaming" in blob or "games" in blob:return "Gaming"
    return "Unclassified"

def rank(row):
    state=row.get("candidate_state")
    recs=row.get("records") or []
    score=0; reasons=[]
    if state=="wishlist_gap_candidate":
        score+=100; reasons.append("explicit_wishlist")
    elif state=="explicit_missing_design_target":
        score+=80; reasons.append("explicit_missing")
    elif state=="maybe_gap_candidate":
        score+=30; reasons.append("maybe_state")
    else:
        score+=10; reasons.append("unknown_state")

    sources=len(set(row.get("source_files") or []))
    if sources>1:
        score+=min(30,(sources-1)*8); reasons.append("cross_source_recurrence")

    names=uniq(r.get("name") for r in recs)
    identities=uniq(r.get("identity") for r in recs)
    variants=uniq(r.get("variant") for r in recs)
    appearances=uniq(r.get("first_appearance") for r in recs)
    years=uniq(r.get("year") for r in recs)
    preferred=uniq(r.get("preferred") for r in recs)
    official=uniq(r.get("official") for r in recs)
    bootleg=uniq(r.get("bootleg") for r in recs)
    universes=uniq(r.get("universe") for r in recs)

    if identities: score+=8; reasons.append("identity_specific")
    if variants: score+=10; reasons.append("variant_specific")
    if appearances: score+=10; reasons.append("source_appearance_present")
    if years: score+=4; reasons.append("year_present")
    if preferred: score+=6; reasons.append("preferred_reference_present")
    if universes: score+=4; reasons.append("universe_present")
    if len(names)==1: score+=3
    if len(identities)>1 or len(universes)>1:
        score-=12; reasons.append("identity_or_universe_ambiguity")
    if len(variants)>3:
        score-=5; reasons.append("variant_ambiguity")

    return max(0,score),reasons,{
        "names":names,"identities":identities,"variants":variants,
        "first_appearances":appearances,"years":years,"preferred":preferred,
        "official_representations":official,"bootleg_representations":bootleg,
        "universes":universes
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--gaps",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--review-output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    actionable=[];review=[];families=Counter();states=Counter()
    for row in load_jsonl(args.gaps):
        score,reasons,meta=rank(row)
        recs=row.get("records") or []
        family_votes=Counter(source_family(r) for r in recs)
        family=family_votes.most_common(1)[0][0] if family_votes else "Unclassified"
        has_existing_representation=bool(meta.get("official_representations") or meta.get("bootleg_representations"))
        if row.get("candidate_state")=="wishlist_gap_candidate":
            gap_mode="acquisition_wishlist"
        elif row.get("candidate_state")=="explicit_missing_design_target" and has_existing_representation:
            gap_mode="existing_representation_compare_or_acquire"
        elif row.get("candidate_state")=="explicit_missing_design_target":
            gap_mode="custom_design_candidate"
        else:
            gap_mode="review_only_unknown_state"

        item={
          "custom_design_candidate_id":"custom-gap-"+re.sub(r"[^a-z0-9]+","-",str(row.get("strict_group_key") or "").casefold()).strip("-")[:180],
          "strict_group_key":row.get("strict_group_key"),
          "candidate_state":row.get("candidate_state"),
          "gap_mode":gap_mode,
          "priority_score":score,
          "priority_reasons":reasons,
          "franchise_family":family,
          "source_files":row.get("source_files") or [],
          "record_count":row.get("record_count"),
          "observed_statuses":row.get("observed_statuses") or [],
          **meta,
          "records":recs,
          "review_status":"pending",
          "policy":"Only explicit missing or wishlist states are actionable. Unknown/maybe states remain review-only. Character/incarnation/source-appearance ambiguity must be resolved before final design execution.",
          "processor_version":VERSION
        }
        states[item["candidate_state"]]+=1
        families[family]+=1
        if item["candidate_state"] in {"wishlist_gap_candidate","explicit_missing_design_target"}:
            actionable.append(item)
        else:
            review.append(item)

    actionable.sort(key=lambda x:(-x["priority_score"],x["franchise_family"],x["strict_group_key"] or ""))
    review.sort(key=lambda x:(-x["priority_score"],x["franchise_family"],x["strict_group_key"] or ""))

    args.output.parent.mkdir(parents=True,exist_ok=True)
    for path,rows in ((args.output,actionable),(args.review_output,review)):
        with path.open("w",encoding="utf-8") as f:
            for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")

    mode_counts=Counter(x["gap_mode"] for x in actionable+review)
    summary={
      "schema":"custom-design-backlog-summary/v1",
      "processor_version":VERSION,
      "actionable_records":len(actionable),
      "review_only_records":len(review),
      "state_counts":dict(states),
      "gap_mode_counts":dict(mode_counts),
      "franchise_counts":dict(families.most_common()),
      "top_actionable":[
        {
          "id":x["custom_design_candidate_id"],
          "score":x["priority_score"],
          "state":x["candidate_state"],
          "mode":x["gap_mode"],
          "family":x["franchise_family"],
          "names":x["names"],
          "identities":x["identities"],
          "variants":x["variants"],
          "sources":len(x["source_files"]),
          "reasons":x["priority_reasons"]
        } for x in actionable[:100]
      ],
      "status":"ranked_custom_design_backlog_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:summary[k] for k in ("actionable_records","review_only_records","state_counts","franchise_counts","status")},indent=2))

if __name__=="__main__":main()
