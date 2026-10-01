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


def resolve_paths(paths: list[str]) -> str | None:
    matches: list[str] = []
    for path in paths:
        if PATTERN.match(path) and path not in matches:
            matches.append(path)
    if len(matches) > 1:
        raise ValueError(
            "push changed multiple numeric Fortnite review batches; "
            "materialize them separately"
        )
    return matches[0] if matches else None


def resolve(event: dict) -> str | None:
    paths: list[str] = []
    for commit in event.get("commits") or []:
        for key in ("added", "modified"):
            paths.extend(str(path) for path in (commit.get(key) or []))
    return resolve_paths(paths)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("event", type=Path, nargs="?")
    parser.add_argument("--paths-stdin", action="store_true")
    args = parser.parse_args()
    if args.paths_stdin:
        import sys

        path = resolve_paths(
            [line.strip() for line in sys.stdin if line.strip()]
        )
    else:
        if args.event is None:
            raise SystemExit("event path is required unless --paths-stdin is used")
        event = json.loads(args.event.read_text(encoding="utf-8"))
        path = resolve(event)
    if path:
        print(path)


if __name__ == "__main__":
    main()
