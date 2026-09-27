from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "build_mask_headgear_candidate_corpus.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_mask_headgear_candidate_corpus",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hipwear_mask_word_does_not_become_headgear() -> None:
    tool = load_tool()
    component = {
        "part_num": "28421pr0002",
        "part_name": (
            "Minifig Hipwear Duck Swim Ring / Floatie / Inflatable "
            "with Black Batman Mask and Orange Bill Print"
        ),
        "component_role": None,
    }

    assert tool.is_body_component(component)
    assert not tool.is_headgear_component(component)


def test_standard_printed_skull_head_is_not_modified_geometry() -> None:
    tool = load_tool()
    component = {
        "part_num": "3626cpr1732",
        "print_of": "3626c",
        "part_name": (
            "Minifig Head Skeleton Guy, Skull Mask with Yellow Eyes "
            "and Tied String on Back Print [Hollow Stud]"
        ),
        "component_role": "head",
    }

    assert tool.is_standard_cylindrical_minifig_head(component)
    assert tool.modified_head_terms(component) == []


def test_nonstandard_wookiee_head_keeps_modified_geometry_signal() -> None:
    tool = load_tool()
    component = {
        "part_num": "15307pb01",
        "print_of": None,
        "part_name": "Minifig Head Wookiee with Fur and Face Print",
        "component_role": "head",
    }

    assert not tool.is_standard_cylindrical_minifig_head(component)
    assert "wookiee" in tool.modified_head_terms(component)


def test_neckwear_cape_does_not_become_headgear() -> None:
    tool = load_tool()
    component = {
        "part_num": "56630",
        "part_name": "Neckwear Cape, Scalloped 5 Points [Traditional Starched Fabric]",
        "component_role": "headgear",
    }

    assert tool.is_body_component(component)
    assert not tool.is_headgear_component(component)


def test_neckwear_mask_can_still_be_headgear() -> None:
    tool = load_tool()
    component = {
        "part_num": "13791pr0001",
        "part_name": "Minifig Neckwear Mask Islander Tiki with Tribal Print",
        "component_role": None,
    }

    assert not tool.is_body_component(component)
    assert tool.is_headgear_component(component)
