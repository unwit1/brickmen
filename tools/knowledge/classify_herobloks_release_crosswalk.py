#!/usr/bin/env python3
"""Classify exact HeroBloks release crosswalks into promotable evidence and review queues."""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

VERSION="user-release-herobloks-review/v1"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--crosswalk",type=Path,required=True)
    ap.add_argument("--promoted-output",type=Path,required=True)
    ap.add_argument("--review-output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    promoted=[];review=[];counts=Counter()
    for r in load_jsonl(args.crosswalk):
        status=r.get("herobloks_match_status")
        consistency=r.get("catalog_identity_consistency")
        matches=r.get("herobloks_matches") or []
        if status=="exact_unique_serial_match" and consistency=="name_supportive" and len(matches)==1:
            m=matches[0]
            promoted.append({
              "figure_release_candidate_id":r.get("figure_release_candidate_id"),
              "maker_product_code":r.get("maker_product_code"),
              "observed_names":r.get("observed_names") or [],
              "observed_variants":r.get("observed_variants") or [],
              "catalog_source":"HeroBloks",
              "herobloks_id":m.get("herobloks_id"),
              "herobloks_brand_slug":m.get("brand_slug"),
              "herobloks_serial":m.get("serial_slug"),
              "herobloks_name":m.get("anchor_text") or m.get("name_slug"),
              "herobloks_url":m.get("url"),
              "name_token_overlap_max":m.get("name_token_overlap_max"),
              "evidence_status":"catalog_backed_exact_serial_and_name_support",
              "canonical_status":"release_evidence_promoted_identity_still_source_aware",
              "policy":"This promotes catalog evidence for the release listing, not manufacturer ownership/factory identity or canonical character/incarnation identity.",
              "processor_version":VERSION
            })
            counts["promoted_exact_serial_name_support"]+=1
            continue

        review_type="other"
        if status=="exact_unique_serial_match":
            review_type="unique_serial_name_review"
        elif status=="exact_serial_collision":
            brands={x.get("brand_slug") for x in matches if x.get("brand_slug")}
            supportive=[x for x in matches if float(x.get("name_token_overlap_max") or 0)>=0.35]
            if len(brands)<=1 and len(matches)>1 and len(supportive)==1:
                review_type="same_brand_multi_record_one_name_supportive_possible_bundle"
            elif len(brands)<=1 and len(matches)>1:
                review_type="same_brand_multi_record_bundle_or_reuse"
            else:
                review_type="cross_brand_serial_collision"
        elif status=="no_exact_serial_match":
            review_type="no_current_herobloks_exact_match"

        counts[review_type]+=1
        review.append({
          **r,
          "review_type":review_type,
          "review_priority":(
            "high" if review_type in {
              "same_brand_multi_record_one_name_supportive_possible_bundle",
              "cross_brand_serial_collision"
            } else
            "medium" if review_type in {"unique_serial_name_review","same_brand_multi_record_bundle_or_reuse"} else
            "low"
          ),
          "processor_version":VERSION
        })

    args.promoted_output.parent.mkdir(parents=True,exist_ok=True)
    with args.promoted_output.open("w",encoding="utf-8") as f:
        for x in promoted:f.write(json.dumps(x,ensure_ascii=False)+"\n")
    with args.review_output.open("w",encoding="utf-8") as f:
        for x in review:f.write(json.dumps(x,ensure_ascii=False)+"\n")
    summary={
      "schema":"user-release-herobloks-review-summary/v1",
      "processor_version":VERSION,
      "promoted_records":len(promoted),
      "review_records":len(review),
      "review_type_counts":dict(counts),
      "high_priority_review_records":sum(x["review_priority"]=="high" for x in review),
      "medium_priority_review_records":sum(x["review_priority"]=="medium" for x in review),
      "low_priority_review_records":sum(x["review_priority"]=="low" for x in review),
      "status":"catalog_release_promotion_and_review_layers_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
