#!/usr/bin/env python3
"""Measure registered binary masks and landmarks using the existing AI metric registry.

No automatic segmentation, registration, semantic judgment, or physical-fit certification.
Every file input is byte-pinned; no resizing or inferred correspondence is permitted.
"""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path

from PIL import Image

VERSION = "brickmen-generation-evaluation/v1"
DATA = Path(__file__).resolve().parents[2] / "knowledge/libraries/lego-minifigure-customs/data"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def evaluate(request, base_dir, data_dir=DATA):
    if not isinstance(request, dict) or request.get("schema") != VERSION:
        raise ValueError(f"Request schema must be {VERSION}")
    if request.get("registration_status") != "reviewed" or not isinstance(request.get("alignment_id"), str) or not request["alignment_id"].strip():
        raise ValueError("Declare a reviewed registration and alignment_id before comparing pixels")
    assets = request.get("assets")
    if not isinstance(assets, dict) or not assets:
        raise ValueError("At least one paired mask measurement is required")
    allowed = {"reference_silhouette", "candidate_silhouette", "art_mask", "safe_zone", "keepout_mask"}
    if set(assets) - allowed:
        raise ValueError("Unknown mask role")
    masks, hashes, grid = {}, {}, None
    for role, asset in assets.items():
        if not isinstance(asset, dict) or not isinstance(asset.get("local_path"), str):
            raise ValueError(f"{role} requires local_path and sha256")
        path = (Path(base_dir) / asset["local_path"]).resolve()
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if asset.get("sha256") != sha:
            raise ValueError(f"{role} hash missing or mismatched")
        with Image.open(BytesIO(raw)) as image:
            if image.mode not in {"1", "L"}:
                raise ValueError(f"{role} must be a single-channel binary mask, not a rendered image")
            image = image.convert("L")
            values = image.tobytes()
            if set(values) - {0, 255}:
                raise ValueError(f"{role} contains nonbinary values")
            if grid is not None and image.size != grid:
                raise ValueError("Masks must share the exact registered pixel grid; no resizing is performed")
            grid = image.size
        masks[role] = [value == 255 for value in values]
        hashes[role] = sha
    measurements = {}
    if {"reference_silhouette", "candidate_silhouette"} & masks.keys():
        if not {"reference_silhouette", "candidate_silhouette"} <= masks.keys():
            raise ValueError("Silhouette comparison requires reference and candidate masks")
        ref, candidate = masks["reference_silhouette"], masks["candidate_silhouette"]
        if not any(ref):
            raise ValueError("Reference silhouette is empty")
        intersection = sum(a and b for a, b in zip(ref, candidate))
        union = sum(a or b for a, b in zip(ref, candidate))
        measurements["silhouette_iou"] = intersection / union
    if {"art_mask", "safe_zone", "keepout_mask"} & masks.keys():
        if not {"art_mask", "safe_zone"} <= masks.keys():
            raise ValueError("Print containment requires art_mask and safe_zone")
        art, safe = masks["art_mask"], masks["safe_zone"]
        if not any(art):
            raise ValueError("Art mask is empty; containment cannot pass an absent design")
        keepout = masks.get("keepout_mask", [False] * len(art))
        outside = sum(a and (not s or k) for a, s, k in zip(art, safe, keepout))
        measurements["print_zone_containment"] = 1 - outside / sum(art)
        measurements["art_outside_safe_zone_pixels"] = outside
        measurements["art_in_keepout_pixels"] = sum(a and k for a, k in zip(art, keepout))
    landmarks = request.get("landmarks")
    if landmarks is not None:
        if not isinstance(landmarks, dict) or set(landmarks) != {"reference", "candidate"}:
            raise ValueError("Landmarks require reference and candidate maps")
        reference, candidate = landmarks["reference"], landmarks["candidate"]
        if not isinstance(reference, dict) or not isinstance(candidate, dict) or not reference or set(reference) != set(candidate):
            raise ValueError("Landmark labels must match exactly and cannot be empty")
        width, height = grid
        def point(value):
            if not isinstance(value, list) or len(value) != 2 or any(type(n) not in (int, float) or not math.isfinite(n) for n in value):
                raise ValueError("Landmarks must be finite pixel-coordinate pairs")
            if not (0 <= value[0] < width and 0 <= value[1] < height):
                raise ValueError("Landmark outside the registered image")
            return value
        errors = [math.dist(point(reference[label]), point(candidate[label])) for label in sorted(reference)]
        measurements["landmark_error"] = sum(errors) / len(errors) / math.hypot(width, height)
        measurements["landmark_max_error"] = max(errors) / math.hypot(width, height)
        measurements["landmark_count"] = len(errors)
    if not measurements:
        raise ValueError("No paired measurement inputs")
    thresholds = request.get("thresholds", {})
    directions = {"silhouette_iou": "minimum", "print_zone_containment": "minimum", "landmark_error": "maximum", "landmark_max_error": "maximum"}
    if not isinstance(thresholds, dict) or set(thresholds) - directions.keys():
        raise ValueError("Unknown threshold metric")
    checks = []
    for metric, threshold in sorted(thresholds.items()):
        if metric not in measurements:
            raise ValueError(f"Threshold has no measured input: {metric}")
        if type(threshold) not in (int, float) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError("Thresholds must be finite values in [0, 1]")
        passed = measurements[metric] >= threshold if directions[metric] == "minimum" else measurements[metric] <= threshold
        checks.append({"metric": metric, "direction": directions[metric], "threshold": threshold, "passed": passed})
    registry = json.loads((data_dir / "ai-evaluation-metrics.json").read_text(encoding="utf-8"))
    return {
        "schema": VERSION, "request_sha256": digest(request), "metrics_registry_sha256": digest(registry),
        "alignment_id": request["alignment_id"], "registration_status": "reviewed_as_declared",
        "pixel_grid": list(grid), "input_sha256": hashes, "measurements": measurements, "checks": checks,
        "status": "technical_checks_failed" if any(not c["passed"] for c in checks) else "technical_checks_passed" if checks else "measurements_only",
        "semantic_features": "unreviewed", "physical_fit": "unvalidated", "manufacturing": "unvalidated",
        "limitations": ["Registration and masks are supplied evidence, not automatically verified truth.",
                       "Thresholds are declared for this run, not calibrated official accuracy criteria.",
                       "Matching silhouette cannot establish part identity, source fidelity, style, hidden surfaces, or P0 feature presence."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.request.resolve() == args.output.resolve():
        parser.error("Output must not overwrite the request")
    try:
        request = json.loads(args.request.read_text(encoding="utf-8-sig"))
        report = evaluate(request, args.request.resolve().parent)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        report = {"schema": VERSION, "status": "blocked", "errors": [str(exc)]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "measurements": report.get("measurements", {}), "errors": report.get("errors", [])}))
    return 2 if report["status"] in {"blocked", "technical_checks_failed"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
