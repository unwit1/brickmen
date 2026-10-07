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
PROCESSOR_VERSION = "brickmen-generation-evaluation/v5"
DATA = Path(__file__).resolve().parents[2] / "knowledge/libraries/lego-minifigure-customs/data"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def declared_input_paths(value, base_dir):
    """Protect every declared local input, including malformed nested requests."""
    if isinstance(value, dict):
        if isinstance(value.get("local_path"), str):
            yield (Path(base_dir) / value["local_path"]).resolve()
        for child in value.values():
            yield from declared_input_paths(child, base_dir)
    elif isinstance(value, list):
        for child in value:
            yield from declared_input_paths(child, base_dir)


def protect_report_inputs(output_path, inputs, label):
    """Reject path and file-identity aliases before any report write."""
    output = output_path.resolve()
    for source in inputs:
        source = source.resolve()
        if output == source or (output.exists() and source.exists() and output.samefile(source)):
            raise ValueError(f"Output must not overwrite {label}")


def pinned_bytes(asset, base_dir, label):
    if not isinstance(asset, dict) or not isinstance(asset.get("local_path"), str):
        raise ValueError(f"{label} requires local_path and sha256")
    raw = (Path(base_dir) / asset["local_path"]).resolve().read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if asset.get("sha256") != sha:
        raise ValueError(f"{label} hash missing or mismatched")
    return raw, sha


def measure_flat_color(config, image):
    """Sample declared native rectangles without resizing or color management."""
    if (not isinstance(config, dict) or set(config) != {"interpretation", "regions"}
            or config["interpretation"] != "decoded_rgba_bytes"
            or not isinstance(config["regions"], list) or not config["regions"]):
        raise ValueError("Flat color requires decoded_rgba_bytes and nonempty regions")
    if image.mode not in {"RGB", "RGBA"} or getattr(image, "n_frames", 1) != 1:
        raise ValueError("Flat color requires a single-frame RGB or RGBA image")
    width, height = image.size
    rgba, regions, checks, seen = image.convert("RGBA"), [], [], set()
    for region in config["regions"]:
        if not isinstance(region, dict) or set(region) != {"id", "box_px", "target_rgba", "max_channel_delta", "minimum_match_fraction"}:
            raise ValueError("Flat color region requires id, box_px, target_rgba, max_channel_delta and minimum_match_fraction")
        name, box, target = region["id"], region["box_px"], region["target_rgba"]
        if not isinstance(name, str) or not name.strip() or name in seen:
            raise ValueError("Flat color region IDs must be nonempty and unique")
        seen.add(name)
        if (not isinstance(box, list) or len(box) != 4 or any(type(v) is not int for v in box)
                or not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height)):
            raise ValueError("Flat color box_px must be a nonempty integer rectangle within the native candidate image")
        if not isinstance(target, list) or len(target) != 4 or any(type(v) is not int or not 0 <= v <= 255 for v in target):
            raise ValueError("Flat color target_rgba must contain four integer bytes")
        tolerance, minimum = region["max_channel_delta"], region["minimum_match_fraction"]
        if type(tolerance) is not int or not 0 <= tolerance <= 255:
            raise ValueError("Flat color max_channel_delta must be an integer byte distance")
        if type(minimum) not in (int, float) or not math.isfinite(minimum) or not 0 < minimum <= 1:
            raise ValueError("Flat color minimum_match_fraction must be finite in (0, 1]")
        raw = rgba.crop(tuple(box)).tobytes()
        pixels = [tuple(raw[i:i + 4]) for i in range(0, len(raw), 4)]
        deltas = [max(abs(a - b) for a, b in zip(pixel, target)) for pixel in pixels]
        matched = sum(delta <= tolerance for delta in deltas)
        fraction = matched / len(pixels)
        regions.append({**region, "sampled_pixels": len(pixels), "matching_pixels": matched,
                        "match_fraction": fraction, "unique_rgba_values": len(set(pixels)),
                        "observed_max_channel_delta": max(deltas),
                        "observed_alpha_range": [min(p[3] for p in pixels), max(p[3] for p in pixels)]})
        checks.append({"constraint": "flat_color_region", "region_id": name,
                       "minimum_match_fraction": minimum, "observed_match_fraction": fraction,
                       "passed": fraction >= minimum})
    return {"flat_color_interpretation": "decoded_rgba_bytes", "flat_color_candidate_dimensions_px": [width, height],
            "flat_color_regions": regions}, checks


def verify_provenance(request, base_dir, masks, grid):
    """Bind supplied measurements to image and registration bytes, not semantic truth."""
    provenance = request.get("provenance")
    dimension_constraint = "candidate_dimensions_px" in request
    required_dimensions = request.get("candidate_dimensions_px")
    if dimension_constraint and (not isinstance(required_dimensions, list) or len(required_dimensions) != 2
                                 or any(type(v) is not int or v <= 0 for v in required_dimensions)):
        raise ValueError("candidate_dimensions_px requires two positive integer native dimensions")
    if provenance is None:
        if request.get("flat_color") is not None:
            raise ValueError("Flat color requires byte-bound source image and registration provenance")
        if dimension_constraint:
            raise ValueError("Native dimensions require byte-bound source image and registration provenance")
        return {"provenance_status": "masks_only"}
    if not isinstance(provenance, dict) or set(provenance) != {"source_images", "registration"}:
        raise ValueError("Provenance requires source_images and registration")
    sources = provenance["source_images"]
    if not isinstance(sources, dict) or "candidate" not in sources or set(sources) - {"reference", "candidate", "production_template"}:
        raise ValueError("Source images require candidate and known evidence roles")
    required_roles = {"candidate"}
    if "reference_silhouette" in masks:
        required_roles.add("reference")
    if "safe_zone" in masks:
        required_roles.add("production_template")
    if not required_roles <= set(sources):
        raise ValueError("Source images missing a measured reference or production template")
    captured, candidate_image = {}, None
    for role, asset in sorted(sources.items()):
        raw, sha = pinned_bytes(asset, base_dir, f"source image {role}")
        with Image.open(BytesIO(raw)) as image:
            image.load()
            captured[role] = {"image_sha256": sha, "original_dimensions_px": list(image.size)}
            if role == "candidate" and dimension_constraint and getattr(image, "n_frames", 1) != 1:
                raise ValueError("Native dimensions require a single-frame candidate image")
            if role == "candidate" and request.get("flat_color") is not None:
                if getattr(image, "n_frames", 1) != 1:
                    raise ValueError("Flat color requires a single-frame RGB or RGBA image")
                candidate_image = image.copy()
    raw, registration_sha = pinned_bytes(provenance["registration"], base_dir, "registration evidence")
    registration = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(registration, dict) or registration.get("schema") != "brickmen-registration-evidence/v1":
        raise ValueError("Registration evidence schema must be brickmen-registration-evidence/v1")
    if registration.get("alignment_id") != request["alignment_id"]:
        raise ValueError("Registration evidence alignment_id differs from request")
    notes, derivation = registration.get("review_notes"), registration.get("mask_derivation")
    if (not isinstance(registration.get("reviewer"), str) or not registration["reviewer"].strip()
            or not isinstance(notes, list) or not notes or any(not isinstance(note, str) or not note.strip() for note in notes)
            or not isinstance(derivation, dict) or not isinstance(derivation.get("method"), str) or not derivation["method"].strip()):
        raise ValueError("Registration evidence requires reviewer, review_notes and mask_derivation")
    declared = registration.get("source_images")
    if not isinstance(declared, dict) or set(declared) != set(captured):
        raise ValueError("Registration source image roles differ from provenance")
    for role, pin in captured.items():
        if not isinstance(declared[role], dict) or any(declared[role].get(key) != value for key, value in pin.items()):
            raise ValueError(f"Registration source image pin differs: {role}")
    if registration.get("mask_sha256") != masks or registration.get("pixel_grid") != list(grid):
        raise ValueError("Registration mask pins or pixel grid differ from measurement inputs")
    if registration.get("landmarks") != request.get("landmarks"):
        raise ValueError("Registration landmarks differ from measurement inputs")
    if registration.get("candidate_dimensions_px") != required_dimensions:
        raise ValueError("Registration candidate dimensions constraint differs from measurement inputs")
    flat_measurements, flat_checks = ({}, []) if candidate_image is None else measure_flat_color(request["flat_color"], candidate_image)
    if registration.get("flat_color") != request.get("flat_color"):
        raise ValueError("Registration flat color regions differ from measurement inputs")
    result = {"provenance_status": "verified_byte_bindings_as_declared",
            "source_image_sha256": {role: pin["image_sha256"] for role, pin in captured.items()},
            "registration_evidence_sha256": registration_sha}
    if candidate_image is not None:
        result.update(flat_measurements)
        result["flat_color_checks"] = flat_checks
    if dimension_constraint:
        native_dimensions = captured["candidate"]["original_dimensions_px"]
        result["native_candidate_dimensions_px"] = native_dimensions
        result["native_dimension_checks"] = [{"constraint": "candidate_dimensions_px",
            "required_dimensions_px": required_dimensions, "observed_dimensions_px": native_dimensions,
            "passed": native_dimensions == required_dimensions}]
    return result


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
        raw, sha = pinned_bytes(asset, base_dir, role)
        with Image.open(BytesIO(raw)) as image:
            if getattr(image, "n_frames", 1) != 1:
                raise ValueError(f"{role} must be a single-frame binary mask")
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
    provenance = verify_provenance(request, base_dir, hashes, grid)
    checks.extend(provenance.pop("flat_color_checks", []))
    checks.extend(provenance.pop("native_dimension_checks", []))
    return {
        "schema": VERSION, "processor_version": PROCESSOR_VERSION,
        "request_sha256": digest(request), "metrics_registry_sha256": digest(registry), **provenance,
        "alignment_id": request["alignment_id"], "registration_status": "reviewed_as_declared",
        "pixel_grid": list(grid), "input_sha256": hashes, "measurements": measurements, "checks": checks,
        "status": "technical_checks_failed" if any(not c["passed"] for c in checks) else "technical_checks_passed" if checks else "measurements_only",
        "semantic_features": "unreviewed", "physical_fit": "unvalidated", "manufacturing": "unvalidated",
        "limitations": ["Registration and masks are supplied evidence, not automatically verified truth.",
                       "Image and registration byte bindings do not establish that masks or landmarks correctly describe those images.",
                       "Thresholds are declared for this run, not calibrated official accuracy criteria.",
                       "Flat color samples decoded native RGBA bytes without color management, resizing or inferred regions; it does not establish physical color accuracy.",
                       "Native dimensions describe decoded source pixels without resizing or orientation correction; registered masks do not waive requested output size.",
                       "Matching silhouette cannot establish part identity, source fidelity, style, hidden surfaces, or P0 feature presence."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        protect_report_inputs(args.output, [args.request], "the request")
    except ValueError as exc:
        parser.error(str(exc))
    try:
        request = json.loads(args.request.read_text(encoding="utf-8-sig"))
        try:
            protect_report_inputs(args.output, declared_input_paths(request, args.request.resolve().parent), "an evidence input")
        except ValueError as exc:
            parser.error(str(exc))
        report = evaluate(request, args.request.resolve().parent)
    except (ValueError, TypeError, KeyError, OSError, SyntaxError) as exc:
        report = {"schema": VERSION, "processor_version": PROCESSOR_VERSION, "status": "blocked", "errors": [str(exc)]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "measurements": report.get("measurements", {}), "errors": report.get("errors", [])}))
    return 2 if report["status"] in {"blocked", "technical_checks_failed"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
