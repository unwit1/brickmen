#!/usr/bin/env python3
"""Index patterned minifigure parts from a local LDraw Parts Library.

The LDraw Parts Library is community-run and not authored/approved by LEGO. This tool
preserves each file's LDraw license header and treats the library as secondary structured
evidence for official LEGO part/pattern reconstructions.

Optional rendering uses LDView if --ldview is supplied. Generated previews stay local.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROCESSOR_VERSION = "ldraw-minifig-pattern-index/v1"

MINIFIG_TOKENS = (
    "minifig head",
    "minifig torso",
    "minifig hips",
    "minifig leg",
    "minifig arm",
    "minifig hand",
    "minifig helmet",
    "minifig headgear",
    "minifig cowl",
    "minifig hair",
    "minifig neck",
)

HEADER_KEYS = ("Name:", "Author:", "!LDRAW_ORG", "!LICENSE", "!KEYWORDS", "!CMDLINE")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_header(path: Path) -> dict:
    result = {
        "description": "",
        "name": "",
        "author": "",
        "ldraw_org": "",
        "license": "",
        "keywords": [],
        "cmdline": "",
    }
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return result
    if lines and lines[0].startswith("0 "):
        result["description"] = lines[0][2:].strip()
    for line in lines[1:80]:
        if not line.startswith("0 "):
            break
        text = line[2:].strip()
        if text.startswith("Name:"):
            result["name"] = text.split(":", 1)[1].strip()
        elif text.startswith("Author:"):
            result["author"] = text.split(":", 1)[1].strip()
        elif text.startswith("!LDRAW_ORG"):
            result["ldraw_org"] = text
        elif text.startswith("!LICENSE"):
            result["license"] = text
        elif text.startswith("!KEYWORDS"):
            result["keywords"].extend(
                part.strip() for part in text.split("!KEYWORDS", 1)[1].split(",") if part.strip()
            )
        elif text.startswith("!CMDLINE"):
            result["cmdline"] = text.split("!CMDLINE", 1)[1].strip()
    return result


def classify_component(description: str) -> str:
    lower = description.lower()
    for component in (
        "head", "torso", "hips", "leg", "arm", "hand", "helmet",
        "headgear", "cowl", "hair", "neck"
    ):
        if f"minifig {component}" in lower:
            return component
    return "other_minifig"


def looks_relevant(header: dict) -> bool:
    description = header["description"].lower()
    if not any(token in description for token in MINIFIG_TOKENS):
        return False
    return "pattern" in description or "printed" in description or "with " in description


def render_preview(ldview: Path, part: Path, output: Path, width: int, height: int) -> tuple[bool, str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(ldview),
        str(part),
        f"-SaveSnapshot={output}",
        f"-SaveWidth={width}",
        f"-SaveHeight={height}",
        "-SaveZoomToFit=1",
        "-AutoCrop=1",
        "-SaveAlpha=1",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.returncode == 0, (proc.stderr or proc.stdout)[-2000:]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ldraw-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--ldview", type=Path)
    ap.add_argument("--render-width", type=int, default=1024)
    ap.add_argument("--render-height", type=int, default=1024)
    args = ap.parse_args()

    root = args.ldraw_root.resolve()
    parts_dir = root / "parts"
    if not parts_dir.is_dir():
        raise SystemExit(f"LDraw parts directory not found: {parts_dir}")

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    previews = out / "previews"

    ldview = args.ldview.resolve() if args.ldview else None
    if ldview and not ldview.exists():
        raise SystemExit(f"LDView executable not found: {ldview}")

    manifest_path = out / "ldraw_minifig_patterns.jsonl"
    count = 0
    rendered = 0
    render_errors = 0
    license_counts: dict[str, int] = {}

    with manifest_path.open("w", encoding="utf-8") as mf:
        for path in sorted(parts_dir.rglob("*.dat")):
            header = parse_header(path)
            if not looks_relevant(header):
                continue

            rel = path.relative_to(root).as_posix()
            digest = sha256_file(path)
            license_text = header["license"] or "unknown"
            license_counts[license_text] = license_counts.get(license_text, 0) + 1
            preview_path = None
            render_status = "not_requested"

            if ldview:
                preview_path = previews / (path.stem + ".png")
                ok, detail = render_preview(
                    ldview, path, preview_path, args.render_width, args.render_height
                )
                if ok:
                    rendered += 1
                    render_status = "rendered"
                else:
                    render_errors += 1
                    render_status = "error"
                    preview_path = None

            record = {
                "reference_asset_id": f"ldraw-{path.stem}-{digest[:16]}",
                "medium": "structured_pattern_reconstruction",
                "authority": "community_structured",
                "source_system": "LDraw Parts Library",
                "source_path": rel,
                "sha256": digest,
                "description": header["description"],
                "component_type": classify_component(header["description"]),
                "ldraw_name": header["name"],
                "author": header["author"],
                "ldraw_org": header["ldraw_org"],
                "license": license_text,
                "keywords": header["keywords"],
                "cmdline": header["cmdline"],
                "preview_path": str(preview_path) if preview_path else None,
                "render_status": render_status,
                "storage_policy": "LDraw license governs source; generated previews local by default",
                "processor_version": PROCESSOR_VERSION,
            }
            mf.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    report = {
        "schema": "ldraw-minifig-pattern-index-report/v1",
        "created_at": now_iso(),
        "processor_version": PROCESSOR_VERSION,
        "ldraw_root": str(root),
        "parts_indexed": count,
        "previews_rendered": rendered,
        "render_errors": render_errors,
        "license_counts": license_counts,
        "manifest": str(manifest_path),
        "note": "LDraw is an unofficial community reconstruction source. Preserve attribution/license and never relabel as LEGO-authored art.",
    }
    (out / "import_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
