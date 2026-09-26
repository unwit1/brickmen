#!/usr/bin/env python3
"""Promote resolved public BrickLink metadata into provenance-bearing physical reference links."""
from __future__ import annotations
import argparse,json,re
from collections import Counter
from pathlib import Path

VERSION="external-catalog-physical-reference-links/v1"

def load_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:
                yield json.loads(line)

def slug(value):
    return re.sub(r"[^a-z0-9]+","-",str(value or "").casefold()).strip("-")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    out=[]
    class_counts=Counter()
    source_counts=Counter()
    unresolved=0

    for src in load_jsonl(args.input):
        catalog_id=str(src.get("catalog_id") or "").strip().lower()
        catalog_name=src.get("bricklink_catalog_name")
        resolved=bool(catalog_id and catalog_name and src.get("resolution_status")=="bricklink_public_metadata_resolved")
        if not resolved:
            unresolved+=1
        record_class=src.get("record_class") or "unknown"
        class_counts[record_class]+=1
        source_counts[src.get("source_file") or "unknown"]+=1
        out.append({
            "physical_reference_id":f"bricklink-minifigure:{catalog_id}" if catalog_id else None,
            "entity_type":"physical_minifigure_catalog_reference",
            "catalog_namespace":"bricklink_minifigure",
            "catalog_id":catalog_id or None,
            "catalog_name":catalog_name,
            "years_released_start":src.get("years_released_start"),
            "years_released_end":src.get("years_released_end"),
            "catalog_url":src.get("bricklink_public_catalog_url") or src.get("catalog_url"),
            "source_record":{
                "source_file":src.get("source_file"),
                "source_title":src.get("source_title"),
                "source_tab":src.get("source_tab"),
                "source_row":src.get("source_row"),
                "record_class":record_class,
                "name_or_note":src.get("name_or_note"),
                "raw_values":src.get("raw_values") or []
            },
            "provenance":{
                "catalog_page_sha256":src.get("page_sha256"),
                "catalog_retrieved_at":src.get("retrieved_at"),
                "metadata_processor_version":src.get("processor_version")
            },
            "link_status":"physical_reference_link_ready" if resolved else "physical_reference_link_unresolved",
            "policy":"This record preserves a direct BrickLink catalog reference and source provenance. It does not imply a Rebrickable fig_num match, ownership, or possession by the user.",
            "processor_version":VERSION
        })

    out.sort(key=lambda x:(x["catalog_id"] or "",x["source_record"]["source_file"] or "",x["source_record"]["source_row"] or 0))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in out:
            f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
        "schema":"external-catalog-physical-reference-links-summary/v1",
        "processor_version":VERSION,
        "records":len(out),
        "resolved_physical_reference_links":len(out)-unresolved,
        "unresolved_records":unresolved,
        "record_class_counts":dict(class_counts),
        "source_file_counts":dict(source_counts),
        "unique_catalog_ids":len({x["catalog_id"] for x in out if x["catalog_id"]}),
        "status":"external_catalog_physical_reference_links_ready" if not unresolved else "external_catalog_physical_reference_links_partial"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
