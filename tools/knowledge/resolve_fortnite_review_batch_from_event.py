#!/usr/bin/env python3
"""Resolve the one numeric Fortnite semantic-review batch changed by a push."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PATTERN = re.compile(
    r"^knowledge/libraries/lego-minifigure-customs/data/"
    r"semantic-review-batches/fortnite-first-review-batch-[0-9]{4}\.json$"
)


def resolve(event: dict) -> str | None:
    matches: list[str] = []
    for commit in event.get("commits") or []:
        for key in ("added", "modified"):
            for path in commit.get(key) or []:
                if PATTERN.match(path) and path not in matches:
                    matches.append(path)
    if len(matches) > 1:
        raise ValueError(
            "push changed multiple numeric Fortnite review batches; "
            "materialize them separately"
        )
    return matches[0] if matches else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("event", type=Path)
    args = parser.parse_args()
    event = json.loads(args.event.read_text(encoding="utf-8"))
    path = resolve(event)
    if path:
        print(path)


if __name__ == "__main__":
    main()
