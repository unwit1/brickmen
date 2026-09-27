from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "audit_mask_topology_against_manual.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location("audit_mask_topology_against_manual", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_expected_diving_topology() -> None:
    tool = load_tool()
    assert (
        tool.expected_topology("human_head_plus_standard_helmet_plus_separate_diving_visor")
        == "head_plus_helmet_plus_diving_facegear"
    )


def test_expected_species_mask_topology() -> None:
    tool = load_tool()
    assert (
        tool.expected_topology("printed_standard_head_plus_separate_wolf_face_mask")
        == "head_plus_separate_species_face_mask"
    )


def test_expected_modified_head_topology() -> None:
    tool = load_tool()
    assert (
        tool.expected_topology("full_modified_wookiee_head_no_standard_cylindrical_head")
        == "dedicated_nonstandard_head_no_separate_headgear"
    )


def test_unmapped_semantic_route_stays_review_gated() -> None:
    tool = load_tool()
    assert tool.expected_topology("printed_balaclava_head_plus_separate_lightning_wing_mask") is None
