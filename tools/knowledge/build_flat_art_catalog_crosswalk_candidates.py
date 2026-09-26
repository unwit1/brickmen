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

VERSION = "flat-art-catalog-crosswalk-candidates/v5"

STOP = {
    "lego","minifig","minifigure","with","and","the","a","an","pattern","printed",
    "print","logo","classic","figure","fig","face","head","torso","hips","hip","leg",
    "legs","arm","arms","helmet","hair","cowl","front","back","left","right","male",
    "female","guy","girl","man","woman","outfit",
    "black","white","red","blue","green","yellow","gray","grey","brown","tan",
    "orange","purple","pink","gold","silver",
}

ROLE_PATTERNS = (
    (r"\bface\b", "head"),
    (r"\bhead\b", "head"),
    (r"\btorso\b", "torso"),
    (r"\bhips?\b", "hips"),
    (r"\blegs?\b", "leg"),
    (r"\b(?:dress|skirt|robe)\b", "leg"),
    (r"\barms?\b", "arm"),
    (r"\b(?:helmet|cowl|hair|hood|mask|hat|cap|headgear)\b", "headgear"),
    (r"\bshield\b", "weapon_or_tool"),
)

SUBJECT_ALIASES = {
    "viking lady": "viking woman",
    "slithra": "slithraa",
}

ROLE_COMPATIBILITY = {
    "leg": {"leg", "hips"},
    "hips": {"hips", "leg"},
}


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
    for pattern,role in ROLE_PATTERNS:
        if re.search(pattern, low):
            return role
    return None


def role_matches(texture_role: str | None, component_role: str | None) -> bool:
    if not texture_role:
        return True
    allowed = ROLE_COMPATIBILITY.get(texture_role, {texture_role})
    return component_role in allowed


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


def normalize_subject_alias(value: str):
    key=re.sub(r"\s+"," ",str(value or "").strip().casefold())
    return SUBJECT_ALIASES.get(key, value)

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
        # Reward coverage of the source identity rather than raw overlap count.
        # This prevents a generic shared phrase from tying a variant-specific name.
        return min(0.88, 0.30 + 0.45 * ratio + 0.05 * len(overlap)), overlap
    only=overlap[0]
    if len(only) >= 7:
        return 0.42, overlap
    return 0.0, overlap


def years_in(value: str):
    return {
        int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", str(value or ""))
        if 1970 <= int(y) <= 2035
    }


def sample_years(sample):
    return {
        int(x.get("year")) for x in (sample.get("set_occurrences") or [])
        if x.get("year")
    }


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
    ap.add_argument("--min-figure-score-for-exact", type=float, default=0.9)
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
        asset_class=rio.get("asset_class") or "legacy_unclassified"
        role=rio.get("surface_role_hint") or infer_role(stem)
        subject=subject_text(stem)
        subject_alias=normalize_subject_alias(subject)
        subject_tokens=tok(subject_alias)
        subject_years=years_in(subject)
        subject_identity_tokens=[t for t in subject_tokens if not t.isdigit()]
        eligible_for_component_crosswalk = (
            asset_class in {"minifigure_surface_map","legacy_unclassified"}
            or role in {"head","torso","leg","hips","arm","headgear"}
        )
        fig_candidates=[]
        for fig_num, stoks in sample_tokens.items():
            if not eligible_for_component_crosswalk:
                break
            sample=physical_by_fig[fig_num]
            sample_identity_tokens=[t for t in stoks if not t.isdigit()]
            score, overlap=figure_match_score(subject_identity_tokens, sample_identity_tokens)
            if not score:
                continue
            sy=sample_years(sample)
            year_match=None
            if subject_years:
                year_match=bool(subject_years & sy)
                score += 0.10 if year_match else -0.10
                score=max(0.0,min(1.0,score))
            if not score:
                continue
            fig_candidates.append({
                "fig_num":fig_num,
                "name":sample.get("name"),
                "score":round(score,4),
                "overlap_tokens":overlap,
                "subject_years":sorted(subject_years),
                "catalog_years":sorted(sy),
                "year_match":year_match,
                "catalog_image_url":sample.get("catalog_image_url"),
                "bricklink_catalog_url":sample.get("bricklink_catalog_url"),
            })
        fig_candidates.sort(key=lambda x:(-x["score"],x["fig_num"]))
        fig_candidates=fig_candidates[:args.top_figures]

        part_candidates=[]
        id_exact_links_unverified=[]
        base_part_ldraw_links=[]
        exact_links=[]
        for fig in fig_candidates:
            for comp in components.get(fig["fig_num"],[]):
                if not role_matches(role, comp.get("component_role")):
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
                    raw_link={
                        **item,
                        "ldraw_reference_asset_id":ld.get("reference_asset_id"),
                        "ldraw_part_id":pid,
                        "ldraw_description":ld.get("description"),
                        "ldraw_source_path":ld.get("source_path"),
                        "ldraw_license":ld.get("license"),
                        "join_method":"exact_rebrickable_part_num_equals_ldraw_part_id",
                    }
                    # Plain substrate matches do not identify decoration artwork.
                    if comp.get("print_of"):
                        id_exact_links_unverified.append(raw_link)
                    else:
                        base_part_ldraw_links.append({
                            **raw_link,
                            "join_method":"base_substrate_exact_ldraw_join_not_print_art",
                        })
                    # Strict links require a decorated variant plus high-confidence
                    # figure and role evidence.
                    if (
                        role
                        and fig["score"] >= args.min_figure_score_for_exact
                        and role_matches(role, comp.get("component_role"))
                        and comp.get("print_of")
                    ):
                        exact_links.append({
                            **raw_link,
                            "join_method":"strict_catalog_role_print_exact_ldraw_join",
                            "strictness":{
                                "explicit_component_role":role,
                                "minimum_figure_match_score":args.min_figure_score_for_exact,
                                "decorated_component_required":True,
                            },
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

        unique_raw_exact={}
        for item in id_exact_links_unverified:
            key=(item.get("component_id"),item.get("ldraw_reference_asset_id"))
            unique_raw_exact[key]=item
        id_exact_links_unverified=list(unique_raw_exact.values())

        unique_base_exact={}
        for item in base_part_ldraw_links:
            key=(item.get("component_id"),item.get("ldraw_reference_asset_id"))
            unique_base_exact[key]=item
        base_part_ldraw_links=list(unique_base_exact.values())

        unique_exact={}
        for item in exact_links:
            key=(item.get("component_id"),item.get("ldraw_reference_asset_id"))
            unique_exact[key]=item
        exact_links=list(unique_exact.values())

        counts[f"asset_class_{asset_class}"]+=1
        if not eligible_for_component_crosswalk: counts["excluded_from_component_crosswalk"]+=1
        if fig_candidates: counts["with_figure_candidates"]+=1
        else: counts["without_figure_candidates"]+=1
        if part_candidates: counts["with_component_candidates"]+=1
        if id_exact_links_unverified: counts["with_id_exact_links_unverified"]+=1
        if base_part_ldraw_links: counts["with_base_part_ldraw_links"]+=1
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
            "asset_class":asset_class,
            "eligible_for_component_crosswalk":eligible_for_component_crosswalk,
            "subject_text":subject,
            "subject_alias_applied":subject_alias if subject_alias != subject else None,
            "subject_tokens":subject_tokens,
            "subject_years":sorted(subject_years),
            "inferred_component_role":role,
            "figure_candidates":fig_candidates,
            "component_candidates":part_candidates,
            "id_exact_links_unverified":id_exact_links_unverified,
            "base_part_ldraw_links":base_part_ldraw_links,
            "exact_ldraw_links":exact_links,
            "review_status":(
                "candidate_review_required"
                if eligible_for_component_crosswalk
                else "non_component_supervision_classified"
            ),
            "promotion_policy":(
                "Plain substrate LDraw joins are tracked separately and are never treated as print-art evidence. Decorated part-number joins remain discovery evidence only; strict exact links additionally require explicit component role, high-confidence figure match, and a decorated component print-of relationship. Independent confirmation is still required before canonical promotion."
                if eligible_for_component_crosswalk
                else "Motif, non-minifigure, and unscoped design assets remain usable supervision but must not be promoted as exact minifigure component maps without independent evidence."
            ),
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
        "min_figure_score_for_exact":args.min_figure_score_for_exact,
        **dict(counts),
        "status":"candidate_only_requires_independent_confirmation",
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
