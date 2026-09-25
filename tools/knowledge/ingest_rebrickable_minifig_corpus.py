#!/usr/bin/env python3
"""Build a local official-minifigure census from Rebrickable bulk CSV exports.

This tool intentionally keeps high-volume catalog rows and image URLs in local
derived storage. The Git repository should retain the extractor, schemas,
manifests, validated aggregate statistics, and provenance -- not a wholesale
mirror of third-party catalog payloads or copyrighted artwork.

Expected source: Rebrickable Downloads CSV exports. Rebrickable explicitly
directs bulk/full-list users to these downloads instead of paginating the API.

The importer builds a fresh SQLite file in a temporary path and atomically
replaces the requested database only after required tables and integrity checks
pass.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Iterable, Iterator, TextIO

PROCESSOR_VERSION = "official-minifigure-census/v1"
SOURCE_NAME = "Rebrickable bulk CSV"
SOURCE_DOCS = "https://rebrickable.com/api/v3/docs/"
DOWNLOAD_PAGE = "https://rebrickable.com/downloads/"

DATASETS: dict[str, tuple[str, ...]] = {
    "minifigs": ("fig_num", "name", "num_parts"),
    "inventories": ("id", "version", "set_num"),
    "inventory_minifigs": ("inventory_id", "fig_num", "quantity"),
    "inventory_parts": ("inventory_id", "part_num", "color_id", "quantity", "is_spare"),
    "parts": ("part_num", "name", "part_cat_id"),
    "part_relationships": ("rel_type", "child_part_num", "parent_part_num"),
    "elements": ("element_id", "part_num", "color_id"),
    "colors": ("id", "name", "rgb", "is_trans"),
    "sets": ("set_num", "name", "year", "theme_id", "num_parts"),
    "themes": ("id", "name"),
}

INDEXES: dict[str, tuple[str, ...]] = {
    "minifigs": ("fig_num",),
    "inventories": ("id", "set_num"),
    "inventory_minifigs": ("inventory_id", "fig_num"),
    "inventory_parts": ("inventory_id", "part_num", "color_id"),
    "parts": ("part_num",),
    "part_relationships": ("child_part_num", "parent_part_num"),
    "elements": ("element_id", "part_num", "color_id"),
    "colors": ("id",),
    "sets": ("set_num", "theme_id", "year"),
    "themes": ("id", "parent_id"),
}

_IDENTIFIER = re.compile(r"[^a-zA-Z0-9_]+")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def quote_identifier(value: str) -> str:
    cleaned = _IDENTIFIER.sub("_", value.strip())
    cleaned = cleaned.strip("_") or "column"
    if cleaned[0].isdigit():
        cleaned = f"c_{cleaned}"
    return '"' + cleaned.replace('"', '""') + '"'


def normalized_column(value: str) -> str:
    cleaned = _IDENTIFIER.sub("_", value.strip()).strip("_").lower()
    if not cleaned:
        raise ValueError(f"empty/invalid CSV header: {value!r}")
    if cleaned[0].isdigit():
        cleaned = f"c_{cleaned}"
    return cleaned


def source_path(input_dir: Path, dataset: str) -> Path:
    candidates = (
        input_dir / f"{dataset}.csv.gz",
        input_dir / f"{dataset}.csv",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"missing {dataset}.csv(.gz) in {input_dir}; "
        f"download Rebrickable bulk CSV files from {DOWNLOAD_PAGE}"
    )


def open_csv(path: Path) -> TextIO:
    if path.suffix.lower() == ".gz":
        return gzip.open(path, mode="rt", encoding="utf-8-sig", newline="")
    return path.open("r", encoding="utf-8-sig", newline="")


def inspect_header(path: Path) -> list[str]:
    with open_csv(path) as handle:
        reader = csv.reader(handle)
        try:
            raw = next(reader)
        except StopIteration as exc:
            raise ValueError(f"empty CSV: {path}") from exc
    columns = [normalized_column(value) for value in raw]
    if len(columns) != len(set(columns)):
        raise ValueError(f"duplicate normalized headers in {path}: {columns}")
    return columns


def validate_headers(dataset: str, columns: Iterable[str]) -> None:
    present = set(columns)
    missing = [column for column in DATASETS[dataset] if column not in present]
    if missing:
        raise ValueError(f"{dataset} is missing required columns: {', '.join(missing)}")


def iter_rows(path: Path, expected_columns: list[str]) -> Iterator[tuple[str, ...]]:
    with open_csv(path) as handle:
        reader = csv.DictReader(handle)
        actual = [normalized_column(v) for v in (reader.fieldnames or [])]
        if actual != expected_columns:
            raise ValueError(f"header changed while reading {path}: {actual!r}")
        original_names = reader.fieldnames or []
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"extra CSV fields in {path} at row {row_number}")
            yield tuple((row.get(original, "") or "").strip() for original in original_names)


def create_table(conn: sqlite3.Connection, dataset: str, columns: list[str]) -> None:
    conn.execute(f'DROP TABLE IF EXISTS {quote_identifier(dataset)}')
    definition = ", ".join(f"{quote_identifier(column)} TEXT" for column in columns)
    conn.execute(f'CREATE TABLE {quote_identifier(dataset)} ({definition})')


def import_dataset(
    conn: sqlite3.Connection,
    dataset: str,
    path: Path,
    *,
    batch_size: int = 5000,
) -> dict[str, object]:
    columns = inspect_header(path)
    validate_headers(dataset, columns)
    create_table(conn, dataset, columns)
    placeholders = ",".join("?" for _ in columns)
    column_sql = ",".join(quote_identifier(c) for c in columns)
    sql = (
        f'INSERT INTO {quote_identifier(dataset)} '
        f'({column_sql}) VALUES ({placeholders})'
    )

    batch: list[tuple[str, ...]] = []
    count = 0
    for values in iter_rows(path, columns):
        batch.append(values)
        if len(batch) >= batch_size:
            conn.executemany(sql, batch)
            count += len(batch)
            batch.clear()
    if batch:
        conn.executemany(sql, batch)
        count += len(batch)

    return {
        "dataset": dataset,
        "filename": path.name,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "rows": count,
        "columns": columns,
    }


def has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(
        f'PRAGMA table_info({quote_identifier(table)})'
    ).fetchall()
    return any(row[1] == column for row in rows)


def create_indexes(conn: sqlite3.Connection) -> None:
    for table, columns in INDEXES.items():
        for column in columns:
            if not has_column(conn, table, column):
                continue
            name = f"idx_{table}_{column}"
            conn.execute(
                f'CREATE INDEX IF NOT EXISTS {quote_identifier(name)} '
                f'ON {quote_identifier(table)} ({quote_identifier(column)})'
            )


def create_views(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP VIEW IF EXISTS minifig_set_links;
        CREATE VIEW minifig_set_links AS
        SELECT DISTINCT
            m.fig_num,
            m.name AS fig_name,
            s.set_num,
            s.name AS set_name,
            CAST(NULLIF(s.year, '') AS INTEGER) AS set_year,
            s.theme_id,
            im.quantity
        FROM minifigs AS m
        JOIN inventory_minifigs AS im ON im.fig_num = m.fig_num
        JOIN inventories AS i ON i.id = im.inventory_id
        JOIN sets AS s ON s.set_num = i.set_num;

        DROP VIEW IF EXISTS minifig_part_links;
        CREATE VIEW minifig_part_links AS
        SELECT
            m.fig_num,
            ip.part_num,
            ip.color_id,
            ip.quantity,
            ip.is_spare,
            p.name AS part_name,
            p.part_cat_id
        FROM minifigs AS m
        JOIN inventories AS i ON i.set_num = m.fig_num
        JOIN inventory_parts AS ip ON ip.inventory_id = i.id
        LEFT JOIN parts AS p ON p.part_num = ip.part_num;

        DROP VIEW IF EXISTS minifig_year_bounds;
        CREATE VIEW minifig_year_bounds AS
        SELECT
            fig_num,
            MIN(set_year) AS first_observed_set_year,
            MAX(set_year) AS last_observed_set_year,
            COUNT(DISTINCT set_num) AS set_count
        FROM minifig_set_links
        GROUP BY fig_num;

        DROP VIEW IF EXISTS minifig_theme_links;
        CREATE VIEW minifig_theme_links AS
        SELECT DISTINCT
            l.fig_num,
            l.theme_id,
            t.name AS theme_name,
            t.parent_id
        FROM minifig_set_links AS l
        LEFT JOIN themes AS t ON t.id = l.theme_id;
        """
    )


def integrity_checks(conn: sqlite3.Connection) -> dict[str, object]:
    counts = {
        table: int(
            conn.execute(
                f"SELECT COUNT(*) FROM {quote_identifier(table)}"
            ).fetchone()[0]
        )
        for table in DATASETS
    }
    if counts["minifigs"] <= 0:
        raise ValueError("minifigs table is empty")
    if counts["inventory_minifigs"] <= 0:
        raise ValueError("inventory_minifigs table is empty")
    if counts["sets"] <= 0 or counts["themes"] <= 0:
        raise ValueError("sets/themes tables are empty")

    orphan_minifig_refs = int(
        conn.execute(
            """
            SELECT COUNT(*)
            FROM inventory_minifigs AS im
            LEFT JOIN minifigs AS m ON m.fig_num = im.fig_num
            WHERE m.fig_num IS NULL
            """
        ).fetchone()[0]
    )
    duplicate_fig_nums = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT fig_num
                FROM minifigs
                GROUP BY fig_num
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]
    )
    physical_part_links = int(
        conn.execute("SELECT COUNT(*) FROM minifig_part_links").fetchone()[0]
    )
    set_links = int(
        conn.execute("SELECT COUNT(*) FROM minifig_set_links").fetchone()[0]
    )

    return {
        "counts": counts,
        "orphan_inventory_minifig_refs": orphan_minifig_refs,
        "duplicate_fig_nums": duplicate_fig_nums,
        "minifig_part_links": physical_part_links,
        "minifig_set_links": set_links,
    }


def theme_ancestry(
    conn: sqlite3.Connection,
) -> dict[str, list[dict[str, str]]]:
    rows = conn.execute("SELECT id, name, parent_id FROM themes").fetchall()
    themes = {
        str(row[0]): {
            "id": str(row[0]),
            "name": row[1],
            "parent_id": row[2],
        }
        for row in rows
    }
    result: dict[str, list[dict[str, str]]] = {}
    for theme_id in themes:
        lineage: list[dict[str, str]] = []
        current = theme_id
        seen: set[str] = set()
        while current and current not in seen and current in themes:
            seen.add(current)
            item = themes[current]
            lineage.append({"id": item["id"], "name": item["name"]})
            parent = item.get("parent_id")
            current = str(parent) if parent not in (None, "") else ""
        result[theme_id] = lineage
    return result


def write_census_jsonl(
    conn: sqlite3.Connection,
    path: Path,
) -> int:
    ancestry = theme_ancestry(conn)
    figures = conn.execute(
        """
        SELECT
            m.fig_num,
            m.name,
            m.num_parts,
            m.img_url,
            y.first_observed_set_year,
            y.last_observed_set_year,
            COALESCE(y.set_count, 0)
        FROM minifigs AS m
        LEFT JOIN minifig_year_bounds AS y ON y.fig_num = m.fig_num
        ORDER BY m.fig_num
        """
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for (
            fig_num,
            name,
            num_parts,
            img_url,
            first_year,
            last_year,
            set_count,
        ) in figures:
            sets = [
                {
                    "set_num": row[0],
                    "name": row[1],
                    "year": row[2],
                    "theme_id": row[3],
                }
                for row in conn.execute(
                    """
                    SELECT DISTINCT set_num, set_name, set_year, theme_id
                    FROM minifig_set_links
                    WHERE fig_num = ?
                    ORDER BY set_year, set_num
                    """,
                    (fig_num,),
                )
            ]
            theme_ids = sorted(
                {
                    str(item["theme_id"])
                    for item in sets
                    if item["theme_id"] not in (None, "")
                }
            )
            themes = [
                {
                    "theme_id": theme_id,
                    "lineage": ancestry.get(theme_id, []),
                }
                for theme_id in theme_ids
            ]
            components = [
                {
                    "part_num": row[0],
                    "color_id": row[1],
                    "quantity": row[2],
                    "is_spare": row[3],
                    "part_name": row[4],
                    "part_cat_id": row[5],
                }
                for row in conn.execute(
                    """
                    SELECT
                        part_num,
                        color_id,
                        quantity,
                        is_spare,
                        part_name,
                        part_cat_id
                    FROM minifig_part_links
                    WHERE fig_num = ?
                    ORDER BY part_num, color_id
                    """,
                    (fig_num,),
                )
            ]
            record = {
                "source": "rebrickable",
                "source_record_type": "minifig",
                "fig_num": fig_num,
                "name": name,
                "num_parts": (
                    int(num_parts)
                    if str(num_parts).isdigit()
                    else num_parts
                ),
                "image_reference_url": img_url or None,
                "first_observed_set_year": first_year,
                "last_observed_set_year": last_year,
                "set_count": set_count,
                "sets": sets,
                "themes": themes,
                "components": components,
                "character_resolution": None,
                "incarnation_resolution": None,
                "source_appearance_resolution": None,
                "style_profile": None,
                "visual_feature_status": "unprocessed",
            }
            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )
            count += 1
    return count


def write_manifest(
    path: Path,
    *,
    db_path: Path,
    census_path: Path,
    source_records: list[dict[str, object]],
    checks: dict[str, object],
    census_rows: int,
) -> None:
    payload = {
        "schema": (
            "personal-agent/"
            "lego-official-minifigure-corpus-manifest/v1"
        ),
        "processor_version": PROCESSOR_VERSION,
        "created_at_utc": utc_now(),
        "source": {
            "name": SOURCE_NAME,
            "documentation": SOURCE_DOCS,
            "download_page": DOWNLOAD_PAGE,
            "files": source_records,
        },
        "outputs": {
            "sqlite": str(db_path),
            "census_jsonl": str(census_path),
            "census_rows": census_rows,
        },
        "integrity": checks,
        "storage_policy": (
            "High-volume catalog payloads and image references are local "
            "derived data. Commit the tool, schemas, reviewed aggregates "
            "and provenance, not a wholesale catalog/image mirror."
        ),
        "next_stage": (
            "Resolve canonical character/incarnation/source appearance, "
            "acquire permitted official visual references, extract visual "
            "features, and assign official style profiles."
        ),
    }
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build(
    input_dir: Path,
    output_dir: Path,
    *,
    keep_existing: bool = False,
) -> dict[str, object]:
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    db_path = output_dir / "official-minifigure-corpus.sqlite3"
    tmp_path = output_dir / ".official-minifigure-corpus.sqlite3.tmp"
    census_path = output_dir / "official-minifigure-census.jsonl"
    manifest_path = (
        output_dir / "official-minifigure-corpus.manifest.json"
    )

    if tmp_path.exists():
        tmp_path.unlink()
    if db_path.exists() and keep_existing:
        raise FileExistsError(
            f"database exists and --keep-existing was supplied: {db_path}"
        )

    source_records: list[dict[str, object]] = []
    conn = sqlite3.connect(tmp_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute(
            """
            CREATE TABLE corpus_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO corpus_meta VALUES (?, ?)",
            ("processor_version", PROCESSOR_VERSION),
        )
        conn.execute(
            "INSERT INTO corpus_meta VALUES (?, ?)",
            ("source_name", SOURCE_NAME),
        )
        conn.execute(
            "INSERT INTO corpus_meta VALUES (?, ?)",
            ("source_docs", SOURCE_DOCS),
        )
        conn.execute(
            "INSERT INTO corpus_meta VALUES (?, ?)",
            ("import_started_at_utc", utc_now()),
        )

        for dataset in DATASETS:
            path = source_path(input_dir, dataset)
            with conn:
                info = import_dataset(conn, dataset, path)
            source_records.append(info)

        with conn:
            create_indexes(conn)
            create_views(conn)
            checks = integrity_checks(conn)
            conn.execute(
                "INSERT OR REPLACE INTO corpus_meta VALUES (?, ?)",
                ("import_completed_at_utc", utc_now()),
            )
            conn.execute(
                "INSERT OR REPLACE INTO corpus_meta VALUES (?, ?)",
                ("integrity_json", json.dumps(checks, sort_keys=True)),
            )

        conn.execute("ANALYZE")
        conn.commit()
        census_rows = write_census_jsonl(conn, census_path)
    except Exception:
        conn.close()
        if tmp_path.exists():
            tmp_path.unlink()
        raise
    else:
        conn.close()

    os.replace(tmp_path, db_path)
    write_manifest(
        manifest_path,
        db_path=db_path,
        census_path=census_path,
        source_records=source_records,
        checks=checks,
        census_rows=census_rows,
    )
    return {
        "database": str(db_path),
        "census": str(census_path),
        "manifest": str(manifest_path),
        "minifig_rows": checks["counts"]["minifigs"],
        "census_rows": census_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build a local official-minifigure census from "
            "Rebrickable bulk CSV exports."
        )
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help=(
            "Directory containing Rebrickable CSV or CSV.GZ downloads."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help=(
            "Local/high-volume output directory (normally gitignored)."
        ),
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Refuse to replace an existing corpus database.",
    )
    args = parser.parse_args()

    result = build(
        args.input_dir,
        args.output_dir,
        keep_existing=args.keep_existing,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
