#!/usr/bin/env python3
"""Compile manual Skywalker review coverage against the latest identity-family snapshot.

The manual review layer is intentionally append-only/auditable. This tool does not promote
or rewrite decisions; it inventories them, detects duplicate/possibly conflicting decisions,
and emits the remaining review queue after joining against current derived classifications.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

VERSION = "skywalker-manual-review-coverage/v1"


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--review-dir", type=Path, required=True)
    ap.add_argument("--identity-families", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True,
                    help="JSONL of identity-family records not yet manually reviewed by asset id.")
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()

    decision_files = sorted(args.review_dir.glob("skywalker-*.json"))
    by_asset: dict[str, list[dict]] = defaultdict(list)
    by_key: dict[str, list[dict]] = defaultdict(list)
    decision_counts = Counter()
    parsed_files = 0
    malformed_files = []

    for path in decision_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            malformed_files.append({"path": str(path), "error": str(exc)})
            continue
        parsed_files += 1
        batch_id = payload.get("batch_id")
        for record in payload.get("records") or []:
            asset_id = record.get("asset_id")
            key = record.get("character_variant_key")
            decision = record.get("decision")
            item = {
                "source_file": str(path),
                "batch_id": batch_id,
                "asset_id": asset_id,
                "character_variant_key": key,
                "decision": decision,
            }
            if decision:
                decision_counts[decision] += 1
            if asset_id:
                by_asset[str(asset_id)].append(item)
            if key:
                by_key[str(key)].append(item)

    identity_rows = list(load_jsonl(args.identity_families))
    unreviewed = [r for r in identity_rows if str(r.get("asset_id") or "") not in by_asset]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for row in unreviewed:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    duplicate_assets = {
        asset: entries for asset, entries in by_asset.items() if len(entries) > 1
    }
    duplicate_keys = {
        key: entries for key, entries in by_key.items() if len(entries) > 1
    }
    conflicting_assets = {}
    for asset, entries in duplicate_assets.items():
        decisions = sorted({str(e.get("decision")) for e in entries if e.get("decision")})
        if len(decisions) > 1:
            conflicting_assets[asset] = {
                "decisions": decisions,
                "entries": entries,
            }

    unreviewed_suffix = [r for r in unreviewed if r.get("variant_suffix_tokens")]
    unreviewed_direct = [
        r for r in unreviewed
        if r.get("suffix_constraint_status") in {
            "suffix_catalog_text_match",
            "specialized_role_catalog_match",
            "negative_feature_filtered_plus_catalog_text_match",
        }
    ]
    unreviewed_unique = [
        r for r in unreviewed
        if r.get("physical_release_status") == "unique_physical_release_candidate"
    ]

    summary = {
        "schema": "skywalker-manual-review-coverage-summary/v1",
        "processor_version": VERSION,
        "identity_records": len(identity_rows),
        "review_files_found": len(decision_files),
        "review_files_parsed": parsed_files,
        "malformed_review_files": malformed_files,
        "reviewed_asset_ids": len(by_asset),
        "reviewed_variant_keys": len(by_key),
        "manual_decision_records": sum(len(v) for v in by_asset.values()),
        "manual_decision_counts": dict(decision_counts),
        "duplicate_reviewed_asset_ids": len(duplicate_assets),
        "duplicate_reviewed_variant_keys": len(duplicate_keys),
        "conflicting_duplicate_asset_ids": len(conflicting_assets),
        "conflicting_duplicate_assets": conflicting_assets,
        "unreviewed_records": len(unreviewed),
        "unreviewed_suffix_records": len(unreviewed_suffix),
        "unreviewed_direct_suffix_match_records": len(unreviewed_direct),
        "unreviewed_unique_physical_release_candidates": len(unreviewed_unique),
        "unreviewed_release_status_counts": dict(Counter(
            str(r.get("physical_release_status")) for r in unreviewed
        )),
        "unreviewed_suffix_constraint_counts": dict(Counter(
            str(r.get("suffix_constraint_status")) for r in unreviewed_suffix
        )),
        "status": "manual_review_coverage_compiled",
    }
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        k: summary[k] for k in (
            "identity_records",
            "review_files_parsed",
            "reviewed_asset_ids",
            "unreviewed_records",
            "unreviewed_suffix_records",
            "unreviewed_direct_suffix_match_records",
            "unreviewed_unique_physical_release_candidates",
            "conflicting_duplicate_asset_ids",
            "status",
        )
    }, indent=2))


if __name__ == "__main__":
    main()
