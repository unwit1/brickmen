from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
)
EXPANSION = DATA / "body-architecture-benchmark-expansion-candidates.json"
ARCHITECTURES = DATA / "figure-architecture-registry.json"
SOURCES = DATA / "body-architecture-source-registry.json"
CANONICAL = DATA / "body-architecture-recognition-benchmark-cases.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_expansion_targets_are_real_and_new_to_canonical_benchmark() -> None:
    expansion = load(EXPANSION)
    registry = load(ARCHITECTURES)
    canonical = load(CANONICAL)

    architecture_ids = {
        row["architecture_id"]
        for row in registry["architectures"]
    }
    canonical_targets = {
        row["expected"]["architecture_id"]
        for row in canonical["cases"]
        if row["expected"]["architecture_id"]
    }
    expansion_targets = [
        row["expected"]["architecture_id"]
        for row in expansion["cases"]
    ]

    assert len(expansion["cases"]) == 10
    assert len(set(expansion_targets)) == 10
    assert set(expansion_targets) <= architecture_ids
    assert set(expansion_targets).isdisjoint(canonical_targets)


def test_every_expansion_source_ref_resolves() -> None:
    expansion = load(EXPANSION)
    source_registry = load(SOURCES)
    source_ids = {
        row["source_id"]
        for row in source_registry["sources"]
    }

    for case in expansion["cases"]:
        refs = case["provenance"]["source_refs"]
        assert refs
        assert set(refs) <= source_ids
        locators = case["input_asset"]["reference_locators"]
        assert locators
        assert any(
            str(locator.get("exact_image_url") or "").startswith("https://")
            for locator in locators
        )


def test_staged_cases_are_not_model_input_or_canonical_score_cases() -> None:
    expansion = load(EXPANSION)

    assert expansion["status"] == "staged_media_verification_pending"
    for case in expansion["cases"]:
        assert case["split"] == "expansion_holdout"
        assert case["promotion_state"] == (
            "blocked_pending_media_verification_and_sanitization"
        )
        guard = case["leakage_guard"]
        assert guard["allow_release_maker_as_model_input"] is False
        assert guard["allow_release_code_as_model_input"] is False
        assert guard["allow_character_label_as_model_input"] is False
        assert guard["allow_source_corpus_name_as_model_input"] is False


def test_hagrid_cross_architecture_pair_stays_grouped() -> None:
    expansion = load(EXPANSION)
    hagrid = [
        row
        for row in expansion["cases"]
        if row["audit_metadata"]["character_group"] == "hagrid"
    ]

    assert len(hagrid) == 2
    assert {
        row["expected"]["architecture_id"]
        for row in hagrid
    } == {
        "lego_hagrid_giant_hybrid",
        "lego_hagrid_half_giant",
    }
    assert {row["split"] for row in hagrid} == {"expansion_holdout"}


def test_summary_matches_cases() -> None:
    expansion = load(EXPANSION)
    cases = expansion["cases"]
    summary = expansion["summary"]

    assert summary["staged_cases"] == len(cases)
    assert summary["distinct_architecture_targets"] == len(
        {row["expected"]["architecture_id"] for row in cases}
    )
    assert summary["core_cases"] == sum(
        row["scoring_track"] == "core"
        for row in cases
    )
    assert summary["provisional_cases"] == sum(
        row["scoring_track"] == "provisional"
        for row in cases
    )
