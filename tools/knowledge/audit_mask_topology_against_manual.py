#!/usr/bin/env python3
"""Audit automated mask topology classifications against manual physical-route reviews."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

VERSION = "mask-topology-manual-audit/v1"
DECISION_GLOB = "mask-headgear-route-review-*.json"


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def expected_topology(confirmed_route: str | None) -> str | None:
    route = str(confirmed_route or "").casefold()
    if not route:
        return None
    if "diving_visor" in route:
        return "head_plus_helmet_plus_diving_facegear"
    if "sports_helmet_plus_separate_faceguard" in route:
        return "head_plus_sports_helmet_plus_faceguard"
    if "transparent_round_bubble_helmet" in route:
        return "head_plus_transparent_or_bubble_enclosure"
    if "mask_wrap" in route:
        return "printed_head_plus_separate_mask_wrap"
    if "separate_bat_cowl" in route:
        return "head_plus_separate_cowl"
    if (
        "full_modified" in route
        or "dedicated_cube_skeleton_head" in route
        or "dedicated_nonstandard_dragonian_head" in route
    ):
        return "dedicated_nonstandard_head_no_separate_headgear"
    if "printed_standard_head_plus_separate_" in route and "_face_mask" in route:
        return "head_plus_separate_species_face_mask"
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--classification", type=Path, required=True)
    parser.add_argument("--decisions-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    auto = {r.get("fig_num"): r for r in load_jsonl(args.classification) if r.get("fig_num")}
    manual = []
    for path in sorted(args.decisions_dir.glob(DECISION_GLOB)):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for record in payload.get("records") or []:
            if record.get("fig_num"):
                manual.append({"source_file": path.name, **record})

    rows = []
    counts = Counter()
    for record in manual:
        expected = expected_topology(record.get("confirmed_physical_route"))
        auto_record = auto.get(record["fig_num"])
        if expected is None:
            status = "manual_route_not_mapped"
        elif auto_record is None:
            status = "not_in_topology_queue"
        else:
            observed = auto_record.get("topology_class")
            confidence = auto_record.get("topology_confidence") or 0
            if observed == expected:
                status = "agreement"
            elif confidence >= 0.95:
                status = "high_confidence_conflict"
            else:
                status = "non_high_confidence_difference"
        counts[status] += 1
        rows.append({
            "fig_num": record["fig_num"],
            "figure_name": record.get("figure_name"),
            "source_file": record["source_file"],
            "confirmed_physical_route": record.get("confirmed_physical_route"),
            "expected_topology_class": expected,
            "auto_topology_class": auto_record.get("topology_class") if auto_record else None,
            "auto_topology_confidence": auto_record.get("topology_confidence") if auto_record else None,
            "status": status,
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    conflicts = [r for r in rows if r["status"] == "high_confidence_conflict"]
    summary = {
        "schema": VERSION,
        "manual_records": len(manual),
        "manual_routes_mapped_to_expected_topology": sum(
            1 for r in rows if r["expected_topology_class"] is not None
        ),
        "status_counts": dict(counts),
        "high_confidence_conflicts": len(conflicts),
        "conflict_fig_nums": [r["fig_num"] for r in conflicts],
        "policy": (
            "The automated topology layer may accelerate physical-structure review, "
            "but a high-confidence result must never silently contradict a mapped "
            "manual physical-route decision."
        ),
        "status": "pass" if not conflicts else "conflict_review_required",
    }
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if conflicts:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
