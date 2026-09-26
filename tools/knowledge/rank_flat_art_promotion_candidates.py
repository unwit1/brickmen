#!/usr/bin/env python3
"""Rank unverified rioforce flat-art catalog candidates for manual/source verification.

This is a review prioritizer only. It never promotes a candidate into canonical supervision.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

VERSION="flat-art-promotion-review/v1"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def role_match(inferred, component_role):
    inferred=(inferred or "").casefold()
    component_role=(component_role or "").casefold()
    if inferred=="head":
        return component_role=="head"
    if inferred=="torso":
        return component_role=="torso"
    if inferred in {"leg","legs","hips","hips_and_legs"}:
        return component_role in {"leg","legs","hips","hips_and_legs"}
    if inferred in {"arm","arms"}:
        return component_role in {"arm","arms"}
    return inferred and inferred==component_role

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",type=Path,required=True)
    ap.add_argument("--verified",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    verified=json.loads(args.verified.read_text(encoding="utf-8"))
    verified_ids={r.get("rioforce_asset_group_id") for r in verified.get("records") or []}
    rows=[];bands=Counter()
    for rec in load_jsonl(args.candidates):
        aid=rec.get("crosswalk_candidate_id")
        if aid in verified_ids:
            continue
        if rec.get("asset_class")!="minifigure_surface_map":
            continue
        figs=rec.get("figure_candidates") or []
        top=figs[0] if figs else None
        second=figs[1] if len(figs)>1 else None
        if not top:
            band="no_figure_candidate"
            score=0.0
            reasons=["no_figure_candidate"]
            top_components=[]
            decorated=[]
            margin=0.0
        else:
            top_score=float(top.get("score") or 0)
            second_score=float(second.get("score") or 0) if second else 0
            margin=round(top_score-second_score,4)
            top_components=[
                c for c in (rec.get("component_candidates") or [])
                if c.get("fig_num")==top.get("fig_num")
                and role_match(rec.get("inferred_component_role"),c.get("component_role"))
            ]
            decorated=[c for c in top_components if c.get("print_of") or "print" in str(c.get("part_name") or "").casefold()]
            score=top_score*60 + max(0,margin)*30
            reasons=[f"top_figure_score:{top_score:.3f}",f"margin:{margin:.3f}"]
            if top.get("year_match") is True:
                score+=20;reasons.append("exact_year_match")
            elif top.get("year_match") is False:
                score-=15;reasons.append("year_mismatch")
            if decorated:
                score+=20;reasons.append("decorated_surface_component")
            if len(decorated)==1:
                score+=10;reasons.append("single_decorated_surface_component")
            elif len(decorated)>1:
                score+=5;reasons.append("multiple_decorated_surface_components")
            if margin>=0.10:
                score+=10;reasons.append("clear_top_figure_margin")
            if top_score>=0.90:
                score+=10;reasons.append("high_figure_identity_score")
            score=round(max(0,score),3)
            if score>=100:
                band="verify_first"
            elif score>=75:
                band="strong_review"
            elif score>=50:
                band="medium_review"
            else:
                band="low_review"
        bands[band]+=1
        rows.append({
            "crosswalk_candidate_id":aid,
            "relative_stem":(rec.get("rioforce") or {}).get("relative_stem"),
            "subject_text":rec.get("subject_text"),
            "surface_role":rec.get("inferred_component_role"),
            "top_figure_candidate":top,
            "second_figure_candidate":second,
            "top_margin":margin,
            "top_role_components":top_components,
            "decorated_role_components":decorated,
            "review_priority_score":score,
            "review_band":band,
            "review_reasons":reasons,
            "review_status":"pending_independent_verification",
            "promotion_policy":"Never auto-promote. Verify subject/version/year, exact minifigure release, exact decorated component/surface, and provenance independently before adding to the canonical verified crosswalk.",
            "processor_version":VERSION
        })
    rows.sort(key=lambda x:(-x["review_priority_score"],x.get("relative_stem") or ""))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
        "schema":"flat-art-promotion-review-summary/v1",
        "processor_version":VERSION,
        "verified_asset_groups_excluded":len(verified_ids),
        "unverified_surface_records_ranked":len(rows),
        "review_band_counts":dict(bands),
        "verify_first_records":sum(r["review_band"]=="verify_first" for r in rows),
        "with_decorated_top_surface_component":sum(bool(r["decorated_role_components"]) for r in rows),
        "top_50":[{
            "id":r["crosswalk_candidate_id"],
            "path":r["relative_stem"],
            "subject":r["subject_text"],
            "surface":r["surface_role"],
            "score":r["review_priority_score"],
            "band":r["review_band"],
            "top_fig":(r["top_figure_candidate"] or {}).get("fig_num"),
            "top_name":(r["top_figure_candidate"] or {}).get("name"),
            "year_match":(r["top_figure_candidate"] or {}).get("year_match"),
            "decorated_components":[c.get("part_num") for c in r["decorated_role_components"]]
        } for r in rows[:50]],
        "status":"manual_verification_queue_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
