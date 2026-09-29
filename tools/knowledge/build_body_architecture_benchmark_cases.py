#!/usr/bin/env python3
"""Build the populated body-architecture recognition benchmark case manifest.

The source corpora intentionally keep release/maker/character metadata for audit and
provenance. Those fields are explicitly forbidden as model inputs so recognition must
come from visual/mesh evidence rather than catalog-label leakage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

VERSION = "body-architecture-benchmark-cases/v1"
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"

DEFAULT_REGISTRY = DATA / "figure-architecture-registry.json"
DEFAULT_SOURCE_REGISTRY = DATA / "body-architecture-source-registry.json"
DEFAULT_OUTPUT = DATA / "body-architecture-recognition-benchmark-cases.json"
DEFAULT_CORPORA = (
    ("hulk", "development", DATA / "hulk-cross-architecture-corpus.json"),
    ("venom", "validation", DATA / "venom-cross-architecture-corpus.json"),
    ("thing", "test", DATA / "thing-cross-architecture-corpus.json"),
)

OPEN_SET_STATUS_MARKERS = (
    "umbrella_candidate_not_a_mechanical_standard",
    "source_label_only",
    "unresolved",
)


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    return json.loads(raw.decode("utf-8")), raw


def git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def classify_target(
    architecture_candidate: str | None,
    architecture_by_id: dict[str, dict[str, Any]],
) -> tuple[str, str, bool]:
    architecture = architecture_by_id.get(architecture_candidate or "")
    if not architecture:
        return "open_set_unknown", "open_set", True

    status = str(architecture.get("status") or "").lower()
    if any(marker in status for marker in OPEN_SET_STATUS_MARKERS):
        return "open_set_unknown", "open_set", True

    if status == "canonical_existing":
        return "canonical", "core", False
    if "strong" in status:
        return "strong_evidence", "core", False
    return "provisional", "provisional", False


def build_case(
    *,
    corpus_id: str,
    split: str,
    source_path: Path,
    record: dict[str, Any],
    architecture_by_id: dict[str, dict[str, Any]],
    architecture_registry_path: Path,
    architecture_registry_blob_sha: str,
    source_registry_by_id: dict[str, dict[str, Any]],
    source_registry_path: Path,
) -> dict[str, Any]:
    candidate = record.get("architecture_candidate")
    tier, track, open_set = classify_target(candidate, architecture_by_id)
    record_id = record["record_id"]
    release = record.get("release") or {}
    source_refs = record.get("source_refs") or []
    reference_locators = []
    for source_id in source_refs:
        source = source_registry_by_id.get(source_id)
        if not source:
            raise ValueError(
                f"Unknown source_ref {source_id!r} on benchmark record {record_id!r}"
            )
        media = source.get("media") or {}
        verification = media.get("byte_verification") or {}
        reference_locators.append(
            {
                "source_id": source_id,
                "url": source.get("url"),
                "authority": source.get("authority"),
                "locator_quality": source.get(
                    "locator_quality", "direct_or_family_reference"
                ),
                "exact_image_url": media.get("primary_image_url"),
                "image_resolution_status": media.get("resolution_status"),
                "byte_verification_status": verification.get("status"),
                "source_file_sha256": verification.get("sha256"),
                "source_size_bytes": verification.get("size_bytes"),
                "source_content_type": verification.get("content_type"),
                "source_image_format": verification.get("image_format"),
                "verification_run_id": verification.get("workflow_run_id"),
                "raw_media_committed": verification.get("raw_media_committed"),
            }
        )

    return {
        "case_id": f"archrec::{record_id}",
        "split": split,
        "source_corpus": corpus_id,
        "source_record_id": record_id,
        "task": (
            "architecture_unknown_rejection"
            if open_set
            else "closed_set_architecture_classification"
        ),
        "expected": {
            "architecture_id": None if open_set else candidate,
            "unresolved_candidate": candidate if open_set else None,
        },
        "target_evidence_tier": tier,
        "scoring_track": track,
        "input_asset": {
            "status": (
                "reference_media_byte_verified_materialization_pending"
                if any(
                    locator.get("source_file_sha256")
                    for locator in reference_locators
                )
                else "reference_locator_only_pending_materialization"
            ),
            "required_view": "canonical_or_best_available_full_figure",
            "materialized_asset_id": None,
            "reference_locators": reference_locators,
        },
        "leakage_guard": {
            "allow_release_maker_as_model_input": False,
            "allow_release_code_as_model_input": False,
            "allow_character_label_as_model_input": False,
            "allow_source_corpus_name_as_model_input": False,
            "note": (
                "Release/maker/character metadata is audit-only. Model input must be "
                "image/mesh-derived evidence."
            ),
        },
        "audit_metadata": {
            "release": release,
            "source_appearance_family": record.get("source_appearance_family"),
            "original_architecture_candidate": candidate,
            "original_confidence": record.get("confidence"),
        },
        "group_keys": {
            "corpus_character_group": corpus_id,
            "maker": release.get("maker"),
            "source_appearance_family": record.get("source_appearance_family"),
            "architecture_candidate": candidate,
        },
        "provenance": {
            "source_path": source_path.relative_to(ROOT).as_posix(),
            "source_record_id": record_id,
            "architecture_registry_path": architecture_registry_path.relative_to(
                ROOT
            ).as_posix(),
            "architecture_registry_blob_sha": architecture_registry_blob_sha,
            "source_registry_path": source_registry_path.relative_to(ROOT).as_posix(),
            "source_refs": source_refs,
        },
    }


def build(
    registry_path: Path = DEFAULT_REGISTRY,
    source_registry_path: Path = DEFAULT_SOURCE_REGISTRY,
    corpora: tuple[tuple[str, str, Path], ...] = DEFAULT_CORPORA,
) -> dict[str, Any]:
    registry, registry_raw = load_json(registry_path)
    architecture_by_id = {
        row["architecture_id"]: row for row in registry.get("architectures", [])
    }
    registry_blob_sha = git_blob_sha(registry_raw)
    source_registry, source_registry_raw = load_json(source_registry_path)
    source_registry_blob_sha = git_blob_sha(source_registry_raw)
    source_registry_by_id = {
        row["source_id"]: row for row in source_registry.get("sources", [])
    }

    cases: list[dict[str, Any]] = []
    source_corpora: list[dict[str, Any]] = []

    for corpus_id, split, path in corpora:
        corpus, corpus_raw = load_json(path)
        source_corpora.append(
            {
                "id": corpus_id,
                "path": path.relative_to(ROOT).as_posix(),
                "blob_sha": git_blob_sha(corpus_raw),
                "status": corpus.get("status"),
                "created": corpus.get("created"),
            }
        )
        for record in corpus.get("records", []):
            cases.append(
                build_case(
                    corpus_id=corpus_id,
                    split=split,
                    source_path=path,
                    record=record,
                    architecture_by_id=architecture_by_id,
                    architecture_registry_path=registry_path,
                    architecture_registry_blob_sha=registry_blob_sha,
                    source_registry_by_id=source_registry_by_id,
                    source_registry_path=source_registry_path,
                )
            )

    summary = {
        "total_cases": len(cases),
        "closed_set_cases": sum(
            case["task"] == "closed_set_architecture_classification"
            for case in cases
        ),
        "open_set_unknown_cases": sum(
            case["task"] == "architecture_unknown_rejection" for case in cases
        ),
        "core_scoring_cases": sum(case["scoring_track"] == "core" for case in cases),
        "provisional_scoring_cases": sum(
            case["scoring_track"] == "provisional" for case in cases
        ),
        "split_counts": {
            split: sum(case["split"] == split for case in cases)
            for split in ("development", "validation", "test")
        },
        "cases_with_reference_locators": sum(
            bool(case["input_asset"]["reference_locators"]) for case in cases
        ),
        "indirect_only_locator_cases": sum(
            bool(case["input_asset"]["reference_locators"])
            and all(
                locator["locator_quality"] == "indirect_identity_graph"
                for locator in case["input_asset"]["reference_locators"]
            )
            for case in cases
        ),
        "cases_with_exact_image_urls": sum(
            any(
                locator.get("exact_image_url")
                for locator in case["input_asset"]["reference_locators"]
            )
            for case in cases
        ),
        "cases_with_verified_image_hashes": sum(
            any(
                locator.get("source_file_sha256")
                for locator in case["input_asset"]["reference_locators"]
            )
            for case in cases
        ),
        "unique_verified_image_hashes": len(
            {
                locator["source_file_sha256"]
                for case in cases
                for locator in case["input_asset"]["reference_locators"]
                if locator.get("source_file_sha256")
            }
        ),
    }

    return {
        "schema_version": "0.1",
        "created": "2026-09-28",
        "status": (
            "populated_case_manifest_reference_media_verified_materialization_pending"
            if summary["cases_with_verified_image_hashes"] == summary["total_cases"]
            else (
                "populated_case_manifest_exact_image_urls_complete_materialization_pending"
                if summary["cases_with_exact_image_urls"] == summary["total_cases"]
                else "populated_case_manifest_assets_pending"
            )
        ),
        "benchmark_id": "body_architecture_recognition_v0_cases",
        "processor_version": VERSION,
        "objective": (
            "Populate the body-architecture recognition benchmark with real "
            "evidence-backed release cases while preventing label leakage."
        ),
        "split_strategy": {
            "method": "corpus_character_group_holdout",
            "assignments": {corpus_id: split for corpus_id, split, _ in corpora},
            "rationale": (
                "Keep each source character corpus in exactly one split so the same "
                "character family cannot leak across benchmark partitions. Maker and "
                "architecture overlap is allowed to test architecture recognition "
                "across characters."
            ),
            "training_rule": (
                "Validation and test cases are evaluation-only. Do not train on audit "
                "metadata or release identifiers from any split."
            ),
        },
        "scoring_policy": {
            "core": "Canonical or strong evidence-backed architecture targets.",
            "provisional": (
                "Specific architecture-family targets retained for separate scoring "
                "because metrology/mechanical validation remains incomplete."
            ),
            "open_set": (
                "Unresolved or umbrella architecture labels must be rejected as "
                "unknown rather than coerced into a known class."
            ),
            "aggregate_rule": (
                "Report core, provisional, and open-set metrics separately; do not "
                "hide uncertainty in one aggregate score."
            ),
        },
        "input_policy": {
            "current_asset_state": (
                "Every benchmark case has an exact source-backed image URL and verified "
                "SHA-256/size/type metadata. Raw image bytes are not stored in Git and "
                "local materialized asset IDs remain pending."
                if summary["cases_with_verified_image_hashes"] == summary["total_cases"]
                else (
                    "Every benchmark case has at least one exact source-backed image URL; "
                    "image byte verification is incomplete."
                    if summary["cases_with_exact_image_urls"] == summary["total_cases"]
                    else (
                        "Reference locators exist in source corpora, but benchmark image/mesh "
                        "assets are not yet materialized here."
                    )
                )
            ),
            "allowed_model_inputs": [
                "materialized_image_pixels",
                "materialized_mesh_geometry",
                "deterministic_features_derived_from_allowed_assets",
            ],
            "forbidden_model_inputs": [
                "maker_name",
                "release_code",
                "character_name_or_label",
                "source_corpus_name",
                "record_id",
                "catalog_text_that_names_the_architecture",
            ],
            "next_step": (
                "Validate canonical-view identity/quality against the verified media, "
                "materialize locally only where needed for evaluation, then add low-resolution/"
                "occlusion/detached-component variants without changing ground-truth groups."
            ),
        },
        "source_corpora": source_corpora,
        "architecture_registry": {
            "path": registry_path.relative_to(ROOT).as_posix(),
            "blob_sha": registry_blob_sha,
        },
        "source_registry": {
            "path": source_registry_path.relative_to(ROOT).as_posix(),
            "blob_sha": source_registry_blob_sha,
            "source_count": len(source_registry_by_id),
        },
        "summary": summary,
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    result = build(args.registry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
