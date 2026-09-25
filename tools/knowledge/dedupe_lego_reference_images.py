#!/usr/bin/env python3
"""Add simple perceptual hashes to locally materialized reference images.

Requires Pillow. Uses a deterministic 64-bit dHash implementation to support near-duplicate
grouping after exact SHA-256 deduplication. It does not delete anything; it writes a new
manifest with perceptual_hash values.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("Pillow is required: python -m pip install Pillow") from exc


def dhash(path: Path, hash_size: int = 8) -> str:
    with Image.open(path) as image:
        image = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        pixels = list(image.getdata())
    bits = []
    width = hash_size + 1
    for y in range(hash_size):
        row = y * width
        for x in range(hash_size):
            bits.append(pixels[row + x] > pixels[row + x + 1])
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return f"{value:0{hash_size * hash_size // 4}x}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    total = 0
    hashed = 0
    errors = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.manifest.open("r", encoding="utf-8") as src, args.output.open("w", encoding="utf-8") as dst:
        for line in src:
            if not line.strip():
                continue
            record = json.loads(line)
            total += 1
            local = record.get("local_path")
            if local:
                try:
                    record["perceptual_hash"] = dhash(Path(local))
                    hashed += 1
                except Exception as exc:
                    record.setdefault("quality_errors", []).append(f"dhash: {exc}")
                    errors += 1
            dst.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(json.dumps({"total": total, "hashed": hashed, "errors": errors}, indent=2))


if __name__ == "__main__":
    main()
