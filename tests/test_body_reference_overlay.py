from pathlib import Path

from tools.geometry.fit_body_skeleton import load_reference
from tools.geometry.generate_body_skeleton import load_spec
from tools.geometry.render_body_reference_overlay import render_overlay


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"


def test_overlay_contains_skeleton_envelope_and_reference_diagnostics():
    spec = load_spec(BASE / "skeletons" / "brickmen-broad-v0.json")
    ref = load_reference(BASE / "reference-landmarks" / "lego-axl-front.json")
    svg, report = render_overlay(spec, ref)

    assert svg.startswith("<svg")
    assert 'data-envelope="torso"' in svg
    assert 'data-bone="upper_arm_l"' in svg
    assert 'data-node="shoulder_l"' in svg
    assert 'data-measurement="shoulder_outer_width"' in svg
    assert report["matched_landmark_count"] > 0
    assert report["overlay_is_source_image_free"] is True
    assert report["production_geometry_authority"] is False


def test_overlay_does_not_embed_source_image():
    spec = load_spec(BASE / "skeletons" / "brickmen-giant-v0.json")
    ref = load_reference(
        BASE / "reference-landmarks" / "lego-sh0371-hulk-front.json"
    )
    svg, _ = render_overlay(spec, ref)
    assert "<image" not in svg
