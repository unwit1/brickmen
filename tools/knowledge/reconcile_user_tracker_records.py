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

VERSION = "user-tracker-reconciliation/v3"

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

def load_semantic_corrections(path: Path | None):
    if not path:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for row in payload.get("records") or []:
        key = (
            str(row.get("source_title") or ""),
            str(row.get("source_tab") or ""),
            int(row.get("source_row") or 0),
        )
        out[key] = row
    return out

def apply_semantic_correction(rec, corrections):
    key = (
        str(rec.get("source_title") or ""),
        str(rec.get("source_tab") or ""),
        int(rec.get("source_row") or 0),
    )
    correction = corrections.get(key)
    if not correction:
        return rec
    expected = str(correction.get("expected_name") or "").strip()
    observed = str(source_name(rec) or "").strip()
    if expected and observed and norm(expected) != norm(observed):
        return rec
    out = dict(rec)
    touched = set((correction.get("corrected_fields") or {}).keys()) | set(correction.get("clear_fields") or [])
    original = {field: rec.get(field) for field in sorted(touched)}
    for field, value in (correction.get("corrected_fields") or {}).items():
        out[field] = value
    for field in correction.get("clear_fields") or []:
        out[field] = None
    out["_semantic_correction"] = {
        "source_title": correction.get("source_title"),
        "source_tab": correction.get("source_tab"),
        "source_row": correction.get("source_row"),
        "original_fields": original,
        "corrected_fields": correction.get("corrected_fields") or {},
        "clear_fields": correction.get("clear_fields") or [],
        "confidence": correction.get("confidence"),
        "rationale": correction.get("rationale"),
        "policy": "Derived semantic overlay only; original source row remains unchanged.",
    }
    return out

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

def load_identity_aliases(path: Path | None):
    if not path:
        return {}, {}, 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    alias_map = {}
    canonical_labels = {}
    records = payload.get("records") or []
    for row in records:
        character_key = norm(row.get("character"))
        canonical_label = str(row.get("canonical_identity") or "").strip()
        canonical_key = norm(canonical_label)
        if not character_key or not canonical_key:
            continue
        canonical_labels[(character_key, canonical_key)] = canonical_label
        for alias in [canonical_label, *(row.get("aliases") or [])]:
            alias_key = norm(alias)
            if alias_key:
                alias_map[(character_key, alias_key)] = canonical_key
    return alias_map, canonical_labels, len(records)

def identity_semantic_key(character, identity, alias_map):
    raw_key = norm(identity)
    if not raw_key:
        return ""
    return alias_map.get((norm(character), raw_key), raw_key)

def external_catalog_id(rec):
    direct = str(rec.get("bricklink_minifigure_id") or "").strip()
    if direct:
        return direct.casefold()
    url = str(rec.get("bricklink_catalog_url") or "")
    m = re.search(r"[?&]M=([^&#]+)", url, re.I)
    return m.group(1).strip().casefold() if m else None

def parse_source_appearance_reference(value):
    raw = " ".join(str(value or "").strip().split())
    if not raw:
        return {"kind":"empty","raw":raw}

    # Remove wrapping quotes and trailing citation markers while preserving the original raw value.
    core = raw.strip().strip('"').strip("'").strip()
    core = re.sub(r"(?:\[[^\]]+\])+\s*$", "", core).strip()

    qualifiers = []
    year_hint = None

    # Peel trailing parenthetical qualifiers/dates from right to left.
    while True:
        pm = re.search(r"\(([^()]*)\)\s*$", core)
        if not pm:
            break
        token = pm.group(1).strip()
        low = token.casefold()
        if re.fullmatch(r"(?:19|20)\d{2}", token):
            year_hint = int(token)
            core = core[:pm.start()].strip()
            continue
        dm = re.search(r"\b((?:19|20)\d{2})\b", token)
        if dm and re.search(r"jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec", low):
            year_hint = int(dm.group(1))
            qualifiers.append(token)
            core = core[:pm.start()].strip()
            continue
        if low in {"digital","web","online","one-shot","one shot"}:
            qualifiers.append(token)
            core = core[:pm.start()].strip()
            continue
        # Parenthesized volume stays in the main parser.
        if re.fullmatch(r"(?:vol(?:\.|ume)?|v)\s*\d+", token, re.I):
            break
        break

    # Normalize harmless terminal punctuation without changing issue designators.
    core = core.rstrip(" .;,]")

    issue_token = r"-?\d+(?:\.\d+)?(?:\.[A-Za-z]+)?(?:[A-Za-z])?(?:\s*[–—-]\s*-?\d+(?:\.\d+)?)?"
    volume_token = r"(?:Vol(?:\.|ume)?|v)\s*(?P<volume>\d+)"

    patterns = [
        # Title (Volume 2) Annual #4 / Title (Vol. 5) #24.NOW / #23.1: subtitle
        rf"^(?P<title>.+?)\s*\((?:Vol(?:\.|ume)?|v)\s*(?P<volume>\d+)\)\s*(?P<annual>Annual\s+)?#\s*(?P<issue>{issue_token})(?:\s*:\s*(?P<subtitle>.+))?$",
        # Title Vol 3 #1 / Title v3 1
        rf"^(?P<title>.+?)\s+{volume_token}\s*(?P<annual>Annual\s+)?#?\s*(?P<issue>{issue_token})(?:\s*:\s*(?P<subtitle>.+))?$",
        # Title (3rd series) #8-13
        rf"^(?P<title>.+?)\s*\((?P<ordinal>\d+)(?:st|nd|rd|th)\s+series\)\s*(?P<annual>Annual\s+)?#\s*(?P<issue>{issue_token})(?:\s*:\s*(?P<subtitle>.+))?$",
        # Title #1 / #1.NOW / #-1 / #4-5 / #23.1: subtitle
        rf"^(?P<title>.+?)\s*(?P<annual>Annual\s+)?#\s*(?P<issue>{issue_token})(?:\s*:\s*(?P<subtitle>.+))?$",
    ]

    for pattern in patterns:
        m = re.match(pattern, core, re.I)
        if not m:
            continue
        title = m.group("title").strip(" -")
        gd = m.groupdict()
        volume = gd.get("volume") or gd.get("ordinal")
        issue = re.sub(r"\s+", "", gd.get("issue") or "")
        annual = bool(gd.get("annual"))
        subtitle = (gd.get("subtitle") or "").strip() or None
        issue_key = issue.casefold().replace("–","-").replace("—","-")
        return {
            "kind":"comic_issue_explicit",
            "raw":raw,
            "source_work":title,
            "source_work_normalized":norm(title),
            "volume":int(volume) if volume else None,
            "issue":issue,
            "annual":annual,
            "subtitle":subtitle,
            "qualifiers":qualifiers,
            "year_hint":year_hint,
            "canonical_issue_key":"|".join([
                norm(title),
                f"v{int(volume)}" if volume else "v?",
                "annual" if annual else "regular",
                f"i{issue_key}",
            ]),
        }

    # Explicit episode syntax with a named work.
    em = re.match(
        r"^(?P<title>.+?)\s+(?:S(?P<season>\d{1,2})E(?P<episode>\d{1,3})|Season\s+(?P<season2>\d+)\s+Episode\s+(?P<episode2>\d+)|Episode\s+(?P<episode3>\d+))$",
        core,
        re.I,
    )
    if em:
        season = em.group("season") or em.group("season2")
        episode = em.group("episode") or em.group("episode2") or em.group("episode3")
        title = em.group("title").strip(" -")
        return {
            "kind":"episode_explicit",
            "raw":raw,
            "source_work":title,
            "source_work_normalized":norm(title),
            "season":int(season) if season else None,
            "episode":int(episode),
            "qualifiers":qualifiers,
            "year_hint":year_hint,
            "canonical_issue_key":"|".join([
                "episode",norm(title),f"s{int(season)}" if season else "s?",f"e{int(episode)}"
            ]),
        }

    # A bare episode number has useful structure but lacks a source work.
    bem = re.fullmatch(r"Episode\s+(\d+)", core, re.I)
    if bem:
        return {
            "kind":"episode_number_without_work",
            "raw":raw,
            "episode":int(bem.group(1)),
            "qualifiers":qualifiers,
            "year_hint":year_hint,
            "canonical_issue_key":None,
        }

    # Title + year is useful for games/films/series but not enough to infer an episode/issue.
    dwork = re.fullmatch(r"(.+?)\s*\(((?:19|20)\d{2})\)", raw.strip().strip('"').strip("'"))
    if dwork:
        title=dwork.group(1).strip()
        return {
            "kind":"dated_work",
            "raw":raw,
            "source_work":title,
            "source_work_normalized":norm(title),
            "year_hint":int(dwork.group(2)),
            "canonical_issue_key":None,
        }

    # If a trailing year/date was peeled above, retain the remaining title as a dated work.
    if year_hint and core and not re.fullmatch(r"(?:19|20)\d{2}", core):
        return {
            "kind":"dated_work",
            "raw":raw,
            "source_work":core,
            "source_work_normalized":norm(core),
            "year_hint":year_hint,
            "qualifiers":qualifiers,
            "canonical_issue_key":None,
        }

    # A bare year is useful chronology metadata but not a SourceAppearance identity.
    if re.fullmatch(r"(?:19|20)\d{2}", core):
        return {
            "kind":"year_only",
            "raw":raw,
            "year_hint":int(core),
            "canonical_issue_key":None,
        }

    # Quoted title-like values are often episode/chapter/work titles; preserve as title candidates.
    stripped_raw=raw.strip()
    if len(stripped_raw)>=2 and stripped_raw[0] in {'"',"'" } and stripped_raw[-1]==stripped_raw[0]:
        title=stripped_raw[1:-1].strip()
        if title:
            return {
                "kind":"quoted_title_candidate",
                "raw":raw,
                "source_work":title,
                "source_work_normalized":norm(title),
                "year_hint":year_hint,
                "canonical_issue_key":None,
            }

    return {
        "kind":"raw_only",
        "raw":raw,
        "qualifiers":qualifiers,
        "year_hint":year_hint,
        "canonical_issue_key":None,
    }

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
        "product_code": rec.get("product_code") or external_catalog_id(rec),
        "product_code_namespace": (
            "maker_product_code"
            if rec.get("product_code") and (
                is_maker_code(rec.get("product_code"))
                or (str(rec.get("product_code")).strip().isdigit() and rec.get("brand_explicit"))
            )
            else "unstructured_source_code_text"
            if rec.get("product_code")
            else "bricklink_minifigure_id"
            if external_catalog_id(rec)
            else None
        ),
        "have": rec.get("have"),
        "ownership_status": rec.get("ownership_status"),
        "preferred": rec.get("preferred") or rec.get("best_representation"),
        "official": rec.get("official"),
        "bootleg": rec.get("bootleg"),
        "semantic_correction": rec.get("_semantic_correction"),
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
        elif raw_code == "DH0213" and "batman new 52" in norm(up.get("C")):
            # Preserve the observed serial verbatim. HeroBloks has a Decool 0213 listing, but
            # that is evidence for a possible cross-catalog relationship, not enough to rewrite
            # the user's DH0213 identifier or assign its manufacturer.
            normalized_code = "DH0213"
            correction = None
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
    ap.add_argument("--semantic-corrections", type=Path)
    ap.add_argument("--identity-aliases", type=Path)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _, prefix_map, alias_map = load_crosswalk(args.crosswalk)
    semantic_corrections = load_semantic_corrections(args.semantic_corrections)
    identity_alias_map, identity_canonical_labels, identity_alias_group_count = load_identity_aliases(args.identity_aliases)

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
                rec = apply_semantic_correction(rec, semantic_corrections)
                recovered_external_id = external_catalog_id(rec)
                if recovered_external_id:
                    external_catalog_records.append({
                        "catalog_namespace":"bricklink_minifigure_id",
                        "catalog_id":recovered_external_id,
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
        identity_semantic_groups = defaultdict(list)
        for identity_label in identities:
            semantic_key = identity_semantic_key(key, identity_label, identity_alias_map)
            if semantic_key:
                identity_semantic_groups[semantic_key].append(identity_label)
        identity_semantic_keys = set(identity_semantic_groups)
        identity_alias_collapses = []
        for semantic_key, raw_labels in sorted(identity_semantic_groups.items()):
            raw_keys = {norm(x) for x in raw_labels if norm(x)}
            if len(raw_keys) > 1 or any(
                identity_semantic_key(key, x, identity_alias_map) != norm(x)
                for x in raw_labels if norm(x)
            ):
                identity_alias_collapses.append({
                    "semantic_key": semantic_key,
                    "canonical_identity": identity_canonical_labels.get((norm(key), semantic_key)),
                    "raw_labels": sorted(set(raw_labels)),
                })
        universe_semantic_keys = {norm(x) for x in universes if norm(x)}
        variant_semantic_keys = {norm(x) for x in variants if norm(x)}
        ambiguity = []
        if len(identity_semantic_keys) > 1:
            ambiguity.append("multiple_identities")
        if len(universe_semantic_keys) > 1:
            ambiguity.append("multiple_universes")
        if len(variant_semantic_keys) > 8:
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
            "identity_semantic_key_count": len(identity_semantic_keys),
            "identity_alias_collapses": identity_alias_collapses,
            "variants": variants,
            "variant_semantic_key_count": len(variant_semantic_keys),
            "universes": universes,
            "universe_semantic_key_count": len(universe_semantic_keys),
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
            identity_semantic_key(rec["normalized_name"], rec.get("identity"), identity_alias_map),
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
        explicit_brand = rec.get("brand_explicit")
        candidates = []
        method = None
        if namespace == "maker_product_code":
            if explicit_brand:
                candidates = list(alias_map.get(norm(explicit_brand), []))
                method = "explicit_brand_name_or_alias" if candidates else None
            if not candidates:
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
            "explicit_brand": explicit_brand,
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

    # SourceAppearance candidates from first-appearance metadata.
    # Explicit issue references are grouped by normalized series + volume + issue so equivalent
    # spellings such as "X-Factor v3 #1" and "X-Factor Vol. 3 #1" converge.
    appearance_groups = defaultdict(list)
    for rec in records:
        raw = str(rec.get("first_appearance") or "").strip()
        if not raw:
            continue
        parsed = parse_source_appearance_reference(raw)
        group_key = parsed.get("canonical_issue_key") or ("raw|" + norm(raw))
        appearance_groups[group_key].append({
            "raw_first_appearance": raw,
            "source_work_candidate": parsed.get("source_work"),
            "source_work_normalized": parsed.get("source_work_normalized"),
            "volume_candidate": parsed.get("volume"),
            "issue_number_candidate": parsed.get("issue"),
            "season_candidate": parsed.get("season"),
            "episode_candidate": parsed.get("episode"),
            "year_hint": parsed.get("year_hint"),
            "parse_status": parsed.get("kind"),
            "canonical_issue_key": parsed.get("canonical_issue_key"),
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
        kinds = {x["parse_status"] for x in items}
        parsed_issue = [x for x in items if x["parse_status"] == "comic_issue_explicit"]
        parsed_episode = [x for x in items if x["parse_status"] == "episode_explicit"]
        parsed = parsed_issue or parsed_episode
        appearance_rows.append({
            "source_appearance_candidate_id":"user-source-appearance-"+re.sub(r"[^a-z0-9]+","-",key)[:120].strip("-"),
            "canonical_reference_key":key if not key.startswith("raw|") else None,
            "normalized_first_appearance":norm((items[0].get("raw_first_appearance") or "")),
            "raw_first_appearance_values":uniq(x["raw_first_appearance"] for x in items),
            "record_count":len(items),
            "observed_names":uniq(x["name"] for x in items),
            "observed_identities":uniq(x["identity"] for x in items),
            "observed_variants":uniq(x["variant"] for x in items),
            "observed_universes":uniq(x["universe"] for x in items),
            "observed_years":uniq(x["year"] for x in items),
            "source_work_candidate":parsed[0]["source_work_candidate"] if parsed and len({x["source_work_candidate"] for x in parsed}) == 1 else None,
            "source_work_normalized":parsed[0]["source_work_normalized"] if parsed and len({x["source_work_normalized"] for x in parsed}) == 1 else None,
            "volume_candidate":parsed[0]["volume_candidate"] if parsed and len({x["volume_candidate"] for x in parsed}) == 1 else None,
            "issue_number_candidate":parsed[0]["issue_number_candidate"] if parsed and len({x["issue_number_candidate"] for x in parsed}) == 1 else None,
            "season_candidate":parsed[0]["season_candidate"] if parsed and len({x["season_candidate"] for x in parsed}) == 1 else None,
            "episode_candidate":parsed[0]["episode_candidate"] if parsed and len({x["episode_candidate"] for x in parsed}) == 1 else None,
            "year_hints":uniq(x["year_hint"] for x in items),
            "parse_status": (
                next(iter(kinds)) if len(kinds) == 1
                else "mixed_or_raw"
            ),
            "source_records":items[:100],
            "resolution_status":"candidate_needs_source_verification",
            "policy":"Every original tracker string is preserved. Structured title/volume/issue or season/episode fields are parser candidates and require source verification before canonical SourceAppearance promotion.",
            "processor_version":VERSION,
        })
    appearance_rows.sort(key=lambda x:(x["parse_status"]!="explicit_hash_issue",-x["record_count"],x["normalized_first_appearance"]))

    # Rank SourceAppearance candidates so exact issue references and parseable screen references
    # are reviewed before free-form notes.
    appearance_review=[]
    for row in appearance_rows:
        raw_text=" | ".join(row.get("raw_first_appearance_values") or [])
        reasons=[]; score=0
        if row.get("parse_status")=="comic_issue_explicit":
            appearance_kind="comic_issue_explicit"
            reasons.append("explicit_issue_number")
            score+=80
        elif row.get("parse_status")=="episode_explicit":
            appearance_kind="episode_explicit"
            reasons.append("explicit_episode_reference")
            score+=75
        elif re.search(r"\b(?:s\d{1,2}e\d{1,2}|season\s+\d+.*episode\s+\d+|episode\s+\d+)\b",raw_text,re.I):
            appearance_kind="episode_like_raw"
            reasons.append("episode_pattern")
            score+=60
        elif "#" in raw_text:
            appearance_kind="issue_like_unparsed"
            reasons.append("hash_issue_syntax_unparsed")
            score+=55
        elif row.get("parse_status")=="dated_work":
            appearance_kind="dated_work"
            reasons.append("work_title_and_year")
            score+=45
        elif row.get("parse_status")=="year_only":
            appearance_kind="year_only"
            reasons.append("year_only")
            score+=15
        elif row.get("parse_status")=="quoted_title_candidate":
            appearance_kind="quoted_title_candidate"
            reasons.append("quoted_title")
            score+=35
        elif row.get("parse_status")=="episode_number_without_work":
            appearance_kind="episode_number_without_work"
            reasons.append("episode_number_without_work")
            score+=30
        elif re.search(r"\b(?:19|20)\d{2}\b",raw_text):
            appearance_kind="dated_raw"
            reasons.append("contains_year")
            score+=35
        else:
            appearance_kind="freeform_or_title_only"
            reasons.append("freeform")
            score+=15
        if row.get("source_work_candidate"):
            reasons.append("source_work_parsed")
            score+=10
        if len(row.get("observed_years") or [])==1:
            reasons.append("single_observed_year")
            score+=5
        score+=min(15,max(0,int(row.get("record_count") or 0)-1)*3)
        appearance_review.append({
            "source_appearance_candidate_id":row.get("source_appearance_candidate_id"),
            "normalized_first_appearance":row.get("normalized_first_appearance"),
            "raw_first_appearance_values":row.get("raw_first_appearance_values"),
            "appearance_kind_candidate":appearance_kind,
            "source_work_candidate":row.get("source_work_candidate"),
            "issue_number_candidate":row.get("issue_number_candidate"),
            "observed_names":row.get("observed_names"),
            "observed_identities":row.get("observed_identities"),
            "observed_variants":row.get("observed_variants"),
            "observed_universes":row.get("observed_universes"),
            "observed_years":row.get("observed_years"),
            "record_count":row.get("record_count"),
            "review_priority_score":score,
            "review_reasons":reasons,
            "review_status":"pending_source_verification",
            "policy":"Priority and parser class only. Canonical SourceAppearance promotion still requires verification of the cited issue/episode/work and the relevant character/incarnation/variant.",
            "processor_version":VERSION,
        })
    appearance_review.sort(key=lambda x:(-x["review_priority_score"],x.get("normalized_first_appearance") or ""))

    # Candidate Character -> Incarnation -> OutfitDesign hierarchy from user tracker facts.
    # This is structural normalization only; it never merges different identities/universes automatically.
    character_groups = defaultdict(list)
    for rec in records:
        character_groups[rec["normalized_name"]].append(rec)

    character_entities = []
    incarnation_entities = []
    outfit_entities = []
    for char_key, items in character_groups.items():
        identities = defaultdict(list)
        for rec in items:
            identity_key = identity_semantic_key(char_key, rec.get("identity"), identity_alias_map) or "__identity_unresolved__"
            identities[identity_key].append(rec)

        character_id = "character-user-" + re.sub(r"[^a-z0-9]+","-",char_key)[:120].strip("-")
        character_entities.append({
            "character_candidate_id":character_id,
            "normalized_character_name":char_key,
            "observed_names":uniq(x.get("name") for x in items),
            "record_count":len(items),
            "source_files":uniq(x.get("source_file") for x in items),
            "identity_candidate_count":len(identities),
            "resolved_identity_candidate_count":sum(k!="__identity_unresolved__" for k in identities),
            "has_unresolved_identity_records":"__identity_unresolved__" in identities,
            "policy":"Character-name grouping is a parent candidate only. Distinct identity/person records remain separate children.",
            "processor_version":VERSION,
        })

        for identity_key, identity_items in identities.items():
            observed_identity=uniq(x.get("identity") for x in identity_items)
            identity_slug=identity_key if identity_key!="__identity_unresolved__" else "identity-unresolved"
            identity_id=character_id+"--"+re.sub(r"[^a-z0-9]+","-",identity_slug)[:100].strip("-")
            universes=defaultdict(list)
            for rec in identity_items:
                universe_key=norm(rec.get("universe")) or "__universe_unresolved__"
                universes[universe_key].append(rec)

            for universe_key, universe_items in universes.items():
                universe_values=uniq(x.get("universe") for x in universe_items)
                universe_slug=universe_key if universe_key!="__universe_unresolved__" else "universe-unresolved"
                incarnation_id=identity_id+"--"+re.sub(r"[^a-z0-9]+","-",universe_slug)[:100].strip("-")
                variants=defaultdict(list)
                for rec in universe_items:
                    variant_key=norm(rec.get("variant")) or "__variant_unresolved__"
                    variants[variant_key].append(rec)

                incarnation_entities.append({
                    "incarnation_candidate_id":incarnation_id,
                    "character_candidate_id":character_id,
                    "identity_candidate_key":identity_key,
                    "observed_identities":observed_identity,
                    "universe_candidate_key":universe_key,
                    "observed_universes":universe_values,
                    "record_count":len(universe_items),
                    "source_files":uniq(x.get("source_file") for x in universe_items),
                    "variant_candidate_count":len(variants),
                    "has_unresolved_variant_records":"__variant_unresolved__" in variants,
                    "first_appearances":uniq(x.get("first_appearance") for x in universe_items),
                    "years":uniq(x.get("year") for x in universe_items),
                    "policy":"Incarnation candidates are scoped by exact normalized identity/person + universe. Missing identity/universe remains explicitly unresolved.",
                    "processor_version":VERSION,
                })

                for variant_key, variant_items in variants.items():
                    variant_values=uniq(x.get("variant") for x in variant_items)
                    variant_slug=variant_key if variant_key!="__variant_unresolved__" else "variant-unresolved"
                    outfit_id=incarnation_id+"--"+re.sub(r"[^a-z0-9]+","-",variant_slug)[:120].strip("-")
                    outfit_entities.append({
                        "outfit_design_candidate_id":outfit_id,
                        "incarnation_candidate_id":incarnation_id,
                        "variant_candidate_key":variant_key,
                        "observed_variants":variant_values,
                        "record_count":len(variant_items),
                        "source_files":uniq(x.get("source_file") for x in variant_items),
                        "first_appearances":uniq(x.get("first_appearance") for x in variant_items),
                        "years":uniq(x.get("year") for x in variant_items),
                        "preferred_references":uniq(x.get("preferred") for x in variant_items),
                        "product_codes":uniq(x.get("product_code") for x in variant_items),
                        "record_classes":uniq(x.get("record_class") for x in variant_items),
                        "policy":"OutfitDesign candidates preserve exact normalized variant labels under one identity/universe incarnation; unresolved variant labels remain explicit.",
                        "processor_version":VERSION,
                    })

    character_entities.sort(key=lambda x:(-x["record_count"],x["normalized_character_name"]))
    incarnation_entities.sort(key=lambda x:(-x["record_count"],x["incarnation_candidate_id"]))
    outfit_entities.sort(key=lambda x:(-x["record_count"],x["outfit_design_candidate_id"]))

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
    for strict_key, recs in strict.items():
        target = any(r.get("record_class") in {"design_target","wishlist"} for r in recs)
        if not target:
            continue
        source_files = uniq(r.get("source_file") for r in recs)
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
            "strict_group_key": strict_key,
            "candidate_state": state,
            "record_count": len(recs),
            "source_files": source_files,
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
    write_jsonl("character-candidates.jsonl", character_entities)
    write_jsonl("incarnation-candidates.jsonl", incarnation_entities)
    write_jsonl("outfit-design-candidates.jsonl", outfit_entities)
    write_jsonl("entity-resolution-review-queue.jsonl", entity_review)
    write_jsonl("collection-gap-candidates.jsonl", gap_rows)
    write_jsonl("source-appearance-candidates.jsonl", appearance_rows)
    write_jsonl("source-appearance-review-queue.jsonl", appearance_review)
    write_jsonl(
        "source-appearance-unresolved.jsonl",
        [x for x in appearance_review if x.get("appearance_kind_candidate") not in {"comic_issue_explicit","episode_explicit"}]
    )
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

    appearance_alias_groups = [
        x for x in appearance_rows if len(x.get("raw_first_appearance_values") or []) > 1
    ]
    (args.output_dir / "source-appearance-summary.json").write_text(json.dumps({
        "schema":"user-source-appearance-summary/v2",
        "processor_version":VERSION,
        "candidate_records":len(appearance_rows),
        "source_records_with_first_appearance":sum(x["record_count"] for x in appearance_rows),
        "explicit_comic_issue_candidates":sum(x["parse_status"]=="comic_issue_explicit" for x in appearance_rows),
        "explicit_episode_candidates":sum(x["parse_status"]=="episode_explicit" for x in appearance_rows),
        "structured_reference_candidates":sum(x["parse_status"] in {"comic_issue_explicit","episode_explicit"} for x in appearance_rows),
        "mixed_or_raw_candidates":sum(x["parse_status"] not in {"comic_issue_explicit","episode_explicit"} for x in appearance_rows),
        "canonical_groups_with_multiple_raw_spellings":len(appearance_alias_groups),
        "raw_spelling_variants_collapsed":sum(len(x.get("raw_first_appearance_values") or [])-1 for x in appearance_alias_groups),
        "top_alias_groups":[{
            "canonical_reference_key":x.get("canonical_reference_key"),
            "raw_values":x.get("raw_first_appearance_values"),
            "records":x.get("record_count"),
            "source_work":x.get("source_work_candidate"),
            "volume":x.get("volume_candidate"),
            "issue":x.get("issue_number_candidate")
        } for x in sorted(appearance_alias_groups,key=lambda x:(-len(x.get("raw_first_appearance_values") or []),-int(x.get("record_count") or 0)))[:100]],
        "status":"source_appearance_candidate_layer_ready"
    }, indent=2)+"\n", encoding="utf-8")

    (args.output_dir / "source-appearance-review-summary.json").write_text(json.dumps({
        "schema":"source-appearance-review-summary/v1",
        "processor_version":VERSION,
        "records":len(appearance_review),
        "kind_counts":dict(Counter(x["appearance_kind_candidate"] for x in appearance_review)),
        "high_priority_records":sum(x["review_priority_score"] >= 80 for x in appearance_review),
        "top_100":[{"appearance":x["normalized_first_appearance"],"score":x["review_priority_score"],"kind":x["appearance_kind_candidate"],"records":x["record_count"]} for x in appearance_review[:100]],
        "status":"source_appearance_review_queue_ready"
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
        "semantic_correction_records_configured": len(semantic_corrections),
        "semantic_corrections_applied": sum(bool(x.get("semantic_correction")) for x in records),
        "identity_alias_groups_configured": identity_alias_group_count,
        "identity_alias_entries_configured": len(identity_alias_map),
        "records_using_identity_aliases": sum(
            bool(rec.get("identity")) and
            identity_semantic_key(rec["normalized_name"], rec.get("identity"), identity_alias_map) != norm(rec.get("identity"))
            for rec in records
        ),
        "name_groups_with_identity_alias_collapses": sum(bool(x.get("identity_alias_collapses")) for x in group_rows),
        "name_groups": len(group_rows),
        "cross_source_name_groups": sum(x["cross_source_candidate"] for x in group_rows),
        "groups_with_multiple_identities": sum("multiple_identities" in x["ambiguity_flags"] for x in group_rows),
        "groups_with_multiple_universes": sum("multiple_universes" in x["ambiguity_flags"] for x in group_rows),
        "groups_with_many_variants": sum("many_variants" in x["ambiguity_flags"] for x in group_rows),
        "strict_duplicate_candidate_groups": len(strict_rows),
        "strict_cross_source_duplicate_candidate_groups": sum(x["cross_source_duplicate_candidate"] for x in strict_rows),
        "character_candidate_records": len(character_entities),
        "incarnation_candidate_records": len(incarnation_entities),
        "outfit_design_candidate_records": len(outfit_entities),
        "character_candidates_with_unresolved_identity": sum(x["has_unresolved_identity_records"] for x in character_entities),
        "incarnation_candidates_with_unresolved_variant": sum(x["has_unresolved_variant_records"] for x in incarnation_entities),
        "entity_resolution_review_records": len(entity_review),
        "entity_resolution_high_priority_records": sum(x["review_priority_score"] >= 40 for x in entity_review),
        "collection_gap_candidate_records": len(gap_rows),
        "collection_gap_state_counts": dict(Counter(x["candidate_state"] for x in gap_rows)),
        "source_appearance_candidate_records": len(appearance_rows),
        "source_records_with_first_appearance": sum(x["record_count"] for x in appearance_rows),
        "explicit_comic_issue_source_appearance_candidates": sum(x["parse_status"] == "comic_issue_explicit" for x in appearance_rows),
        "explicit_episode_source_appearance_candidates": sum(x["parse_status"] == "episode_explicit" for x in appearance_rows),
        "structured_source_appearance_candidates": sum(x["parse_status"] in {"comic_issue_explicit","episode_explicit"} for x in appearance_rows),
        "source_appearance_review_records": len(appearance_review),
        "source_appearance_high_priority_records": sum(x["review_priority_score"] >= 80 for x in appearance_review),
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
