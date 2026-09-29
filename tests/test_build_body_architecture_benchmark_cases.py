from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "build_body_architecture_benchmark_cases.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_body_architecture_benchmark_cases",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_populated_case_manifest_baseline() -> None:
    tool = load_tool()
    result = tool.build()
    summary = result["summary"]

    assert summary["total_cases"] == 27
    assert summary["closed_set_cases"] == 18
    assert summary["open_set_unknown_cases"] == 9
    assert summary["core_scoring_cases"] == 11
    assert summary["provisional_scoring_cases"] == 7
    assert summary["split_counts"] == {
        "development": 11,
        "validation": 6,
        "test": 10,
    }

    assert {row["source_corpus"] for row in result["cases"] if row["split"] == "development"} == {"hulk"}
    assert {row["source_corpus"] for row in result["cases"] if row["split"] == "validation"} == {"venom"}
    assert {row["source_corpus"] for row in result["cases"] if row["split"] == "test"} == {"thing"}


def test_label_leakage_is_forbidden() -> None:
    tool = load_tool()
    result = tool.build()

    forbidden = set(result["input_policy"]["forbidden_model_inputs"])
    assert "maker_name" in forbidden
    assert "release_code" in forbidden
    assert "character_name_or_label" in forbidden
    assert "record_id" in forbidden

    for case in result["cases"]:
        guard = case["leakage_guard"]
        assert guard["allow_release_maker_as_model_input"] is False
        assert guard["allow_release_code_as_model_input"] is False
        assert guard["allow_character_label_as_model_input"] is False
        assert guard["allow_source_corpus_name_as_model_input"] is False


def test_open_set_cases_are_not_coerced_into_known_architectures() -> None:
    tool = load_tool()
    result = tool.build()
    unknown = [
        row for row in result["cases"]
        if row["task"] == "architecture_unknown_rejection"
    ]

    assert unknown
    assert all(row["expected"]["architecture_id"] is None for row in unknown)
    assert all(row["expected"]["unresolved_candidate"] for row in unknown)
    assert all(row["scoring_track"] == "open_set" for row in unknown)


def test_target_classification_tracks_evidence_strength() -> None:
    tool = load_tool()
    registry = {
        "canonical": {"status": "canonical_existing"},
        "strong": {"status": "strong_catalog_evidence_physical_measurement_pending"},
        "provisional": {"status": "provisional_visual_family_metrology_pending"},
        "umbrella": {"status": "umbrella_candidate_not_a_mechanical_standard"},
    }

    assert tool.classify_target("canonical", registry) == ("canonical", "core", False)
    assert tool.classify_target("strong", registry) == ("strong_evidence", "core", False)
    assert tool.classify_target("provisional", registry) == (
        "provisional",
        "provisional",
        False,
    )
    assert tool.classify_target("umbrella", registry) == (
        "open_set_unknown",
        "open_set",
        True,
    )
    assert tool.classify_target("missing", registry) == (
        "open_set_unknown",
        "open_set",
        True,
    )
