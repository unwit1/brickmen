from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "build_body_architecture_challenge_cases.py"
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_body_architecture_challenge_cases",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_challenge_cohort_is_character_disjoint_and_byte_verified() -> None:
    tool = load_tool()
    result = tool.build()

    assert result["status"] == "byte_verified_pending_sanitization"
    assert result["summary"] == {
        "total_cases": 8,
        "unique_character_groups": 8,
        "unique_architectures": 8,
        "core_cases": 8,
        "cases_with_exact_image_urls": 8,
        "byte_verified_cases": 8,
    }
    assert result["split_policy"]["training_allowed"] is False
    assert result["split_policy"]["character_overlap_with_baseline"] is False

    baseline_groups = set(result["baseline_benchmark"]["character_groups"])
    challenge_groups = {
        row["group_keys"]["challenge_character_group"]
        for row in result["cases"]
    }
    assert challenge_groups.isdisjoint(baseline_groups)


def test_challenge_targets_are_all_distinct_core_architectures() -> None:
    tool = load_tool()
    result = tool.build()

    targets = [
        row["expected"]["architecture_id"]
        for row in result["cases"]
    ]
    assert len(targets) == len(set(targets)) == 8
    assert all(row["scoring_track"] == "core" for row in result["cases"])
    assert all(
        row["task"] == "closed_set_architecture_classification"
        for row in result["cases"]
    )


def test_challenge_model_inputs_forbid_catalog_identity_leakage() -> None:
    tool = load_tool()
    result = tool.build()

    for row in result["cases"]:
        guard = row["leakage_guard"]
        assert guard["allow_release_maker_as_model_input"] is False
        assert guard["allow_release_code_as_model_input"] is False
        assert guard["allow_character_label_as_model_input"] is False
        assert guard["allow_character_id_as_model_input"] is False
        assert guard["allow_theme_as_model_input"] is False
        assert guard["allow_source_labels_as_model_input"] is False


def test_checked_in_challenge_manifest_matches_builder() -> None:
    tool = load_tool()
    expected = tool.build()
    path = DATA / "body-architecture-recognition-challenge-cases-v1.json"
    actual = json.loads(path.read_text(encoding="utf-8"))

    assert actual == expected
