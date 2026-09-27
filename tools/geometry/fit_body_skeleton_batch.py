#!/usr/bin/env python3
"""Batch-fit Brickmen body references declared in a manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.geometry.fit_body_skeleton import fit_skeleton, load_reference
from tools.geometry.generate_body_skeleton import load_spec


def resolve_from_manifest(manifest_path: Path, relative: str) -> Path:
    return (manifest_path.parent / relative).resolve()


def run_manifest(manifest_path: str | Path) -> dict:
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    results = []

    for entry in manifest["references"]:
        reference_path = resolve_from_manifest(manifest_path, entry["reference"])
        skeleton_path = resolve_from_manifest(manifest_path, entry["skeleton"])
        reference = load_reference(reference_path)
        skeleton = load_spec(skeleton_path)
        fit = fit_skeleton(skeleton, reference)
        fit["role"] = entry.get("role")
        fit["reference_file"] = str(reference_path)
        fit["skeleton_file"] = str(skeleton_path)
        results.append(fit)

    status_counts = {}
    for result in results:
        status_counts[result["fit_status"]] = (
            status_counts.get(result["fit_status"], 0) + 1
        )

    return {
        "schema_version": "0.1",
        "manifest": str(manifest_path),
        "result_count": len(results),
        "status_counts": status_counts,
        "results": results,
        "production_geometry_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("-o", "--output", default=None)
    args = parser.parse_args()

    payload = json.dumps(run_manifest(args.manifest), indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
