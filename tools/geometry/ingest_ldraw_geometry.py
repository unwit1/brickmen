#!/usr/bin/env python3
"""Flatten an LDraw part/shortcut hierarchy into auditable geometry.

The ingester works against a local LDraw library. It recursively resolves type-1
subfile references, applies the published affine transforms, triangulates type-4
quads, records source hashes/header/license metadata, and can export an OBJ.

Its output is reference/digital-twin geometry only. It does not infer physical
fit tolerances or manufacturing dimensions from CAD.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

LDU_TO_MM = 0.4
IDENTITY = (
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
)


def ldraw_to_brickmen(
    p: Sequence[float],
) -> tuple[float, float, float]:
    """Map raw LDraw coordinates into Brickmen semantic body axes.

    LDraw uses a right-handed frame with -Y as up. Brickmen uses:
      X = left/right
      Y = back/front depth
      Z = feet/head (up)

    The right-handed mapping is therefore:
      brickmen_x = ldraw_x
      brickmen_y = ldraw_z
      brickmen_z = -ldraw_y
    """
    x, y, z = map(float, p)
    return (x, z, -y)


def apply_transform(t: Sequence[float], p: Sequence[float]) -> tuple[float, float, float]:
    x, y, z = map(float, p)
    return (
        t[0] * x + t[1] * y + t[2] * z + t[3],
        t[4] * x + t[5] * y + t[6] * z + t[7],
        t[8] * x + t[9] * y + t[10] * z + t[11],
    )


def compose_transform(
    parent: Sequence[float], child: Sequence[float]
) -> tuple[float, ...]:
    # R = Rp * Rc; translation = Rp * tc + tp.
    result = [0.0] * 12
    for row in range(3):
        pr = row * 4
        for col in range(3):
            result[pr + col] = sum(
                parent[pr + k] * child[k * 4 + col] for k in range(3)
            )
        result[pr + 3] = (
            sum(parent[pr + k] * child[k * 4 + 3] for k in range(3))
            + parent[pr + 3]
        )
    return tuple(result)


def determinant3(t: Sequence[float]) -> float:
    a, b, c = t[0], t[1], t[2]
    d, e, f = t[4], t[5], t[6]
    g, h, i = t[8], t[9], t[10]
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def type1_transform(tokens: Sequence[str]) -> tuple[float, ...]:
    # tokens after colour: x y z a b c d e f g h i
    x, y, z = map(float, tokens[2:5])
    a, b, c, d, e, f, g, h, i = map(float, tokens[5:14])
    return (a, b, c, x, d, e, f, y, g, h, i, z)


def header_metadata(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": None,
        "author": None,
        "ldraw_org": None,
        "license": None,
        "category": None,
        "help": [],
        "history": [],
        "bfc_certify": None,
    }
    first_description = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("0"):
            continue
        payload = line[1:].strip()
        if first_description is None and payload and not payload.startswith(("!", "BFC")):
            first_description = payload
        if payload.startswith("Name:"):
            result["name"] = payload[5:].strip()
        elif payload.startswith("Author:"):
            result["author"] = payload[7:].strip()
        elif payload.startswith("!LDRAW_ORG"):
            result["ldraw_org"] = payload[len("!LDRAW_ORG"):].strip()
        elif payload.startswith("!LICENSE"):
            result["license"] = payload[len("!LICENSE"):].strip()
        elif payload.startswith("!CATEGORY"):
            result["category"] = payload[len("!CATEGORY"):].strip()
        elif payload.startswith("!HELP"):
            result["help"].append(payload[len("!HELP"):].strip())
        elif payload.startswith("!HISTORY"):
            result["history"].append(payload[len("!HISTORY"):].strip())
        elif payload.startswith("BFC CERTIFY"):
            result["bfc_certify"] = payload[len("BFC CERTIFY"):].strip().split()[0]
    result["description"] = first_description
    return result


def _try_case_insensitive(base: Path, rel: Path) -> Path | None:
    current = base
    for component in rel.parts:
        if not current.is_dir():
            return None
        exact = current / component
        if exact.exists():
            current = exact
            continue
        lowered = component.lower()
        matches = [item for item in current.iterdir() if item.name.lower() == lowered]
        if len(matches) != 1:
            return None
        current = matches[0]
    return current if current.is_file() else None


def resolve_reference(ldraw_root: Path, current_file: Path, ref: str) -> Path | None:
    normalized = Path(ref.replace("\\", "/"))
    candidates = [
        current_file.parent / normalized,
        ldraw_root / "parts" / normalized,
        ldraw_root / "p" / normalized,
        ldraw_root / "models" / normalized,
        ldraw_root / normalized,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    bases = [current_file.parent, ldraw_root / "parts", ldraw_root / "p", ldraw_root / "models", ldraw_root]
    for base in bases:
        if base.exists():
            found = _try_case_insensitive(base, normalized)
            if found:
                return found.resolve()
    return None


def resolve_root_file(ldraw_root: Path, root_file: str) -> Path:
    supplied = Path(root_file)
    if supplied.is_file():
        return supplied.resolve()
    fake_current = ldraw_root / "models" / "__root__.ldr"
    resolved = resolve_reference(ldraw_root, fake_current, root_file)
    if not resolved:
        raise FileNotFoundError(f"Unable to resolve LDraw root file: {root_file}")
    return resolved


def _vertex_tokens(tokens: Sequence[str], start: int) -> tuple[float, float, float]:
    return tuple(map(float, tokens[start : start + 3]))  # type: ignore[return-value]


def flatten_ldraw(
    ldraw_root: str | Path,
    root_file: str,
    *,
    strict_missing: bool = True,
    confine_to_library: bool = False,
    max_depth: int = 128,
) -> dict[str, Any]:
    root = Path(ldraw_root).resolve()
    entry = resolve_root_file(root, root_file)

    triangles: list[tuple[tuple[float, float, float], ...]] = []
    dependencies: dict[str, dict[str, Any]] = {}
    unresolved: list[dict[str, str]] = []
    line_counts = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "other": 0}
    bfc_invertnext_count = 0

    def relative_label(path: Path) -> str:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            return str(path)

    def recurse(
        path: Path,
        transform: Sequence[float],
        *,
        inherited_flip: bool,
        stack: tuple[Path, ...],
        depth: int,
    ) -> None:
        nonlocal bfc_invertnext_count
        if depth > max_depth:
            raise RecursionError(f"LDraw recursion exceeded {max_depth}: {path}")
        if path in stack:
            chain = " -> ".join(relative_label(p) for p in (*stack, path))
            raise ValueError(f"Cyclic LDraw subfile reference: {chain}")

        if confine_to_library and not path.resolve().is_relative_to(root):
            raise ValueError(f"LDraw dependency outside library: {path}")

        source_bytes = path.read_bytes()
        # Preserve read_text's UTF-8 replacement and universal-newline parsing,
        # while provenance identifies the original bytes rather than decoded text.
        text = (
            source_bytes.decode("utf-8", errors="replace")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )
        label = relative_label(path)
        record = dependencies.setdefault(
            label,
            {
                "path": label,
                "sha256": hashlib.sha256(source_bytes).hexdigest(),
                "bytes_utf8": len(text.encode("utf-8")),
                "metadata": header_metadata(text),
                "occurrences": 0,
            },
        )
        record["occurrences"] += 1

        file_flip = inherited_flip
        invert_next = False
        new_stack = (*stack, path)

        for raw in text.splitlines():
            stripped = raw.strip()
            if not stripped:
                continue
            tokens = stripped.split()
            line_type = tokens[0]
            if line_type in line_counts:
                line_counts[line_type] += 1
            else:
                line_counts["other"] += 1

            if line_type == "0":
                upper = stripped.upper()
                if upper.startswith("0 BFC CERTIFY CW"):
                    file_flip = not inherited_flip
                elif upper.startswith("0 BFC CERTIFY CCW"):
                    file_flip = inherited_flip
                elif upper.startswith("0 BFC INVERTNEXT"):
                    invert_next = True
                    bfc_invertnext_count += 1
                continue

            if line_type == "1":
                # Split at most 14 times so a filename containing spaces survives.
                fields = stripped.split(maxsplit=14)
                if len(fields) < 15:
                    raise ValueError(f"Malformed type-1 line in {label}: {stripped}")
                local = type1_transform(fields)
                ref = fields[14].strip()
                child = resolve_reference(root, path, ref)
                if not child:
                    unresolved.append({"parent": label, "reference": ref})
                    if strict_missing:
                        raise FileNotFoundError(
                            f"Unable to resolve {ref!r} referenced by {label}"
                        )
                    invert_next = False
                    continue
                mirrored = determinant3(local) < 0
                child_flip = file_flip ^ invert_next ^ mirrored
                invert_next = False
                recurse(
                    child,
                    compose_transform(transform, local),
                    inherited_flip=child_flip,
                    stack=new_stack,
                    depth=depth + 1,
                )
                continue

            if line_type == "3":
                if len(tokens) < 11:
                    raise ValueError(f"Malformed type-3 line in {label}: {stripped}")
                points = [
                    apply_transform(transform, _vertex_tokens(tokens, 2)),
                    apply_transform(transform, _vertex_tokens(tokens, 5)),
                    apply_transform(transform, _vertex_tokens(tokens, 8)),
                ]
                if file_flip:
                    points[1], points[2] = points[2], points[1]
                triangles.append(tuple(points))
                continue

            if line_type == "4":
                if len(tokens) < 14:
                    raise ValueError(f"Malformed type-4 line in {label}: {stripped}")
                points = [
                    apply_transform(transform, _vertex_tokens(tokens, 2)),
                    apply_transform(transform, _vertex_tokens(tokens, 5)),
                    apply_transform(transform, _vertex_tokens(tokens, 8)),
                    apply_transform(transform, _vertex_tokens(tokens, 11)),
                ]
                if file_flip:
                    points.reverse()
                triangles.append((points[0], points[1], points[2]))
                triangles.append((points[0], points[2], points[3]))
                continue

            # Type 2 lines and type 5 conditional lines are intentionally retained
            # only in source statistics; surface flattening uses triangles/quads.

    recurse(entry, IDENTITY, inherited_flip=False, stack=(), depth=0)

    all_points = [p for tri in triangles for p in tri]
    if all_points:
        mins = [min(p[i] for p in all_points) for i in range(3)]
        maxs = [max(p[i] for p in all_points) for i in range(3)]
        brickmen_points = [ldraw_to_brickmen(p) for p in all_points]
        brickmen_mins = [
            min(p[i] for p in brickmen_points) for i in range(3)
        ]
        brickmen_maxs = [
            max(p[i] for p in brickmen_points) for i in range(3)
        ]
    else:
        mins = maxs = [0.0, 0.0, 0.0]
        brickmen_mins = brickmen_maxs = [0.0, 0.0, 0.0]

    return {
        "schema_version": "0.2",
        "root_file": relative_label(entry),
        "ldraw_root": str(root),
        "triangle_count": len(triangles),
        "source_file_count": len(dependencies),
        "source_occurrence_count": sum(x["occurrences"] for x in dependencies.values()),
        "line_counts": line_counts,
        "bfc_invertnext_count": bfc_invertnext_count,
        "bbox_ldu": {"min": mins, "max": maxs},
        "coordinate_frames": {
            "ldraw": {
                "handedness": "right",
                "axes": {
                    "x": "lateral",
                    "y": "vertical_down; -Y is up",
                    "z": "depth",
                },
            },
            "brickmen": {
                "handedness": "right",
                "axes": {
                    "x": "left_to_right",
                    "y": "back_to_front_depth",
                    "z": "feet_to_head_up",
                },
                "from_ldraw": {
                    "x": "ldraw_x",
                    "y": "ldraw_z",
                    "z": "-ldraw_y",
                },
            },
        },
        "bbox_nominal_mm": {
            "min": [v * LDU_TO_MM for v in mins],
            "max": [v * LDU_TO_MM for v in maxs],
        },
        "bbox_brickmen_ldu": {
            "min": brickmen_mins,
            "max": brickmen_maxs,
        },
        "bbox_brickmen_nominal_mm": {
            "min": [v * LDU_TO_MM for v in brickmen_mins],
            "max": [v * LDU_TO_MM for v in brickmen_maxs],
        },
        "dependencies": sorted(dependencies.values(), key=lambda x: x["path"]),
        "unresolved_references": unresolved,
        "triangles_ldu": triangles,
        "production_geometry_authority": False,
        "warning": (
            "Flattened LDraw geometry is reference CAD. Nominal LDU conversion does "
            "not establish mould tolerances, fit forces, friction, or printable clearances."
        ),
    }


def obj_from_triangles(
    triangles: Iterable[Sequence[Sequence[float]]],
    *,
    scale: float = 1.0,
    frame: str = "ldraw",
    title: str = "Brickmen LDraw reference geometry",
) -> str:
    if frame not in {"ldraw", "brickmen"}:
        raise ValueError("frame must be 'ldraw' or 'brickmen'")
    vertices: list[tuple[float, float, float]] = []
    index: dict[tuple[float, float, float], int] = {}
    faces: list[tuple[int, int, int]] = []

    for triangle in triangles:
        face = []
        for point in triangle:
            output_point = (
                ldraw_to_brickmen(point) if frame == "brickmen" else point
            )
            key = tuple(round(float(v) * scale, 9) for v in output_point)
            if key not in index:
                index[key] = len(vertices) + 1
                vertices.append(key)
            face.append(index[key])
        faces.append(tuple(face))  # type: ignore[arg-type]

    lines = [f"# {title}"]
    for x, y, z in vertices:
        lines.append(f"v {x:.9f} {y:.9f} {z:.9f}")
    for a, b, c in faces:
        lines.append(f"f {a} {b} {c}")
    return "\n".join(lines) + "\n"


def manifest_without_geometry(result: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if key != "triangles_ldu"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ldraw_root", help="Root of an extracted/local LDraw library")
    parser.add_argument("root_file", help="Part/shortcut filename or local path")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--obj", default=None)
    parser.add_argument("--obj-units", choices=["ldu", "mm"], default="mm")
    parser.add_argument(
        "--obj-frame",
        choices=["ldraw", "brickmen"],
        default="ldraw",
        help="Coordinate frame for exported OBJ; manifests always contain both.",
    )
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args()

    result = flatten_ldraw(
        args.ldraw_root,
        args.root_file,
        strict_missing=not args.allow_missing,
    )
    Path(args.manifest).write_text(
        json.dumps(manifest_without_geometry(result), indent=2) + "\n",
        encoding="utf-8",
    )
    if args.obj:
        scale = LDU_TO_MM if args.obj_units == "mm" else 1.0
        payload = obj_from_triangles(
            result["triangles_ldu"],
            scale=scale,
            frame=args.obj_frame,
            title=(
                f"{result['root_file']} ({args.obj_units}; "
                f"{args.obj_frame} frame)"
            ),
        )
        Path(args.obj).write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
