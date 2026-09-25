#!/usr/bin/env python3
"""Build a provenance-aware LEGO minifigure reference manifest from Rebrickable bulk CSVs.

This tool indexes metadata and source image URLs. It does NOT mirror the image corpus into
Git. Raw reference images should be materialized into a local research directory by a
separate fetcher that respects source terms and records hashes/provenance.

Required Rebrickable bulk files:
  minifigs.csv(.gz)
  inventories.csv(.gz)
  inventory_minifigs.csv(.gz)
  sets.csv(.gz)
  themes.csv(.gz)

Strongly recommended optional files:
  inventory_parts.csv(.gz)
  parts.csv(.gz)
  colors.csv(.gz)
  part_relationships.csv(.gz)
  elements.csv(.gz)

When inventory_parts is available, this importer also resolves the component inventory
inside each minifig (heads, torsos, legs, helmets, accessories, etc.) and emits each
available component image as a separate reference candidate. Rebrickable documents
minifigures as a special type of Set and exposes their parts separately.

Outputs:
  physical_samples.jsonl
  component_samples.jsonl
  reference_manifest.jsonl
  corpus.sqlite3
  import_report.json
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

PROCESSOR_VERSION = "lego-reference-manifest/v2"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8-sig", newline="")
    return path.open("r", encoding="utf-8-sig", newline="")


def resolve_table(root: Path, name: str, *, required: bool = True) -> Path | None:
    for candidate in (root / f"{name}.csv.gz", root / f"{name}.csv"):
        if candidate.exists():
            return candidate
    if required:
        raise FileNotFoundError(f"missing Rebrickable table: {name}.csv(.gz) in {root}")
    return None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rows(path: Path) -> Iterator[dict[str, str]]:
    with open_text(path) as f:
        yield from csv.DictReader(f)


def theme_ancestry(theme_id: str, themes: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    current = theme_id
    while current and current not in seen and current in themes:
        seen.add(current)
        item = themes[current]
        result.append({"id": current, "name": item.get("name", "")})
        current = item.get("parent_id", "") or ""
    return result


def stable_id(kind: str, *parts: str) -> str:
    payload = json.dumps([kind, *parts], separators=(",", ":"), ensure_ascii=False)
    return f"{kind}-{hashlib.sha256(payload.encode()).hexdigest()[:24]}"


def as_int(value: str | None, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;

        CREATE TABLE IF NOT EXISTS sample (
            sample_id TEXT PRIMARY KEY,
            fig_num TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            num_parts INTEGER,
            image_url TEXT,
            medium TEXT NOT NULL,
            authority TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS set_occurrence (
            sample_id TEXT NOT NULL,
            set_num TEXT NOT NULL,
            set_name TEXT,
            year INTEGER,
            theme_id TEXT,
            theme_path_json TEXT,
            quantity INTEGER,
            PRIMARY KEY(sample_id, set_num)
        );

        CREATE TABLE IF NOT EXISTS component (
            component_id TEXT PRIMARY KEY,
            sample_id TEXT NOT NULL,
            inventory_id TEXT NOT NULL,
            part_num TEXT NOT NULL,
            part_name TEXT,
            color_id TEXT,
            color_name TEXT,
            quantity INTEGER,
            is_spare INTEGER,
            image_url TEXT,
            print_of TEXT,
            component_role TEXT,
            UNIQUE(sample_id, inventory_id, part_num, color_id, is_spare)
        );

        CREATE TABLE IF NOT EXISTS reference_asset (
            reference_asset_id TEXT PRIMARY KEY,
            sample_id TEXT NOT NULL,
            component_id TEXT,
            medium TEXT NOT NULL,
            authority TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_role TEXT NOT NULL,
            sha256 TEXT,
            retrieved_at TEXT
        );

        CREATE TABLE IF NOT EXISTS source_file (
            table_name TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            sha256 TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_occurrence_set ON set_occurrence(set_num);
        CREATE INDEX IF NOT EXISTS idx_occurrence_theme ON set_occurrence(theme_id);
        CREATE INDEX IF NOT EXISTS idx_component_sample ON component(sample_id);
        CREATE INDEX IF NOT EXISTS idx_component_part ON component(part_num);
        """
    )


def infer_component_role(name: str) -> str:
    lower = name.lower()
    ordered = [
        ("headgear", ("helmet", "cowl", "hood", "mask", "hat", "cap", "hair", "headgear")),
        ("head", ("minifig head", "head ")),
        ("torso", ("torso", "upper body")),
        ("arm", ("minifig arm", " arm")),
        ("hand", ("minifig hand", " hand")),
        ("hips", ("hips", "hip ")),
        ("leg", ("minifig leg", "legs", "leg ")),
        ("bodywear", ("armor", "armour", "pauldron", "neck bracket", "shoulder", "cape", "backpack")),
        ("weapon_or_tool", ("sword", "gun", "blaster", "staff", "axe", "shield", "tool", "weapon")),
    ]
    for role, tokens in ordered:
        if any(token in lower for token in tokens):
            return role
    return "other"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebrickable-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    root = args.rebrickable_dir.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    required_names = ["minifigs", "inventories", "inventory_minifigs", "sets", "themes"]
    optional_names = ["inventory_parts", "parts", "colors", "part_relationships", "elements"]

    files: dict[str, Path] = {}
    for name in required_names:
        path = resolve_table(root, name, required=True)
        assert path is not None
        files[name] = path
    for name in optional_names:
        path = resolve_table(root, name, required=False)
        if path is not None:
            files[name] = path

    source_hashes = {name: sha256_file(path) for name, path in files.items()}

    themes = {r["id"]: r for r in rows(files["themes"])}
    sets = {r["set_num"]: r for r in rows(files["sets"])}

    inventory_to_set: dict[str, str] = {}
    set_to_inventories: dict[str, list[str]] = defaultdict(list)
    for r in rows(files["inventories"]):
        inventory_id = r["id"]
        set_num = r["set_num"]
        inventory_to_set[inventory_id] = set_num
        set_to_inventories[set_num].append(inventory_id)

    fig_occurrences: dict[str, list[dict[str, object]]] = defaultdict(list)
    for r in rows(files["inventory_minifigs"]):
        fig_num = r["fig_num"]
        set_num = inventory_to_set.get(r["inventory_id"])
        if not set_num:
            continue
        set_row = sets.get(set_num, {})
        theme_id = set_row.get("theme_id", "")
        fig_occurrences[fig_num].append(
            {
                "set_num": set_num,
                "set_name": set_row.get("name", ""),
                "year": as_int(set_row.get("year")) or None,
                "theme_id": theme_id or None,
                "theme_path": theme_ancestry(theme_id, themes) if theme_id else [],
                "quantity": as_int(r.get("quantity")),
            }
        )

    parts: dict[str, dict[str, str]] = {}
    if "parts" in files:
        parts = {r["part_num"]: r for r in rows(files["parts"])}

    colors: dict[str, dict[str, str]] = {}
    if "colors" in files:
        colors = {r["id"]: r for r in rows(files["colors"])}

    print_of: dict[str, str] = {}
    if "part_relationships" in files:
        for r in rows(files["part_relationships"]):
            rel = (r.get("rel_type") or "").lower()
            child = r.get("child_part_num") or ""
            parent = r.get("parent_part_num") or ""
            if rel == "p" and child and parent:
                # Rebrickable relationship P is commonly "print of".
                print_of[child] = parent

    components_by_inventory: dict[str, list[dict[str, object]]] = defaultdict(list)
    if "inventory_parts" in files:
        for r in rows(files["inventory_parts"]):
            inventory_id = r.get("inventory_id") or ""
            part_num = r.get("part_num") or ""
            if not inventory_id or not part_num:
                continue
            part_row = parts.get(part_num, {})
            color_id = r.get("color_id") or ""
            color_row = colors.get(color_id, {})
            name = part_row.get("name") or part_num
            image_url = (r.get("img_url") or "").strip()
            components_by_inventory[inventory_id].append(
                {
                    "inventory_id": inventory_id,
                    "part_num": part_num,
                    "part_name": name,
                    "color_id": color_id or None,
                    "color_name": color_row.get("name") or None,
                    "quantity": as_int(r.get("quantity"), 1),
                    "is_spare": as_int(r.get("is_spare")),
                    "image_url": image_url or None,
                    "print_of": print_of.get(part_num),
                    "component_role": infer_component_role(name),
                }
            )

    db_path = out / "corpus.sqlite3"
    conn = sqlite3.connect(db_path)
    init_db(conn)
    for name, path in files.items():
        conn.execute(
            "INSERT OR REPLACE INTO source_file(table_name,path,sha256) VALUES(?,?,?)",
            (name, str(path), source_hashes[name]),
        )

    samples_path = out / "physical_samples.jsonl"
    components_path = out / "component_samples.jsonl"
    refs_path = out / "reference_manifest.jsonl"

    counts = {
        "physical_samples": 0,
        "figure_reference_assets": 0,
        "component_records": 0,
        "component_reference_assets": 0,
        "set_occurrence_links": 0,
        "figures_without_catalog_image": 0,
        "figures_without_set_occurrence": 0,
        "figures_without_component_inventory": 0,
        "printed_component_records": 0,
    }

    with (
        samples_path.open("w", encoding="utf-8") as sf,
        components_path.open("w", encoding="utf-8") as cf,
        refs_path.open("w", encoding="utf-8") as rf,
    ):
        for r in rows(files["minifigs"]):
            fig_num = r["fig_num"]
            sample_id = stable_id("sample", "rebrickable", fig_num)
            image_url = (r.get("img_url") or "").strip()
            num_parts = as_int(r.get("num_parts"))

            occurrences = sorted(
                fig_occurrences.get(fig_num, []),
                key=lambda x: ((x.get("year") or 0), str(x.get("set_num") or "")),
            )
            if not occurrences:
                counts["figures_without_set_occurrence"] += 1
            if not image_url:
                counts["figures_without_catalog_image"] += 1

            # Rebrickable minifigs are special Set-like records. Their component parts
            # live in inventory_parts under inventories whose set_num is the fig_num.
            figure_inventory_ids = set_to_inventories.get(fig_num, [])
            component_rows: list[dict[str, object]] = []
            for inventory_id in figure_inventory_ids:
                component_rows.extend(components_by_inventory.get(inventory_id, []))
            if not component_rows:
                counts["figures_without_component_inventory"] += 1

            sample = {
                "sample_id": sample_id,
                "medium": "physical",
                "authority": "structured_catalog",
                "source_catalog": "rebrickable",
                "fig_num": fig_num,
                "name": r.get("name", ""),
                "num_parts": num_parts,
                "catalog_image_url": image_url or None,
                "set_occurrences": occurrences,
                "component_inventory_ids": figure_inventory_ids,
                "component_count_resolved": len(component_rows),
                "bricklink_catalog_url": f"https://www.bricklink.com/v2/catalog/catalogitem.page?M={fig_num}",
                "processor_version": PROCESSOR_VERSION,
            }
            sf.write(json.dumps(sample, ensure_ascii=False) + "\n")

            conn.execute(
                "INSERT OR REPLACE INTO sample(sample_id,fig_num,name,num_parts,image_url,medium,authority) VALUES(?,?,?,?,?,?,?)",
                (sample_id, fig_num, sample["name"], num_parts, image_url or None, "physical", "structured_catalog"),
            )

            for occ in occurrences:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO set_occurrence
                    (sample_id,set_num,set_name,year,theme_id,theme_path_json,quantity)
                    VALUES(?,?,?,?,?,?,?)
                    """,
                    (
                        sample_id,
                        occ["set_num"],
                        occ["set_name"],
                        occ["year"],
                        occ["theme_id"],
                        json.dumps(occ["theme_path"], ensure_ascii=False),
                        occ["quantity"],
                    ),
                )
                counts["set_occurrence_links"] += 1

            if image_url:
                ref_id = stable_id("ref", "rebrickable", fig_num, image_url)
                ref = {
                    "reference_asset_id": ref_id,
                    "sample_id": sample_id,
                    "component_id": None,
                    "medium": "physical_render_or_catalog_photo",
                    "authority": "structured_catalog",
                    "source_catalog": "rebrickable",
                    "source_url": image_url,
                    "source_role": "catalog_primary_image",
                    "materialized_locally": False,
                    "sha256": None,
                    "perceptual_hash": None,
                    "retrieved_at": None,
                }
                rf.write(json.dumps(ref, ensure_ascii=False) + "\n")
                conn.execute(
                    """
                    INSERT OR REPLACE INTO reference_asset
                    (reference_asset_id,sample_id,component_id,medium,authority,source_url,source_role,sha256,retrieved_at)
                    VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    (ref_id, sample_id, None, ref["medium"], ref["authority"], image_url, ref["source_role"], None, None),
                )
                counts["figure_reference_assets"] += 1

            seen_components: set[tuple[str, str | None, int]] = set()
            for comp in component_rows:
                key = (
                    str(comp["part_num"]),
                    str(comp.get("color_id")) if comp.get("color_id") is not None else None,
                    int(comp["is_spare"]),
                )
                if key in seen_components:
                    continue
                seen_components.add(key)
                component_id = stable_id(
                    "component",
                    fig_num,
                    str(comp["part_num"]),
                    str(comp.get("color_id") or ""),
                    str(comp["is_spare"]),
                )
                component_record = {
                    "component_id": component_id,
                    "sample_id": sample_id,
                    "fig_num": fig_num,
                    **comp,
                }
                cf.write(json.dumps(component_record, ensure_ascii=False) + "\n")
                conn.execute(
                    """
                    INSERT OR REPLACE INTO component
                    (component_id,sample_id,inventory_id,part_num,part_name,color_id,color_name,
                     quantity,is_spare,image_url,print_of,component_role)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        component_id,
                        sample_id,
                        comp["inventory_id"],
                        comp["part_num"],
                        comp["part_name"],
                        comp.get("color_id"),
                        comp.get("color_name"),
                        comp["quantity"],
                        comp["is_spare"],
                        comp.get("image_url"),
                        comp.get("print_of"),
                        comp["component_role"],
                    ),
                )
                counts["component_records"] += 1
                if comp.get("print_of"):
                    counts["printed_component_records"] += 1

                component_image = str(comp.get("image_url") or "")
                if component_image:
                    ref_id = stable_id("ref", "rebrickable-part", fig_num, component_id, component_image)
                    ref = {
                        "reference_asset_id": ref_id,
                        "sample_id": sample_id,
                        "component_id": component_id,
                        "medium": "physical_component_catalog_image",
                        "authority": "structured_catalog",
                        "source_catalog": "rebrickable",
                        "source_url": component_image,
                        "source_role": "component_catalog_image",
                        "component_role": comp["component_role"],
                        "part_num": comp["part_num"],
                        "print_of": comp.get("print_of"),
                        "materialized_locally": False,
                        "sha256": None,
                        "perceptual_hash": None,
                        "retrieved_at": None,
                    }
                    rf.write(json.dumps(ref, ensure_ascii=False) + "\n")
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO reference_asset
                        (reference_asset_id,sample_id,component_id,medium,authority,source_url,source_role,sha256,retrieved_at)
                        VALUES(?,?,?,?,?,?,?,?,?)
                        """,
                        (ref_id, sample_id, component_id, ref["medium"], ref["authority"], component_image, ref["source_role"], None, None),
                    )
                    counts["component_reference_assets"] += 1

            counts["physical_samples"] += 1

    conn.commit()
    conn.close()

    report = {
        "schema": "lego-minifigure-reference-import/v2",
        "processor_version": PROCESSOR_VERSION,
        "created_at": now_iso(),
        "source_root": str(root),
        "source_files": {
            name: {"path": str(path), "sha256": source_hashes[name]}
            for name, path in files.items()
        },
        "optional_tables_present": sorted(set(files) - set(required_names)),
        "outputs": {
            "samples": str(samples_path),
            "components": str(components_path),
            "references": str(refs_path),
            "sqlite": str(db_path),
        },
        "counts": counts,
        "raw_image_policy": "not mirrored by this tool; materialize locally with source-specific fetch policy",
        "notes": [
            "Rebrickable documents minifigs as a special type of Set and provides a minifig-parts endpoint.",
            "Component classification is a heuristic used for routing/review, not authoritative LEGO taxonomy.",
            "Part relationship P is treated as print-of only when supplied by the bulk relationship table; validate unusual records.",
        ],
    }
    (out / "import_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["counts"], indent=2))


if __name__ == "__main__":
    main()
