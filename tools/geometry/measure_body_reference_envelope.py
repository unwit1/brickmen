#!/usr/bin/env python3
"""Normalize visual-envelope measurements from a body reference.

Silhouette measurements are intentionally separate from skeletal landmarks.
They describe visual mass/outer shape, not mechanical pivot locations.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from tools.geometry.fit_body_skeleton import load_reference


def measure_envelope(reference: Mapping[str, Any]) -> dict[str, Any]:
    bbox = reference.get("body_bbox_px")
    pairs = reference.get("silhouette_pairs_px", {})
    if not bbox:
        raise ValueError("Envelope measurement requires body_bbox_px")
    if not pairs:
        raise ValueError("Reference has no silhouette_pairs_px")

    left, top, right, bottom = [float(v) for v in bbox]
    height = bottom - top
    if height <= 0:
        raise ValueError("Invalid body bounding box")

    measurements = {}
    for name, pair in pairs.items():
        width_px = float(pair["right_x"]) - float(pair["left_x"])
        measurements[name] = {
            "width_px": width_px,
            "width_over_body_height": width_px / height,
            "confidence": float(pair.get("confidence", 1.0)),
            "semantic": pair.get("semantic"),
            "notes": pair.get("notes"),
        }

    return {
        "schema_version": "0.1",
        "reference_id": reference["reference_id"],
        "architecture_candidate_id": reference.get("architecture_candidate_id"),
        "evidence_class": reference["evidence_class"],
        "body_height_px": height,
        "measurements": measurements,
        "mechanical_authority": False,
        "warning": (
            "Silhouette widths describe visual envelopes only. They are not "
            "joint spacing, connector geometry, or physical metrology."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("-o", "--output", default=None)
    args = parser.parse_args()

    reference = load_reference(args.reference)
    result = measure_envelope(reference)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
