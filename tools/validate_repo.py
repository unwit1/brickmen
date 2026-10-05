#!/usr/bin/env python3
"""Offline integrity checks for Brickmen tooling and committed metadata.

Checks Python syntax without importing optional model dependencies, literal local
tool references in workflows, JSON syntax and consolidated backlog pointers.
Does not validate physical measurements, source truth or model accuracy.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re


def validate(root):
    root = root.resolve()
    errors = []
    counts = {"python_files": 0, "json_files": 0, "workflow_tool_references": 0, "record_references": 0}
    for base in ("tools", "tests"):
        for path in sorted((root / base).rglob("*.py")):
            counts["python_files"] += 1
            try:
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            except (SyntaxError, ValueError) as exc:
                errors.append(f"{path.relative_to(root)}: {exc}")
    for path in sorted((root / ".github/workflows").glob("*.yml")):
        for target in sorted(set(re.findall(r"\btools/[\w/-]+\.py\b", path.read_text(encoding="utf-8-sig")))):
            counts["workflow_tool_references"] += 1
            if not (root / target).is_file():
                errors.append(f"{path.relative_to(root)} invokes missing tool {target}")
    for path in sorted((root / "knowledge/libraries/lego-minifigure-customs/data").rglob("*.json")):
        counts["json_files"] += 1
        try:
            record = json.loads(path.read_text(encoding="utf-8-sig"))
            if isinstance(record, dict) and "record_ref" in record:
                counts["record_references"] += 1
                location, pointer = record["record_ref"].split("#", 1)
                target = (path.parent / location).resolve()
                if not target.is_relative_to(root):
                    raise ValueError("record_ref leaves repository")
                value = json.loads(target.read_text(encoding="utf-8-sig"))
                if not pointer.startswith("/"):
                    raise ValueError("record_ref requires a JSON pointer")
                for token in pointer[1:].split("/"):
                    key = token.replace("~1", "/").replace("~0", "~")
                    value = value[int(key)] if isinstance(value, list) else value[key]
        except (ValueError, TypeError, KeyError, OSError, AttributeError, IndexError) as exc:
            errors.append(f"{path.relative_to(root)}: {exc}")
    return {"status": "failed" if errors else "passed", "counts": counts, "errors": errors}


def main():
    report = validate(Path(__file__).resolve().parents[1])
    print(json.dumps(report, indent=2))
    return bool(report["errors"])


if __name__ == "__main__":
    raise SystemExit(main())
