from pathlib import Path

import pytest

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



def test_side_view_horizontal_spans_fit_depth_not_width():
    spec = load_spec(BROAD)
    reference = {
        "schema_version": "0.1",
        "reference_id": "synthetic_broad_side",
        "view": "left",
        "evidence_class": "synthetic",
        "body_bbox_px": [0, 0, 100, 200],
        "landmarks": {
            "neck": {"position": [50, 44], "confidence": 1.0}
        },
        "silhouette_pairs_px": {
            "head_depth": {
                "left_x": 20,
                "right_x": 77.2,
                "y_px": 30,
                "confidence": 1.0,
                "semantic": "head_depth",
            },
            "chest_outer_depth": {
                "left_x": 25,
                "right_x": 73,
                "y_px": 90,
                "confidence": 1.0,
                "semantic": "torso_depth",
            },
            "waist_outer_depth": {
                "left_x": 30,
                "right_x": 69.6,
                "y_px": 120,
                "confidence": 1.0,
                "semantic": "abdomen_depth",
            },
        },
    }
    fit = fit_envelope_profile(spec, reference)

    assert fit["parameter_overrides"]["head_depth_scale"] == pytest.approx(1.1)
    assert fit["parameter_overrides"]["torso_depth_scale"] == pytest.approx(1.2)
    assert fit["parameter_overrides"]["abdomen_projection_scale"] == pytest.approx(1.1)
    assert "torso_width_scale" not in fit["parameter_overrides"]


def test_vertical_head_span_fits_visual_head_height():
    spec = load_spec(BROAD)
    reference = {
        "schema_version": "0.1",
        "reference_id": "synthetic_head_height",
        "view": "front",
        "evidence_class": "synthetic",
        "body_bbox_px": [0, 0, 100, 200],
        "landmarks": {
            "neck": {"position": [50, 44], "confidence": 1.0}
        },
        "silhouette_vertical_pairs_px": {
            "head_height": {
                "top_y": 10,
                "bottom_y": 58.4,
                "x_px": 50,
                "confidence": 1.0,
                "semantic": "head_outer_height",
            }
        },
    }
    fit = fit_envelope_profile(spec, reference)

    assert fit["parameter_overrides"]["head_height_scale"] == pytest.approx(1.1)
    assert fit["mechanical_parameter_changes"] == []



def test_direct_normalized_ldraw_giant_envelope_reference():
    spec = load_spec(GIANT)
    reference = load_reference(
        BASE / "reference-landmarks" / "lego-giant-10128-ldraw-body-profile.json"
    )
    fit = fit_envelope_profile(spec, reference)

    assert fit["parameter_overrides"]["torso_width_scale"] == pytest.approx(
        0.44822387062555535 / 0.43
    )
    assert fit["parameter_overrides"]["head_width_scale"] == pytest.approx(
        0.24846648683542003 / 0.23
    )
    assert fit["parameter_overrides"]["head_depth_scale"] == pytest.approx(
        0.29639736661412464 / 0.23
    )

    # Current Giant visual-depth design space is intentionally diagnosed as too
    # shallow for this official CAD reference rather than silently expanded.
    assert fit["parameter_overrides"]["torso_depth_scale"] == pytest.approx(
        spec["parameters"]["torso_depth_scale"]["max"]
    )
    assert fit["parameter_overrides"]["abdomen_projection_scale"] == pytest.approx(
        spec["parameters"]["abdomen_projection_scale"]["max"]
    )
    assert "torso_depth_scale" in fit["bound_hits"]
    assert "abdomen_projection_scale" in fit["bound_hits"]
    assert fit["mechanical_parameter_changes"] == []
