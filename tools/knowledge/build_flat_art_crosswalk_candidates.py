#!/usr/bin/env python3
"""Build reviewable rioforce -> LDraw flat-art crosswalk candidates.

This script deliberately produces *candidates*, not canonical links. rioforce assets are
named descriptively while LDraw patterned parts generally use part IDs plus descriptions,
so token/component similarity is useful for narrowing review but insufficient for silent
promotion to canonical identity.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

VERSION = "flat-art-crosswalk-candidates/v1"

STOP = {
    "lego", "minifig", "minifigure", "with", "and", "the", "a", "an", "pattern",
    "printed", "print", "logo", "classic", "figure", "fig", "left", "right",
}

COMPONENT_HINTS = (
    ("face", "head"),
    ("head", "head"),
    ("torso", "torso"),
    ("hips", "hips"),
    ("hip", "hips"),
    ("legs", "leg"),
    ("leg", "leg"),
    ("arm", "arm"),
    ("helmet", "helmet"),
    ("cowl", "cowl"),
    ("hair", "hair"),
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def tokens(value: str) -> set[str]:
    parts = re.findall(r"[a-z0-9]+", str(value or "").casefold())
    return {p for p in parts if p not in STOP and len(p) > 1}


def infer_rioforce_component(stem: str) -> str | None:
    low = stem.casefold()
    for needle, component in COMPONENT_HINTS:
        if needle in low:
            return component
    return None


def ldraw_part_id(record: dict) -> str | None:
    candidates = [
        record.get("ldraw_name"),
        record.get("source_path"),
    ]
    for value in candidates:
        if not value:
            continue
        m = re.search(r"([0-9][0-9a-z_-]*)\.dat(?:$|\s)", str(value), re.I)
        if m:
            return m.group(1)
        m = re.search(r"/([0-9][0-9a-z_-]*)\.dat$", str(value), re.I)
        if m:
            return m.group(1)
    return None


def similarity(a: set[str], b: set[str]) -> tuple[float, list[str]]:
    if not a or not b:
        return 0.0, []
    overlap = sorted(a & b)
    if not overlap:
        return 0.0, []
    union = a | b
    score = len(overlap) / max(1, len(union))
    # Character/person tokens are highly informative in this corpus. Give a modest boost
    # when at least two descriptive tokens agree.
    if len(overlap) >= 2:
        score += 0.15
    elif len(overlap) == 1 and len(next(iter(overlap))) >= 6:
        score += 0.05
    return min(score, 1.0), overlap


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rioforce-index", type=Path, required=True)
    ap.add_argument("--ldraw-index", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--min-score", type=float, default=0.18)
    args = ap.parse_args()

    ldraw = list(load_jsonl(args.ldraw_index))
    by_component: dict[str, list[tuple[dict, set[str]]]] = {}
    for rec in ldraw:
        component = rec.get("component_type") or "other_minifig"
        desc_tokens = tokens(
            " ".join(
                str(x or "")
                for x in (
                    rec.get("description"),
                    rec.get("ldraw_name"),
                    " ".join(rec.get("keywords") or []),
                )
            )
        )
        by_component.setdefault(component, []).append((rec, desc_tokens))

    rows = []
    resolvedish = 0
    no_candidates = 0
    component_counts = Counter()
    score_bands = Counter()

    for rio in load_jsonl(args.rioforce_index):
        stem = rio.get("relative_stem") or ""
        component = infer_rioforce_component(stem)
        component_counts[component or "unknown"] += 1
        rio_tokens = tokens(stem.replace("/", " "))

        pool = by_component.get(component, []) if component else []
        if not pool:
            pool = [
                item
                for comp, items in by_component.items()
                if comp not in {"other_minifig"}
                for item in items
            ]

        ranked = []
        for rec, rec_tokens in pool:
            score, overlap = similarity(rio_tokens, rec_tokens)
            if component and rec.get("component_type") == component:
                score = min(1.0, score + 0.12)
            if score < args.min_score:
                continue
            ranked.append(
                {
                    "ldraw_reference_asset_id": rec.get("reference_asset_id"),
                    "ldraw_part_id": ldraw_part_id(rec),
                    "ldraw_description": rec.get("description"),
                    "ldraw_source_path": rec.get("source_path"),
                    "component_type": rec.get("component_type"),
                    "score": round(score, 4),
                    "overlap_tokens": overlap,
                    "license": rec.get("license"),
                }
            )

        ranked.sort(key=lambda x: (-x["score"], x.get("ldraw_source_path") or ""))
        ranked = ranked[: args.top_k]

        if ranked:
            resolvedish += 1
            top = ranked[0]["score"]
            score_bands[
                "high" if top >= 0.7 else "medium" if top >= 0.45 else "low"
            ] += 1
        else:
            no_candidates += 1

        rows.append(
            {
                "crosswalk_candidate_id": rio.get("asset_group_id"),
                "rioforce": {
                    "asset_group_id": rio.get("asset_group_id"),
                    "relative_stem": stem,
                    "category": rio.get("category"),
                    "files": rio.get("files"),
                    "license": rio.get("license"),
                    "authority": rio.get("authority"),
                },
                "inferred_component_type": component,
                "candidate_ldraw_matches": ranked,
                "review_status": (
                    "candidate_review_required" if ranked else "unresolved_no_candidate"
                ),
                "promotion_policy": (
                    "Do not promote to canonical component ID without independent "
                    "catalog/component evidence."
                ),
                "processor_version": VERSION,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "schema": "flat-art-crosswalk-candidate-summary/v1",
        "created_at": now_iso(),
        "processor_version": VERSION,
        "rioforce_records": len(rows),
        "ldraw_records": len(ldraw),
        "records_with_candidates": resolvedish,
        "records_without_candidates": no_candidates,
        "component_counts": dict(component_counts),
        "top_candidate_score_bands": dict(score_bands),
        "min_score": args.min_score,
        "top_k": args.top_k,
        "status": "candidate_only_requires_independent_confirmation",
    }
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
