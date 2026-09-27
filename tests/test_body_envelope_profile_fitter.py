from pathlib import Path

from tools.geometry.fit_body_envelope_profile import fit_envelope_profile
from tools.geometry.fit_body_skeleton import load_reference
from tools.geometry.generate_body_skeleton import compile_skeleton, load_spec


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
BROAD = BASE / "skeletons" / "brickmen-broad-v0.json"
GIANT = BASE / "skeletons" / "brickmen-giant-v0.json"


def test_axl_visual_width_does_not_move_shoulders():
    spec = load_spec(BROAD)
    reference = load_reference(BASE / "reference-landmarks" / "lego-axl-front.json")
    fit = fit_envelope_profile(spec, reference)

    assert fit["parameter_overrides"]["torso_width_scale"] > 1.5
    assert "shoulder_width_scale" not in fit["parameter_overrides"]
    assert fit["mechanical_parameter_changes"] == []
    assert "shoulder_outer_width" in fit["unmapped_measurements"]

    default = compile_skeleton(spec, target_height_mm=1.0)
    fitted = compile_skeleton(
        spec,
        target_height_mm=1.0,
        parameter_overrides=fit["parameter_overrides"],
    )
    assert default["nodes_mm"]["shoulder_l"] == fitted["nodes_mm"]["shoulder_l"]
    assert fitted["envelopes"][0]["size_mm"][0] > default["envelopes"][0]["size_mm"][0]


def test_giant_envelope_fits_without_mechanical_authority():
    spec = load_spec(GIANT)
    reference = load_reference(BASE / "reference-landmarks" / "lego-sh0371-hulk-front.json")
    fit = fit_envelope_profile(spec, reference)

    assert fit["parameter_overrides"]["torso_width_scale"] > 1.0
    assert fit["production_geometry_authority"] is False
    assert fit["mechanical_parameter_changes"] == []


def test_joint_width_and_torso_width_are_independent_parameters():
    spec = load_spec(BROAD)
    default = compile_skeleton(spec, target_height_mm=1.0)
    wider_shell = compile_skeleton(
        spec, target_height_mm=1.0, parameter_overrides={"torso_width_scale": 2.0}
    )
    wider_joints = compile_skeleton(
        spec, target_height_mm=1.0, parameter_overrides={"shoulder_width_scale": 1.2}
    )

    assert wider_shell["nodes_mm"]["shoulder_l"] == default["nodes_mm"]["shoulder_l"]
    assert wider_shell["envelopes"][0]["size_mm"][0] > default["envelopes"][0]["size_mm"][0]
    assert wider_joints["nodes_mm"]["shoulder_l"] != default["nodes_mm"]["shoulder_l"]
    assert wider_joints["envelopes"][0]["size_mm"][0] == default["envelopes"][0]["size_mm"][0]
