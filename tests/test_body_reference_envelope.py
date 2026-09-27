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



def test_vertical_span_is_normalized_by_body_height():
    ref = {
        "reference_id": "vertical_test",
        "view": "front",
        "evidence_class": "synthetic",
        "body_bbox_px": [0, 0, 100, 200],
        "landmarks": {
            "neck": {"position": [50, 50], "confidence": 1.0}
        },
        "silhouette_vertical_pairs_px": {
            "head_height": {
                "top_y": 10,
                "bottom_y": 50,
                "confidence": 1.0,
                "semantic": "head_outer_height",
            }
        },
    }
    result = measure_envelope(ref)
    assert result["measurements"]["head_height"]["orientation"] == "vertical"
    assert result["measurements"]["head_height"]["span_over_body_height"] == 0.2
