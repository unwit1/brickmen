#!/usr/bin/env python3
"""Refine the ranked custom-design backlog using known existing-release evidence."""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

VERSION="custom-design-backlog-refinement/v1"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--backlog",type=Path,required=True)
    ap.add_argument("--release-crosswalk",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--review-output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    rel={r.get("custom_design_candidate_id"):r for r in load_jsonl(args.release_crosswalk)}
    actionable=[];review=[];counts=Counter()
    for row in load_jsonl(args.backlog):
        x=dict(row)
        evidence=rel.get(x.get("custom_design_candidate_id"))
        status=(evidence or {}).get("representation_status")
        if x.get("gap_mode")=="existing_representation_compare_or_acquire":
            x["refined_gap_mode"]="existing_representation_compare_or_acquire"
            x["refinement_reason"]="source_tracker_already_records_existing_representation"
            if evidence:
                x["existing_release_evidence"]=evidence
            review.append(x)
        elif x.get("gap_mode")=="acquisition_wishlist":
            x["refined_gap_mode"]="acquisition_wishlist"
            x["refinement_reason"]="explicit_wishlist_acquisition"
            actionable.append(x)
        elif status=="likely_existing_representation":
            x["refined_gap_mode"]="existing_representation_compare_or_acquire"
            x["refinement_reason"]="variant_supported_existing_release_candidate"
            x["existing_release_evidence"]=evidence
            review.append(x)
        elif status=="existing_name_level_representation":
            x["refined_gap_mode"]="existing_name_level_representation_review"
            x["refinement_reason"]="same_character_release_exists_variant_not_established"
            x["existing_release_evidence"]=evidence
            review.append(x)
        elif status=="name_match_variant_unresolved":
            x["refined_gap_mode"]="representation_variant_review"
            x["refinement_reason"]="same_character_release_candidates_exist_but_variant_unresolved"
            x["existing_release_evidence"]=evidence
            review.append(x)
        else:
            x["refined_gap_mode"]=x.get("gap_mode") or "custom_design_candidate"
            x["refinement_reason"]="no_exact_name_release_candidate"
            actionable.append(x)
        counts[x["refined_gap_mode"]]+=1

    actionable.sort(key=lambda x:(-(x.get("priority_score") or 0),x.get("custom_design_candidate_id") or ""))
    review.sort(key=lambda x:(
        0 if x["refined_gap_mode"]=="existing_representation_compare_or_acquire" else
        1 if x["refined_gap_mode"]=="existing_name_level_representation_review" else 2,
        -(x.get("priority_score") or 0),
        x.get("custom_design_candidate_id") or ""
    ))

    for path,rows in ((args.output,actionable),(args.review_output,review)):
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("w",encoding="utf-8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")

    summary={
      "schema":"custom-design-backlog-refinement-summary/v1",
      "processor_version":VERSION,
      "input_design_candidates":len(actionable)+len(review),
      "refined_actionable_custom_design_candidates":len(actionable),
      "representation_review_records":len(review),
      "refined_mode_counts":dict(counts),
      "status":"refined_custom_design_backlog_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
