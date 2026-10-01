#!/usr/bin/env python3
"""Rewrite Fortnite semantic-review IDs from their exact canonical payload.

This is a mechanical integrity tool. It does not change annotations, evidence,
review status, reviewer identity, or training eligibility.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.knowledge.validate_fortnite_semantic_reviews import canonical_review_id

VERSION = "fortnite-semantic-review-id-canonicalizer/v1"


def canonicalize_file(path: Path) -> dict[str, int]:
    records = []
    changed = 0
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        expected = canonical_review_id(record)
        if record.get("review_id") != expected:
            record["review_id"] = expected
            changed += 1
        records.append(record)

    if changed:
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
            encoding="utf-8",
        )
    return {"records": len(records), "changed": changed}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    args = parser.parse_args()

    total_records = 0
    total_changed = 0
    for path in args.input:
        result = canonicalize_file(path)
        total_records += result["records"]
        total_changed += result["changed"]
        print(json.dumps({"path": str(path), **result}))
    print(json.dumps({
        "processor_version": VERSION,
        "records": total_records,
        "changed": total_changed,
    }))


if __name__ == "__main__":
    main()
