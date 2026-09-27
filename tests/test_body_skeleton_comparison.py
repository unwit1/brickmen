from pathlib import Path

from tools.geometry.compare_body_skeletons import compare_reference


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
REGISTRY = BASE / "skeletons" / "registry.json"


def test_alpha_venom_comparison_reports_scale():
    result = compare_reference(
        BASE / "reference-landmarks" / "alpha-af325-venom-front.json",
        REGISTRY,
    )
    broad = next(
        item for item in result["candidates"]
        if item["skeleton_id"] == "brickmen_broad_v0_skeleton"
    )
    assert broad["height_compatibility"]["status"] == "within_design_range"
    assert result["production_geometry_authority"] is False


def test_alpha_hulk_xl_scale_is_compatible():
    result = compare_reference(
        BASE / "reference-landmarks" / "alpha-af345-hulk-front.json",
        REGISTRY,
    )
    xl = next(
        item for item in result["candidates"]
        if item["skeleton_id"] == "brickmen_xl_v0_skeleton"
    )
    assert xl["height_compatibility"]["status"] == "within_design_range"
