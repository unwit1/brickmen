#!/usr/bin/env python3
"""Index extracted TT Games LEGO assets for minifigure reference discovery.

This tool assumes the user has already extracted files from a legally obtained local game
installation using a compatible external tool. It does not bypass DRM, download game data,
or redistribute assets.

It creates a provenance-aware candidate manifest from file paths, hashes and lightweight
path heuristics. Actual model/texture decoding is delegated to format-aware tools.

Outputs:
  game_assets.jsonl
  corpus.sqlite3
  import_report.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROCESSOR_VERSION = "lego-game-asset-index/v1"

TEXTURE_EXTS = {".png", ".dds", ".tex", ".tga", ".bmp", ".jpg", ".jpeg", ".tsh", ".nxg_textures"}
MODEL_EXTS = {".ghg", ".gsc", ".cmo", ".obj", ".fbx", ".dae", ".glb", ".gltf"}
META_EXTS = {".xml", ".csv", ".txt", ".cfg", ".ini", ".lua", ".scp", ".sf", ".sub", ".subopt"}
STRONG_PATH_TOKENS = {
    "char", "chars", "character", "characters", "minifig", "minifigs", "minifigure",
    "player", "hero", "heroes", "villain", "villains", "costume", "costumes", "skin", "skins"
}
WEAK_PATH_TOKENS = {
    "head", "heads", "face", "faces", "torso", "body", "legs", "arms", "helmet", "helmets",
    "hair", "mask", "masks", "npc", "ped", "avatar"
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(kind: str, *parts: str) -> str:
    raw = json.dumps([kind, *parts], separators=(",", ":"), ensure_ascii=False)
    return f"{kind}-{hashlib.sha256(raw.encode()).hexdigest()[:24]}"


def classify(path: Path) -> tuple[str, int, list[str]]:
    ext = path.suffix.lower()
    if ext in TEXTURE_EXTS:
        kind = "texture_or_texture_archive"
    elif ext in MODEL_EXTS:
        kind = "model"
    elif ext in META_EXTS:
        kind = "metadata_or_config"
    else:
        kind = "other"

    text = "/".join(part.lower() for part in path.parts)
    hits = sorted({token for token in STRONG_PATH_TOKENS if token in text})
    weak = sorted({token for token in WEAK_PATH_TOKENS if token in text})
    score = min(100, len(hits) * 25 + len(weak) * 8 + (15 if kind in {"texture_or_texture_archive", "model"} else 0))
    return kind, score, hits + weak


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS game_asset (
            asset_id TEXT PRIMARY KEY,
            game_id TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            extension TEXT,
            asset_kind TEXT NOT NULL,
            candidate_score INTEGER NOT NULL,
            path_tokens_json TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            sha256 TEXT NOT NULL,
            source_root TEXT NOT NULL,
            indexed_at TEXT NOT NULL,
            UNIQUE(game_id, relative_path)
        );
        CREATE INDEX IF NOT EXISTS idx_game_asset_score ON game_asset(game_id,candidate_score DESC);
        CREATE INDEX IF NOT EXISTS idx_game_asset_kind ON game_asset(game_id,asset_kind);
        """
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-id", required=True, help="Stable slug, e.g. lego-marvel-super-heroes-2")
    ap.add_argument("--game-title", required=True)
    ap.add_argument("--game-version", default="unknown")
    ap.add_argument("--platform", default="pc")
    ap.add_argument("--source-root", type=Path, required=True, help="Already-extracted game asset directory")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--extraction-tool", default="unknown")
    ap.add_argument("--extraction-tool-version", default="unknown")
    ap.add_argument("--min-score", type=int, default=15)
    args = ap.parse_args()

    root = args.source_root.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    if not root.is_dir():
        raise SystemExit(f"source root is not a directory: {root}")

    db_path = out / "corpus.sqlite3"
    conn = sqlite3.connect(db_path)
    init_db(conn)

    manifest_path = out / "game_assets.jsonl"
    counts = Counter()
    candidates = 0
    indexed_at = now_iso()

    with manifest_path.open("w", encoding="utf-8") as mf:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            relative = path.relative_to(root).as_posix()
            kind, score, tokens = classify(Path(relative))
            counts[kind] += 1
            if score < args.min_score:
                continue
            digest = sha256_file(path)
            asset_id = stable_id("gameasset", args.game_id, relative, digest)
            record = {
                "asset_id": asset_id,
                "game_id": args.game_id,
                "game_title": args.game_title,
                "game_version": args.game_version,
                "platform": args.platform,
                "relative_path": relative,
                "extension": path.suffix.lower(),
                "asset_kind": kind,
                "candidate_score": score,
                "path_tokens": tokens,
                "size_bytes": path.stat().st_size,
                "sha256": digest,
                "source_provenance": {
                    "source_type": "legally_obtained_local_game_install",
                    "source_root": str(root),
                    "extraction_tool": args.extraction_tool,
                    "extraction_tool_version": args.extraction_tool_version,
                    "indexed_at": indexed_at,
                },
                "character_id": None,
                "appearance_id": None,
                "sample_id": None,
                "decode_status": "candidate",
                "storage_policy": "local_only_raw_asset",
                "processor_version": PROCESSOR_VERSION,
            }
            mf.write(json.dumps(record, ensure_ascii=False) + "\n")
            conn.execute(
                """
                INSERT OR REPLACE INTO game_asset
                (asset_id,game_id,relative_path,extension,asset_kind,candidate_score,
                 path_tokens_json,size_bytes,sha256,source_root,indexed_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    asset_id, args.game_id, relative, path.suffix.lower(), kind, score,
                    json.dumps(tokens), path.stat().st_size, digest, str(root), indexed_at
                ),
            )
            candidates += 1

    conn.commit()
    conn.close()

    report = {
        "schema": "lego-game-asset-index-report/v1",
        "processor_version": PROCESSOR_VERSION,
        "created_at": indexed_at,
        "game": {
            "id": args.game_id,
            "title": args.game_title,
            "version": args.game_version,
            "platform": args.platform,
        },
        "source_root": str(root),
        "extraction_tool": args.extraction_tool,
        "extraction_tool_version": args.extraction_tool_version,
        "counts_by_kind": dict(counts),
        "candidate_assets": candidates,
        "min_score": args.min_score,
        "outputs": {
            "manifest": str(manifest_path),
            "sqlite": str(db_path),
        },
        "next_stage": "decode/view texture and model candidates, resolve character IDs, render canonical views, deduplicate",
    }
    (out / "import_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
