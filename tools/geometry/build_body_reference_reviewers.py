#!/usr/bin/env python3
"""Build source-image-free HTML reviewers for all pixel references in a manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.geometry.build_body_reference_review_ui import build_review_html
from tools.geometry.fit_body_skeleton import load_reference


def build_reviewers(manifest_path: str | Path, output_dir: str | Path) -> dict:
    manifest_path = Path(manifest_path)
    output_dir = Path(output_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    skipped = []

    for entry in manifest["references"]:
        source = (base / entry["reference"]).resolve()
        ref = load_reference(source)
        if ref.get("landmark_coordinate_mode", "pixel") != "pixel":
            skipped.append(
                {
                    "reference_id": ref["reference_id"],
                    "reason": "non_pixel_reference",
                }
            )
            continue
        filename = f"{ref['reference_id']}.html"
        output = output_dir / filename
        output.write_text(build_review_html(ref), encoding="utf-8")
        records.append(
            {
                "reference_id": ref["reference_id"],
                "reference_file": entry["reference"],
                "reviewer_file": filename,
                "source_image_embedded": False,
            }
        )

    index = {
        "schema_version": "0.1",
        "source_manifest": str(manifest_path),
        "reviewers": records,
        "skipped": skipped,
        "production_geometry_authority": False,
    }
    (output_dir / "index.json").write_text(
        json.dumps(index, indent=2) + "\n", encoding="utf-8"
    )
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("output_dir")
    args = parser.parse_args()
    build_reviewers(args.manifest, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
