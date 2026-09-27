#!/usr/bin/env python3
"""Group exact mask/headgear component signatures and propagate reviewed physical topology."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

VERSION = "mask-route-signature-propagation/v1"
DECISION_GLOB = "mask-headgear-route-review-*.json"


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def component_signature(record: dict) -> tuple[tuple[str, ...], tuple[str, ...]]:
    heads = record.get("head_components") or record.get("head_evidence") or []
    headgear = record.get("headgear_components") or record.get("headgear_evidence") or []
    head_ids = tuple(sorted(str(x.get("part_num")) for x in heads if x.get("part_num")))
    headgear_ids = tuple(sorted(str(x.get("part_num")) for x in headgear if x.get("part_num")))
    return head_ids, headgear_ids


def sig_json(sig):
    return {"head_part_nums": list(sig[0]), "headgear_part_nums": list(sig[1])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranked", type=Path, required=True)
    parser.add_argument("--decisions-dir", type=Path, required=True)
    parser.add_argument("--groups-output", type=Path, required=True)
    parser.add_argument("--propagated-output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    ranked = list(load_jsonl(args.ranked))
    groups = defaultdict(list)
    for row in ranked:
        groups[component_signature(row)].append(row)

    reviewed = []
    for path in sorted(args.decisions_dir.glob(DECISION_GLOB)):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for record in payload.get("records") or []:
            if record.get("fig_num"):
                reviewed.append({"source_file": path.name, **record})

    reviewed_ids = {r["fig_num"] for r in reviewed}
    reviewed_by_sig = defaultdict(list)
    for record in reviewed:
        reviewed_by_sig[component_signature(record)].append(record)

    propagated = []
    review_groups = []
    ambiguous_reviewed_signatures = []

    for sig, rows in groups.items():
        refs = reviewed_by_sig.get(sig, [])
        routes = {r.get("confirmed_physical_route") for r in refs if r.get("confirmed_physical_route")}
        if len(routes) > 1:
            ambiguous_reviewed_signatures.append({
                "component_signature": sig_json(sig),
                "routes": sorted(routes),
                "reviewed_fig_nums": sorted(r["fig_num"] for r in refs),
            })

        unreviewed = [r for r in rows if r.get("fig_num") not in reviewed_ids]
        review_groups.append({
            "component_signature": sig_json(sig),
            "record_count": len(rows),
            "reviewed_record_count": len(rows) - len(unreviewed),
            "unreviewed_record_count": len(unreviewed),
            "reviewed_examples": [
                {
                    "fig_num": r.get("fig_num"),
                    "figure_name": r.get("figure_name"),
                    "confirmed_physical_route": r.get("confirmed_physical_route"),
                    "semantic_function": r.get("semantic_function"),
                    "source_file": r.get("source_file"),
                }
                for r in refs
            ],
            "unreviewed_examples": [
                {
                    "fig_num": r.get("fig_num"),
                    "figure_name": r.get("figure_name"),
                    "route_review_priority_score": r.get("route_review_priority_score"),
                    "candidate_routes": r.get("candidate_routes"),
                }
                for r in unreviewed[:12]
            ],
            "representative_fig_num": rows[0].get("fig_num") if rows else None,
            "max_priority_score": max((r.get("route_review_priority_score") or 0) for r in rows),
        })

        if refs and len(routes) == 1:
            inherited_route = next(iter(routes))
            source_review_files = sorted({r["source_file"] for r in refs})
            source_fig_nums = sorted({r["fig_num"] for r in refs})
            for row in unreviewed:
                propagated.append({
                    "fig_num": row.get("fig_num"),
                    "figure_name": row.get("figure_name"),
                    "component_signature": sig_json(sig),
                    "inherited_physical_route": inherited_route,
                    "propagation_basis": "exact_head_and_headgear_part_signature_with_unanimous_manual_route",
                    "reviewed_source_fig_nums": source_fig_nums,
                    "reviewed_source_files": source_review_files,
                    "semantic_function_status": "not_propagated_requires_independent_review",
                    "source_translation_status": "not_propagated_requires_exact_source_appearance_pairing",
                    "confidence": 1.0,
                })

    review_groups.sort(
        key=lambda g: (
            -g["unreviewed_record_count"],
            -g["record_count"],
            -g["max_priority_score"],
            g["representative_fig_num"] or "",
        )
    )
    propagated.sort(key=lambda r: r.get("fig_num") or "")

    args.groups_output.parent.mkdir(parents=True, exist_ok=True)
    with args.groups_output.open("w", encoding="utf-8") as handle:
        for group in review_groups:
            handle.write(json.dumps(group, ensure_ascii=False) + "\n")

    with args.propagated_output.open("w", encoding="utf-8") as handle:
        for record in propagated:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    counts = Counter(len(rows) for rows in groups.values())
    summary = {
        "schema": VERSION,
        "ranked_records": len(ranked),
        "unique_component_signatures": len(groups),
        "duplicate_signature_groups": sum(1 for rows in groups.values() if len(rows) > 1),
        "records_in_duplicate_signature_groups": sum(len(rows) for rows in groups.values() if len(rows) > 1),
        "manual_review_records": len(reviewed),
        "reviewed_component_signatures": len(reviewed_by_sig),
        "propagated_physical_route_records": len(propagated),
        "ambiguous_reviewed_signatures": len(ambiguous_reviewed_signatures),
        "signature_size_distribution": {str(k): v for k, v in sorted(counts.items())},
        "policy": (
            "Only confirmed physical component topology is propagated, and only when the exact "
            "head+headgear part-number signature matches a manually reviewed signature with one "
            "unanimous route. Semantic function and source-to-LEGO translation are never propagated."
        ),
        "status": "exact_component_signature_groups_ready",
        "ambiguous_reviewed_signature_details": ambiguous_reviewed_signatures,
    }
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "ambiguous_reviewed_signature_details"}, indent=2))


if __name__ == "__main__":
    main()
