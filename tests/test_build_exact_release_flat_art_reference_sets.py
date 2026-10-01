from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
TOOL = ROOT / "tools" / "knowledge" / "build_exact_release_flat_art_reference_sets.py"
INPUT = DATA / "flat-art-verified-crosswalk-2026-09-25.json"
OUTPUT = DATA / "exact-release-flat-art-reference-sets-v1.jsonl"
SUMMARY = DATA / "exact-release-flat-art-reference-sets-v1-summary.json"


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_exact_release_flat_art_reference_sets",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_output() -> list[dict]:
    return [
        json.loads(line)
        for line in OUTPUT.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_checked_in_exact_release_reference_sets_match_builder() -> None:
    tool = load_tool()
    source = json.loads(INPUT.read_text(encoding="utf-8"))
    expected, summary = tool.build(source)
    actual = load_output()

    assert actual == expected
    assert json.loads(SUMMARY.read_text(encoding="utf-8")) == summary


def test_exact_release_reference_set_gate_is_conservative() -> None:
    rows = load_output()
    assert len(rows) == 23
    assert all(row["exact_release_identity"] is True for row in rows)
    assert all(
        isinstance(row["identifiers"]["bricklink_minifigure_id"], str)
        and isinstance(row["identifiers"]["rebrickable_fig_num"], str)
        for row in rows
    )
    assert all(
        row["policy"]["hidden_surface_inference"] is False
        and row["policy"]["geometry_equivalence_inferred"] is False
        for row in rows
    )


def test_known_front_rear_torso_pairs_are_linked_without_alignment_claims() -> None:
    by_id = {row["reference_set_id"]: row for row in load_output()}
    expected = {
        "refset-flatart-mof002-fig-003303",
        "refset-flatart-sh0003-fig-000227",
        "refset-flatart-sh0004-fig-000008",
        "refset-flatart-mof001-fig-000900",
        "refset-flatart-njo0047-fig-000149",
    }
    observed = {
        refset_id
        for refset_id, row in by_id.items()
        if row["completeness"]["has_explicit_torso_front_rear"]
    }
    assert observed == expected
    for refset_id in expected:
        links = by_id[refset_id]["same_component_cross_surface_correspondence"]
        assert links
        assert all(link["alignment_inferred"] is False for link in links)


def test_summary_locks_current_evidence_gain() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert summary == {
        "schema": "exact-release-flat-art-reference-set-summary/v1",
        "processor_version": "exact-release-flat-art-reference-sets/v1",
        "source_file": "knowledge/libraries/lego-minifigure-customs/data/flat-art-verified-crosswalk-2026-09-25.json",
        "source_records": 61,
        "exact_single_release_records": 47,
        "excluded_records": 14,
        "reference_sets": 23,
        "multi_surface_reference_sets": 13,
        "explicit_torso_front_rear_reference_sets": 5,
        "same_component_cross_surface_correspondences": 5,
        "policy": (
            "Only independently reviewed records with one explicit BrickLink "
            "minifigure ID and one explicit Rebrickable figure ID are admitted. "
            "Missing surfaces remain missing."
        ),
    }
