from pathlib import Path

import pytest

from tools.geometry.fit_body_skeleton import (
    fit_skeleton,
    normalized_landmarks,
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


def synthetic_reference():
    return {
        "schema_version": "0.1",
        "reference_id": "synthetic_broad",
        "view": "front",
        "evidence_class": "synthetic",
        "landmark_coordinate_mode": "normalized_body_height",
        "landmarks": {
            "neck": {"position": [0.0, 0.78], "confidence": 1.0},
            "shoulder_l": {"position": [-0.222, 0.70], "confidence": 1.0},
            "shoulder_r": {"position": [0.222, 0.70], "confidence": 1.0},
            "wrist_l": {"position": [-0.294, 0.44], "confidence": 1.0},
            "wrist_r": {"position": [0.294, 0.44], "confidence": 1.0},
        },
        "fit_parameters": ["shoulder_width_scale", "arm_length_scale"],
    }


def test_pixel_landmarks_normalize_to_body_height():
    ref = {
        "reference_id": "pixels",
        "view": "front",
        "evidence_class": "catalog_manual_estimate",
        "body_bbox_px": [100, 50, 300, 450],
        "landmark_coordinate_mode": "pixel",
        "landmarks": {
            "neck": {"position": [200, 150], "confidence": 1.0},
            "shoulder_l": {"position": [160, 180], "confidence": 1.0},
        },
    }
    points = normalized_landmarks(ref)
    assert points["neck"]["coords"]["x"] == pytest.approx(0.0)
    assert points["neck"]["coords"]["z"] == pytest.approx(0.75)
    assert points["shoulder_l"]["coords"]["x"] == pytest.approx(-0.1)


def test_fitter_recovers_wider_shoulders():
    spec = load_spec(SKELETON)
    result = fit_skeleton(spec, synthetic_reference())
    assert result["fit_parameters"]["shoulder_width_scale"] > 1.0
    assert result["final_normalized_rmse"] < result["initial_normalized_rmse"]


def test_fit_never_claims_production_authority():
    spec = load_spec(SKELETON)
    result = fit_skeleton(spec, synthetic_reference())
    assert result["production_geometry_authority"] is False
    assert "connector" in result["warning"].lower()
