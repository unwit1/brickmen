#!/usr/bin/env python3
"""Build a deterministic review queue from rioforce face SVG profile records."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

VERSION="face-landmark-review-queue/v1"
EMOTION_MAP={
    "happy":"happiness",
    "scared":"fear",
    "angry":"anger",
    "sad":"sadness",
}

def now_iso(): return datetime.now(timezone.utc).isoformat()

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def priority(rec):
    tokens=set(rec.get("filename_semantic_tokens") or [])
    score=0
    reasons=[]
    explicit=[EMOTION_MAP[t] for t in tokens if t in EMOTION_MAP]
    if explicit:
        score+=100
        reasons.append("explicit_filename_emotion")
    if rec.get("side_hint") in {"front","reverse"}:
        score+=30
        reasons.append("explicit_side_hint")
    n=int(rec.get("primitive_candidate_count") or 0)
    if n:
        score+=min(n,20)
        reasons.append("machine_readable_geometry")
    else:
        reasons.append("no_simple_primitive_candidates")
    path=(rec.get("relative_path") or "").casefold()
    if any(x in path for x in ("classics/","city/","lego minifigures/")):
        score+=10
        reasons.append("calibration_or_cmf_value")
    if any(x in path for x in ("star wars/","super heroes/","ninjago/")):
        score+=8
        reasons.append("licensed_or_longitudinal_theme_value")
    return score,reasons,explicit

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--profiles",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()
    rows=[]
    for rec in load_jsonl(args.profiles):
        score,reasons,explicit=priority(rec)
        rows.append({
            "face_asset_id":rec.get("face_asset_id"),
            "source_system":rec.get("source_system"),
            "relative_path":rec.get("relative_path"),
            "sha256":rec.get("sha256"),
            "side_hint":rec.get("side_hint"),
            "canvas":rec.get("canvas"),
            "primitive_candidate_count":rec.get("primitive_candidate_count"),
            "filename_semantic_tokens":rec.get("filename_semantic_tokens") or [],
            "weak_expression_labels_from_filename":explicit,
            "priority_score":score,
            "priority_reasons":reasons,
            "annotation_tasks":[
                "verify face region/orientation",
                "annotate left/right eye centers and bounds",
                "annotate brow paths/bounds when present",
                "annotate mouth path/bounds and mouth family",
                "annotate facial hair/eyewear/scars/freckles/wrinkles",
                "assign expression family only with reviewed evidence",
                "link front/reverse face relationship when applicable",
                "record era/theme/head color/catalog identity when resolved"
            ],
            "review_status":"pending",
            "semantic_policy":"Filename-derived emotion labels are weak supervision only. Geometry candidates are not semantic landmarks until reviewed."
        })
    rows.sort(key=lambda x:(-x["priority_score"],x["relative_path"] or ""))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
        "schema":"face-landmark-review-queue-summary/v1",
        "created_at":now_iso(),
        "processor_version":VERSION,
        "records":len(rows),
        "with_explicit_filename_emotion":sum(bool(r["weak_expression_labels_from_filename"]) for r in rows),
        "with_explicit_side_hint":sum(r["side_hint"] in {"front","reverse"} for r in rows),
        "with_machine_readable_geometry":sum((r["primitive_candidate_count"] or 0)>0 for r in rows),
        "without_simple_primitive_candidates":sum((r["primitive_candidate_count"] or 0)==0 for r in rows),
        "status":"review_queue_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
