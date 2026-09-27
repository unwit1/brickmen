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
    horizontal = reference.get("silhouette_pairs_px", {})
    vertical = reference.get("silhouette_vertical_pairs_px", {})
    if not bbox:
        raise ValueError("Envelope measurement requires body_bbox_px")
    if not horizontal and not vertical:
        raise ValueError("Reference has no silhouette span observations")

    left, top, right, bottom = [float(v) for v in bbox]
    height = bottom - top
    if height <= 0:
        raise ValueError("Invalid body bounding box")

    measurements = {}
    for name, pair in horizontal.items():
        span_px = float(pair["right_x"]) - float(pair["left_x"])
        measurements[name] = {
            "orientation": "horizontal",
            "span_px": span_px,
            "span_over_body_height": span_px / height,
            # Backward-compatible names for existing front-view consumers.
            "width_px": span_px,
            "width_over_body_height": span_px / height,
            "confidence": float(pair.get("confidence", 1.0)),
            "semantic": pair.get("semantic"),
            "notes": pair.get("notes"),
        }

    for name, pair in vertical.items():
        span_px = float(pair["bottom_y"]) - float(pair["top_y"])
        measurements[name] = {
            "orientation": "vertical",
            "span_px": span_px,
            "span_over_body_height": span_px / height,
            "confidence": float(pair.get("confidence", 1.0)),
            "semantic": pair.get("semantic"),
            "notes": pair.get("notes"),
        }

    return {
        "schema_version": "0.2",
        "reference_id": reference["reference_id"],
        "architecture_candidate_id": reference.get("architecture_candidate_id"),
        "view": reference.get("view"),
        "evidence_class": reference["evidence_class"],
        "body_height_px": height,
        "measurements": measurements,
        "mechanical_authority": False,
        "warning": (
            "Silhouette spans describe visual envelopes only. They are not joint "
            "spacing, connector geometry, or physical metrology."
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
