from pathlib import Path

from tools.geometry.measure_body_reference_envelope import measure_envelope
from tools.geometry.fit_body_skeleton import load_reference


ROOT = Path(__file__).resolve().parents[1]
BASE = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "reference-landmarks"
)


def test_venom_envelope_is_separate_from_mechanics():
    ref = load_reference(BASE / "alpha-af325-venom-front.json")
    result = measure_envelope(ref)
    assert result["measurements"]["shoulder_outer_width"]["width_over_body_height"] > 0.5
    assert result["mechanical_authority"] is False


def test_axl_armor_width_is_recorded_as_visual_envelope():
    ref = load_reference(BASE / "lego-axl-front.json")
    result = measure_envelope(ref)
    assert result["measurements"]["shoulder_outer_width"]["semantic"] == "armor_outer_shoulders"
