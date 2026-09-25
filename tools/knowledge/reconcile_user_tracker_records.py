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
        "have": rec.get("have"),
        "ownership_status": rec.get("ownership_status"),
        "preferred": rec.get("preferred") or rec.get("best_representation"),
        "official": rec.get("official"),
        "bootleg": rec.get("bootleg"),
    }

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
                name_alias_map[norm(alias)].append(entry)
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
    for root in (args.collection_dir, args.design_dir):
        for path in sorted(root.glob("*.jsonl")):
            if path.name in GENERATED_COLLECTION_FILES:
                continue
            input_files.append(path)
            for rec in load_jsonl(path):
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
        prefix = code_prefix(code)
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
            "observed_prefix": prefix,
            "name": rec.get("name"),
            "variant": rec.get("variant"),
            "brand_candidates": candidates,
            "candidate_method": method,
            "resolution_status": (
                "brand_candidate_single" if len(candidates) == 1
                else "brand_candidate_ambiguous" if len(candidates) > 1
                else "unresolved_prefix"
            ),
            "policy": "Prefix or exact brand-token evidence proposes a brand only; release identity, ownership/factory relationships and chronology require independent evidence.",
            "processor_version": VERSION,
        })

    def write_jsonl(name, rows):
        with (args.output_dir / name).open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    write_jsonl("name-group-candidates.jsonl", group_rows)
    write_jsonl("strict-duplicate-candidates.jsonl", strict_rows)
    write_jsonl("product-code-brand-candidates.jsonl", code_rows)

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
        "name_groups": len(group_rows),
        "cross_source_name_groups": sum(x["cross_source_candidate"] for x in group_rows),
        "groups_with_multiple_identities": sum("multiple_identities" in x["ambiguity_flags"] for x in group_rows),
        "groups_with_multiple_universes": sum("multiple_universes" in x["ambiguity_flags"] for x in group_rows),
        "groups_with_many_variants": sum("many_variants" in x["ambiguity_flags"] for x in group_rows),
        "strict_duplicate_candidate_groups": len(strict_rows),
        "strict_cross_source_duplicate_candidate_groups": sum(x["cross_source_duplicate_candidate"] for x in strict_rows),
        "coded_records": len(code_rows),
        "single_brand_candidates": sum(x["resolution_status"] == "brand_candidate_single" for x in code_rows),
        "ambiguous_brand_candidates": sum(x["resolution_status"] == "brand_candidate_ambiguous" for x in code_rows),
        "unresolved_code_prefix_records": sum(x["resolution_status"] == "unresolved_prefix" for x in code_rows),
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
