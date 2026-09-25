#!/usr/bin/env python3
"""Compute deterministic visual-difference features for Fortnite -> LEGO Style pairs.

This is a measurement stage, not a semantic judge. It downloads only the preferred image
for each side into memory, extracts compact reproducible visual features, writes derived
measurements, and discards raw bytes. Signals such as lower edge density are explicitly
heuristics and must not be promoted to preserve/simplify/omit labels without review.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import statistics
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

VERSION = "fortnite-translation-visual-features/v2"
USER_AGENT = "BrickmenResearch/1.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def preferred_url(side: dict) -> str | None:
    pref = side.get("preferred_image")
    if isinstance(pref, dict) and pref.get("url"):
        return pref["url"]
    urls = side.get("images") or []
    return urls[0] if urls else None


def fetch_image(url: str, timeout: int = 30) -> Image.Image:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = response.read(12_000_000)
    im = Image.open(io.BytesIO(data))
    im.load()
    return im.convert("RGBA")


def quantized_palette(rgb: Image.Image, n=8):
    small = rgb.resize((96, 96), Image.Resampling.LANCZOS).convert("RGB")
    q = small.quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    colors = q.getcolors(maxcolors=n) or []
    pal = q.getpalette() or []
    total = sum(count for count, _ in colors) or 1
    rows = []
    for count, idx in sorted(colors, reverse=True):
        base = idx * 3
        rows.append(
            {
                "rgb": pal[base : base + 3],
                "fraction": round(count / total, 4),
            }
        )
    return rows


def foreground_bbox(im: Image.Image):
    alpha = im.getchannel("A")
    extrema = alpha.getextrema()
    if extrema != (255, 255):
        mask = alpha.point(lambda p: 255 if p > 20 else 0)
    else:
        # Fallback: transparent data is ideal; for opaque images use luminance distance
        # from the four-corner median as a conservative background estimate.
        rgb = im.convert("RGB")
        w, h = rgb.size
        corners = [rgb.getpixel((0, 0)), rgb.getpixel((w - 1, 0)), rgb.getpixel((0, h - 1)), rgb.getpixel((w - 1, h - 1))]
        bg = tuple(int(statistics.median(c[i] for c in corners)) for i in range(3))
        pix = rgb.load()
        mask = Image.new("L", rgb.size, 0)
        mp = mask.load()
        for y in range(h):
            for x in range(w):
                p = pix[x, y]
                dist = sum(abs(p[i] - bg[i]) for i in range(3))
                if dist > 45:
                    mp[x, y] = 255
    bbox = mask.getbbox()
    if not bbox:
        return None, 0.0
    w, h = im.size
    x0, y0, x1, y1 = bbox
    occupancy = ((x1 - x0) * (y1 - y0)) / max(1, w * h)
    return [round(x0 / w, 4), round(y0 / h, 4), round(x1 / w, 4), round(y1 / h, 4)], round(occupancy, 4)


def region_features(rgb: Image.Image):
    """Measure coarse vertical regions after foreground-bbox normalization."""
    rgba = rgb.convert("RGBA")
    bbox_norm, _ = foreground_bbox(rgba.resize((256, 256), Image.Resampling.LANCZOS))
    if bbox_norm:
        w, h = rgb.size
        x0 = max(0, min(w - 1, int(bbox_norm[0] * w)))
        y0 = max(0, min(h - 1, int(bbox_norm[1] * h)))
        x1 = max(x0 + 1, min(w, int(bbox_norm[2] * w)))
        y1 = max(y0 + 1, min(h, int(bbox_norm[3] * h)))
        crop = rgb.crop((x0, y0, x1, y1))
    else:
        crop = rgb
    crop = crop.resize((128, 192), Image.Resampling.LANCZOS).convert("RGB")
    bands = {
        "head_upper": (0, 0, 128, 68),
        "torso_middle": (0, 68, 128, 132),
        "legs_lower": (0, 132, 128, 192),
    }
    out = {}
    for name, box in bands.items():
        band = crop.crop(box)
        gray = band.convert("L")
        edges = gray.filter(ImageFilter.FIND_EDGES)
        vals = list(edges.getdata())
        edge_density = sum(1 for v in vals if v >= 32) / max(1, len(vals))
        stats = ImageStat.Stat(band)
        palette = quantized_palette(band, 4)
        out[name] = {
            "mean_rgb": [round(x, 2) for x in stats.mean[:3]],
            "stddev_rgb": [round(x, 2) for x in stats.stddev[:3]],
            "edge_density": round(edge_density, 5),
            "palette_4": palette,
            "palette_effective_colors": sum(1 for x in palette if x["fraction"] >= 0.05),
        }
    return out


def visual_features(im: Image.Image):
    w, h = im.size
    rgb = im.convert("RGB")
    thumb = rgb.resize((128, 128), Image.Resampling.LANCZOS)
    gray = thumb.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    vals = list(edges.getdata())
    edge_density = sum(1 for v in vals if v >= 32) / max(1, len(vals))
    stats = ImageStat.Stat(thumb)
    bbox, occupancy = foreground_bbox(im.resize((256, 256), Image.Resampling.LANCZOS))
    palette = quantized_palette(rgb, 8)
    return {
        "width": w,
        "height": h,
        "aspect_ratio": round(w / max(1, h), 4),
        "mean_rgb": [round(x, 2) for x in stats.mean[:3]],
        "stddev_rgb": [round(x, 2) for x in stats.stddev[:3]],
        "edge_density_128": round(edge_density, 5),
        "foreground_bbox_norm": bbox,
        "foreground_bbox_occupancy": occupancy,
        "palette_8": palette,
        "palette_effective_colors": sum(1 for x in palette if x["fraction"] >= 0.025),
        "foreground_normalized_regions": region_features(rgb),
    }


def delta(src: dict, lego: dict):
    src_edges = src.get("edge_density_128") or 0
    lego_edges = lego.get("edge_density_128") or 0
    src_palette = src.get("palette_effective_colors") or 0
    lego_palette = lego.get("palette_effective_colors") or 0
    src_occ = src.get("foreground_bbox_occupancy") or 0
    lego_occ = lego.get("foreground_bbox_occupancy") or 0
    regional = {}
    for name in ("head_upper", "torso_middle", "legs_lower"):
        sr = (src.get("foreground_normalized_regions") or {}).get(name) or {}
        lr = (lego.get("foreground_normalized_regions") or {}).get(name) or {}
        se = sr.get("edge_density") or 0
        le = lr.get("edge_density") or 0
        regional[name] = {
            "edge_density_delta_lego_minus_source": round(le - se, 5),
            "edge_density_ratio_lego_to_source": round(le / se, 4) if se else None,
            "effective_palette_delta_lego_minus_source": (lr.get("palette_effective_colors") or 0) - (sr.get("palette_effective_colors") or 0),
            "mean_rgb_delta_lego_minus_source": [
                round((lr.get("mean_rgb") or [0,0,0])[i] - (sr.get("mean_rgb") or [0,0,0])[i], 2)
                for i in range(3)
            ],
        }
    return {
        "edge_density_delta_lego_minus_source": round(lego_edges - src_edges, 5),
        "edge_density_ratio_lego_to_source": round(lego_edges / src_edges, 4) if src_edges else None,
        "effective_palette_delta_lego_minus_source": lego_palette - src_palette,
        "foreground_occupancy_delta": round(lego_occ - src_occ, 4),
        "aspect_ratio_delta": round((lego.get("aspect_ratio") or 0) - (src.get("aspect_ratio") or 0), 4),
        "regional_differences": regional,
        "heuristic_signals": {
            "lower_edge_density_in_lego": bool(src_edges and lego_edges < src_edges * 0.85),
            "smaller_effective_palette_in_lego": lego_palette < src_palette,
            "large_silhouette_bbox_change": abs(lego_occ - src_occ) >= 0.15,
        },
        "semantic_label_policy": "heuristic_signals_are_measurements_only_not_semantic_ground_truth",
    }


def norm_name(value: str) -> str:
    return " ".join(str(value or "").casefold().split())


def attach_alias_fallbacks(pairs: list[dict]) -> int:
    """Resolve missing LEGO image URLs from same-name image-bearing pair aliases.

    Prefer legacy/current combat IDs (CID_A_*) over casual Character_* aliases because
    placeholder recruits share the Default C3 body family with the combat records.
    The fallback remains explicit provenance and never rewrites the original pair ID.
    """
    by_name: dict[str, list[dict]] = {}
    for pair in pairs:
        name = norm_name((pair.get("source_appearance") or {}).get("name"))
        if name and preferred_url(pair.get("lego_target") or {}):
            by_name.setdefault(name, []).append(pair)
    resolved = 0
    for pair in pairs:
        if preferred_url(pair.get("lego_target") or {}):
            continue
        name = norm_name((pair.get("source_appearance") or {}).get("name"))
        candidates = by_name.get(name, [])
        if not candidates:
            continue
        def rank(candidate):
            sid = str((candidate.get("source_appearance") or {}).get("br_id") or "")
            return (0 if sid.startswith("CID_A_") else 1, candidate.get("translation_pair_id") or "")
        chosen = sorted(candidates, key=rank)[0]
        pair["_lego_alias_fallback"] = {
            "image_url": preferred_url(chosen.get("lego_target") or {}),
            "alias_pair_id": chosen.get("translation_pair_id"),
            "alias_source_id": (chosen.get("source_appearance") or {}).get("br_id"),
            "alias_lego_id": (chosen.get("lego_target") or {}).get("lego_id"),
            "method": "same_normalized_source_name_prefer_CID_A_combat_alias",
        }
        resolved += 1
    return resolved


def process_pair(pair: dict):
    pid = pair.get("translation_pair_id")
    su = preferred_url(pair.get("source_appearance") or {})
    lu = preferred_url(pair.get("lego_target") or {})
    fallback = pair.get("_lego_alias_fallback") or {}
    if not lu and fallback.get("image_url"):
        lu = fallback["image_url"]
    rec = {
        "translation_pair_id": pid,
        "source_image_url": su,
        "lego_image_url": lu,
        "lego_image_resolution": "alias_fallback" if fallback else "direct_pair",
        "lego_alias_fallback": fallback or None,
        "processor_version": VERSION,
    }
    if not su or not lu:
        rec["status"] = "missing_preferred_image"
        return rec
    try:
        src = visual_features(fetch_image(su))
        lego = visual_features(fetch_image(lu))
        rec.update({"status": "complete", "source_features": src, "lego_features": lego, "difference": delta(src, lego)})
    except Exception as exc:
        rec.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"[:500]})
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    pairs = list(load_jsonl(args.pairs))
    if args.limit:
        pairs = pairs[: args.limit]
    alias_resolved = attach_alias_fallbacks(pairs)

    results = [None] * len(pairs)
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(process_pair, pair): i for i, pair in enumerate(pairs)}
        for future in as_completed(futures):
            results[futures[future]] = future.result()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for rec in results:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")

    complete = [r for r in results if r.get("status") == "complete"]
    errors = [r for r in results if r.get("status") == "error"]
    missing = [r for r in results if r.get("status") == "missing_preferred_image"]
    signal_counts = {
        "lower_edge_density_in_lego": sum(bool(r["difference"]["heuristic_signals"]["lower_edge_density_in_lego"]) for r in complete),
        "smaller_effective_palette_in_lego": sum(bool(r["difference"]["heuristic_signals"]["smaller_effective_palette_in_lego"]) for r in complete),
        "large_silhouette_bbox_change": sum(bool(r["difference"]["heuristic_signals"]["large_silhouette_bbox_change"]) for r in complete),
    }
    summary = {
        "schema": "fortnite-translation-visual-feature-summary/v2",
        "created_at": now_iso(),
        "processor_version": VERSION,
        "pair_records_requested": len(pairs),
        "complete": len(complete),
        "errors": len(errors),
        "missing_preferred_image": len(missing),
        "alias_fallbacks_attached": alias_resolved,
        "complete_via_alias_fallback": sum(r.get("status") == "complete" and r.get("lego_image_resolution") == "alias_fallback" for r in results),
        "heuristic_signal_counts": signal_counts,
        "semantic_policy": "derived visual measurements support review; they do not auto-assert preserve/simplify/omit/mould/accessory labels",
    }
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
