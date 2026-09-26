#!/usr/bin/env python3
"""Build a conservative review queue for tracker values that may not be person identities."""
from __future__ import annotations

import argparse, json, re, unicodedata
from collections import Counter
from pathlib import Path

VERSION="tracker-identity-field-audit/v2"
COLORS={"black","white","gold","green","yellow","red","blue","silver","gray","grey","purple","orange","pink","brown","tan","azure","teal"}
MEDIA_OR_STYLE={"mvc","mcu","dcau","dceu","arrowverse","classic","modern","animated"}
ROLE_OR_ERA={"atlantean","phoenix","pirate queen","wild west"}

def norm(value):
    s=unicodedata.normalize("NFKD",str(value or ""))
    s="".join(ch for ch in s if not unicodedata.combining(ch)).casefold()
    s=s.replace("&"," and ")
    s=re.sub(r"[^a-z0-9]+"," ",s)
    return " ".join(s.split())

def load_jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:
                yield json.loads(line)

def source_name(rec):
    return rec.get("name") or rec.get("character") or rec.get("character_or_product_name") or rec.get("name_or_note")

def load_corrections(path):
    if not path:
        return {}
    data=json.loads(path.read_text(encoding="utf-8"))
    out={}
    for row in data.get("records") or []:
        key=(str(row.get("source_title") or ""),str(row.get("source_tab") or ""),int(row.get("source_row") or 0))
        out[key]=row
    return out

def corrected(rec, corrections):
    key=(str(rec.get("source_title") or ""),str(rec.get("source_tab") or ""),int(rec.get("source_row") or 0))
    row=corrections.get(key)
    if not row:
        return rec, None
    out=dict(rec)
    for field,val in (row.get("corrected_fields") or {}).items():
        out[field]=val
    for field in row.get("clear_fields") or []:
        out[field]=None
    return out,row

def signals(rec):
    identity=str(rec.get("identity") or "").strip()
    if not identity:
        return []
    ni=norm(identity)
    toks=set(ni.split())
    out=[]
    if re.fullmatch(r"(?:18|19|20)\d{2}",identity):
        out.append("identity_year_like")
    if rec.get("universe") and ni==norm(rec.get("universe")):
        out.append("identity_duplicates_universe")
    if rec.get("variant") and ni==norm(rec.get("variant")):
        out.append("identity_duplicates_variant")
    if toks and toks <= (COLORS|{"and"}):
        out.append("identity_color_or_material_descriptor")
    if ni in MEDIA_OR_STYLE:
        out.append("identity_media_or_style_descriptor")
    if ni in ROLE_OR_ERA:
        out.append("identity_role_or_era_descriptor")
    if re.search(r"\\$|\)$",identity):
        out.append("identity_trailing_punctuation")
    if re.search(r"\d",identity) and not re.search(r"[A-Za-z].*\d|\d.*[A-Za-z]",identity):
        out.append("identity_numeric_only")
    return sorted(set(out))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--collection-dir",type=Path,required=True)
    ap.add_argument("--design-dir",type=Path,required=True)
    ap.add_argument("--semantic-corrections",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    corrections=load_corrections(args.semantic_corrections)
    rows=[]
    source_records=0
    reason_counts=Counter()
    name_counts=Counter()
    for root in (args.collection_dir,args.design_dir):
        for path in sorted(root.glob("*.jsonl")):
            for raw in load_jsonl(path):
                name=source_name(raw)
                if not name:
                    continue
                source_records+=1
                rec,corr=corrected(raw,corrections)
                ss=signals(rec)
                if not ss:
                    continue
                for sig in ss:
                    reason_counts[sig]+=1
                name_counts[norm(name)]+=1
                score=0
                score+=40 if "identity_year_like" in ss else 0
                score+=35 if "identity_color_or_material_descriptor" in ss else 0
                score+=30 if "identity_duplicates_universe" in ss else 0
                score+=25 if "identity_media_or_style_descriptor" in ss else 0
                score+=20 if "identity_role_or_era_descriptor" in ss else 0
                score+=15 if "identity_duplicates_variant" in ss else 0
                score+=10 if "identity_trailing_punctuation" in ss else 0
                rows.append({
                    "source_file":path.name,
                    "source_title":raw.get("source_title"),
                    "source_tab":raw.get("source_tab"),
                    "source_row":raw.get("source_row"),
                    "record_class":raw.get("record_class"),
                    "name":name,
                    "identity":rec.get("identity"),
                    "variant":rec.get("variant"),
                    "universe":rec.get("universe"),
                    "year":rec.get("year"),
                    "first_appearance":rec.get("first_appearance"),
                    "review_signals":ss,
                    "review_priority_score":score,
                    "known_semantic_correction_applied":bool(corr),
                    "review_status":"needs_identity_field_semantic_review",
                    "policy":"Review-only. A suspicious Identity value is never replaced with a person name automatically. Raw source provenance remains authoritative.",
                    "processor_version":VERSION
                })

    rows.sort(key=lambda x:(-x["review_priority_score"],norm(x["name"]),str(x.get("source_tab") or ""),int(x.get("source_row") or 0)))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
        "schema":"tracker-identity-field-audit-summary/v2",
        "processor_version":VERSION,
        "named_source_records_scanned":source_records,
        "review_records":len(rows),
        "review_reason_counts":dict(reason_counts),
        "top_character_groups":[{"name":name,"records":count} for name,count in name_counts.most_common(50)],
        "status":"identity_field_review_queue_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
