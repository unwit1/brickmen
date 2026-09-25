#!/usr/bin/env python3
"""Build evidence-backed rioforce flat-art crosswalk candidates via Rebrickable census.

Unlike filename-only fuzzy matching, this stage first resolves a likely figure identity
against the current Rebrickable physical census, then restricts candidate parts to that
figure's actual component inventory and matching component role. Exact LDraw joins are
only emitted when a Rebrickable part number exactly matches an indexed LDraw part ID.

Everything remains candidate-level until independently confirmed.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION = "flat-art-catalog-crosswalk-candidates/v1"

STOP = {
    "lego","minifig","minifigure","with","and","the","a","an","pattern","printed",
    "print","logo","classic","figure","fig","face","head","torso","hips","hip","leg",
    "legs","arm","arms","helmet","hair","cowl","front","back","left","right","male",
    "female","guy","girl","man","woman",
}

ROLE_HINTS = (
    ("face", "head"), ("head", "head"), ("torso", "torso"), ("hips", "hips"),
    ("hip", "hips"), ("legs", "leg"), ("leg", "leg"), ("arm", "arm"),
    ("helmet", "headgear"), ("cowl", "headgear"), ("hair", "headgear"),
)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line=line.strip()
            if line:
                yield json.loads(line)


def tok(value: str):
    return [
        p for p in re.findall(r"[a-z0-9]+", str(value or "").casefold())
        if len(p) > 1 and p not in STOP
    ]


def infer_role(stem: str):
    low=stem.casefold()
    for needle,role in ROLE_HINTS:
        if needle in low:
            return role
    return None


def subject_text(stem: str):
    parts=Path(stem).parts
    # Nested repositories commonly use Theme / Character / Asset Name.
    if len(parts) >= 3:
        return parts[-2]
    leaf=parts[-1] if parts else stem
    cleaned=re.sub(
        r"\b(face|head|torso|hips?|legs?|arms?|helmet|hair|cowl|front|back)\b",
        " ", leaf, flags=re.I
    )
    return re.sub(r"\s+", " ", cleaned).strip()


def figure_match_score(subject_tokens, sample_tokens):
    if not subject_tokens or not sample_tokens:
        return 0.0, []
    s=set(subject_tokens); t=set(sample_tokens); overlap=sorted(s & t)
    if not overlap:
        return 0.0, []
    if s <= t:
        return min(1.0, 0.72 + 0.07 * len(s)), overlap
    ratio=len(overlap)/len(s)
    if len(overlap) >= 2:
        return min(0.9, 0.45 + 0.12 * len(overlap) + 0.15 * ratio), overlap
    only=overlap[0]
    if len(only) >= 7:
        return 0.42, overlap
    return 0.0, overlap


def ldraw_id(record):
    path=str(record.get("source_path") or "")
    name=str(record.get("ldraw_name") or "")
    for value in (path,name):
        m=re.search(r"(?:^|/)([0-9][0-9a-z_-]*)\.dat$", value, re.I)
        if m:
            return m.group(1).casefold()
    return None


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--rioforce-index", type=Path, required=True)
    ap.add_argument("--physical-samples", type=Path, required=True)
    ap.add_argument("--component-samples", type=Path, required=True)
    ap.add_argument("--ldraw-index", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    ap.add_argument("--top-figures", type=int, default=8)
    args=ap.parse_args()

    physical=list(load_jsonl(args.physical_samples))
    sample_tokens={
        r.get("fig_num"): tok(r.get("name") or "")
        for r in physical
        if r.get("fig_num")
    }
    physical_by_fig={r.get("fig_num"):r for r in physical if r.get("fig_num")}

    components=defaultdict(list)
    for r in load_jsonl(args.component_samples):
        if r.get("fig_num"):
            components[r["fig_num"]].append(r)

    ldraw_exact=defaultdict(list)
    for r in load_jsonl(args.ldraw_index):
        pid=ldraw_id(r)
        if pid:
            ldraw_exact[pid].append(r)

    rows=[]
    counts=Counter()
    for rio in load_jsonl(args.rioforce_index):
        stem=rio.get("relative_stem") or ""
        role=infer_role(stem)
        subject=subject_text(stem)
        subject_tokens=tok(subject)
        fig_candidates=[]
        for fig_num, stoks in sample_tokens.items():
            score, overlap=figure_match_score(subject_tokens, stoks)
            if not score:
                continue
            sample=physical_by_fig[fig_num]
            fig_candidates.append({
                "fig_num":fig_num,
                "name":sample.get("name"),
                "score":round(score,4),
                "overlap_tokens":overlap,
                "catalog_image_url":sample.get("catalog_image_url"),
                "bricklink_catalog_url":sample.get("bricklink_catalog_url"),
            })
        fig_candidates.sort(key=lambda x:(-x["score"],x["fig_num"]))
        fig_candidates=fig_candidates[:args.top_figures]

        part_candidates=[]
        exact_links=[]
        for fig in fig_candidates:
            for comp in components.get(fig["fig_num"],[]):
                if role and comp.get("component_role") != role:
                    continue
                item={
                    "fig_num":fig["fig_num"],
                    "figure_name":fig["name"],
                    "figure_match_score":fig["score"],
                    "component_id":comp.get("component_id"),
                    "part_num":comp.get("part_num"),
                    "part_name":comp.get("part_name"),
                    "component_role":comp.get("component_role"),
                    "color_id":comp.get("color_id"),
                    "color_name":comp.get("color_name"),
                    "image_url":comp.get("image_url"),
                    "print_of":comp.get("print_of"),
                }
                part_candidates.append(item)
                pid=str(comp.get("part_num") or "").casefold()
                for ld in ldraw_exact.get(pid,[]):
                    exact_links.append({
                        **item,
                        "ldraw_reference_asset_id":ld.get("reference_asset_id"),
                        "ldraw_part_id":pid,
                        "ldraw_description":ld.get("description"),
                        "ldraw_source_path":ld.get("source_path"),
                        "ldraw_license":ld.get("license"),
                        "join_method":"exact_rebrickable_part_num_equals_ldraw_part_id",
                    })

        # Deduplicate components reached through multiple figure candidates.
        unique_parts={}
        for item in part_candidates:
            key=(item.get("component_id"),item.get("part_num"),item.get("color_id"))
            prev=unique_parts.get(key)
            if prev is None or item["figure_match_score"] > prev["figure_match_score"]:
                unique_parts[key]=item
        part_candidates=sorted(
            unique_parts.values(),
            key=lambda x:(-x["figure_match_score"],x.get("part_num") or "")
        )[:30]

        unique_exact={}
        for item in exact_links:
            key=(item.get("component_id"),item.get("ldraw_reference_asset_id"))
            unique_exact[key]=item
        exact_links=list(unique_exact.values())

        if fig_candidates: counts["with_figure_candidates"]+=1
        else: counts["without_figure_candidates"]+=1
        if part_candidates: counts["with_component_candidates"]+=1
        if exact_links: counts["with_exact_ldraw_links"]+=1
        if fig_candidates and fig_candidates[0]["score"] >= 0.9: counts["top_figure_high_confidence"]+=1

        rows.append({
            "crosswalk_candidate_id":rio.get("asset_group_id"),
            "rioforce":{
                "asset_group_id":rio.get("asset_group_id"),
                "relative_stem":stem,
                "category":rio.get("category"),
                "files":rio.get("files"),
                "authority":rio.get("authority"),
                "license":rio.get("license"),
            },
            "subject_text":subject,
            "subject_tokens":subject_tokens,
            "inferred_component_role":role,
            "figure_candidates":fig_candidates,
            "component_candidates":part_candidates,
            "exact_ldraw_links":exact_links,
            "review_status":"candidate_review_required",
            "promotion_policy":"Independent confirmation required; exact ID joins improve evidence but do not prove rioforce asset identity.",
            "processor_version":VERSION,
        })

    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row,ensure_ascii=False)+"\n")

    summary={
        "schema":"flat-art-catalog-crosswalk-candidate-summary/v1",
        "created_at":now_iso(),
        "processor_version":VERSION,
        "rioforce_records":len(rows),
        "physical_samples_indexed":len(physical),
        "component_records_indexed":sum(len(v) for v in components.values()),
        "ldraw_exact_ids_indexed":len(ldraw_exact),
        **dict(counts),
        "status":"candidate_only_requires_independent_confirmation",
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
