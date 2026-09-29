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

    assert corpus["status"] == "byte_verified_pending_sanitization"
    assert corpus["summary"]["total_pairs"] == 2
    assert corpus["summary"]["total_unique_assets"] == 4
    assert corpus["summary"]["byte_verified_assets"] == 4
    assert corpus["summary"]["runnable_pairs"] == 0

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
        assert pair["pair_status"] == (
            "blocked_until_both_assets_model_input_approved"
        )

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


def test_contrast_assets_remain_metadata_only_until_sanitized() -> None:
    corpus = load(CONTRAST)

    for pair in corpus["pairs"]:
        for side in ("left", "right"):
            row = pair[side]
            assert row["exact_image_url"].startswith("https://")
            assert len(row["source_file_sha256"]) == 64

    hagrid = next(
        pair for pair in corpus["pairs"]
        if pair["character_id"] == "hagrid"
    )
    assert hagrid["left"]["model_input_state"] == "pending_visual_sanitization"
    assert hagrid["right"]["model_input_state"] == "pending_visual_sanitization"

    hulk = next(
        pair for pair in corpus["pairs"]
        if pair["character_id"] == "hulk"
    )
    assert hulk["left"]["model_input_state"] == "pending_visual_sanitization"
    assert hulk["right"]["model_input_state"] == "approved_raw_reference"


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
