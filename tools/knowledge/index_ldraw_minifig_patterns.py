#!/usr/bin/env python3
"""Index local LDraw parts; optional previews reuse the verified renderer.

Default selection and IDs remain compatible with the minifigure-pattern catalog.
Broader catalogs require declared standalone Part/Shortcut headers. LDraw remains
community reconstruction evidence; its identifiers are not LEGO design IDs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.geometry.ingest_ldraw_geometry import header_metadata

PROCESSOR_VERSION = "ldraw-minifig-pattern-index/v2"
COMPONENTS = ("head", "torso", "hips", "leg", "arm", "hand", "helmet",
              "headgear", "cowl", "hair", "neck")
MINIFIG_TOKENS = tuple(f"minifig {component}" for component in COMPONENTS)
STANDALONE_TYPES = {"Part", "Shortcut", "Unofficial_Part", "Unofficial_Shortcut"}
CATALOG_FILES = {"minifig_patterns": "ldraw_minifig_patterns.jsonl",
                 "patterned_parts": "ldraw_part_patterns.jsonl",
                 "all_parts": "ldraw_parts.jsonl"}


def parse_header(path: Path, source_bytes: bytes | None = None) -> dict:
    """Parse the leading header from the same bytes used for the source hash."""
    raw = path.read_bytes() if source_bytes is None else source_bytes
    lines = []
    for line in raw.decode("utf-8-sig", errors="replace").splitlines():
        fields = line.strip().split(maxsplit=1)
        if fields and fields[0] != "0":
            break
        lines.append(line)
    metadata = header_metadata("\n".join(lines))
    result = {key: metadata.get(key) or "" for key in
              ("description", "name", "author", "category")}
    for key, prefix in (("ldraw_org", "!LDRAW_ORG"), ("license", "!LICENSE")):
        result[key] = f"{prefix} {metadata[key]}" if metadata[key] else ""
    result["part_type"] = (metadata["ldraw_org"] or "").split()[0] if metadata["ldraw_org"] else ""
    result.update(keywords=[], cmdline="")
    for line in lines:
        fields = line.strip().split(maxsplit=2)
        if len(fields) < 3:
            continue
        if fields[1] == "!KEYWORDS":
            result["keywords"].extend(p.strip() for p in fields[2].split(",") if p.strip())
        elif fields[1] == "!CMDLINE":
            result["cmdline"] = fields[2]
    return result


def classify_component(description: str) -> str:
    lower = description.lower()
    for component in COMPONENTS:
        if f"minifig {component}" in lower:
            return component
    return "other_minifig" if "minifig" in lower else "other_part"


def looks_relevant(header: dict) -> bool:
    description = header["description"].lower()
    return (any(token in description for token in MINIFIG_TOKENS)
            and any(token in description for token in ("pattern", "printed", "with ")))


def selected(header: dict, catalog: str) -> bool:
    if catalog == "minifig_patterns":
        return looks_relevant(header)
    if header["part_type"] not in STANDALONE_TYPES:
        return False
    return catalog == "all_parts" or any(
        token in header["description"].lower() for token in ("pattern", "printed"))


def write_manifest(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ldraw-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--catalog", choices=list(CATALOG_FILES), default="minifig_patterns")
    ap.add_argument("--part", action="append", help="Select a .dat path relative to parts/; repeat to avoid scanning the full catalog")
    ap.add_argument("--ldview", type=Path)
    ap.add_argument("--library-revision", help="Required for previews: pinned library archive hash or commit")
    ap.add_argument("--render-width", type=int, default=1024)
    ap.add_argument("--render-height", type=int, default=1024)
    args = ap.parse_args(argv)
    root = args.ldraw_root.resolve()
    parts_dir = root / "parts"
    if not parts_dir.is_dir():
        ap.error(f"LDraw parts directory not found: {parts_dir}")
    if args.render_width <= 0 or args.render_height <= 0:
        ap.error("Render width and height must be positive")
    if args.ldview and (not args.library_revision or not args.library_revision.strip()):
        ap.error("--library-revision is required with --ldview")
    if args.ldview and not args.ldview.is_file():
        ap.error("LDView executable not found")
    if args.part:
        paths = []
        for name in args.part:
            path = parts_dir / name
            if (Path(name).is_absolute() or not path.resolve().is_relative_to(parts_dir.resolve())
                    or not path.is_file() or path.suffix.lower() != ".dat"):
                ap.error(f"Selected part must be an existing .dat file inside parts/: {name}")
            if path.resolve() in {p.resolve() for p in paths}:
                ap.error(f"Duplicate selected part: {name}")
            paths.append(path)
    else:
        paths = (p for p in parts_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".dat")
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / CATALOG_FILES[args.catalog]
    records = []
    identities = set()
    license_counts: dict[str, int] = {}
    for path in sorted(paths):
        if not path.resolve().is_relative_to(root):
            ap.error(f"Part resolves outside the library: {path}")
        raw = path.read_bytes()
        header = parse_header(path, raw)
        if not selected(header, args.catalog):
            continue
        digest = hashlib.sha256(raw).hexdigest()
        identity = f"ldraw-{path.stem}-{digest[:16]}"
        if identity in identities:
            ap.error(f"Duplicate asset identity in library: {identity}; resolve duplicate standalone sources")
        identities.add(identity)
        license_text = header["license"] or "unknown"
        license_counts[license_text] = license_counts.get(license_text, 0) + 1
        records.append({
            "reference_asset_id": identity,
            "medium": "structured_pattern_reconstruction" if args.catalog != "all_parts" else "structured_part_reconstruction",
            "authority": "community_structured", "source_system": "LDraw Parts Library",
            "source_path": path.relative_to(root).as_posix(), "sha256": digest,
            "description": header["description"], "component_type": classify_component(header["description"]),
            "ldraw_name": header["name"], "author": header["author"],
            "ldraw_org": header["ldraw_org"], "license": license_text,
            "keywords": header["keywords"], "cmdline": header["cmdline"],
            "part_namespace": "ldraw", "part_id": path.stem, "part_type": header["part_type"] or "unknown",
            "category": header["category"] or None, "category_source": "header" if header["category"] else "not_supplied",
            "catalog": args.catalog, "selection_basis": "description_heuristic" if args.catalog != "all_parts" else "declared_standalone_type",
            "preview_path": None, "render_status": "not_requested",
            "storage_policy": "LDraw license governs source; generated previews local by default",
            "processor_version": PROCESSOR_VERSION,
        })
    write_manifest(manifest, records)
    render_manifest = None
    rendered = 0
    failures = 0
    if args.ldview:
        from tools.knowledge import render_ldraw_pattern_training_views as renderer

        render_out = out / "rendered"
        result = renderer.main([
            "--manifest", str(manifest), "--ldraw-root", str(root), "--ldview", str(args.ldview.resolve()),
            "--library-revision", args.library_revision, "--output-dir", str(render_out),
            "--profile", "physical_like", "--view", "front", "--width", str(args.render_width),
            "--height", str(args.render_height)], quiet=True)
        render_manifest = render_out / "render_manifest.jsonl"
        previews = {r["source_reference_asset_id"]: r for r in renderer.load(render_manifest)}
        for record in records:
            preview = previews.get(record["reference_asset_id"])
            if preview:
                record.update(preview_path=preview["local_path"], render_status="rendered",
                              preview_sha256=preview["sha256"], derived_asset_id=preview["derived_asset_id"])
                rendered += 1
            else:
                record["render_status"] = "error"
                failures += 1
        write_manifest(manifest, records)
        if result and not failures:
            failures = 1
    report = {
        "schema": "ldraw-minifig-pattern-index-report/v2", "created_at": datetime.now(timezone.utc).isoformat(),
        "processor_version": PROCESSOR_VERSION, "ldraw_root": str(root), "catalog": args.catalog,
        "parts_indexed": len(records), "previews_rendered": rendered, "render_errors": failures,
        "license_counts": license_counts, "manifest": str(manifest),
        "render_manifest": str(render_manifest) if render_manifest else None,
        "note": "LDraw is community reconstruction evidence. Preserve attribution/license and catalog namespace; generated previews do not validate physical fit.",
    }
    (out / "import_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
