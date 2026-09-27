#!/usr/bin/env python3
"""Render a transparent SVG review overlay for body-reference fitting.

The output is intentionally an overlay, not a copy of the reference image.
Open it above the source image in an editor/browser to review:
- fitted generation skeleton nodes/bones;
- reference landmarks and residual vectors;
- fitted visual-envelope primitives;
- annotated silhouette-width observations.

This tool does not make manufacturing geometry authoritative.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any, Mapping

from tools.geometry.fit_body_envelope_profile import fit_envelope_profile
from tools.geometry.fit_body_skeleton import (
    fit_skeleton,
    load_reference,
    normalized_landmarks,
)
from tools.geometry.generate_body_skeleton import compile_skeleton, load_spec


def _fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _canvas(reference: Mapping[str, Any]) -> tuple[float, float]:
    size = reference.get("image_size_px")
    if size:
        return float(size[0]), float(size[1])
    bbox = reference.get("body_bbox_px")
    if bbox:
        return max(float(bbox[2]), 1.0), max(float(bbox[3]), 1.0)
    raise ValueError("SVG overlay requires image_size_px or body_bbox_px")


def _project(reference: Mapping[str, Any], x: float, z: float) -> tuple[float, float]:
    bbox = reference.get("body_bbox_px")
    if not bbox:
        raise ValueError("SVG overlay requires body_bbox_px")
    left, top, right, bottom = [float(v) for v in bbox]
    height = bottom - top
    center_x = (left + right) / 2.0
    return center_x + x * height, bottom - z * height


def _envelope_fit_or_empty(
    spec: Mapping[str, Any], reference: Mapping[str, Any]
) -> dict[str, Any]:
    if not reference.get("silhouette_pairs_px"):
        return {
            "parameter_overrides": {},
            "measurements": {},
            "unmapped_measurements": {},
            "production_geometry_authority": False,
        }
    return fit_envelope_profile(spec, reference)


def render_overlay(
    spec: Mapping[str, Any],
    reference: Mapping[str, Any],
    *,
    show_labels: bool = True,
) -> tuple[str, dict[str, Any]]:
    width, height = _canvas(reference)
    skeleton_fit = fit_skeleton(spec, reference)
    envelope_fit = _envelope_fit_or_empty(spec, reference)

    params = dict(skeleton_fit["fit_parameters"])
    params.update(envelope_fit.get("parameter_overrides", {}))
    compiled = compile_skeleton(
        spec,
        target_height_mm=1.0,
        parameter_overrides=params,
    )

    nodes = {
        node_id: _project(reference, float(pos[0]), float(pos[2]))
        for node_id, pos in compiled["nodes_mm"].items()
    }
    observations = normalized_landmarks(reference)

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {_fmt(width)} {_fmt(height)}" '
        f'width="{_fmt(width)}" height="{_fmt(height)}">',
        "<title>Brickmen body-reference fitting review overlay</title>",
        "<desc>Transparent visual review aid. Not manufacturing geometry.</desc>",
        """<style>
.overlay-bbox{fill:none;stroke:currentColor;stroke-width:1;stroke-dasharray:6 4;opacity:.35}
.envelope{fill:currentColor;fill-opacity:.08;stroke:currentColor;stroke-width:1;stroke-dasharray:3 3;opacity:.45}
.bone{stroke:currentColor;stroke-width:2;opacity:.7}
.model-node{fill:none;stroke:currentColor;stroke-width:2}
.reference-node{fill:currentColor;fill-opacity:.2;stroke:currentColor;stroke-width:1.5}
.residual{stroke:currentColor;stroke-width:1;stroke-dasharray:2 2;opacity:.6}
.silhouette{stroke:currentColor;stroke-width:2;opacity:.45}
.label{font-family:monospace;font-size:10px;fill:currentColor}
</style>""",
    ]

    bbox = reference.get("body_bbox_px")
    if bbox:
        left, top, right, bottom = [float(v) for v in bbox]
        parts.append(
            f'<rect class="overlay-bbox" x="{_fmt(left)}" y="{_fmt(top)}" '
            f'width="{_fmt(right-left)}" height="{_fmt(bottom-top)}"/>'
        )

    # Visual envelope primitives are rendered behind the skeleton.
    for envelope in compiled.get("envelopes", []):
        center = nodes.get(envelope.get("center_node"))
        size = envelope.get("size_mm")
        if not center or not size:
            continue
        px_per_norm = float(bbox[3] - bbox[1]) if bbox else 1.0
        w = float(size[0]) * px_per_norm
        h = float(size[2]) * px_per_norm
        cx, cy = center
        if envelope.get("shape") == "capsule":
            parts.append(
                f'<ellipse class="envelope" data-envelope="{html.escape(envelope["id"])}" '
                f'cx="{_fmt(cx)}" cy="{_fmt(cy)}" rx="{_fmt(w/2)}" ry="{_fmt(h/2)}"/>'
            )
        else:
            parts.append(
                f'<rect class="envelope" data-envelope="{html.escape(envelope["id"])}" '
                f'x="{_fmt(cx-w/2)}" y="{_fmt(cy-h/2)}" '
                f'width="{_fmt(w)}" height="{_fmt(h)}"/>'
            )

    for bone in compiled["bones"]:
        if bone["a"] not in nodes or bone["b"] not in nodes:
            continue
        ax, ay = nodes[bone["a"]]
        bx, by = nodes[bone["b"]]
        parts.append(
            f'<line class="bone" data-bone="{html.escape(bone["id"])}" '
            f'x1="{_fmt(ax)}" y1="{_fmt(ay)}" x2="{_fmt(bx)}" y2="{_fmt(by)}"/>'
        )

    matched = 0
    for node_id, observation in observations.items():
        target = observation["coords"]
        if node_id not in nodes or "x" not in target or "z" not in target:
            continue
        matched += 1
        mx, my = nodes[node_id]
        tx, ty = _project(reference, float(target["x"]), float(target["z"]))
        parts.append(
            f'<line class="residual" data-node="{html.escape(node_id)}" '
            f'x1="{_fmt(tx)}" y1="{_fmt(ty)}" x2="{_fmt(mx)}" y2="{_fmt(my)}"/>'
        )
        parts.append(
            f'<circle class="reference-node" data-node="{html.escape(node_id)}" '
            f'cx="{_fmt(tx)}" cy="{_fmt(ty)}" r="4"/>'
        )
        parts.append(
            f'<circle class="model-node" data-node="{html.escape(node_id)}" '
            f'cx="{_fmt(mx)}" cy="{_fmt(my)}" r="3"/>'
        )
        if show_labels:
            label = html.escape(node_id)
            parts.append(
                f'<text class="label" x="{_fmt(mx+5)}" y="{_fmt(my-5)}">{label}</text>'
            )

    for name, pair in reference.get("silhouette_pairs_px", {}).items():
        y = pair.get("y_px")
        if y is None:
            continue
        lx = float(pair["left_x"])
        rx = float(pair["right_x"])
        py = float(y)
        parts.append(
            f'<line class="silhouette" data-measurement="{html.escape(name)}" '
            f'x1="{_fmt(lx)}" y1="{_fmt(py)}" x2="{_fmt(rx)}" y2="{_fmt(py)}"/>'
        )

    parts.append("</svg>")

    report = {
        "schema_version": "0.1",
        "reference_id": reference["reference_id"],
        "skeleton_id": spec["skeleton_id"],
        "matched_landmark_count": matched,
        "skeleton_fit": skeleton_fit,
        "envelope_fit": envelope_fit,
        "overlay_is_source_image_free": True,
        "production_geometry_authority": False,
        "warning": (
            "SVG is a visual review overlay. It does not establish connector "
            "geometry, fit tolerances, or manufacturing authority."
        ),
    }
    return "\n".join(parts) + "\n", report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skeleton")
    parser.add_argument("reference")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--report", default=None)
    parser.add_argument("--no-labels", action="store_true")
    args = parser.parse_args()

    spec = load_spec(args.skeleton)
    reference = load_reference(args.reference)
    svg, report = render_overlay(spec, reference, show_labels=not args.no_labels)
    Path(args.output).write_text(svg, encoding="utf-8")
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
