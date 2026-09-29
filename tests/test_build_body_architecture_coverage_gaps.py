from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "build_body_architecture_coverage_gaps.py"
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
REPORT = DATA / "body-architecture-recognition-coverage-gaps.json"

P0_EXPECTED = {
    "lego_homemaker_maxifigure_legacy",
}


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
        "covered_architectures": 33,
        "uncovered_architectures": 16,
        "coverage_fraction": 0.673469,
        "p0_official_gaps": 1,
        "p1_gaps": 3,
        "p2_gaps": 12,
    }



def test_challenge_v3_is_the_active_coverage_cohort() -> None:
    tool = load_tool()
    result = tool.build()

    assert "challenge_v3" in result["coverage_sources"]
    assert "challenge_v2" not in result["coverage_sources"]
    assert result["inputs"]["challenge"].endswith(
        "body-architecture-recognition-challenge-cases-v3.json"
    )
    assert len(result["coverage_sources"]["challenge_v3"]) == 22


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
