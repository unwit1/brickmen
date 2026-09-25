#!/usr/bin/env python3
"""Extract a high-information local frame corpus from a legally obtained LEGO film video.

Requires ffmpeg/ffprobe on PATH. Raw frames stay local. The script samples:
1. fixed interval frames for coverage;
2. scene-change frames for visual-state diversity.

It then hashes exact files and writes a provenance manifest. Character detection,
cropping and perceptual deduplication are later stages.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROCESSOR_VERSION = "lego-film-frame-extract/v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def probe_duration(video: Path) -> float:
    proc = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video)
    ])
    return float(proc.stdout.strip())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--film-id", required=True)
    ap.add_argument("--film-title", required=True)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--interval-seconds", type=float, default=10.0)
    ap.add_argument("--scene-threshold", type=float, default=0.30)
    ap.add_argument("--jpeg-quality", type=int, default=2, help="ffmpeg q:v, 2 is high quality")
    args = ap.parse_args()

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe must be available on PATH")

    video = args.input.resolve()
    if not video.is_file():
        raise SystemExit(f"input video not found: {video}")

    out = args.output_dir.resolve()
    interval_dir = out / "frames_interval"
    scene_dir = out / "frames_scene"
    interval_dir.mkdir(parents=True, exist_ok=True)
    scene_dir.mkdir(parents=True, exist_ok=True)

    duration = probe_duration(video)
    video_sha = sha256_file(video)

    # Fixed interval coverage.
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video),
        "-vf", f"fps=1/{args.interval_seconds}",
        "-q:v", str(args.jpeg_quality),
        str(interval_dir / "%08d.jpg"),
    ])

    # Scene-change diversity.
    scene_filter = f"select='gt(scene,{args.scene_threshold})',showinfo"
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video),
        "-vf", scene_filter,
        "-vsync", "vfr",
        "-q:v", str(args.jpeg_quality),
        str(scene_dir / "%08d.jpg"),
    ])

    created_at = now_iso()
    manifest_path = out / "frame_manifest.jsonl"
    total = 0
    with manifest_path.open("w", encoding="utf-8") as mf:
        for mode, folder in (("interval", interval_dir), ("scene_change", scene_dir)):
            for frame in sorted(folder.glob("*.jpg")):
                record = {
                    "reference_asset_id": f"filmframe-{args.film_id}-{mode}-{frame.stem}",
                    "medium": "film_frame",
                    "authority": "official_film_local_copy",
                    "film_id": args.film_id,
                    "film_title": args.film_title,
                    "source_video_sha256": video_sha,
                    "source_video_path": str(video),
                    "frame_path": str(frame),
                    "sampling_mode": mode,
                    "frame_sha256": sha256_file(frame),
                    "character_ids": [],
                    "appearance_ids": [],
                    "crop_regions": [],
                    "view": "unknown",
                    "expression": None,
                    "mask_headgear_state": None,
                    "perceptual_hash": None,
                    "review_status": "unprocessed",
                    "storage_policy": "local_only_raw_frame",
                    "created_at": created_at,
                    "processor_version": PROCESSOR_VERSION,
                }
                mf.write(json.dumps(record, ensure_ascii=False) + "\n")
                total += 1

    report = {
        "schema": "lego-film-frame-extract-report/v1",
        "processor_version": PROCESSOR_VERSION,
        "created_at": created_at,
        "film_id": args.film_id,
        "film_title": args.film_title,
        "input": str(video),
        "input_sha256": video_sha,
        "duration_seconds": duration,
        "sampling": {
            "interval_seconds": args.interval_seconds,
            "scene_threshold": args.scene_threshold,
        },
        "frame_count": total,
        "outputs": {
            "manifest": str(manifest_path),
            "interval_frames": str(interval_dir),
            "scene_frames": str(scene_dir),
        },
        "next_stage": "detect/crop minifigure characters, add timestamps, perceptual-deduplicate, cluster costume/expression/view states",
    }
    (out / "import_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
