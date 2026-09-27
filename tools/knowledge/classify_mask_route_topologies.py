#!/usr/bin/env python3
"""Assign conservative physical mask/head topology classes to ranked candidates.

This classifier is intentionally narrower than source-to-LEGO translation. It may
auto-classify physical component topology when part evidence is deterministic, but
semantic function and source-appearance equivalence remain review-gated.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

VERSION = "mask-route-topology-classifier/v1"

SPECIES_TERMS = {
    "bear", "bird", "crocodile", "eagle", "gorilla", "lion", "phoenix",
    "raven", "vulture", "wolf", "wookiee", "dragon", "dragonian",
}


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def text_of(parts):
    return " ".join(str(p.get("part_name") or "") for p in parts).casefold()


def part_ids(parts):
    return {str(p.get("part_num") or "").casefold() for p in parts if p.get("part_num")}


def is_standard_3626_head(part: dict) -> bool:
    part_num = str(part.get("part_num") or "").casefold()
    print_of = str(part.get("print_of") or "").casefold()
    return part_num.startswith("3626") or print_of.startswith("3626")


def shared_species_terms(head_text: str, headgear_text: str) -> list[str]:
    return sorted(term for term in SPECIES_TERMS if term in head_text and term in headgear_text)


def classify(record: dict) -> dict:
    heads = record.get("head_components") or []
    headgear = record.get("headgear_components") or []
    routes = set(record.get("candidate_routes") or [])
    head_text = text_of(heads)
    gear_text = text_of(headgear)
    gear_ids = part_ids(headgear)
    standard_heads = bool(heads) and all(is_standard_3626_head(p) for p in heads)

    result = {
        "fig_num": record.get("fig_num"),
        "figure_name": record.get("figure_name"),
        "candidate_routes": record.get("candidate_routes") or [],
        "route_review_priority_score": record.get("route_review_priority_score"),
        "component_route_confidence_band": record.get("component_route_confidence_band"),
        "topology_class": "unresolved_topology",
        "topology_confidence": 0.0,
        "classification_basis": [],
        "semantic_function_status": "manual_review_required",
        "source_translation_status": "exact_source_appearance_pairing_required",
        "processor_version": VERSION,
    }

    def set_result(label: str, confidence: float, *basis: str):
        result["topology_class"] = label
        result["topology_confidence"] = confidence
        result["classification_basis"] = list(basis)
        result["auto_review_status"] = (
            "high_confidence_physical_topology"
            if confidence >= 0.95
            else "candidate_physical_topology"
        )
        return result

    if not headgear and "modified_or_nonhuman_head" in routes and heads:
        if not standard_heads:
            return set_result(
                "dedicated_nonstandard_head_no_separate_headgear",
                0.99,
                "modified_or_nonhuman_head candidate route",
                "head part is outside the standard 3626 family",
                "no separate headgear components",
            )

    if not headgear and heads and standard_heads and (
        "head_print_or_decorated_head_only" in routes
        or any(term in head_text for term in ("mask", "balaclava", "goggles"))
    ):
        return set_result(
            "standard_head_print_only",
            0.98,
            "standard 3626-family head",
            "no separate headgear components",
            "head decoration carries mask/face-cover signal",
        )

    if headgear:
        diver = any(
            term in gear_text
            for term in ("diver's mask", "divers mask", "diver’s mask", "underwater")
        )
        helmet = "helmet" in gear_text
        if diver and helmet:
            return set_result(
                "head_plus_helmet_plus_diving_facegear",
                1.0,
                "separate helmet present",
                "separate diver/underwater facegear present",
            )

        sports_faceguard = (
            "93561" in gear_ids
            or "hockey mask" in gear_text
        )
        if sports_faceguard:
            return set_result(
                "head_plus_sports_helmet_plus_faceguard",
                1.0,
                "sports helmet/faceguard component pattern",
            )

        if any(term in gear_text for term in ("round bubble", "fishbowl", "bubble helmet")):
            return set_result(
                "head_plus_transparent_or_bubble_enclosure",
                1.0,
                "bubble/fishbowl enclosure component",
            )

        if "cowl" in gear_text:
            return set_result(
                "head_plus_separate_cowl",
                0.99,
                "separate cowl component",
            )

        shared_species = shared_species_terms(head_text, gear_text)
        if "mask" in gear_text and shared_species:
            return set_result(
                "head_plus_separate_species_face_mask",
                0.99,
                "separate mask component",
                "matching species term on head and mask: " + ",".join(shared_species),
            )

        if "wrap" in gear_text and "mask" in gear_text:
            return set_result(
                "printed_head_plus_separate_mask_wrap",
                0.98,
                "separate wrap component with mask semantics",
            )

        if "costume" in gear_text and "mask" in gear_text:
            return set_result(
                "human_or_standard_head_plus_costume_head_cover",
                0.98,
                "separate costume/mask head-cover component",
            )

        if "mask" in gear_text:
            return set_result(
                "head_plus_separate_mask_untyped",
                0.88,
                "separate component explicitly named as mask",
                "semantic subtype not deterministic from component names alone",
            )

        if "hood" in gear_text:
            return set_result(
                "head_plus_separate_hood",
                0.90,
                "separate hood component",
            )

        if helmet:
            return set_result(
                "head_plus_separate_helmet",
                0.82,
                "separate helmet component",
                "no stronger mask/enclosure subtype detected",
            )

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranked", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    rows = [classify(record) for record in load_jsonl(args.ranked)]
    topology_counts = Counter(r["topology_class"] for r in rows)
    status_counts = Counter(r.get("auto_review_status", "unresolved") for r in rows)
    high_conf = sum(r.get("topology_confidence", 0) >= 0.95 for r in rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "schema": "mask-route-topology-classifier-summary/v1",
        "processor_version": VERSION,
        "records": len(rows),
        "high_confidence_physical_topology_records": high_conf,
        "topology_counts": dict(topology_counts.most_common()),
        "auto_review_status_counts": dict(status_counts.most_common()),
        "policy": (
            "This layer classifies only observable physical component topology. "
            "Semantic function and source-to-LEGO translation remain review-gated."
        ),
        "status": "physical_topology_classification_ready",
    }
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
