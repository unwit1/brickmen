#!/usr/bin/env python3
"""Build a compact ranked semantic-review queue from Fortnite->LEGO visual measurements.

Signals are prioritization hints, not semantic ground truth.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path

VERSION="fortnite-semantic-review-queue/v1"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:yield json.loads(line)

def mag(value):
    try:return abs(float(value))
    except (TypeError,ValueError):return 0.0

def region_signals(name,d):
    if not isinstance(d,dict):return []
    out=[]
    er=d.get("edge_density_ratio_lego_to_source")
    pd=d.get("effective_palette_delta_lego_minus_source")
    occ=d.get("foreground_occupancy_delta")
    if er is not None:
        if er<0.70:out.append({"signal":"substantial_edge_reduction","region":name,"value":er})
        elif er<0.85:out.append({"signal":"moderate_edge_reduction","region":name,"value":er})
        elif er>1.25:out.append({"signal":"edge_increase","region":name,"value":er})
    if pd is not None:
        if pd<=-2:out.append({"signal":"palette_reduction","region":name,"value":pd})
        elif pd>=2:out.append({"signal":"palette_increase","region":name,"value":pd})
    if occ is not None and abs(occ)>=0.12:
        out.append({"signal":"silhouette_or_occupancy_change","region":name,"value":occ})
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--features",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()
    rows=[]
    direct=alias=missing=0
    for rec in load_jsonl(args.features):
        if rec.get("status")!="complete":
            if rec.get("status")=="missing_preferred_image":missing+=1
            continue
        resolution=rec.get("lego_image_resolution") or "direct_pair"
        direct += resolution=="direct_pair"
        alias += resolution=="alias_fallback"
        diff=rec.get("difference") or {}
        signals=[]
        # Newer extractor stores per-region deltas in regional_differences.
        regional=diff.get("regional_differences") or {}
        for region,rd in regional.items():
            signals.extend(region_signals(region,rd))
        # Retain global signals as review context.
        hs=diff.get("heuristic_signals") or {}
        for k,v in hs.items():
            if v:signals.append({"signal":k,"region":"global","value":True})
        score=0.0
        for s in signals:
            if s["signal"]=="substantial_edge_reduction":score+=3
            elif s["signal"] in {"palette_reduction","silhouette_or_occupancy_change"}:score+=2
            else:score+=1
        # Favor records with several independent regional cues.
        score += len({s["region"] for s in signals if s["region"]!="global"})*0.5
        rows.append({
          "translation_pair_id":rec.get("translation_pair_id"),
          "source_image_url":rec.get("source_image_url"),
          "lego_image_url":rec.get("lego_image_url"),
          "lego_image_resolution":resolution,
          "lego_alias_fallback":rec.get("lego_alias_fallback"),
          "review_priority_score":round(score,2),
          "measurement_signals":signals,
          "requested_semantic_labels":{
            "regions":["head","torso","lower_body","accessory_or_silhouette"],
            "label_space":["preserved","simplified","omitted","exaggerated","moved_to_mould","moved_to_accessory","moved_to_cloth","color_block_changed","not_applicable","uncertain"]
          },
          "review_status":"pending",
          "policy":"Measurement signals only prioritize review. They must not be treated as preserve/simplify/omit/mould/accessory ground truth.",
          "processor_version":VERSION
        })
    rows.sort(key=lambda x:(-x["review_priority_score"],x["translation_pair_id"] or ""))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"fortnite-semantic-review-queue-summary/v1",
      "processor_version":VERSION,
      "complete_feature_records":len(rows),
      "direct_image_records":direct,
      "alias_fallback_records":alias,
      "missing_image_records":missing,
      "records_with_measurement_signals":sum(bool(r["measurement_signals"]) for r in rows),
      "high_priority_records":sum(r["review_priority_score"]>=6 for r in rows),
      "status":"semantic_review_queue_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
