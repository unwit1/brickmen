#!/usr/bin/env python3
"""Render source-image-free structural guide SVGs from BodyGenerationConditioning.

The guide pack is designed for provider adapters and human inspection. It
projects the selected skeleton, visual envelopes, fixed mechanical keep-outs,
and optional conservative articulation sweeps into front/side orthographic
views.

It is guidance/validation material only, never manufacturing geometry.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


CANVAS = 1000.0
MARGIN = 70.0


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _axes(view: str) -> tuple[int, int, str, str]:
    if view == "front":
        return 0, 2, "x", "z"
    if view == "side":
        return 1, 2, "y", "z"
    raise ValueError("view must be front or side")


def _fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _bounds_from_conditioning(
    conditioning: Mapping[str, Any],
    *,
    view: str,
    sweeps: Mapping[str, Any] | None,
) -> tuple[float, float, float, float]:
    h_axis, v_axis, _, _ = _axes(view)
    points: list[tuple[float, float]] = []

    for node in conditioning["skeleton_control"]["nodes"].values():
        p = node["position_normalized_body_height"]
        points.append((float(p[h_axis]), float(p[v_axis])))

    for env in conditioning.get("visual_envelopes", []):
        size = env.get("size_normalized_body_height") or [0, 0, 0]
        if env.get("a_normalized_body_height") is not None:
            for p in (
                env["a_normalized_body_height"],
                env["b_normalized_body_height"],
            ):
                radius = max(abs(float(size[0])), abs(float(size[1]))) / 2.0
                points.extend(
                    [
                        (float(p[h_axis]) - radius, float(p[v_axis]) - radius),
                        (float(p[h_axis]) + radius, float(p[v_axis]) + radius),
                    ]
                )
        else:
            center_id = env.get("center_node")
            if center_id not in conditioning["skeleton_control"]["nodes"]:
                continue
            p = conditioning["skeleton_control"]["nodes"][center_id][
                "position_normalized_body_height"
            ]
            points.extend(
                [
                    (
                        float(p[h_axis]) - abs(float(size[h_axis])) / 2.0,
                        float(p[v_axis]) - abs(float(size[v_axis])) / 2.0,
                    ),
                    (
                        float(p[h_axis]) + abs(float(size[h_axis])) / 2.0,
                        float(p[v_axis]) + abs(float(size[v_axis])) / 2.0,
                    ),
                ]
            )

    for constraint in conditioning.get("mechanical_constraints", []):
        for placement in constraint.get("placements", []):
            p = placement.get("anchor_normalized_body_height")
            lo = placement.get("reference_keepout_local_min_normalized")
            hi = placement.get("reference_keepout_local_max_normalized")
            if p is None or lo is None or hi is None:
                continue
            points.extend(
                [
                    (float(p[h_axis]) + float(lo[h_axis]), float(p[v_axis]) + float(lo[v_axis])),
                    (float(p[h_axis]) + float(hi[h_axis]), float(p[v_axis]) + float(hi[v_axis])),
                ]
            )

    if sweeps:
        for sweep in sweeps.get("joint_sweeps", []):
            box = sweep.get("combined_swept_aabb_normalized_body_height")
            if not box:
                continue
            points.extend(
                [
                    (float(box["min"][h_axis]), float(box["min"][v_axis])),
                    (float(box["max"][h_axis]), float(box["max"][v_axis])),
                ]
            )

    if not points:
        return -0.5, 0.5, 0.0, 1.0
    hmin = min(x for x, _ in points)
    hmax = max(x for x, _ in points)
    vmin = min(y for _, y in points)
    vmax = max(y for _, y in points)
    hspan = max(hmax - hmin, 0.2)
    vspan = max(vmax - vmin, 1.0)
    pad = max(hspan, vspan) * 0.08
    return hmin - pad, hmax + pad, vmin - pad, vmax + pad


def _transform(
    h: float,
    v: float,
    bounds: Sequence[float],
) -> tuple[float, float]:
    hmin, hmax, vmin, vmax = map(float, bounds)
    w = CANVAS - 2 * MARGIN
    hgt = CANVAS - 2 * MARGIN
    x = MARGIN + (h - hmin) / (hmax - hmin) * w
    y = CANVAS - MARGIN - (v - vmin) / (vmax - vmin) * hgt
    return x, y


def _project_box(
    min3: Sequence[float],
    max3: Sequence[float],
    *,
    view: str,
    bounds: Sequence[float],
) -> tuple[float, float, float, float]:
    h_axis, v_axis, _, _ = _axes(view)
    x1, y1 = _transform(float(min3[h_axis]), float(max3[v_axis]), bounds)
    x2, y2 = _transform(float(max3[h_axis]), float(min3[v_axis]), bounds)
    return min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)


def render_guide_svg(
    conditioning: Mapping[str, Any],
    *,
    view: str,
    sweeps: Mapping[str, Any] | None = None,
) -> str:
    h_axis, v_axis, h_name, v_name = _axes(view)
    bounds = _bounds_from_conditioning(conditioning, view=view, sweeps=sweeps)
    nodes = conditioning["skeleton_control"]["nodes"]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS:g} {CANVAS:g}">',
        f"<title>Brickmen {html.escape(conditioning['architecture_id'])} {view} generation guide</title>",
        "<desc>Source-image-free structural generation guide. Not manufacturing geometry.</desc>",
        """<style>
.bg{fill:#111}
.axis{stroke:#555;stroke-width:1;stroke-dasharray:5 5}
.bone{stroke:#ddd;stroke-width:4;stroke-linecap:round}
.node{fill:#fff;stroke:#111;stroke-width:2}
.envelope{fill:#4cc9f0;fill-opacity:.13;stroke:#4cc9f0;stroke-width:2}
.link-envelope{stroke:#4cc9f0;stroke-opacity:.35;stroke-linecap:round;fill:none}
.keepout{fill:#ff6b6b;fill-opacity:.12;stroke:#ff6b6b;stroke-width:2;stroke-dasharray:8 5}
.sweep{fill:#f9c74f;fill-opacity:.07;stroke:#f9c74f;stroke-width:2;stroke-dasharray:4 5}
.label{font-family:monospace;font-size:16px;fill:#fff;paint-order:stroke;stroke:#111;stroke-width:4}
.meta{font-family:monospace;font-size:15px;fill:#bbb}
</style>""",
        '<rect class="bg" x="0" y="0" width="1000" height="1000"/>',
    ]

    # Reference axes at normalized 0.
    x0, _ = _transform(0, bounds[2], bounds)
    _, y0 = _transform(bounds[0], 0, bounds)
    parts.append(f'<line class="axis" x1="{_fmt(x0)}" y1="{MARGIN}" x2="{_fmt(x0)}" y2="{CANVAS-MARGIN}"/>')
    parts.append(f'<line class="axis" x1="{MARGIN}" y1="{_fmt(y0)}" x2="{CANVAS-MARGIN}" y2="{_fmt(y0)}"/>')

    if sweeps:
        for sweep in sweeps.get("joint_sweeps", []):
            box = sweep.get("combined_swept_aabb_normalized_body_height")
            if not box:
                continue
            x, y, w, h = _project_box(box["min"], box["max"], view=view, bounds=bounds)
            parts.append(
                f'<rect class="sweep" data-joint="{html.escape(sweep["joint_id"])}" '
                f'x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(w)}" height="{_fmt(h)}"/>'
            )

    # Mechanical keep-outs behind visual envelopes.
    for constraint in conditioning.get("mechanical_constraints", []):
        profile_id = constraint.get("joint_profile_id") or "mechanical"
        for placement in constraint.get("placements", []):
            p = placement.get("anchor_normalized_body_height")
            lo = placement.get("reference_keepout_local_min_normalized")
            hi = placement.get("reference_keepout_local_max_normalized")
            if p is None or lo is None or hi is None:
                continue
            mn = [float(p[i]) + float(lo[i]) for i in range(3)]
            mx = [float(p[i]) + float(hi[i]) for i in range(3)]
            x, y, w, h = _project_box(mn, mx, view=view, bounds=bounds)
            parts.append(
                f'<rect class="keepout" data-profile="{html.escape(profile_id)}" '
                f'data-anchor="{html.escape(str(placement.get("anchor_node")))}" '
                f'x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(w)}" height="{_fmt(h)}"/>'
            )

    # Visual envelopes.
    for env in conditioning.get("visual_envelopes", []):
        slot = env.get("component_slot_id") or ""
        size = env.get("size_normalized_body_height") or [0, 0, 0]
        if env.get("a_normalized_body_height") is not None:
            a = env["a_normalized_body_height"]
            b = env["b_normalized_body_height"]
            ax, ay = _transform(float(a[h_axis]), float(a[v_axis]), bounds)
            bx, by = _transform(float(b[h_axis]), float(b[v_axis]), bounds)
            # Convert normalized cross-section to screen width using horizontal scale.
            p0 = _transform(0, 0, bounds)
            p1 = _transform(max(abs(float(size[0])), abs(float(size[1]))), 0, bounds)
            width_px = max(abs(p1[0] - p0[0]), 5.0)
            parts.append(
                f'<line class="link-envelope" data-envelope="{html.escape(env["envelope_id"])}" '
                f'data-slot="{html.escape(slot)}" x1="{_fmt(ax)}" y1="{_fmt(ay)}" '
                f'x2="{_fmt(bx)}" y2="{_fmt(by)}" stroke-width="{_fmt(width_px)}"/>'
            )
            lx, ly = (ax + bx) / 2, (ay + by) / 2
        else:
            center_id = env.get("center_node")
            if center_id not in nodes:
                continue
            p = nodes[center_id]["position_normalized_body_height"]
            half = [abs(float(v)) / 2.0 for v in size]
            mn = [float(p[i]) - half[i] for i in range(3)]
            mx = [float(p[i]) + half[i] for i in range(3)]
            x, y, w, h = _project_box(mn, mx, view=view, bounds=bounds)
            tag = "ellipse" if env.get("shape") == "capsule" else "rect"
            if tag == "ellipse":
                parts.append(
                    f'<ellipse class="envelope" data-envelope="{html.escape(env["envelope_id"])}" '
                    f'data-slot="{html.escape(slot)}" cx="{_fmt(x+w/2)}" cy="{_fmt(y+h/2)}" '
                    f'rx="{_fmt(w/2)}" ry="{_fmt(h/2)}"/>'
                )
            else:
                parts.append(
                    f'<rect class="envelope" data-envelope="{html.escape(env["envelope_id"])}" '
                    f'data-slot="{html.escape(slot)}" x="{_fmt(x)}" y="{_fmt(y)}" '
                    f'width="{_fmt(w)}" height="{_fmt(h)}"/>'
                )
            lx, ly = x + w / 2, y + h / 2

        label = slot or env["envelope_id"]
        parts.append(
            f'<text class="label" data-envelope-label="{html.escape(env["envelope_id"])}" '
            f'x="{_fmt(lx+6)}" y="{_fmt(ly-6)}">{html.escape(label)}</text>'
        )

    # Skeleton bones on top.
    for bone in conditioning["skeleton_control"]["bones"]:
        if bone["a"] not in nodes or bone["b"] not in nodes:
            continue
        a = nodes[bone["a"]]["position_normalized_body_height"]
        b = nodes[bone["b"]]["position_normalized_body_height"]
        ax, ay = _transform(float(a[h_axis]), float(a[v_axis]), bounds)
        bx, by = _transform(float(b[h_axis]), float(b[v_axis]), bounds)
        parts.append(
            f'<line class="bone" data-bone="{html.escape(bone["id"])}" '
            f'x1="{_fmt(ax)}" y1="{_fmt(ay)}" x2="{_fmt(bx)}" y2="{_fmt(by)}"/>'
        )

    for node_id, node in nodes.items():
        p = node["position_normalized_body_height"]
        x, y = _transform(float(p[h_axis]), float(p[v_axis]), bounds)
        parts.append(
            f'<circle class="node" data-node="{html.escape(node_id)}" cx="{_fmt(x)}" cy="{_fmt(y)}" r="5"/>'
        )

    parts.append(
        f'<text class="meta" x="20" y="28">view={view} axes={h_name}/{v_name} '
        f'architecture={html.escape(conditioning["architecture_id"])}</text>'
    )
    parts.append(
        '<text class="meta" x="20" y="50">blue=visual envelope; red=mechanical reference/keep-out; yellow=conservative sweep</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def build_guide_pack(
    conditioning: Mapping[str, Any],
    output_dir: str | Path,
    *,
    sweeps: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    for view in ("front", "side"):
        name = f"{view}.svg"
        (output_dir / name).write_text(
            render_guide_svg(conditioning, view=view, sweeps=sweeps),
            encoding="utf-8",
        )
        files[view] = name

    manifest = {
        "schema_version": "0.1",
        "architecture_id": conditioning["architecture_id"],
        "target_height_mm": conditioning["target_height_mm"],
        "views": files,
        "component_slots": conditioning.get("component_plan", {}).get(
            "generated_component_slots", []
        ),
        "has_articulation_sweeps": sweeps is not None,
        "source_image_embedded": False,
        "production_geometry_authority": False,
        "warning": (
            "Guide SVGs are structural visual controls, not manufacturing drawings "
            "or physical clearance/tolerance specifications."
        ),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("output_dir")
    parser.add_argument("--sweeps", default=None)
    args = parser.parse_args()
    conditioning = load_json(args.conditioning)
    sweeps = load_json(args.sweeps) if args.sweeps else None
    build_guide_pack(conditioning, args.output_dir, sweeps=sweeps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
