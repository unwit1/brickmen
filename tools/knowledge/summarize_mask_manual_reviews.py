#!/usr/bin/env python3
"""Summarize manual reviews for the ranked mask/headgear route queue."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

VERSION = "mask-route-manual-review-summary/v1"
DECISION_GLOB = "mask-headgear-route-review-*.json"


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranked", type=Path, required=True)
    parser.add_argument("--decisions-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--unreviewed-output", type=Path, required=True)
    args = parser.parse_args()

    ranked = list(load_jsonl(args.ranked))
    ranked_by_fig = {row.get("fig_num"): row for row in ranked if row.get("fig_num")}

    decision_files = sorted(args.decisions_dir.glob(DECISION_GLOB))
    records = []
    parsed_files = []
    parse_errors = []

    for path in decision_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            parsed_files.append(path.name)
            for record in payload.get("records") or []:
                if record.get("fig_num"):
                    records.append({"source_file": path.name, **record})
        except Exception as exc:
            parse_errors.append({"file": path.name, "error": str(exc)})

    by_fig = defaultdict(list)
    for record in records:
        by_fig[record["fig_num"]].append(record)

    reviewed = set(by_fig)
    decision_counts = Counter()
    semantic_counts = Counter()
    translation_counts = Counter()
    conflicts = []

    for fig_num, items in by_fig.items():
        decisions = {item.get("decision") for item in items if item.get("decision")}
        routes = {item.get("confirmed_physical_route") for item in items if item.get("confirmed_physical_route")}
        semantics = {item.get("semantic_function") for item in items if item.get("semantic_function")}
        for item in items:
            if item.get("decision"):
                decision_counts[item["decision"]] += 1
            if item.get("semantic_function"):
                semantic_counts[item["semantic_function"]] += 1
            if item.get("source_translation_status"):
                translation_counts[item["source_translation_status"]] += 1
        if len(decisions) > 1 or len(routes) > 1 or len(semantics) > 1:
            conflicts.append({
                "fig_num": fig_num,
                "decision_count": len(items),
                "decisions": sorted(decisions),
                "confirmed_physical_routes": sorted(routes),
                "semantic_functions": sorted(semantics),
                "source_files": sorted({item["source_file"] for item in items}),
            })

    reviewed_ranked = sorted(fig for fig in reviewed if fig in ranked_by_fig)
    reviewed_outside_ranked = sorted(fig for fig in reviewed if fig not in ranked_by_fig)
    unreviewed = [row for row in ranked if row.get("fig_num") not in reviewed]

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.unreviewed_output.parent.mkdir(parents=True, exist_ok=True)

    with args.unreviewed_output.open("w", encoding="utf-8") as handle:
        for row in unreviewed:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "schema": VERSION,
        "ranked_records": len(ranked),
        "review_files_found": len(decision_files),
        "review_files_parsed": len(parsed_files),
        "review_files_with_errors": len(parse_errors),
        "manual_decision_records": len(records),
        "unique_reviewed_fig_nums": len(reviewed),
        "reviewed_ranked_fig_nums": len(reviewed_ranked),
        "reviewed_outside_ranked_queue": len(reviewed_outside_ranked),
        "unreviewed_ranked_records": len(unreviewed),
        "decision_counts": dict(decision_counts.most_common()),
        "semantic_function_counts": dict(semantic_counts.most_common()),
        "source_translation_status_counts": dict(translation_counts.most_common()),
        "conflicting_review_fig_nums": len(conflicts),
        "conflicts": conflicts,
        "parse_errors": parse_errors,
        "policy": (
            "Manual physical-route decisions are an overlay on the ranked component corpus. "
            "A confirmed physical route does not become source-to-LEGO translation supervision "
            "until an exact source appearance has been independently paired and reviewed."
        ),
        "status": "manual_mask_route_coverage_compiled",
    }
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in {"conflicts", "parse_errors"}}, indent=2))


if __name__ == "__main__":
    main()
