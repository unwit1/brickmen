from pathlib import Path

from tools.geometry.compare_body_fit_parameterizations import (
    compare_reference,
    safe_expanded_parameters,
)
from tools.geometry.fit_body_skeleton import load_reference
from tools.geometry.generate_body_skeleton import load_spec


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"


def test_safe_expansion_keeps_current_and_adds_identifiable_segments():
    spec = load_spec(BASE / "skeletons" / "brickmen-broad-v0.json")
    ref = load_reference(BASE / "reference-landmarks" / "alpha-af325-venom-front.json")
    names = safe_expanded_parameters(spec, ref)

    for name in ref["fit_parameters"]:
        assert name in names
    assert "neck_head_offset_scale" in names
    assert "thigh_length_scale" in names
    assert "shin_length_scale" in names
    assert "lower_torso_length_scale" not in names
    assert "upper_torso_length_scale" not in names


def test_safe_expanded_fit_is_not_worse_on_seed_reference():
    spec = load_spec(BASE / "skeletons" / "brickmen-broad-v0.json")
    ref = load_reference(BASE / "reference-landmarks" / "alpha-af325-venom-front.json")
    result = compare_reference(spec, ref)

    assert result["expanded_not_worse"] is True
    assert (
        result["safe_expanded_v1"]["final_normalized_rmse"]
        <= result["current"]["final_normalized_rmse"]
    )
    assert result["production_geometry_authority"] is False
