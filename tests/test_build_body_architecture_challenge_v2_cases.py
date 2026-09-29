from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "build_body_architecture_challenge_cases.py"
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
CORPUS = DATA / "body-architecture-recognition-challenge-corpus-v2.json"
MANIFEST = DATA / "body-architecture-recognition-challenge-cases-v2.json"

NEW_ARCHITECTURES = {
    "minifig_medium_leg",
    "minifig_lowerbody_serpent",
    "minifig_lowerbody_merfolk",
    "minifig_lowerbody_faun_digitigrade",
    "specialized_tail_body_jabba",
    "minifig_battle_droid_mechanical",
    "minifig_super_battle_droid_integrated",
    "minifig_lowerbody_robot_rollers",
}


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_body_architecture_challenge_cases",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_challenge_v2_is_fully_byte_verified_and_character_disjoint() -> None:
    tool = load_tool()
    result = tool.build(corpus_path=CORPUS)

    assert result["benchmark_id"] == "body_architecture_challenge_v2"
    assert result["status"] == "byte_verified_pending_sanitization"
    assert result["summary"] == {
        "total_cases": 16,
        "unique_character_groups": 16,
        "unique_architectures": 16,
        "core_cases": 16,
        "cases_with_exact_image_urls": 16,
        "byte_verified_cases": 16,
    }
    assert result["split_policy"]["training_allowed"] is False
    assert result["split_policy"]["character_overlap_with_baseline"] is False

    groups = [
        row["group_keys"]["challenge_character_group"]
        for row in result["cases"]
    ]
    assert len(groups) == len(set(groups)) == 16
    assert set(groups).isdisjoint(
        set(result["baseline_benchmark"]["character_groups"])
    )


def test_challenge_v2_adds_eight_new_official_architectures() -> None:
    tool = load_tool()
    result = tool.build(corpus_path=CORPUS)
    targets = {
        row["expected"]["architecture_id"]
        for row in result["cases"]
    }

    assert NEW_ARCHITECTURES <= targets
    assert len(targets) == 16
    assert all(row["scoring_track"] == "core" for row in result["cases"])

    for row in result["cases"]:
        locator = row["input_asset"]["reference_locators"][0]
        assert len(locator["source_file_sha256"]) == 64
        assert locator["source_width"] > 0
        assert locator["source_height"] > 0
        assert locator["verification_run_id"] > 0
        assert locator["verification_artifact_id"] > 0


def test_challenge_v2_inherits_v1_without_mutating_it() -> None:
    v1 = json.loads(
        (
            DATA / "body-architecture-recognition-challenge-corpus-v1.json"
        ).read_text(encoding="utf-8")
    )
    v2 = json.loads(CORPUS.read_text(encoding="utf-8"))

    v1_ids = [row["record_id"] for row in v1["records"]]
    v2_ids = [row["record_id"] for row in v2["records"]]

    assert v2_ids[: len(v1_ids)] == v1_ids
    assert len(v1_ids) == 8
    assert len(v2_ids) == 16
    assert len(set(v2_ids) - set(v1_ids)) == 8


def test_checked_in_challenge_v2_manifest_matches_builder() -> None:
    tool = load_tool()
    expected = tool.build(corpus_path=CORPUS)
    actual = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert actual == expected
