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



def test_thigh_scale_moves_knee_and_preserves_shin_length():
    spec = load_spec(SKELETONS / "brickmen-broad-v0.json")
    default = compile_skeleton(spec, target_height_mm=1.0)
    longer = compile_skeleton(
        spec,
        target_height_mm=1.0,
        parameter_overrides={"thigh_length_scale": 1.2},
    )

    default_thigh = abs(
        default["nodes_mm"]["hip_l"][2] - default["nodes_mm"]["knee_l"][2]
    )
    longer_thigh = abs(
        longer["nodes_mm"]["hip_l"][2] - longer["nodes_mm"]["knee_l"][2]
    )
    default_shin = abs(
        default["nodes_mm"]["knee_l"][2] - default["nodes_mm"]["ankle_l"][2]
    )
    longer_shin = abs(
        longer["nodes_mm"]["knee_l"][2] - longer["nodes_mm"]["ankle_l"][2]
    )

    assert longer_thigh == pytest.approx(default_thigh * 1.2)
    assert longer_shin == pytest.approx(default_shin)


def test_shin_scale_does_not_change_thigh_length():
    spec = load_spec(SKELETONS / "brickmen-broad-v0.json")
    default = compile_skeleton(spec, target_height_mm=1.0)
    longer = compile_skeleton(
        spec,
        target_height_mm=1.0,
        parameter_overrides={"shin_length_scale": 1.2},
    )

    assert longer["nodes_mm"]["knee_l"] == default["nodes_mm"]["knee_l"]
    default_shin = abs(
        default["nodes_mm"]["knee_l"][2] - default["nodes_mm"]["ankle_l"][2]
    )
    longer_shin = abs(
        longer["nodes_mm"]["knee_l"][2] - longer["nodes_mm"]["ankle_l"][2]
    )
    assert longer_shin == pytest.approx(default_shin * 1.2)


def test_neck_head_offset_is_independent_from_upper_torso_length():
    spec = load_spec(SKELETONS / "brickmen-broad-v0.json")
    default = compile_skeleton(spec, target_height_mm=1.0)
    head_only = compile_skeleton(
        spec,
        target_height_mm=1.0,
        parameter_overrides={"neck_head_offset_scale": 1.2},
    )

    assert head_only["nodes_mm"]["neck"] == default["nodes_mm"]["neck"]
    assert head_only["nodes_mm"]["shoulder_l"] == default["nodes_mm"]["shoulder_l"]
    default_offset = (
        default["nodes_mm"]["head_center"][2] - default["nodes_mm"]["neck"][2]
    )
    head_offset = (
        head_only["nodes_mm"]["head_center"][2] - head_only["nodes_mm"]["neck"][2]
    )
    assert head_offset == pytest.approx(default_offset * 1.2)


def test_lower_torso_segment_moves_upper_chain_without_changing_upper_segment():
    spec = load_spec(SKELETONS / "brickmen-broad-v0.json")
    default = compile_skeleton(spec, target_height_mm=1.0)
    adjusted = compile_skeleton(
        spec,
        target_height_mm=1.0,
        parameter_overrides={"lower_torso_length_scale": 1.2},
    )

    default_lower = default["nodes_mm"]["chest"][2] - default["nodes_mm"]["waist"][2]
    adjusted_lower = (
        adjusted["nodes_mm"]["chest"][2] - adjusted["nodes_mm"]["waist"][2]
    )
    default_upper = default["nodes_mm"]["neck"][2] - default["nodes_mm"]["chest"][2]
    adjusted_upper = (
        adjusted["nodes_mm"]["neck"][2] - adjusted["nodes_mm"]["chest"][2]
    )

    assert adjusted_lower == pytest.approx(default_lower * 1.2)
    assert adjusted_upper == pytest.approx(default_upper)



def test_giant_arm_visual_envelope_tracks_skeleton_endpoints():
    spec = load_spec(SKELETONS / "brickmen-giant-v0.json")
    compiled = compile_skeleton(spec, target_height_mm=1.0)
    arm = next(item for item in compiled["envelopes"] if item["id"] == "arm_l")

    assert arm["shape"] == "capsule_between_nodes"
    assert arm["a_mm"] == compiled["nodes_mm"]["shoulder_l"]
    assert arm["b_mm"] == compiled["nodes_mm"]["wrist_l"]
    expected = sum(
        (
            compiled["nodes_mm"]["wrist_l"][i]
            - compiled["nodes_mm"]["shoulder_l"][i]
        )
        ** 2
        for i in range(3)
    ) ** 0.5
    assert arm["derived_length_mm"] == pytest.approx(expected, abs=1e-6)
    assert arm["size_mm"][0] == pytest.approx(0.18)
    assert arm["size_mm"][1] == pytest.approx(0.28)


def test_giant_arm_bulk_parameter_does_not_move_joint_nodes():
    spec = load_spec(SKELETONS / "brickmen-giant-v0.json")
    default = compile_skeleton(spec, target_height_mm=1.0)
    bulk = compile_skeleton(
        spec,
        target_height_mm=1.0,
        parameter_overrides={
            "arm_bulk_width_scale": 1.25,
            "arm_bulk_depth_scale": 1.1,
        },
    )

    assert bulk["nodes_mm"]["shoulder_l"] == default["nodes_mm"]["shoulder_l"]
    assert bulk["nodes_mm"]["wrist_l"] == default["nodes_mm"]["wrist_l"]
    default_arm = next(x for x in default["envelopes"] if x["id"] == "arm_l")
    bulk_arm = next(x for x in bulk["envelopes"] if x["id"] == "arm_l")
    assert bulk_arm["size_mm"][0] == pytest.approx(default_arm["size_mm"][0] * 1.25)
    assert bulk_arm["size_mm"][1] == pytest.approx(default_arm["size_mm"][1] * 1.1)
