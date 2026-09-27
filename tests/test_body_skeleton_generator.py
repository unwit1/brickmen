import json
from pathlib import Path

import pytest

from tools.geometry.generate_body_skeleton import (
    compile_skeleton,
    load_spec,
    skeleton_to_obj,
)


ROOT = Path(__file__).resolve().parents[1]
SKELETONS = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "skeletons"
)


@pytest.mark.parametrize(
    "name",
    [
        "brickmen-broad-v0.json",
        "brickmen-mid-v0.json",
        "brickmen-xl-v0.json",
        "brickmen-giant-v0.json",
    ],
)
def test_all_skeleton_specs_compile(name):
    spec = load_spec(SKELETONS / name)
    compiled = compile_skeleton(spec)
    assert compiled["nodes_mm"]
    assert compiled["bones"]
    assert compiled["joints"]
    assert compiled["production_warning"]


def test_target_height_scales_coordinates():
    spec = load_spec(SKELETONS / "brickmen-broad-v0.json")
    default = compile_skeleton(spec, target_height_mm=42)
    double = compile_skeleton(spec, target_height_mm=84)
    assert double["nodes_mm"]["neck"][2] == pytest.approx(
        default["nodes_mm"]["neck"][2] * 2
    )


def test_shoulder_width_parameter_changes_lateral_positions():
    spec = load_spec(SKELETONS / "brickmen-broad-v0.json")
    default = compile_skeleton(spec)
    wide = compile_skeleton(
        spec, parameter_overrides={"shoulder_width_scale": 1.2}
    )
    assert abs(wide["nodes_mm"]["shoulder_l"][0]) > abs(
        default["nodes_mm"]["shoulder_l"][0]
    )
    assert abs(wide["nodes_mm"]["shoulder_r"][0]) > abs(
        default["nodes_mm"]["shoulder_r"][0]
    )


def test_out_of_range_parameter_is_rejected():
    spec = load_spec(SKELETONS / "brickmen-broad-v0.json")
    with pytest.raises(ValueError):
        compile_skeleton(
            spec, parameter_overrides={"shoulder_width_scale": 99}
        )


def test_obj_export_has_vertices_and_bones():
    spec = load_spec(SKELETONS / "brickmen-mid-v0.json")
    compiled = compile_skeleton(spec)
    payload = skeleton_to_obj(compiled)
    assert "\nv " in payload
    assert "\nl " in payload
    assert "# Units: mm" in payload
