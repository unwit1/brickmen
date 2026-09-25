#!/usr/bin/env python3
"""Build a weak semantic corpus of decorated minifigure heads from Rebrickable metadata.

Catalog part names provide useful descriptive supervision (grin, glasses, beard, scar,
etc.) but are not human-rated emotion ground truth. This tool preserves that distinction.
"""
from __future__ import annotations
import argparse, json, re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION="decorated-head-semantic-corpus/v1"

FEATURES={
    "smile":("smile","smiling"),
    "grin":("grin","grinning"),
    "frown":("frown","frowning"),
    "angry":("angry","anger","snarl","scowl"),
    "scared":("scared","fear","fright"),
    "surprised":("surprised","surprise","shocked"),
    "open_mouth":("open mouth","open-mouth"),
    "teeth":("teeth","tooth"),
    "tongue":("tongue",),
    "eyebrows":("eyebrow","eyebrows"),
    "eyelashes":("eyelash","eyelashes"),
    "glasses":("glasses","spectacles"),
    "sunglasses":("sunglasses",),
    "goggles":("goggles",),
    "beard":("beard",),
    "moustache":("moustache","mustache"),
    "stubble":("stubble",),
    "freckles":("freckle","freckles"),
    "scar":("scar","scars"),
    "wrinkles":("wrinkle","wrinkles"),
    "headset":("headset",),
    "eyepatch":("eyepatch","eye patch"),
    "makeup":("makeup","lipstick","eye shadow","eyeshadow"),
    "mask_print":("mask print","masked"),
}

def now_iso(): return datetime.now(timezone.utc).isoformat()
def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def tags(name):
    low=str(name or "").casefold()
    out=[]
    for tag,terms in FEATURES.items():
        if any(term in low for term in terms): out.append(tag)
    return out

def weak_expression(ts):
    s=set(ts)
    labels=[]
    if {"smile","grin"} & s: labels.append("happiness_candidate")
    if "frown" in s: labels.append("sadness_or_displeasure_candidate")
    if "angry" in s: labels.append("anger_candidate")
    if "scared" in s: labels.append("fear_candidate")
    if "surprised" in s: labels.append("surprise_candidate")
    return labels

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--samples",type=Path,required=True)
    ap.add_argument("--components",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    samples={s.get("fig_num"):s for s in load_jsonl(args.samples) if s.get("fig_num")}
    grouped=defaultdict(list)
    for c in load_jsonl(args.components):
        if c.get("component_role")=="head" and c.get("print_of"):
            grouped[c.get("part_num")].append(c)

    rows=[]; feature_counts=Counter(); expr_counts=Counter()
    for part_num,items in sorted(grouped.items()):
        names=Counter(str(x.get("part_name") or "") for x in items)
        canonical_name=names.most_common(1)[0][0] if names else ""
        ts=tags(canonical_name)
        for t in ts: feature_counts[t]+=1
        expr=weak_expression(ts)
        for e in expr: expr_counts[e]+=1
        figs=sorted({x.get("fig_num") for x in items if x.get("fig_num")})
        fig_records=[]
        themes=set();years=set();colors=set()
        for fig in figs:
            s=samples.get(fig) or {}
            fig_records.append({"fig_num":fig,"name":s.get("name")})
            for occ in s.get("set_occurrences") or []:
                if occ.get("year"):years.add(int(occ["year"]))
                for node in occ.get("theme_path") or []:
                    if node.get("name"):themes.add(node["name"])
        for x in items:
            if x.get("color_name"):colors.add(x["color_name"])
        low=canonical_name.casefold()
        alternate_expression=bool(
            re.search(r"(smile|grin|frown|angry|scared|surpris)[^/]{0,50}/[^/]{0,50}(smile|grin|frown|angry|scared|surpris)",low)
            or "dual sided" in low or "dual-sided" in low
        )
        rows.append({
            "part_num":part_num,
            "part_name":canonical_name,
            "print_of":items[0].get("print_of"),
            "catalog_semantic_tags":ts,
            "weak_expression_candidates":expr,
            "alternate_expression_or_dual_side_candidate":alternate_expression,
            "colors":sorted(colors),
            "figure_count":len(figs),
            "figures":fig_records[:100],
            "theme_names":sorted(themes),
            "observed_year_min":min(years) if years else None,
            "observed_year_max":max(years) if years else None,
            "provenance":{
                "source":"Rebrickable bulk component metadata",
                "component_ids":sorted({x.get("component_id") for x in items if x.get("component_id")})[:200]
            },
            "supervision_class":"weak_catalog_semantics",
            "policy":"Catalog descriptors support feature/search labels only. Do not treat weak expression candidates as human-rated emotion ground truth.",
            "processor_version":VERSION
        })

    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
        "schema":"decorated-head-semantic-corpus-summary/v1",
        "created_at":now_iso(),"processor_version":VERSION,
        "unique_decorated_head_parts":len(rows),
        "parts_with_semantic_tags":sum(bool(r["catalog_semantic_tags"]) for r in rows),
        "parts_with_weak_expression_candidates":sum(bool(r["weak_expression_candidates"]) for r in rows),
        "alternate_expression_or_dual_side_candidates":sum(r["alternate_expression_or_dual_side_candidate"] for r in rows),
        "feature_counts":dict(feature_counts.most_common()),
        "weak_expression_counts":dict(expr_counts.most_common()),
        "status":"weak_catalog_semantic_corpus_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
