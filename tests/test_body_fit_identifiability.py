from pathlib import Path

import pytest

from tools.geometry.analyze_body_fit_identifiability import (
    analyze_identifiability,
    matrix_rank,
)
from tools.geometry.generate_body_skeleton import load_spec


ROOT = Path(__file__).resolve().parents[1]
SKELETON = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "skeletons"
    / "brickmen-broad-v0.json"
)


def reference_with(*names):
    landmarks = {}
    source = {
        "neck": [0.0, 0.78],
        "chest": [0.0, 0.62],
        "shoulder_l": [-0.185, 0.70],
        "shoulder_r": [0.185, 0.70],
        "wrist_l": [-0.245, 0.44],
        "wrist_r": [0.245, 0.44],
    }
    for name in names:
        landmarks[name] = {"position": source[name], "confidence": 1.0}
    return {
        "reference_id": "synthetic_identifiability",
        "view": "front",
        "evidence_class": "synthetic",
        "landmark_coordinate_mode": "normalized_body_height",
        "landmarks": landmarks,
    }


def test_matrix_rank_basic_cases():
    assert matrix_rank([[1, 0], [0, 1]]) == 2
    assert matrix_rank([[1, 1], [2, 2]]) == 1
    assert matrix_rank([[0, 0], [0, 0]]) == 0


def test_shoulder_width_and_arm_length_are_distinguishable():
    spec = load_spec(SKELETON)
    ref = reference_with("shoulder_l", "shoulder_r", "wrist_l", "wrist_r")
    result = analyze_identifiability(
        spec,
        ref,
        parameter_names=["shoulder_width_scale", "arm_length_scale"],
    )
    assert result["jacobian_rank"] == 2
    assert result["status"] == "locally_identifiable"


def test_lower_and_upper_torso_are_confounded_without_chest_landmark():
    spec = load_spec(SKELETON)
    ref = reference_with("neck")
    result = analyze_identifiability(
        spec,
        ref,
        parameter_names=["lower_torso_length_scale", "upper_torso_length_scale"],
    )
    assert result["jacobian_rank"] == 1
    assert result["status"] == "partially_identifiable"
    assert result["confounded_pairs"]
    pair = result["confounded_pairs"][0]
    assert pair["absolute_cosine"] == pytest.approx(1.0)


def test_chest_landmark_breaks_torso_segment_confounding():
    spec = load_spec(SKELETON)
    ref = reference_with("chest", "neck")
    result = analyze_identifiability(
        spec,
        ref,
        parameter_names=["lower_torso_length_scale", "upper_torso_length_scale"],
    )
    assert result["jacobian_rank"] == 2
    assert result["status"] == "locally_identifiable"


def test_envelope_only_parameter_is_unobserved_by_skeleton_landmarks():
    spec = load_spec(SKELETON)
    ref = reference_with("neck", "shoulder_l", "shoulder_r")
    result = analyze_identifiability(
        spec,
        ref,
        parameter_names=["torso_width_scale"],
    )
    assert result["jacobian_rank"] == 0
    assert result["unobserved_parameters"] == ["torso_width_scale"]
