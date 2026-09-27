from pathlib import Path

import pytest

from tools.geometry.compile_body_generation_conditioning import (
    compile_conditioning,
    load_json,
    merge_envelope_fits,
)
from tools.geometry.fit_body_envelope_profile import fit_envelope_profile
from tools.geometry.fit_body_skeleton import fit_skeleton, load_reference
from tools.geometry.generate_body_skeleton import load_spec


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"


def envelope_by_id(payload, envelope_id):
    return next(
        item
        for item in payload["visual_envelopes"]
        if item["envelope_id"] == envelope_id
    )


def test_giant_conditioning_merges_official_shape_and_reference_hardware():
    spec = load_spec(BASE / "skeletons" / "brickmen-giant-v0.json")
    shoulder_ref = load_reference(
        BASE / "reference-landmarks" / "lego-giant-ldraw-shoulders-fit.json"
    )
    envelope_ref = load_reference(
        BASE / "reference-landmarks" / "lego-giant-10128-ldraw-body-profile.json"
    )
    joint = load_json(
        BASE
        / "joint-profiles"
        / "lego-giant-43093-shoulder-reference-v0.json"
    )

    skeleton_fit = fit_skeleton(spec, shoulder_ref)
    body_envelope_fit = fit_envelope_profile(spec, envelope_ref)
    limb_ref = load_reference(
        BASE / "reference-landmarks" / "lego-giant-limb-ldraw-envelope-profile.json"
    )
    limb_envelope_fit = fit_envelope_profile(spec, limb_ref)
    envelope_fit = merge_envelope_fits([body_envelope_fit, limb_envelope_fit])
    payload = compile_conditioning(
        spec,
        skeleton_fit=skeleton_fit,
        envelope_fit=envelope_fit,
        joint_profiles=[joint],
    )

    assert payload["target_height_mm"] == pytest.approx(62.0)
    torso = envelope_by_id(payload, "torso")
    abdomen = envelope_by_id(payload, "abdomen")
    assert torso["size_normalized_body_height"][0] == pytest.approx(
        0.44822387062555535
    )
    assert torso["size_normalized_body_height"][1] == pytest.approx(
        0.41732606682059015
    )
    assert abdomen["size_normalized_body_height"][0] == pytest.approx(
        0.38169368033424167
    )
    assert abdomen["size_normalized_body_height"][1] == pytest.approx(
        0.34055415885259605
    )
    arm = envelope_by_id(payload, "arm_l")
    hand = envelope_by_id(payload, "hand_l")
    assert arm["size_normalized_body_height"][0] == pytest.approx(
        0.181781764684078, abs=1e-6
    )
    assert arm["size_normalized_body_height"][1] == pytest.approx(
        0.27980484946128936, abs=1e-6
    )
    assert arm["a_node"] == "shoulder_l"
    assert arm["b_node"] == "wrist_l"
    assert arm["derived_length_normalized_body_height"] > 0
    assert hand["size_normalized_body_height"] == pytest.approx(
        [0.17426889310845864, 0.24813372766299466, 0.20941651574293846],
        abs=1e-6,
    )

    left_shoulder = payload["skeleton_control"]["nodes"]["shoulder_l"]
    assert left_shoulder["position_normalized_body_height"][0] == pytest.approx(
        -0.224858333348, abs=0.001
    )

    mechanical = payload["mechanical_constraints"][0]
    assert mechanical["joint_profile_id"] == "lego_giant_43093_shoulder_reference_v0"
    assert mechanical["authority_class"] == "reference_only_not_manufacturing_authority"
    assert mechanical["manufacturing_authority"] is False
    assert mechanical["reference_keepout_bbox_mm"] == [16, 6.4, 6.4]
    assert mechanical["reference_keepout_normalized_at_target_height"][0] == pytest.approx(
        16 / 62
    )
    placements = mechanical["placements"]
    assert len(placements) == 2
    left_keepout = next(
        item for item in placements if item["anchor_node"] == "shoulder_l"
    )
    assert left_keepout["anchor_normalized_body_height"] == pytest.approx(
        payload["skeleton_control"]["nodes"]["shoulder_l"][
            "position_normalized_body_height"
        ]
    )
    assert left_keepout["anchor_mm_at_target_height"] == pytest.approx(
        payload["skeleton_control"]["nodes"]["shoulder_l"][
            "position_mm_at_target_height"
        ]
    )
    assert left_keepout["reference_keepout_local_min_mm"] == pytest.approx(
        [-8, -3.2, -3.2]
    )
    assert left_keepout["reference_keepout_local_max_mm"] == pytest.approx(
        [8, 3.2, 3.2]
    )
    assert left_keepout["manufacturing_authority"] is False
    assert payload["production_geometry_authority"] is False
    assert any("reference-only" in text for text in payload["generation_constraints"])


def test_axl_visual_mass_can_change_without_moving_default_broad_shoulders():
    spec = load_spec(BASE / "skeletons" / "brickmen-broad-v0.json")
    ref = load_reference(BASE / "reference-landmarks" / "lego-axl-front.json")
    envelope_fit = fit_envelope_profile(spec, ref)
    payload = compile_conditioning(spec, envelope_fit=envelope_fit)

    torso = envelope_by_id(payload, "torso")
    assert torso["size_normalized_body_height"][0] == pytest.approx(
        0.6743648961, rel=1e-5
    )
    assert payload["skeleton_control"]["nodes"]["shoulder_l"][
        "position_normalized_body_height"
    ][0] == pytest.approx(-0.185)
    assert payload["parameter_layers"]["mechanical_shape_and_landmarks"][
        "shoulder_width_scale"
    ] == pytest.approx(1.0)
    assert payload["parameter_layers"]["visual_envelope"]["torso_width_scale"] > 1.9


def test_reference_height_does_not_override_design_target_height():
    spec = load_spec(BASE / "skeletons" / "brickmen-giant-v0.json")
    shoulder_ref = load_reference(
        BASE / "reference-landmarks" / "lego-giant-ldraw-shoulders-fit.json"
    )
    skeleton_fit = fit_skeleton(spec, shoulder_ref)
    assert skeleton_fit["target_height_mm"] > 70

    payload = compile_conditioning(spec, skeleton_fit=skeleton_fit)
    assert payload["target_height_mm"] == pytest.approx(
        spec["default_target_height_mm"]
    )
    assert payload["source_fits"]["skeleton_reference_height_mm"] > 70


def test_explicit_target_height_controls_mm_only_not_normalized_shape():
    spec = load_spec(BASE / "skeletons" / "brickmen-giant-v0.json")
    payload_62 = compile_conditioning(spec, target_height_mm=62)
    payload_70 = compile_conditioning(spec, target_height_mm=70)

    torso_62 = envelope_by_id(payload_62, "torso")
    torso_70 = envelope_by_id(payload_70, "torso")
    assert torso_62["size_normalized_body_height"] == torso_70[
        "size_normalized_body_height"
    ]
    assert torso_70["size_mm_at_target_height"][0] == pytest.approx(
        torso_62["size_mm_at_target_height"][0] * 70 / 62
    )



def test_merge_envelope_fits_rejects_parameter_conflicts():
    first = {
        "reference_id": "a",
        "parameter_overrides": {"torso_width_scale": 1.1},
        "bound_hits": [],
        "mechanical_parameter_changes": [],
    }
    second = {
        "reference_id": "b",
        "parameter_overrides": {"torso_width_scale": 1.2},
        "bound_hits": [],
        "mechanical_parameter_changes": [],
    }
    with pytest.raises(ValueError, match="Conflicting envelope fits"):
        merge_envelope_fits([first, second])



def test_fixed_hardware_keepout_mm_does_not_scale_with_body_height():
    spec = load_spec(BASE / "skeletons" / "brickmen-giant-v0.json")
    joint = load_json(
        BASE
        / "joint-profiles"
        / "lego-giant-43093-shoulder-reference-v0.json"
    )

    payload_62 = compile_conditioning(
        spec, joint_profiles=[joint], target_height_mm=62
    )
    payload_70 = compile_conditioning(
        spec, joint_profiles=[joint], target_height_mm=70
    )

    mech_62 = payload_62["mechanical_constraints"][0]
    mech_70 = payload_70["mechanical_constraints"][0]
    assert mech_62["reference_keepout_bbox_mm"] == [16, 6.4, 6.4]
    assert mech_70["reference_keepout_bbox_mm"] == [16, 6.4, 6.4]

    left_62 = next(
        item for item in mech_62["placements"] if item["anchor_node"] == "shoulder_l"
    )
    left_70 = next(
        item for item in mech_70["placements"] if item["anchor_node"] == "shoulder_l"
    )
    assert left_62["anchor_normalized_body_height"] == left_70[
        "anchor_normalized_body_height"
    ]
    assert left_70["anchor_mm_at_target_height"][0] == pytest.approx(
        left_62["anchor_mm_at_target_height"][0] * 70 / 62
    )
    assert left_62["reference_keepout_local_max_mm"] == left_70[
        "reference_keepout_local_max_mm"
    ]
    assert left_62["reference_keepout_local_max_normalized"][0] == pytest.approx(
        8 / 62
    )
    assert left_70["reference_keepout_local_max_normalized"][0] == pytest.approx(
        8 / 70
    )
