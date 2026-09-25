#!/usr/bin/env python3
"""Profile face-like SVG assets from a reviewed local rioforce/LEGO-Textures clone.

This tool deliberately extracts structural candidates rather than asserting semantic
landmarks. SVG primitives, colors, transforms, side hints, and filename descriptors are
useful supervision, but eye/brow/mouth labels require review or independent validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

VERSION = "rioforce-face-svg-profile/v1"
FACE_HINTS = (
    "face", "eyes", "head",
)
SEMANTIC_TOKENS = (
    "happy", "scared", "angry", "sad", "smile", "sunglasses", "glasses",
    "ghost", "skeleton", "cowboy", "viking", "mermaid", "magician",
    "wrestler", "princess", "superman", "wonder woman", "anakin",
    "leia", "lex luther", "johnny thunder",
)

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1] if "}" in value else value

def attr_local(elem: ET.Element, name: str):
    for key, value in elem.attrib.items():
        if local_name(key) == name:
            return value
    return None

def parse_num(value):
    if value is None:
        return None
    m = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", str(value))
    return float(m.group(0)) if m else None

def parse_style(style: str | None) -> dict[str, str]:
    out = {}
    for part in (style or "").split(";"):
        if ":" in part:
            key, value = part.split(":", 1)
            out[key.strip()] = value.strip()
    return out

def side_hint(path: str) -> str:
    low = path.casefold()
    if re.search(r"\b(back|reverse|rear)\b", low):
        return "reverse"
    if re.search(r"\bfront\b", low):
        return "front"
    return "unknown"

def semantic_tokens(path: str) -> list[str]:
    low = path.casefold()
    return [token for token in SEMANTIC_TOKENS if token in low]

def is_face_like(path: Path) -> bool:
    low = path.as_posix().casefold()
    name = path.stem.casefold()
    if "torso" in name or "legs" in name or "dress" in name or "shield" in name:
        return False
    return any(hint in name for hint in FACE_HINTS) or any(
        f"/{hint}" in low for hint in ("face", "head")
    )

def primitive_record(elem: ET.Element, transform_chain: list[str]) -> dict | None:
    tag = local_name(elem.tag)
    style = parse_style(elem.attrib.get("style"))
    fill = elem.attrib.get("fill") or style.get("fill")
    stroke = elem.attrib.get("stroke") or style.get("stroke")
    base = {
        "tag": tag,
        "id": elem.attrib.get("id"),
        "fill": fill,
        "stroke": stroke,
        "transform_chain": [x for x in transform_chain if x],
    }
    if tag in {"circle", "ellipse"}:
        base.update({
            "cx": parse_num(elem.attrib.get("cx")),
            "cy": parse_num(elem.attrib.get("cy")),
            "rx": parse_num(elem.attrib.get("r") or elem.attrib.get("rx")),
            "ry": parse_num(elem.attrib.get("r") or elem.attrib.get("ry")),
            "candidate_kind": "ellipse_or_circle",
        })
        return base
    if tag == "path" and attr_local(elem, "type") == "arc":
        base.update({
            "cx": parse_num(attr_local(elem, "cx")),
            "cy": parse_num(attr_local(elem, "cy")),
            "rx": parse_num(attr_local(elem, "rx")),
            "ry": parse_num(attr_local(elem, "ry")),
            "candidate_kind": "sodipodi_arc",
        })
        return base
    if tag in {"rect", "polygon", "polyline", "line"}:
        base["candidate_kind"] = "simple_shape"
        return base
    return None

def profile_svg(path: Path, root: Path) -> dict:
    rel = path.relative_to(root).as_posix()
    tree = ET.parse(path)
    svg = tree.getroot()
    width = parse_num(svg.attrib.get("width"))
    height = parse_num(svg.attrib.get("height"))
    view_box = svg.attrib.get("viewBox")
    tag_counts = Counter()
    fills = Counter()
    strokes = Counter()
    primitives = []

    def walk(elem: ET.Element, chain: list[str]):
        tag = local_name(elem.tag)
        tag_counts[tag] += 1
        style = parse_style(elem.attrib.get("style"))
        fill = elem.attrib.get("fill") or style.get("fill")
        stroke = elem.attrib.get("stroke") or style.get("stroke")
        if fill and fill not in {"none", "transparent"}:
            fills[fill] += 1
        if stroke and stroke not in {"none", "transparent"}:
            strokes[stroke] += 1
        transform = elem.attrib.get("transform")
        new_chain = chain + ([transform] if transform else [])
        prim = primitive_record(elem, new_chain)
        if prim:
            primitives.append(prim)
        for child in list(elem):
            walk(child, new_chain)

    walk(svg, [])
    png_sibling = path.with_suffix(".png")
    digest = sha256_file(path)
    return {
        "face_asset_id": f"rioforce-face-{digest[:24]}",
        "source_system": "rioforce/LEGO-Textures",
        "authority": "community_scan_reconstruction",
        "license": "CC BY 3.0",
        "attribution": "LEGO Textures by rioforce",
        "relative_path": rel,
        "sha256": digest,
        "png_sibling": png_sibling.relative_to(root).as_posix() if png_sibling.exists() else None,
        "side_hint": side_hint(rel),
        "filename_semantic_tokens": semantic_tokens(rel),
        "canvas": {
            "width": width,
            "height": height,
            "view_box": view_box,
        },
        "element_counts": dict(tag_counts),
        "fill_counts": dict(fills),
        "stroke_counts": dict(strokes),
        "primitive_candidates": primitives,
        "primitive_candidate_count": len(primitives),
        "extraction": {
            "method": "svg_geometry_candidate",
            "processor_version": VERSION,
            "review_status": "candidate",
            "semantic_landmarks_asserted": False,
        },
        "policy": "Primitive geometry and filename semantics are candidates only; do not treat them as eye/brow/mouth landmarks until reviewed.",
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    rows = []
    errors = []
    for path in sorted(root.rglob("*.svg")):
        if not is_face_like(path.relative_to(root)):
            continue
        try:
            rows.append(profile_svg(path, root))
        except Exception as exc:
            errors.append({"path": path.relative_to(root).as_posix(), "error": str(exc)})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    side_counts = Counter(r["side_hint"] for r in rows)
    summary = {
        "schema": "rioforce-face-svg-profile-summary/v1",
        "created_at": now_iso(),
        "processor_version": VERSION,
        "face_like_svg_records": len(rows),
        "with_png_sibling": sum(1 for r in rows if r["png_sibling"]),
        "with_primitive_candidates": sum(1 for r in rows if r["primitive_candidate_count"]),
        "primitive_candidates_total": sum(r["primitive_candidate_count"] for r in rows),
        "side_hints": dict(side_counts),
        "parse_errors": len(errors),
        "errors": errors,
        "status": "candidate_geometry_requires_semantic_review",
    }
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
