#!/usr/bin/env python3
"""Inventory a local training-source tree into compact provenance metadata.

This helper intentionally stores metadata only. Raw source assets remain outside Git
unless another ingestion step explicitly promotes a derived artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROCESSOR_VERSION = "training-source-tree-inventory/v1"

RASTER_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
VECTOR_EXTS = {".svg", ".eps", ".ai", ".pdf"}
MODEL_EXTS = {".dat", ".ldr", ".mpd", ".obj", ".fbx", ".gltf", ".glb", ".dae", ".stl"}
DATA_EXTS = {".json", ".jsonl", ".csv", ".tsv", ".xml", ".yaml", ".yml", ".txt"}
CODE_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".ps1", ".bat"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def classify(ext: str) -> str:
    if ext == ".svg":
        return "vector_art"
    if ext in RASTER_EXTS:
        return "raster_image"
    if ext in VECTOR_EXTS:
        return "vector_or_document"
    if ext in MODEL_EXTS:
        return "geometry_or_model"
    if ext in DATA_EXTS:
        return "structured_or_text_data"
    if ext in CODE_EXTS:
        return "code"
    if not ext:
        return "no_extension"
    return "other"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-id", required=True)
    ap.add_argument("--source-url", required=True)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--hash-files-under-bytes", type=int, default=2_000_000)
    args = ap.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"source root not found: {root}")

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    ext_counts: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    top_counts: Counter[str] = Counter()
    total_bytes = 0
    records = []

    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".git/"):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        total_bytes += size
        ext = path.suffix.lower()
        ext_counts[ext or "<none>"] += 1
        asset_class = classify(ext)
        class_counts[asset_class] += 1
        top_counts[rel.split("/", 1)[0]] += 1
        rec = {
            "path": rel,
            "bytes": size,
            "extension": ext or None,
            "asset_class": asset_class,
        }
        if size <= args.hash_files_under_bytes:
            try:
                rec["sha256"] = sha256_file(path)
            except OSError:
                rec["sha256"] = None
        records.append(rec)

    summary = {
        "schema": "training-source-tree-inventory-summary/v1",
        "processor_version": PROCESSOR_VERSION,
        "created_at": now_iso(),
        "source_id": args.source_id,
        "source_url": args.source_url,
        "git_commit": git_commit(root),
        "files": len(records),
        "total_bytes": total_bytes,
        "asset_classes": dict(sorted(class_counts.items())),
        "extensions": dict(sorted(ext_counts.items())),
        "top_level_counts": dict(sorted(top_counts.items())),
        "svg_files_profiled": ext_counts.get(".svg", 0),
        "raster_files_profiled": sum(ext_counts.get(ext, 0) for ext in RASTER_EXTS),
        "inventory_jsonl": "source_inventory.jsonl",
        "storage_policy": "metadata/provenance in Git; raw source tree remains external/local",
    }

    with (out / "source_inventory.jsonl").open("w", encoding="utf-8") as handle:
        for rec in records:
            handle.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    (out / "source_inventory_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
