#!/usr/bin/env python3
"""Build Fortnite normal-style -> LEGO Style TranslationPairs and annotation queues.

Inputs are Fortnite-Datamining/Fortnite-API compatible BR and LEGO cosmetics JSON
snapshots. Strong identifiers are preferred and every derived pair preserves the raw
image references and selected source metadata needed for downstream visual differencing.

The output is still candidate supervision: feature-level preserve/simplify/omit/mould
labels require visual review or a validated vision pipeline and are never guessed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION = "fortnite-lego-translation-pairs/v2"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    obj = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for k in ("data", "items", "cosmetics", "results"):
            if isinstance(obj.get(k), list):
                return obj[k]
    raise ValueError(f"could not find list payload in {path}")


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").casefold()).strip()


def scalars(obj, prefix=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (str, int, float, bool)) or v is None:
                out.append((key, v))
            elif isinstance(v, (dict, list)):
                out.extend(scalars(v, key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(scalars(v, f"{prefix}[{i}]"))
    return out


def first(obj, *keys):
    for k in keys:
        if isinstance(obj, dict) and obj.get(k) not in (None, ""):
            return obj[k]
    return None


def image_urls(obj):
    vals = []
    for k, v in scalars(obj):
        if (
            isinstance(v, str)
            and v.startswith(("http://", "https://"))
            and any(x in k.casefold() for x in ("image", "icon", "small", "large", "wide"))
        ):
            vals.append(v)
    return sorted(set(vals))


def stable(*parts):
    return hashlib.sha256("|".join(str(x) for x in parts).encode()).hexdigest()[:24]


def selected_metadata(obj):
    """Keep compact semantic context without copying the entire upstream record."""
    if not isinstance(obj, dict):
        return {}
    keys = (
        "added",
        "description",
        "introduction",
        "rarity",
        "series",
        "set",
        "type",
        "variants",
        "metaTags",
        "searchTags",
        "soundLibraryTags",
        "builtInEmoteIds",
        "unlockRequirements",
    )
    return {k: obj[k] for k in keys if k in obj and obj[k] not in (None, "", [], {})}


def annotation_queue_record(pair):
    src = pair["source_appearance"]
    tgt = pair["lego_target"]
    return {
        "translation_pair_id": pair["translation_pair_id"],
        "pair_family": pair["pair_family"],
        "identity_match_confidence": pair["identity_match_confidence"],
        "source": {
            "id": src.get("br_id"),
            "name": src.get("name"),
            "images": src.get("images", []),
            "metadata": src.get("metadata", {}),
        },
        "lego": {
            "id": tgt.get("lego_id"),
            "name": tgt.get("name"),
            "images": tgt.get("images", []),
            "metadata": tgt.get("metadata", {}),
        },
        "annotation_status": "pending_visual_semantic_review",
        "required_labels": {
            "preserved": [],
            "simplified": [],
            "omitted": [],
            "exaggerated": [],
            "moved_to_mould": [],
            "moved_to_accessory": [],
            "moved_to_cloth": [],
            "base_plastic_color_decisions": [],
            "print_region_allocation": [],
            "mask_headgear_route": None,
            "expression_translation": None,
            "identity_critical_features": [],
        },
        "review_requirements": [
            "verify exact source and LEGO image views",
            "do not infer hidden/rear features from front-only evidence",
            "record uncertainty and competing interpretations",
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--br", type=Path, required=True)
    ap.add_argument("--lego", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    br = load(args.br)
    lego = load(args.lego)
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    br_by_id = {
        str(first(x, "id", "backendValue", "path")): x
        for x in br
        if first(x, "id", "backendValue", "path")
    }
    br_name = defaultdict(list)
    for x in br:
        n = norm(first(x, "name", "displayName"))
        if n:
            br_name[n].append(x)

    pairs = []
    methods = Counter()
    unmatched = []
    image_coverage = Counter()

    for l in lego:
        lid = str(first(l, "id", "backendValue", "path") or "")
        lname = str(first(l, "name", "displayName") or "")
        candidate = None
        method = None
        confidence = 0.0
        evidence = []

        if lid and lid in br_by_id:
            candidate = br_by_id[lid]
            method = "exact_primary_id"
            confidence = 1.0
            evidence = [lid]

        if candidate is None:
            hits = []
            for k, v in scalars(l):
                if isinstance(v, str) and v in br_by_id:
                    hits.append((k, v))
            unique = {v for _, v in hits}
            if len(unique) == 1:
                bid = next(iter(unique))
                candidate = br_by_id[bid]
                method = "embedded_br_id"
                confidence = 0.98
                evidence = hits

        if candidate is None:
            n = norm(lname)
            if n and len(br_name[n]) == 1:
                candidate = br_name[n][0]
                method = "unique_exact_name"
                confidence = 0.85
                evidence = [lname]

        if candidate is None:
            unmatched.append(
                {
                    "lego_id": lid or None,
                    "lego_name": lname or None,
                    "field_names": sorted(l.keys()) if isinstance(l, dict) else [],
                }
            )
            continue

        bid = str(first(candidate, "id", "backendValue", "path") or "")
        bname = str(first(candidate, "name", "displayName") or "")
        source_images = image_urls(candidate)
        lego_images = image_urls(l)
        if source_images:
            image_coverage["source_has_image"] += 1
        if lego_images:
            image_coverage["lego_has_image"] += 1
        if source_images and lego_images:
            image_coverage["both_have_images"] += 1

        rec = {
            "translation_pair_id": "fortnitepair-" + stable(lid, bid, method),
            "pair_family": "fortnite_outfit_to_lego_style",
            "source_appearance": {
                "provider": "Fortnite",
                "br_id": bid or None,
                "name": bname or None,
                "images": source_images,
                "metadata": selected_metadata(candidate),
            },
            "lego_target": {
                "provider": "Fortnite LEGO Style",
                "lego_id": lid or None,
                "name": lname or None,
                "images": lego_images,
                "metadata": selected_metadata(l),
            },
            "join_method": method,
            "join_evidence": evidence,
            "identity_match_confidence": confidence,
            "exactness": "candidate_same_cosmetic_identity",
            "semantic_supervision_status": "identity_resolved_visual_labels_pending",
            "review_status": "automatic_candidate",
            "processor_version": VERSION,
        }
        pairs.append(rec)
        methods[method] += 1

    pairs.sort(key=lambda x: (x["source_appearance"]["name"] or "", x["translation_pair_id"]))

    with (out / "fortnite_lego_translation_pairs.jsonl").open("w", encoding="utf-8") as handle:
        for rec in pairs:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with (out / "fortnite_lego_semantic_annotation_queue.jsonl").open("w", encoding="utf-8") as handle:
        for rec in pairs:
            handle.write(json.dumps(annotation_queue_record(rec), ensure_ascii=False) + "\n")

    with (out / "fortnite_lego_unmatched.jsonl").open("w", encoding="utf-8") as handle:
        for rec in unmatched:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")

    summary = {
        "schema": "fortnite-lego-translation-pair-summary/v2",
        "created_at": now_iso(),
        "processor_version": VERSION,
        "input_sha256": {
            "br": sha256_file(args.br),
            "lego": sha256_file(args.lego),
        },
        "br_records": len(br),
        "lego_records": len(lego),
        "candidate_pairs": len(pairs),
        "unmatched_lego": len(unmatched),
        "pair_methods": dict(methods),
        "image_coverage": dict(image_coverage),
        "semantic_annotation_queue_records": len(pairs),
        "lego_top_level_fields": sorted(
            set(k for x in lego if isinstance(x, dict) for k in x.keys())
        ),
        "br_top_level_fields": sorted(
            set(k for x in br if isinstance(x, dict) for k in x.keys())
        ),
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
