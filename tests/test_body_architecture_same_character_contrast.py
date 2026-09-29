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
CONTRAST = DATA / "body-architecture-same-character-contrast-v1.json"
ARCHITECTURES = DATA / "figure-architecture-registry.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_same_character_contrast_pairs_are_hash_pinned() -> None:
    corpus = load(CONTRAST)

    assert corpus["status"] == "runnable_all_assets_visual_sanitization_approved"
    assert corpus["summary"]["total_pairs"] == 2
    assert corpus["summary"]["total_unique_assets"] == 4
    assert corpus["summary"]["byte_verified_assets"] == 4
    assert corpus["summary"]["runnable_pairs"] == 2
    assert corpus["summary"]["model_input_approved_assets"] == 4

    hashes = []
    for pair in corpus["pairs"]:
        assert pair["left"]["source_file_sha256"]
        assert pair["right"]["source_file_sha256"]
        hashes.extend(
            [
                pair["left"]["source_file_sha256"],
                pair["right"]["source_file_sha256"],
            ]
        )
        assert pair["pair_status"] == "runnable"

    assert len(hashes) == len(set(hashes)) == 4


def test_each_pair_holds_character_constant_and_changes_architecture() -> None:
    corpus = load(CONTRAST)
    registry = load(ARCHITECTURES)
    valid = {
        row["architecture_id"]
        for row in registry["architectures"]
    }

    for pair in corpus["pairs"]:
        left = pair["left"]
        right = pair["right"]
        assert left["architecture_id"] in valid
        assert right["architecture_id"] in valid
        assert left["architecture_id"] != right["architecture_id"]
        assert pair["character_id"]


def test_contrast_assets_are_exact_hash_approved_raw_inputs() -> None:
    corpus = load(CONTRAST)

    for pair in corpus["pairs"]:
        for side in ("left", "right"):
            row = pair[side]
            assert row["exact_image_url"].startswith("https://")
            assert len(row["source_file_sha256"]) == 64
            assert row["model_input_state"] == "approved_raw_reference"

    assert corpus["sanitization_reviews"].endswith(
        "body-architecture-same-character-contrast-sanitization-reviews-v1.json"
    )


def test_pair_case_references_point_to_existing_benchmark_cases() -> None:
    corpus = load(CONTRAST)
    canonical = load(DATA / "body-architecture-recognition-benchmark-cases.json")
    challenge = load(DATA / "body-architecture-recognition-challenge-cases-v1.json")
    known = {
        row["case_id"]
        for row in canonical["cases"]
    } | {
        row["case_id"]
        for row in challenge["cases"]
    }

    referenced = {
        side["case_ref"]
        for pair in corpus["pairs"]
        for side in (pair["left"], pair["right"])
        if side["case_ref"]
    }
    assert referenced <= known


def test_contrast_model_input_manifest_is_fully_runnable() -> None:
    manifest = load(
        DATA / "body-architecture-same-character-contrast-model-input-v1.json"
    )
    corpus = load(CONTRAST)

    assert manifest["summary"] == {
        "total_pairs": 2,
        "total_assets": 4,
        "model_input_allowed_assets": 4,
        "runnable_pairs": 2,
    }
    assert all(row["model_input_allowed"] is True for row in manifest["assets"])

    corpus_assets = {
        side["source_record_id"]: side["source_file_sha256"]
        for pair in corpus["pairs"]
        for side in (pair["left"], pair["right"])
    }
    manifest_assets = {
        row["source_record_id"]: row["asset_sha256"]
        for row in manifest["assets"]
    }
    assert manifest_assets == corpus_assets


def test_contrast_visual_reviews_cover_every_asset_exactly_once() -> None:
    reviews = load(
        DATA
        / "body-architecture-same-character-contrast-sanitization-reviews-v1.json"
    )
    corpus = load(CONTRAST)

    expected = {
        side["source_record_id"]: side["source_file_sha256"]
        for pair in corpus["pairs"]
        for side in (pair["left"], pair["right"])
    }
    actual = {
        row["source_record_id"]: row["source_file_sha256"]
        for row in reviews["reviews"]
    }

    assert actual == expected
    assert len(reviews["reviews"]) == 4
    assert all(row["status"] == "approved_raw" for row in reviews["reviews"])
    assert all(row["raw_model_input_allowed"] is True for row in reviews["reviews"])
