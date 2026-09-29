#!/usr/bin/env python3
"""Build the character-disjoint architecture-recognition challenge cohort.

Challenge cases broaden official FigureArchitecture coverage without changing the
original Hulk/Venom/Thing benchmark partitions. All challenge cases are evaluation-only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
DEFAULT_CORPUS = DATA / "body-architecture-recognition-challenge-corpus-v1.json"
DEFAULT_REGISTRY = DATA / "figure-architecture-registry.json"
DEFAULT_SOURCE_REGISTRY = DATA / "body-architecture-source-registry.json"
DEFAULT_BASELINE = DATA / "body-architecture-recognition-benchmark-cases.json"
DEFAULT_OUTPUT = DATA / "body-architecture-recognition-challenge-cases-v1.json"
VERSION = "body-architecture-challenge-cases/v1"

BASE_BUILDER = Path(__file__).with_name(
    "build_body_architecture_benchmark_cases.py"
)


def _load_base():
    spec = importlib.util.spec_from_file_location(
        "build_body_architecture_benchmark_cases",
        BASE_BUILDER,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    return json.loads(raw.decode("utf-8")), raw


def build(
    corpus_path: Path = DEFAULT_CORPUS,
    registry_path: Path = DEFAULT_REGISTRY,
    source_registry_path: Path = DEFAULT_SOURCE_REGISTRY,
    baseline_path: Path = DEFAULT_BASELINE,
) -> dict[str, Any]:
    base = _load_base()
    corpus, corpus_raw = load_json(corpus_path)
    registry, registry_raw = load_json(registry_path)
    source_registry, source_raw = load_json(source_registry_path)
    baseline, baseline_raw = load_json(baseline_path)

    architecture_by_id = {
        row["architecture_id"]: row
        for row in registry.get("architectures", [])
    }
    source_by_id = {
        row["source_id"]: row
        for row in source_registry.get("sources", [])
    }

    baseline_character_groups = {
        str(row.get("source_corpus") or "").strip().lower()
        for row in baseline.get("cases", [])
        if row.get("source_corpus")
    }
    challenge_character_groups: set[str] = set()
    cases = []
    corpus_id = str(
        corpus.get("corpus_id") or "body_architecture_challenge_v1"
    ).strip()
    if not corpus_id:
        raise ValueError("challenge corpus requires corpus_id")

    for record in corpus.get("records", []):
        record_id = record["record_id"]
        character_id = str(record.get("character_id") or "").strip().lower()
        if not character_id:
            raise ValueError(f"challenge record lacks character_id: {record_id}")
        if character_id in challenge_character_groups:
            raise ValueError(
                f"challenge character group repeated: {character_id}"
            )
        if character_id in baseline_character_groups:
            raise ValueError(
                f"challenge character overlaps baseline group: {character_id}"
            )
        challenge_character_groups.add(character_id)

        candidate = record.get("architecture_candidate")
        if candidate not in architecture_by_id:
            raise ValueError(
                f"unknown architecture target {candidate!r}: {record_id}"
            )
        tier, track, open_set = base.classify_target(
            candidate,
            architecture_by_id,
        )
        if open_set:
            raise ValueError(
                f"challenge target is unresolved/open-set: {candidate}"
            )
        if track != "core":
            raise ValueError(
                f"challenge target is not core evidence: {candidate} ({tier})"
            )

        locators = []
        for source_id in record.get("source_refs") or []:
            source = source_by_id.get(source_id)
            if source is None:
                raise ValueError(
                    f"unknown source_ref {source_id!r}: {record_id}"
                )
            media = source.get("media") or {}
            image_url = media.get("primary_image_url")
            if not image_url:
                raise ValueError(
                    f"challenge source lacks exact image URL: {source_id}"
                )
            byte = media.get("byte_verification") or {}
            locators.append(
                {
                    "source_id": source_id,
                    "url": source.get("url"),
                    "authority": source.get("authority"),
                    "exact_image_url": image_url,
                    "image_resolution_status": media.get(
                        "resolution_status"
                    ),
                    "source_file_sha256": (
                        byte.get("sha256")
                        if byte.get("status") == "verified"
                        else None
                    ),
                    "source_size_bytes": (
                        byte.get("size_bytes")
                        if byte.get("status") == "verified"
                        else None
                    ),
                    "source_width": (
                        byte.get("width")
                        if byte.get("status") == "verified"
                        else None
                    ),
                    "source_height": (
                        byte.get("height")
                        if byte.get("status") == "verified"
                        else None
                    ),
                    "source_content_type": (
                        byte.get("content_type")
                        if byte.get("status") == "verified"
                        else None
                    ),
                    "source_image_format": (
                        byte.get("image_format")
                        if byte.get("status") == "verified"
                        else None
                    ),
                    "verification_run_id": (
                        byte.get("workflow_run_id")
                        if byte.get("status") == "verified"
                        else None
                    ),
                    "verification_artifact_id": (
                        byte.get("workflow_artifact_id")
                        if byte.get("status") == "verified"
                        else None
                    ),
                }
            )
        if not locators:
            raise ValueError(f"challenge record lacks source_refs: {record_id}")

        release = record.get("release") or {}
        cases.append(
            {
                "case_id": f"archchallenge::{record_id}",
                "source_record_id": record_id,
                "split": "challenge_test",
                "task": "closed_set_architecture_classification",
                "expected": {
                    "architecture_id": candidate,
                    "unresolved_candidate": None,
                },
                "target_evidence_tier": tier,
                "scoring_track": track,
                "input_asset": {
                    "status": (
                        "byte_verified_pending_sanitization"
                        if any(
                            locator.get("source_file_sha256")
                            for locator in locators
                        )
                        else "exact_url_pending_byte_verification"
                    ),
                    "required_view": (
                        "canonical_or_best_available_full_figure"
                    ),
                    "materialized_asset_id": None,
                    "reference_locators": locators,
                },
                "leakage_guard": {
                    "allow_release_maker_as_model_input": False,
                    "allow_release_code_as_model_input": False,
                    "allow_character_label_as_model_input": False,
                    "allow_character_id_as_model_input": False,
                    "allow_theme_as_model_input": False,
                    "allow_source_labels_as_model_input": False,
                    "note": (
                        "Identity/catalog metadata is audit-only. "
                        "Model input must be sanitized image/mesh evidence."
                    ),
                },
                "audit_metadata": {
                    "release": release,
                    "character_id": character_id,
                    "evidence_summary": record.get(
                        "evidence_summary"
                    ) or [],
                    "original_confidence": record.get("confidence"),
                },
                "group_keys": {
                    "challenge_character_group": character_id,
                    "release_code": release.get("code"),
                    "architecture_candidate": candidate,
                },
                "provenance": {
                    "source_corpus_path": corpus_path.relative_to(
                        ROOT
                    ).as_posix(),
                    "source_record_id": record_id,
                    "architecture_registry_path": (
                        registry_path.relative_to(ROOT).as_posix()
                    ),
                    "source_registry_path": (
                        source_registry_path.relative_to(ROOT).as_posix()
                    ),
                    "source_refs": record.get("source_refs") or [],
                },
            }
        )

    verified = sum(
        any(
            locator.get("source_file_sha256")
            for locator in case["input_asset"]["reference_locators"]
        )
        for case in cases
    )
    architectures = sorted(
        {
            case["expected"]["architecture_id"]
            for case in cases
        }
    )

    return {
        "schema_version": "0.1",
        "created": "2026-09-29",
        "status": (
            "byte_verified_pending_sanitization"
            if verified == len(cases)
            else "exact_urls_pending_byte_verification"
        ),
        "benchmark_id": corpus_id,
        "processor_version": VERSION,
        "purpose": (
            "Evaluation-only, character-disjoint expansion of official "
            "body-architecture recognition coverage."
            if corpus_id == "body_architecture_challenge_v1"
            else str(
                corpus.get("purpose")
                or "Evaluation-only body-architecture challenge cohort."
            )
        ),
        "baseline_benchmark": {
            "path": baseline_path.relative_to(ROOT).as_posix(),
            "blob_sha": base.git_blob_sha(baseline_raw),
            "character_groups": sorted(baseline_character_groups),
        },
        "source_corpus": {
            "path": corpus_path.relative_to(ROOT).as_posix(),
            "blob_sha": base.git_blob_sha(corpus_raw),
        },
        "architecture_registry": {
            "path": registry_path.relative_to(ROOT).as_posix(),
            "blob_sha": base.git_blob_sha(registry_raw),
        },
        "source_registry": {
            "path": source_registry_path.relative_to(ROOT).as_posix(),
            "blob_sha": base.git_blob_sha(source_raw),
        },
        "split_policy": {
            "split": "challenge_test",
            "training_allowed": False,
            "character_overlap_with_baseline": False,
            "architecture_overlap_allowed": True,
            "rule": (
                "Challenge cases never enter training. Character groups are "
                "disjoint from baseline Hulk/Venom/Thing groups."
            ),
        },
        "summary": {
            "total_cases": len(cases),
            "unique_character_groups": len(challenge_character_groups),
            "unique_architectures": len(architectures),
            "core_cases": sum(
                case["scoring_track"] == "core"
                for case in cases
            ),
            "cases_with_exact_image_urls": sum(
                any(
                    locator.get("exact_image_url")
                    for locator in case["input_asset"][
                        "reference_locators"
                    ]
                )
                for case in cases
            ),
            "byte_verified_cases": verified,
        },
        "architecture_ids": architectures,
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument(
        "--source-registry",
        type=Path,
        default=DEFAULT_SOURCE_REGISTRY,
    )
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    result = build(
        args.corpus,
        args.registry,
        args.source_registry,
        args.baseline,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
