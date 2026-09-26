#!/usr/bin/env python3
"""Audit entity-resolution review rows without confusing valid universe notation with bad data."""
from __future__ import annotations
import argparse,json,re,unicodedata
from collections import Counter,defaultdict
from pathlib import Path

VERSION="entity-resolution-data-quality-audit/v2"

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

    rows=[]
    review_reason_counts=Counter()
    context_signal_counts=Counter()
    alias_field_counts=Counter()

    for rank,src in enumerate(load_jsonl(args.input),start=1):
        identities=src.get("identities") or []
        universes=src.get("universes") or []
        variants=src.get("variants") or []

        id_alias=alias_groups(identities)
        uni_alias=alias_groups(universes)
        var_alias=alias_groups(variants)
        for field,groups in [("identity",id_alias),("universe",uni_alias),("variant",var_alias)]:
            alias_field_counts[field]+=len(groups)

        id_norm={norm(x) for x in identities if norm(x)}
        char_norm=norm(src.get("normalized_name"))
        identity_years=[x for x in identities if year_like(x)]
        universe_years=[x for x in universes if year_like(x)]
        bare_numeric_universes=[x for x in universes if numeric_like(x)]
        universe_identity_overlap=sorted({x for x in universes if norm(x) in id_norm})
        universe_character_overlap=sorted({x for x in universes if norm(x)==char_norm})

        # These are source-field review signals, not automatic corrections.
        field_review=[]
        if identity_years:
            field_review.append("identity_contains_year_like_values")
        if universe_years:
            field_review.append("universe_contains_year_like_values_requires_context")
        if universe_identity_overlap:
            field_review.append("universe_duplicates_identity_label")
        if universe_character_overlap:
            field_review.append("universe_duplicates_character_label")
        for reason in field_review:
            review_reason_counts[reason]+=1

        # Numeric universe labels such as Marvel 616 are legitimate notation and are
        # retained as context signals only. They must not inflate anomaly counts.
        context_signals=[]
        if bare_numeric_universes:
            context_signals.append("bare_numeric_universe_notation")
        for signal in context_signals:
            context_signal_counts[signal]+=1

        aliases={
            "identity":id_alias,
            "universe":uni_alias,
            "variant":var_alias,
        }
        presentation_alias_count=sum(len(v) for v in aliases.values())

        rows.append({
            "review_rank":rank,
            "character_group_candidate_id":src.get("character_group_candidate_id"),
            "normalized_name":src.get("normalized_name"),
            "original_review_priority_score":src.get("review_priority_score"),
            "record_count":src.get("record_count"),
            "raw_identity_count":len(identities),
            "normalized_identity_key_count":len({norm(x) for x in identities if norm(x)}),
            "raw_universe_count":len(universes),
            "normalized_universe_key_count":len({norm(x) for x in universes if norm(x)}),
            "raw_variant_count":len(variants),
            "normalized_variant_key_count":len({norm(x) for x in variants if norm(x)}),
            "presentation_alias_groups":aliases,
            "presentation_alias_group_count":presentation_alias_count,
            "presentation_alias_cleanup_available":presentation_alias_count>0,
            "field_shape_review_signals":field_review,
            "requires_source_field_review":bool(field_review),
            "context_signals_not_anomalies":context_signals,
            "identity_year_like_values":identity_years,
            "universe_year_like_values":universe_years,
            "bare_numeric_universe_values":bare_numeric_universes,
            "universe_identity_overlap":universe_identity_overlap,
            "universe_character_overlap":universe_character_overlap,
            "review_status":"derived_data_quality_audit_ready",
            "policy":"Presentation aliases are normalization candidates only. Numeric universe labels such as 616 are valid contextual notation. Year-like or identity-duplicating field values are review signals, not automatic errors or merge instructions.",
            "processor_version":VERSION
        })

    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row,ensure_ascii=False)+"\n")

    summary={
        "schema":"entity-resolution-data-quality-audit-summary/v2",
        "processor_version":VERSION,
        "records":len(rows),
        "top_60_records":min(60,len(rows)),
        "records_with_presentation_alias_cleanup":sum(x["presentation_alias_cleanup_available"] for x in rows),
        "presentation_alias_group_counts_by_field":dict(alias_field_counts),
        "records_requiring_source_field_review":sum(x["requires_source_field_review"] for x in rows),
        "source_field_review_reason_counts":dict(review_reason_counts),
        "top_60_requiring_source_field_review":sum(x["requires_source_field_review"] for x in rows[:60]),
        "top_60_with_presentation_alias_cleanup":sum(x["presentation_alias_cleanup_available"] for x in rows[:60]),
        "records_with_numeric_universe_notation":sum(bool(x["bare_numeric_universe_values"]) for x in rows),
        "context_signal_counts_not_anomalies":dict(context_signal_counts),
        "status":"entity_resolution_data_quality_audit_ready_numeric_universes_not_treated_as_errors"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
