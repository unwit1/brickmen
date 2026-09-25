#!/usr/bin/env python3
"""Reconcile Brickmen user collection/design-target JSONL sources into candidate entity groups.

This is deliberately a candidate/retrieval layer, not an automatic canonical merge.
It preserves source-specific identities, variants, universes, ownership states and codes.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION = "user-tracker-reconciliation/v1"

GENERATED_COLLECTION_FILES = {
    "product-code-brand-candidates-2026-09-25.jsonl",
}

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)

def norm(value) -> str:
    s = unicodedata.normalize("NFKD", str(value or ""))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).casefold()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())

def is_maker_code(value):
    s = str(value or "").strip()
    return bool(re.match(r"^[A-Za-z]{1,10}(?:[-_]?\d+)[A-Za-z0-9_-]*$", s))

def uniq(values):
    return sorted({str(v).strip() for v in values if v is not None and str(v).strip()})

def source_name(rec):
    return (
        rec.get("name")
        or rec.get("character")
        or rec.get("character_or_product_name")
        or rec.get("name_or_note")
    )

def classify_record(rec, source_path):
    return rec.get("record_class") or rec.get("provenance_class") or (
        "design_target" if "user-design-targets" in source_path.as_posix() else "collection_record"
    )

def canonical_source_stub(rec, source_path):
    return {
        "source_file": source_path.name,
        "source_title": rec.get("source_title"),
        "source_tab": rec.get("source_tab"),
        "source_row": rec.get("source_row"),
        "record_class": classify_record(rec, source_path),
        "name": source_name(rec),
        "identity": rec.get("identity"),
        "variant": rec.get("variant"),
        "universe": rec.get("universe"),
        "first_appearance": rec.get("first_appearance"),
        "year": rec.get("year"),
        "category": rec.get("category") or rec.get("category_or_franchise"),
        "subcategory": rec.get("subcategory"),
        "collection": rec.get("collection") or rec.get("group"),
        "product_code": rec.get("product_code") or rec.get("bricklink_minifigure_id"),
        "product_code_namespace": (
            "maker_product_code"
            if rec.get("product_code") and is_maker_code(rec.get("product_code"))
            else "unstructured_source_code_text"
            if rec.get("product_code")
            else "bricklink_minifigure_id"
            if rec.get("bricklink_minifigure_id")
            else None
        ),
        "have": rec.get("have"),
        "ownership_status": rec.get("ownership_status"),
        "preferred": rec.get("preferred") or rec.get("best_representation"),
        "official": rec.get("official"),
        "bootleg": rec.get("bootleg"),
    }


def raw_cell_map(rec):
    return {str(x.get("column")): x.get("value") for x in (rec.get("nonempty_cells") or []) if x.get("column")}

def dc_normalized_record(rec):
    """Normalize one row from the lossless standalone DC workbook archive.

    Rules are tab-specific and intentionally conservative. The raw archive remains canonical
    source evidence; this derived layer exists for reconciliation/search only.
    """
    tab = rec.get("source_tab")
    c = raw_cell_map(rec)
    up = {k: str(v or "").strip() for k, v in c.items()}
    header_tokens = {"HAVE","HAVE?","BEST","NAME","COLLECTION","ERA","YEAR","NUMBER","BRAND","IN COLLECTION?","LEGO ID","CLONE S/N"}
    if rec.get("row_class") == "header_or_schema_hint":
        return None
    if sum(str(v).strip().upper() in header_tokens for v in up.values()) >= 2:
        return None

    field = {
        "source_system": "user_google_sheet",
        "source_title": "DC",
        "source_tab": tab,
        "source_row": rec.get("source_row"),
        "source_last_modified": rec.get("source_last_modified"),
        "record_class": "collection_target",
        "canonical_resolution_status": "pending",
        "derived_from": "dc-legacy-workbook-raw-2026-09-25.jsonl",
        "ingestion_date": "2026-09-25",
    }

    # Stable observed schemas.
    if tab == "Justice League":
        field.update(ownership_status=up.get("A") or None, best_representation=up.get("B") or None,
                     name=up.get("C") or None, era=up.get("D") or None, year=up.get("E") or None,
                     collection=up.get("F") or None)
    elif tab in {"Silver Age Misc", "Doom Patrol", "Suicide Squad", "Copy of Titans Collection", "Copy of DC Villains"}:
        field.update(ownership_status=up.get("A") or None, best_representation=up.get("B") or None,
                     name=up.get("C") or None, era=up.get("E") or None,
                     year=up.get("F") or None if tab == "Silver Age Misc" else None,
                     collection=(up.get("G") or up.get("F")) or None)
    elif tab == "Copy of Justice Society":
        field.update(best_representation=up.get("A") or None, ownership_status=up.get("B") or None,
                     name=up.get("C") or None, identity=up.get("D") or None, era=up.get("E") or None,
                     collection=up.get("G") or None, product_code=up.get("H") or None,
                     parts_needed=up.get("J") or None)
    elif tab == "Copy of Copy of DC - AQUAMAN":
        field.update(name=up.get("C") or None, collection=up.get("G") or None)
    elif tab == "Copy of New 52-Rebirth":
        field.update(ownership_status=up.get("A") or None, name=up.get("B") or None,
                     collection=up.get("E") or None)
    elif tab in {"Copy of Post-Crisis-Flashpoint", "Copy of Justice League"}:
        field.update(name=up.get("A") or None, collection=up.get("D") or None)
    elif tab == "Copy of Justice Society 1":
        field.update(collection=up.get("A") or None, name=up.get("B") or None,
                     reference_image=up.get("C") or None, best_representation=up.get("D") or None,
                     ownership_status=up.get("E") or None, era=up.get("F") or None,
                     parts_needed=up.get("G") or None)
    elif tab in {"Copy of Superman Collection", "Copy of Green Arrow Collection"}:
        field.update(ownership_status=up.get("A") or None, best_representation=up.get("B") or None,
                     name=up.get("C") or None, collection=up.get("D") or None)
    elif tab == "Copy of DC - BATMAN":
        field.update(section_context=up.get("A") or None, ownership_status=up.get("B") or None,
                     best_representation=up.get("C") or None, name=up.get("D") or None,
                     era=up.get("E") or None, lego_id=up.get("F") or None,
                     product_code=up.get("G") or None)
    elif tab == "Copy of DC - Nightwing":
        field.update(name=up.get("C") or None)
    elif tab == "Copy of Titans 1":
        field.update(ownership_status=up.get("A") or None, best_representation=up.get("B") or None,
                     name=up.get("C") or None, collection=up.get("F") or None)
    elif tab == "Copy of DC 1":
        # The copied header is stale/misaligned and rows use D/E/F inconsistently for
        # brand, collection and serial. Resolve by value shape while preserving raw cells.
        candidates = [(col, up.get(col)) for col in ("D","E","F") if up.get(col)]
        serial = next(((col, val) for col, val in candidates if is_maker_code(val)), (None, None))
        brand_text = up.get("D") if up.get("D") and not is_maker_code(up.get("D")) else None
        collection_text = next(
            (val for col, val in candidates if (col, val) != serial and val != brand_text),
            None
        )
        raw_code = serial[1]
        normalized_code = raw_code
        correction = None
        if raw_code == "X1880" and "catwoman" in norm(up.get("C")):
            normalized_code = "XH1880"
            correction = {
                "raw": "X1880",
                "normalized": "XH1880",
                "reason": "adjacent Xinh XH1879/XH1881 wave plus independent catalog confirmation for Catwoman/Selina Kyle XH1880",
                "evidence_sources": ["HeroBloks","Brixtoy","DownTheBlocks"]
            }
        elif raw_code == "X1881" and "batman" in norm(up.get("C")):
            normalized_code = "XH1881"
            correction = {
                "raw": "X1881",
                "normalized": "XH1881",
                "reason": "independent HeroBloks catalog confirmation for Xinh XH1881 Batman (Tim Burton/Michael Keaton)",
                "evidence_sources": ["HeroBloks"]
            }
        field.update(
            ownership_status=up.get("A") or None,
            name=up.get("C") or None,
            brand_explicit=brand_text,
            product_code=normalized_code,
            collection=collection_text,
            source_product_code_raw=raw_code if correction else None,
            product_code_correction=correction,
            schema_warning="stale_or_misaligned_header_observed"
        )
    else:
        return None

    if not field.get("name"):
        return None
    field["raw_cells"] = rec.get("nonempty_cells") or []
    field["normalization_policy"] = "Tab-specific extraction from lossless raw archive; ambiguous semantics remain raw fields or warnings."
    return field

def load_crosswalk(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    prefix_map = defaultdict(list)
    name_alias_map = defaultdict(list)
    for fam in data.get("families") or []:
        brand = fam.get("brand")
        entry = {
            "brand": brand,
            "confidence": fam.get("confidence"),
            "relationship_note": fam.get("notes"),
        }
        for prefix in fam.get("observed_product_prefixes") or []:
            prefix_map[str(prefix).upper()].append(entry)
        for alias in [brand, *(fam.get("aliases") or [])]:
            if alias:
                key = norm(alias)
                existing = name_alias_map[key]
                if not any(x.get("brand") == brand for x in existing):
                    existing.append(entry)
    return data, prefix_map, name_alias_map

def code_prefix(code):
    m = re.match(r"^([A-Za-z]+)", str(code or "").strip())
    return m.group(1).upper() if m else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection-dir", type=Path, required=True)
    ap.add_argument("--design-dir", type=Path, required=True)
    ap.add_argument("--crosswalk", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _, prefix_map, alias_map = load_crosswalk(args.crosswalk)

    input_files = []
    records = []
    external_catalog_records = []
    dc_normalized = []
    for root in (args.collection_dir, args.design_dir):
        for path in sorted(root.glob("*.jsonl")):
            if path.name in GENERATED_COLLECTION_FILES:
                continue
            input_files.append(path)
            for rec in load_jsonl(path):
                if rec.get("bricklink_minifigure_id"):
                    external_catalog_records.append({
                        "catalog_namespace":"bricklink_minifigure_id",
                        "catalog_id":str(rec.get("bricklink_minifigure_id")).lower(),
                        "source_file":path.name,
                        "source_title":rec.get("source_title"),
                        "source_tab":rec.get("source_tab"),
                        "source_row":rec.get("source_row"),
                        "record_class":classify_record(rec,path),
                        "name_or_note":source_name(rec),
                        "catalog_url":rec.get("bricklink_catalog_url"),
                        "raw_values":rec.get("raw_values"),
                        "resolution_status":"catalog_id_observed_needs_official_crosswalk",
                        "policy":"External catalog identity is preserved even when the tracker row has no human-readable name. Cross-namespace mapping requires verified evidence.",
                        "processor_version":VERSION,
                    })
                if path.name == "dc-legacy-workbook-raw-2026-09-25.jsonl":
                    derived = dc_normalized_record(rec)
                    if derived:
                        dc_normalized.append(derived)
                        name = source_name(derived)
                        key = norm(name)
                        if key:
                            records.append({
                                "normalized_name": key,
                                **canonical_source_stub(derived, path),
                            })
                    continue
                name = source_name(rec)
                if not name:
                    continue
                key = norm(name)
                if not key:
                    continue
                records.append({
                    "normalized_name": key,
                    **canonical_source_stub(rec, path),
                })

    # Candidate character/name groups.
    groups = defaultdict(list)
    for rec in records:
        groups[rec["normalized_name"]].append(rec)

    group_rows = []
    for key, items in groups.items():
        sources = uniq(x.get("source_file") for x in items)
        identities = uniq(x.get("identity") for x in items)
        variants = uniq(x.get("variant") for x in items)
        universes = uniq(x.get("universe") for x in items)
        ambiguity = []
        if len(identities) > 1:
            ambiguity.append("multiple_identities")
        if len(universes) > 1:
            ambiguity.append("multiple_universes")
        if len(variants) > 8:
            ambiguity.append("many_variants")
        group_rows.append({
            "character_group_candidate_id": "user-name-" + re.sub(r"\s+", "-", key)[:100],
            "normalized_name": key,
            "observed_names": uniq(x.get("name") for x in items),
            "record_count": len(items),
            "source_file_count": len(sources),
            "source_files": sources,
            "record_classes": uniq(x.get("record_class") for x in items),
            "identities": identities,
            "variants": variants,
            "universes": universes,
            "product_codes": uniq(x.get("product_code") for x in items),
            "first_appearances": uniq(x.get("first_appearance") for x in items),
            "years": uniq(x.get("year") for x in items),
            "categories": uniq(x.get("category") for x in items),
            "collections": uniq(x.get("collection") for x in items),
            "cross_source_candidate": len(sources) > 1,
            "ambiguity_flags": ambiguity,
            "resolution_status": "cross_source_character_candidate" if len(sources) > 1 else "single_source_name_group",
            "sample_records": items[:20],
            "policy": "Name grouping is a retrieval/dedup candidate only. Distinct identities, universes, source appearances and variants remain separate until reconciled.",
            "processor_version": VERSION,
        })
    group_rows.sort(key=lambda x: (-int(x["cross_source_candidate"]), -x["record_count"], x["normalized_name"]))

    # Strict name+identity+variant groups are safer duplicate candidates.
    strict = defaultdict(list)
    for rec in records:
        strict_key = "|".join([
            rec["normalized_name"],
            norm(rec.get("identity")),
            norm(rec.get("variant")),
            norm(rec.get("universe")),
        ])
        strict[strict_key].append(rec)
    strict_rows = []
    for key, items in strict.items():
        source_files = uniq(x.get("source_file") for x in items)
        if len(items) < 2:
            continue
        strict_rows.append({
            "strict_group_key": key,
            "record_count": len(items),
            "source_file_count": len(source_files),
            "source_files": source_files,
            "records": items[:50],
            "cross_source_duplicate_candidate": len(source_files) > 1,
            "policy": "Exact normalized name+identity+variant+universe grouping is a strong duplicate candidate, not automatic canonical identity.",
            "processor_version": VERSION,
        })
    strict_rows.sort(key=lambda x: (-int(x["cross_source_duplicate_candidate"]), -x["record_count"], x["strict_group_key"]))

    # Product-code -> brand candidates using both observed prefixes and exact brand/alias tokens.
    code_rows = []
    for rec in records:
        code = rec.get("product_code")
        if not code:
            continue
        namespace = rec.get("product_code_namespace") or "maker_product_code"
        prefix = code_prefix(code)
        candidates = []
        method = None
        if namespace == "maker_product_code":
            candidates = list(prefix_map.get(prefix or "", []))
            method = "observed_product_prefix" if candidates else None
            if not candidates and prefix:
                candidates = list(alias_map.get(norm(prefix), []))
                method = "exact_brand_or_alias_token" if candidates else None
        code_rows.append({
            "source_record": {
                "source_file": rec.get("source_file"),
                "source_title": rec.get("source_title"),
                "source_tab": rec.get("source_tab"),
                "source_row": rec.get("source_row"),
            },
            "product_code": code,
            "product_code_namespace": namespace,
            "observed_prefix": prefix,
            "name": rec.get("name"),
            "variant": rec.get("variant"),
            "brand_candidates": candidates,
            "candidate_method": method,
            "resolution_status": (
                "external_catalog_id_observed"
                if namespace == "bricklink_minifigure_id"
                else "unstructured_source_code_text"
                if namespace == "unstructured_source_code_text"
                else "brand_candidate_single"
                if len(candidates) == 1
                else "brand_candidate_ambiguous"
                if len(candidates) > 1
                else "unresolved_prefix"
            ),
            "policy": "Prefix or exact brand-token evidence proposes a brand only; release identity, ownership/factory relationships and chronology require independent evidence.",
            "processor_version": VERSION,
        })

    # SourceAppearance candidates from explicit first-appearance metadata.
    appearance_groups = defaultdict(list)
    for rec in records:
        raw = str(rec.get("first_appearance") or "").strip()
        if not raw:
            continue
        normalized = " ".join(raw.split())
        issue_number = None
        source_work = None
        parse_status = "raw_only"
        m = re.match(r"^(.*?)(?:\s+Vol(?:\.|ume)?\s*\d+)?\s*#\s*([0-9]+(?:\.[0-9]+)?)\s*$", normalized, re.I)
        if m:
            source_work = m.group(1).strip(" -")
            issue_number = m.group(2)
            parse_status = "explicit_hash_issue"
        appearance_groups[norm(normalized)].append({
            "raw_first_appearance": raw,
            "source_work_candidate": source_work,
            "issue_number_candidate": issue_number,
            "parse_status": parse_status,
            "name": rec.get("name"),
            "identity": rec.get("identity"),
            "variant": rec.get("variant"),
            "universe": rec.get("universe"),
            "year": rec.get("year"),
            "source_file": rec.get("source_file"),
            "source_title": rec.get("source_title"),
            "source_tab": rec.get("source_tab"),
            "source_row": rec.get("source_row"),
        })
    appearance_rows = []
    for key, items in appearance_groups.items():
        parsed = [x for x in items if x["parse_status"] == "explicit_hash_issue"]
        appearance_rows.append({
            "source_appearance_candidate_id":"user-first-appearance-"+re.sub(r"[^a-z0-9]+","-",key)[:120].strip("-"),
            "normalized_first_appearance":key,
            "raw_first_appearance_values":uniq(x["raw_first_appearance"] for x in items),
            "record_count":len(items),
            "observed_names":uniq(x["name"] for x in items),
            "observed_identities":uniq(x["identity"] for x in items),
            "observed_variants":uniq(x["variant"] for x in items),
            "observed_universes":uniq(x["universe"] for x in items),
            "observed_years":uniq(x["year"] for x in items),
            "source_work_candidate":parsed[0]["source_work_candidate"] if parsed and len({x["source_work_candidate"] for x in parsed}) == 1 else None,
            "issue_number_candidate":parsed[0]["issue_number_candidate"] if parsed and len({x["issue_number_candidate"] for x in parsed}) == 1 else None,
            "parse_status":"explicit_hash_issue" if parsed and len(parsed) == len(items) else "mixed_or_raw",
            "source_records":items[:100],
            "resolution_status":"candidate_needs_source_verification",
            "policy":"The tracker string is preserved verbatim. Parsed work/issue fields are only extracted from explicit '#number' syntax and remain candidates until source verification.",
            "processor_version":VERSION,
        })
    appearance_rows.sort(key=lambda x:(x["parse_status"]!="explicit_hash_issue",-x["record_count"],x["normalized_first_appearance"]))

    # Prioritized entity-resolution queue.
    entity_review = []
    for g in group_rows:
        reasons = []
        score = 0
        if g.get("cross_source_candidate"):
            reasons.append("cross_source")
            score += 10
        if "multiple_identities" in (g.get("ambiguity_flags") or []):
            reasons.append("multiple_identities")
            score += 25
        if "multiple_universes" in (g.get("ambiguity_flags") or []):
            reasons.append("multiple_universes")
            score += 25
        if "many_variants" in (g.get("ambiguity_flags") or []):
            reasons.append("many_variants")
            score += 15
        score += min(20, int(g.get("record_count") or 0) // 5)
        if reasons:
            entity_review.append({
                "character_group_candidate_id": g.get("character_group_candidate_id"),
                "normalized_name": g.get("normalized_name"),
                "observed_names": g.get("observed_names"),
                "record_count": g.get("record_count"),
                "source_file_count": g.get("source_file_count"),
                "identities": g.get("identities"),
                "variants": g.get("variants"),
                "universes": g.get("universes"),
                "review_reasons": reasons,
                "review_priority_score": score,
                "review_status": "pending",
                "policy": "Priority only; never merge identities/universes/variants automatically from this queue.",
                "processor_version": VERSION,
            })
    entity_review.sort(key=lambda x: (-x["review_priority_score"], x.get("normalized_name") or ""))

    # Conservative collection/design-gap candidates at strict name+identity+variant+universe granularity.
    owned_like = {"YES","TRUE","LEGO","CLONE","CUSTOM","PREPPED","ORDERED","SHIPPED","OWNED","HAVE"}
    missing_like = {"NO","FALSE","MISSING"}
    maybe_like = {"MAYBE"}
    gap_rows = []
    for item in strict_rows:
        recs = item.get("records") or []
        target = any(r.get("record_class") in {"design_target","wishlist"} for r in recs)
        if not target:
            continue
        statuses = []
        any_owned = False
        any_missing = False
        any_maybe = False
        wishlist = any(r.get("record_class") == "wishlist" for r in recs)
        explicit_false = False
        for r in recs:
            if r.get("have") is True:
                any_owned = True
            elif r.get("have") is False:
                explicit_false = True
                any_missing = True
            raw = str(r.get("ownership_status") or "").strip().upper()
            if raw in owned_like:
                any_owned = True
            elif raw in missing_like:
                any_missing = True
            elif raw in maybe_like:
                any_maybe = True
            if raw:
                statuses.append(raw)
        if any_owned:
            state = "target_covered_or_in_pipeline"
        elif wishlist:
            state = "wishlist_gap_candidate"
        elif any_missing or explicit_false:
            state = "explicit_missing_design_target"
        elif any_maybe:
            state = "maybe_gap_candidate"
        else:
            state = "unknown_target_state"
        if state == "target_covered_or_in_pipeline":
            continue
        gap_rows.append({
            "strict_group_key": item.get("strict_group_key"),
            "candidate_state": state,
            "record_count": item.get("record_count"),
            "source_files": item.get("source_files"),
            "observed_statuses": sorted(set(statuses)),
            "records": recs,
            "promotion_policy": "Only explicit missing/wishlist states are actionable gap candidates. Unknown/maybe states require review before backlog promotion.",
            "processor_version": VERSION,
        })
    gap_rank = {"wishlist_gap_candidate":0,"explicit_missing_design_target":1,"maybe_gap_candidate":2,"unknown_target_state":3}
    gap_rows.sort(key=lambda x: (gap_rank.get(x["candidate_state"],9), x.get("strict_group_key") or ""))

    # FigureRelease candidates: group maker product codes without collapsing name/variant conflicts.
    release_groups = defaultdict(list)
    for row in code_rows:
        if row.get("product_code_namespace") != "maker_product_code":
            continue
        release_groups[str(row.get("product_code") or "").upper()].append(row)
    release_rows = []
    for code, items in release_groups.items():
        brands = []
        for item in items:
            for cand in item.get("brand_candidates") or []:
                key = (cand.get("brand"), cand.get("confidence"), cand.get("relationship_note"))
                if key not in [(x.get("brand"), x.get("confidence"), x.get("relationship_note")) for x in brands]:
                    brands.append(cand)
        names = uniq(x.get("name") for x in items)
        variants = uniq(x.get("variant") for x in items)
        source_records = [x.get("source_record") for x in items]
        release_rows.append({
            "figure_release_candidate_id": "user-release-" + re.sub(r"[^a-z0-9]+", "-", code.casefold()).strip("-"),
            "maker_product_code": code,
            "maker_candidates": brands,
            "observed_names": names,
            "observed_variants": variants,
            "source_record_count": len(items),
            "source_records": source_records,
            "identity_conflict_flags": [
                *([] if len(names) <= 1 else ["multiple_names_for_same_code"]),
                *([] if len(variants) <= 1 else ["multiple_variants_for_same_code"]),
                *([] if len(brands) <= 1 else ["multiple_brand_candidates"]),
            ],
            "release_resolution_status": (
                "candidate_ready_for_identity_resolution"
                if len(brands) == 1
                else "brand_or_identity_review_required"
            ),
            "policy": "User tracker product-code grouping creates FigureRelease candidates only. Canonical maker/release identity requires corroborating catalog or primary-source evidence.",
            "processor_version": VERSION,
        })
    release_rows.sort(key=lambda x: (x["release_resolution_status"] != "brand_or_identity_review_required", x["maker_product_code"]))

    def write_jsonl(name, rows):
        with (args.output_dir / name).open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    write_jsonl("name-group-candidates.jsonl", group_rows)
    write_jsonl("strict-duplicate-candidates.jsonl", strict_rows)
    write_jsonl("product-code-brand-candidates.jsonl", code_rows)
    write_jsonl("dc-legacy-normalized.jsonl", dc_normalized)
    write_jsonl("figure-release-candidates.jsonl", release_rows)
    write_jsonl("external-catalog-id-queue.jsonl", external_catalog_records)
    write_jsonl("entity-resolution-review-queue.jsonl", entity_review)
    write_jsonl("collection-gap-candidates.jsonl", gap_rows)
    write_jsonl("source-appearance-candidates.jsonl", appearance_rows)
    (args.output_dir / "entity-resolution-review-summary.json").write_text(json.dumps({
        "schema":"entity-resolution-review-summary/v1",
        "processor_version":VERSION,
        "records":len(entity_review),
        "high_priority_records":sum(x["review_priority_score"] >= 40 for x in entity_review),
        "reason_counts":dict(Counter(r for x in entity_review for r in x["review_reasons"])),
        "top_records":[{
            "name":x["normalized_name"],
            "score":x["review_priority_score"],
            "records":x["record_count"],
            "sources":x["source_file_count"],
            "reasons":x["review_reasons"],
            "identities":len(x["identities"]),
            "variants":len(x["variants"]),
            "universes":len(x["universes"])
        } for x in entity_review[:100]],
        "status":"entity_resolution_review_queue_ready"
    }, indent=2)+"\n", encoding="utf-8")
    (args.output_dir / "collection-gap-summary.json").write_text(json.dumps({
        "schema":"collection-gap-summary/v1",
        "processor_version":VERSION,
        "records":len(gap_rows),
        "state_counts":dict(Counter(x["candidate_state"] for x in gap_rows)),
        "actionable_records":sum(x["candidate_state"] in {"wishlist_gap_candidate","explicit_missing_design_target"} for x in gap_rows),
        "review_required_records":sum(x["candidate_state"] in {"maybe_gap_candidate","unknown_target_state"} for x in gap_rows),
        "status":"collection_gap_queue_ready"
    }, indent=2)+"\n", encoding="utf-8")
    write_jsonl(
        "unresolved-code-prefixes.jsonl",
        [x for x in code_rows if x.get("resolution_status") in {"unresolved_prefix","brand_candidate_ambiguous"}]
    )

    (args.output_dir / "source-appearance-summary.json").write_text(json.dumps({
        "schema":"user-source-appearance-summary/v1",
        "processor_version":VERSION,
        "candidate_records":len(appearance_rows),
        "source_records_with_first_appearance":sum(x["record_count"] for x in appearance_rows),
        "explicit_hash_issue_candidates":sum(x["parse_status"]=="explicit_hash_issue" for x in appearance_rows),
        "mixed_or_raw_candidates":sum(x["parse_status"]!="explicit_hash_issue" for x in appearance_rows),
        "status":"source_appearance_candidate_layer_ready"
    }, indent=2)+"\n", encoding="utf-8")

    unresolved_prefix = Counter(
        x.get("observed_prefix") or "UNKNOWN"
        for x in code_rows if x["resolution_status"] == "unresolved_prefix"
    )
    summary = {
        "schema": "user-tracker-reconciliation-summary/v1",
        "created_at": now_iso(),
        "processor_version": VERSION,
        "input_files": [p.name for p in input_files],
        "input_records_with_names": len(records),
        "dc_legacy_raw_rows_normalized": len(dc_normalized),
        "name_groups": len(group_rows),
        "cross_source_name_groups": sum(x["cross_source_candidate"] for x in group_rows),
        "groups_with_multiple_identities": sum("multiple_identities" in x["ambiguity_flags"] for x in group_rows),
        "groups_with_multiple_universes": sum("multiple_universes" in x["ambiguity_flags"] for x in group_rows),
        "groups_with_many_variants": sum("many_variants" in x["ambiguity_flags"] for x in group_rows),
        "strict_duplicate_candidate_groups": len(strict_rows),
        "strict_cross_source_duplicate_candidate_groups": sum(x["cross_source_duplicate_candidate"] for x in strict_rows),
        "entity_resolution_review_records": len(entity_review),
        "entity_resolution_high_priority_records": sum(x["review_priority_score"] >= 40 for x in entity_review),
        "collection_gap_candidate_records": len(gap_rows),
        "collection_gap_state_counts": dict(Counter(x["candidate_state"] for x in gap_rows)),
        "source_appearance_candidate_records": len(appearance_rows),
        "source_records_with_first_appearance": sum(x["record_count"] for x in appearance_rows),
        "explicit_hash_issue_source_appearance_candidates": sum(x["parse_status"] == "explicit_hash_issue" for x in appearance_rows),
        "coded_records": len(code_rows),
        "maker_product_code_records": sum(x.get("product_code_namespace") == "maker_product_code" for x in code_rows),
        "external_catalog_id_records_in_named_records": sum(x.get("product_code_namespace") == "bricklink_minifigure_id" for x in code_rows),
        "external_catalog_id_records_total": len(external_catalog_records),
        "external_catalog_id_unique_ids": len({x["catalog_id"] for x in external_catalog_records}),
        "unstructured_source_code_text_records": sum(x.get("product_code_namespace") == "unstructured_source_code_text" for x in code_rows),
        "figure_release_candidate_records": len(release_rows),
        "figure_release_candidates_with_identity_conflicts": sum(bool(x.get("identity_conflict_flags")) for x in release_rows),
        "single_brand_candidates": sum(x["resolution_status"] == "brand_candidate_single" for x in code_rows),
        "ambiguous_brand_candidates": sum(x["resolution_status"] == "brand_candidate_ambiguous" for x in code_rows),
        "unresolved_code_prefix_records": sum(x["resolution_status"] == "unresolved_prefix" for x in code_rows),
        "external_catalog_ids_observed": sum(x["resolution_status"] == "external_catalog_id_observed" for x in code_rows),
        "unstructured_code_text_observations": sum(x["resolution_status"] == "unstructured_source_code_text" for x in code_rows),
        "unresolved_prefix_counts": dict(unresolved_prefix.most_common()),
        "largest_name_groups": [
            {
                "name": x["normalized_name"],
                "records": x["record_count"],
                "source_files": x["source_file_count"],
                "identities": len(x["identities"]),
                "variants": len(x["variants"]),
            }
            for x in sorted(group_rows, key=lambda x: -x["record_count"])[:30]
        ],
        "status": "candidate_reconciliation_layers_ready",
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
