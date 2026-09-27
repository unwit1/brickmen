#!/usr/bin/env python3
"""Measure orthographic cross-section profiles from reference OBJ meshes.

Designed for flattened reference geometry, but intentionally OBJ-generic.

The default preset is the Brickmen semantic frame:
- X is lateral width;
- Y is front/back depth;
- Z is vertical and increases upward.

A raw-LDraw preset remains available for source-frame meshes:
- X is lateral width;
- Y is vertical with -Y upward;
- Z is front/back depth.

The tool intersects triangle faces with horizontal planes instead of sampling
only existing vertices, so silhouette spans remain stable across sparse meshes.
Outputs are reference geometry only, never manufacturing tolerances.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

AXIS_INDEX = {"x": 0, "y": 1, "z": 2}

FRAME_PRESETS = {
    "brickmen": {
        "vertical_axis": "z",
        "vertical_direction": "positive",
        "front_horizontal_axis": "x",
        "side_horizontal_axis": "y",
    },
    "ldraw": {
        "vertical_axis": "y",
        "vertical_direction": "negative",
        "front_horizontal_axis": "x",
        "side_horizontal_axis": "z",
    },
}


def load_obj_triangles(path: str | Path) -> list[tuple[tuple[float, float, float], ...]]:
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[tuple[float, float, float], ...]] = []
    for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("v "):
            fields = line.split()
            vertices.append(tuple(map(float, fields[1:4])))
        elif line.startswith("f "):
            refs = line.split()[1:]
            indices = []
            for ref in refs:
                raw_index = int(ref.split("/")[0])
                index = raw_index - 1 if raw_index > 0 else len(vertices) + raw_index
                indices.append(index)
            if len(indices) < 3:
                continue
            # Fan triangulation keeps this usable for generic OBJ faces.
            for i in range(1, len(indices) - 1):
                triangles.append(
                    (vertices[indices[0]], vertices[indices[i]], vertices[indices[i + 1]])
                )
    return triangles


def _dedupe(points: Iterable[Sequence[float]], digits: int = 9) -> list[tuple[float, float, float]]:
    seen = set()
    result = []
    for point in points:
        key = tuple(round(float(v), digits) for v in point)
        if key not in seen:
            seen.add(key)
            result.append(key)
    return result


def triangle_plane_intersections(
    triangle: Sequence[Sequence[float]],
    *,
    axis: int,
    coordinate: float,
    eps: float = 1e-9,
) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        a = tuple(map(float, triangle[i]))
        b = tuple(map(float, triangle[j]))
        da = a[axis] - coordinate
        db = b[axis] - coordinate

        if abs(da) <= eps:
            points.append(a)
        if abs(db) <= eps:
            points.append(b)

        if (da < -eps and db > eps) or (da > eps and db < -eps):
            t = (coordinate - a[axis]) / (b[axis] - a[axis])
            p = tuple(a[k] + t * (b[k] - a[k]) for k in range(3))
            points.append(p)

    return _dedupe(points)


def _bounds(triangles: Sequence[Sequence[Sequence[float]]]) -> tuple[list[float], list[float]]:
    points = [point for tri in triangles for point in tri]
    if not points:
        raise ValueError("Mesh contains no triangle geometry")
    mins = [min(p[i] for p in points) for i in range(3)]
    maxs = [max(p[i] for p in points) for i in range(3)]
    return mins, maxs


def measure_profile(
    triangles: Sequence[Sequence[Sequence[float]]],
    *,
    vertical_axis: str = "z",
    vertical_direction: str = "positive",
    front_horizontal_axis: str = "x",
    side_horizontal_axis: str = "y",
    samples: int = 101,
    extra_heights: Sequence[float] | None = None,
) -> dict[str, Any]:
    if samples < 2:
        raise ValueError("samples must be at least 2")
    va = AXIS_INDEX[vertical_axis]
    fa = AXIS_INDEX[front_horizontal_axis]
    sa = AXIS_INDEX[side_horizontal_axis]
    if len({va, fa, sa}) != 3:
        raise ValueError("vertical/front/side axes must be distinct")
    if vertical_direction not in {"negative", "positive"}:
        raise ValueError("vertical_direction must be 'negative' or 'positive'")

    mins, maxs = _bounds(triangles)
    vertical_min, vertical_max = mins[va], maxs[va]
    body_height = vertical_max - vertical_min
    if body_height <= 0:
        raise ValueError("Mesh has zero vertical extent")

    heights = {i / (samples - 1) for i in range(samples)}
    for value in extra_heights or ():
        if not 0.0 <= float(value) <= 1.0:
            raise ValueError("extra normalized heights must be in [0,1]")
        heights.add(float(value))

    slices = []
    for height_norm in sorted(heights):
        if vertical_direction == "negative":
            plane = vertical_max - height_norm * body_height
        else:
            plane = vertical_min + height_norm * body_height

        points = []
        for triangle in triangles:
            points.extend(
                triangle_plane_intersections(
                    triangle, axis=va, coordinate=plane
                )
            )
        points = _dedupe(points)

        if points:
            front_min = min(p[fa] for p in points)
            front_max = max(p[fa] for p in points)
            side_min = min(p[sa] for p in points)
            side_max = max(p[sa] for p in points)
            front_span = front_max - front_min
            side_span = side_max - side_min
        else:
            front_min = front_max = side_min = side_max = None
            front_span = side_span = 0.0

        slices.append(
            {
                "height_norm": height_norm,
                "plane_coordinate": plane,
                "intersection_point_count": len(points),
                "front": {
                    "min": front_min,
                    "max": front_max,
                    "span": front_span,
                    "span_over_body_height": front_span / body_height,
                },
                "side": {
                    "min": side_min,
                    "max": side_max,
                    "span": side_span,
                    "span_over_body_height": side_span / body_height,
                },
            }
        )

    return {
        "schema_version": "0.2",
        "coordinate_mapping": {
            "vertical_axis": vertical_axis,
            "vertical_direction": vertical_direction,
            "front_horizontal_axis": front_horizontal_axis,
            "side_horizontal_axis": side_horizontal_axis,
        },
        "triangle_count": len(triangles),
        "bbox": {"min": mins, "max": maxs},
        "body_height": body_height,
        "overall": {
            "front_span": maxs[fa] - mins[fa],
            "front_span_over_body_height": (maxs[fa] - mins[fa]) / body_height,
            "side_span": maxs[sa] - mins[sa],
            "side_span_over_body_height": (maxs[sa] - mins[sa]) / body_height,
        },
        "slices": slices,
        "production_geometry_authority": False,
        "warning": (
            "Orthographic profile is derived from reference CAD mesh geometry. "
            "It does not establish physical fit, tolerance, or manufacturing authority."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("obj")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--samples", type=int, default=101)
    parser.add_argument(
        "--height",
        action="append",
        type=float,
        default=[],
        help="Additional normalized height to sample; repeat as needed.",
    )
    parser.add_argument(
        "--frame",
        choices=["brickmen", "ldraw"],
        default="brickmen",
        help="Coordinate-frame preset for interpreting the OBJ.",
    )
    parser.add_argument("--vertical-axis", choices=["x", "y", "z"], default=None)
    parser.add_argument(
        "--vertical-direction",
        choices=["negative", "positive"],
        default=None,
    )
    parser.add_argument("--front-axis", choices=["x", "y", "z"], default=None)
    parser.add_argument("--side-axis", choices=["x", "y", "z"], default=None)
    args = parser.parse_args()

    triangles = load_obj_triangles(args.obj)
    preset = FRAME_PRESETS[args.frame]
    vertical_axis = args.vertical_axis or preset["vertical_axis"]
    vertical_direction = (
        args.vertical_direction or preset["vertical_direction"]
    )
    front_axis = args.front_axis or preset["front_horizontal_axis"]
    side_axis = args.side_axis or preset["side_horizontal_axis"]

    result = measure_profile(
        triangles,
        vertical_axis=vertical_axis,
        vertical_direction=vertical_direction,
        front_horizontal_axis=front_axis,
        side_horizontal_axis=side_axis,
        samples=args.samples,
        extra_heights=args.height,
    )
    result["source_obj"] = str(args.obj)
    result["coordinate_frame_preset"] = args.frame
    Path(args.output).write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
