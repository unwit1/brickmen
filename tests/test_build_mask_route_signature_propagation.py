from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "build_mask_route_signature_propagation.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_mask_route_signature_propagation",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_component_signature_is_order_independent() -> None:
    tool = load_tool()
    left = {
        "head_components": [{"part_num": "h2"}, {"part_num": "h1"}],
        "headgear_components": [{"part_num": "g2"}, {"part_num": "g1"}],
    }
    right = {
        "head_evidence": [{"part_num": "h1"}, {"part_num": "h2"}],
        "headgear_evidence": [{"part_num": "g1"}, {"part_num": "g2"}],
    }

    assert tool.component_signature(left) == tool.component_signature(right)


def test_signature_uses_head_and_headgear_channels_separately() -> None:
    tool = load_tool()
    head = {
        "head_components": [{"part_num": "same"}],
        "headgear_components": [],
    }
    headgear = {
        "head_components": [],
        "headgear_components": [{"part_num": "same"}],
    }

    assert tool.component_signature(head) != tool.component_signature(headgear)
