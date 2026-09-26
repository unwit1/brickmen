#!/usr/bin/env python3
"""Audit entity-resolution review rows for presentation aliases and structural data-quality anomalies."""
from __future__ import annotations
import argparse,json,re,unicodedata
from collections import Counter,defaultdict
from pathlib import Path

VERSION="entity-resolution-data-quality-audit/v1"

def load_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:
                yield json.loads(line)

def norm(v):
    s=unicodedata.normalize("NFKD",str(v or ""))
    s="".join(c for c in s if not unicodedata.combining(c)).casefold()
    return " ".join(re.findall(r"[a-z0-9]+",s))

def alias_groups(values):
    groups=defaultdict(list)
    for value in values or []:
        key=norm(value)
        if key:
            groups[key].append(value)
    return [
        {"normalized_key":k,"raw_labels":sorted(set(v),key=lambda x:(len(str(x)),str(x)))}
        for k,v in sorted(groups.items())
        if len(set(v))>1
    ]

def year_like(value):
    return bool(re.fullmatch(r"(?:18|19|20)\d{2}",str(value or "").strip()))

def numeric_like(value):
    return bool(re.fullmatch(r"\d{2,6}",str(value or "").strip()))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    rows=[]; reason_counts=Counter(); alias_field_counts=Counter()
    for rank,src in enumerate(load_jsonl(args.input),start=1):
        identities=src.get("identities") or []
        universes=src.get("universes") or []
        variants=src.get("variants") or []
        id_alias=alias_groups(identities)
        uni_alias=alias_groups(universes)
        var_alias=alias_groups(variants)
        for field,groups in [("identity",id_alias),("universe",uni_alias),("variant",var_alias)]:
            if groups: alias_field_counts[field]+=len(groups)

        id_norm={norm(x) for x in identities if norm(x)}
        uni_norm={norm(x) for x in universes if norm(x)}
        char_norm=norm(src.get("normalized_name"))
        anomalies=[]
        identity_years=[x for x in identities if year_like(x)]
        universe_years=[x for x in universes if year_like(x)]
        bare_numeric_universes=[x for x in universes if numeric_like(x)]
        universe_identity_overlap=sorted({x for x in universes if norm(x) in id_norm})
        universe_character_overlap=[x for x in universes if norm(x)==char_norm]
        if identity_years: anomalies.append("identity_contains_year_like_values")
        if universe_years: anomalies.append("universe_contains_year_like_values")
        if bare_numeric_universes: anomalies.append("universe_contains_bare_numeric_values")
        if universe_identity_overlap: anomalies.append("universe_duplicates_identity_label")
        if universe_character_overlap: anomalies.append("universe_duplicates_character_label")
        if id_alias: anomalies.append("identity_presentation_aliases")
        if uni_alias: anomalies.append("universe_presentation_aliases")
        if var_alias: anomalies.append("variant_presentation_aliases")
        for a in anomalies: reason_counts[a]+=1

        semantic_identity_count=len(id_norm)
        semantic_universe_count=len(uni_norm)
        semantic_variant_count=len({norm(x) for x in variants if norm(x)})
        rows.append({
            "review_rank":rank,
            "character_group_candidate_id":src.get("character_group_candidate_id"),
            "normalized_name":src.get("normalized_name"),
            "original_review_priority_score":src.get("review_priority_score"),
            "record_count":src.get("record_count"),
            "raw_identity_count":len(identities),
            "normalized_identity_key_count":semantic_identity_count,
            "raw_universe_count":len(universes),
            "normalized_universe_key_count":semantic_universe_count,
            "raw_variant_count":len(variants),
            "normalized_variant_key_count":semantic_variant_count,
            "identity_alias_groups":id_alias,
            "universe_alias_groups":uni_alias,
            "variant_alias_groups":var_alias,
            "structural_anomalies":anomalies,
            "identity_year_like_values":identity_years,
            "universe_year_like_values":universe_years,
            "bare_numeric_universe_values":bare_numeric_universes,
            "universe_identity_overlap":universe_identity_overlap,
            "universe_character_overlap":universe_character_overlap,
            "review_status":"derived_data_quality_audit_ready",
            "policy":"This audit only normalizes punctuation, spacing, case and diacritics for comparison. It never declares semantically different identities, universes or variants equivalent.",
            "processor_version":VERSION
        })

    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
        "schema":"entity-resolution-data-quality-audit-summary/v1",
        "processor_version":VERSION,
        "records":len(rows),
        "top_60_records":min(60,len(rows)),
        "records_with_structural_anomalies":sum(bool(x["structural_anomalies"]) for x in rows),
        "records_with_identity_alias_groups":sum(bool(x["identity_alias_groups"]) for x in rows),
        "records_with_universe_alias_groups":sum(bool(x["universe_alias_groups"]) for x in rows),
        "records_with_variant_alias_groups":sum(bool(x["variant_alias_groups"]) for x in rows),
        "alias_group_counts_by_field":dict(alias_field_counts),
        "anomaly_reason_counts":dict(reason_counts),
        "top_60_with_structural_anomalies":sum(bool(x["structural_anomalies"]) for x in rows[:60]),
        "status":"entity_resolution_data_quality_audit_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
