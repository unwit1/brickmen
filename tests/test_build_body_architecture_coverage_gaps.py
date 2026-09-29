from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "build_body_architecture_coverage_gaps.py"
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
REPORT = DATA / "body-architecture-recognition-coverage-gaps.json"

P0_EXPECTED = set()


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_body_architecture_coverage_gaps",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_coverage_report_tracks_current_breadth() -> None:
    tool = load_tool()
    result = tool.build()

    assert result["summary"] == {
        "registry_architectures": 49,
        "covered_architectures": 37,
        "uncovered_architectures": 12,
        "coverage_fraction": 0.755102,
        "p0_official_gaps": 0,
        "p1_gaps": 0,
        "p2_gaps": 12,
    }



def test_challenge_v4_is_the_active_coverage_cohort() -> None:
    tool = load_tool()
    result = tool.build()

    assert "challenge_v4" in result["coverage_sources"]
    assert "challenge_v3" not in result["coverage_sources"]
    assert result["inputs"]["challenge"].endswith(
        "body-architecture-recognition-challenge-cases-v4.json"
    )
    assert len(result["coverage_sources"]["challenge_v4"]) == 23


def test_p0_gaps_are_concrete_official_architectures() -> None:
    tool = load_tool()
    result = tool.build()
    p0 = {
        row["architecture_id"]
        for row in result["gaps"]
        if row["priority"] == "P0"
    }

    assert p0 == P0_EXPECTED
    assert all(
        row["gap_type"] == "official_evaluation_gap"
        for row in result["gaps"]
        if row["priority"] == "P0"
    )


def test_unresolved_umbrellas_are_not_promoted_to_p0() -> None:
    tool = load_tool()
    result = tool.build()

    for row in result["gaps"]:
        status = str(row["status"] or "").lower()
        if any(
            marker in status
            for marker in (
                "umbrella",
                "source_label",
                "unresolved",
                "construction_style_not_single",
            )
        ):
            assert row["priority"] == "P2"
            assert row["gap_type"] == "ontology_resolution"


def test_checked_in_coverage_report_matches_builder() -> None:
    tool = load_tool()
    expected = tool.build()
    actual = json.loads(REPORT.read_text(encoding="utf-8"))

    assert actual == expected

def test_custom_challenge_is_gated_and_closes_p1_gaps() -> None:
    tool = load_tool()
    result = tool.build()

    assert result["inputs"]["custom_challenge"].endswith(
        "body-architecture-custom-acquisition-candidates-v1.json"
    )
    assert result["inputs"]["custom_model_input_gate"].endswith(
        "body-architecture-custom-model-input-manifest-v1.json"
    )
    assert set(result["coverage_sources"]["custom_challenge_v1"]) == {
        "custom_midfig_balljoint_upper",
        "custom_sidan_full_balljoint_poseable",
        "custom_standard_four_arm_single_torso",
    }
    assert not any(row["priority"] == "P1" for row in result["gaps"])

    coverage = {
        row["architecture_id"]: row
        for row in result["coverage"]
    }
    for architecture_id in result["coverage_sources"]["custom_challenge_v1"]:
        assert coverage[architecture_id]["covered"] is True
        assert "custom_challenge_v1" in coverage[architecture_id]["coverage_sources"]


def test_custom_coverage_requires_model_input_admission() -> None:
    tool = load_tool()
    custom = json.loads(
        (DATA / "body-architecture-custom-acquisition-candidates-v1.json")
        .read_text(encoding="utf-8")
    )
    gate = json.loads(
        (DATA / "body-architecture-custom-model-input-manifest-v1.json")
        .read_text(encoding="utf-8")
    )
    gate["entries"][0]["model_input_allowed"] = False

    covered = tool.gated_target_ids(custom, gate)
    assert "custom_midfig_balljoint_upper" not in covered
    assert "custom_sidan_full_balljoint_poseable" in covered
    assert "custom_standard_four_arm_single_torso" in covered

