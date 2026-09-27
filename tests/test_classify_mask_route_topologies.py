from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "classify_mask_route_topologies.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location("classify_mask_route_topologies", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_diving_route_is_high_confidence() -> None:
    tool = load_tool()
    row = {
        "fig_num": "fig-test",
        "candidate_routes": ["helmet_plus_head", "separate_mask_headgear"],
        "head_components": [{"part_num": "3626cpr1", "print_of": "3626c", "part_name": "Minifig Head"}],
        "headgear_components": [
            {"part_num": "2446", "part_name": "Helmet, Standard"},
            {"part_num": "30090", "part_name": "Headwear Accessory Visor / Diver's Mask"},
        ],
    }
    result = tool.classify(row)
    assert result["topology_class"] == "head_plus_helmet_plus_diving_facegear"
    assert result["topology_confidence"] == 1.0


def test_species_mask_requires_shared_species_signal() -> None:
    tool = load_tool()
    row = {
        "fig_num": "fig-test",
        "candidate_routes": ["separate_mask_headgear"],
        "head_components": [{"part_num": "3626cpr1", "print_of": "3626c", "part_name": "Minifig Head Wolf with Fangs"}],
        "headgear_components": [{"part_num": "mask1", "part_name": "Mask Wolf with White Ears"}],
    }
    result = tool.classify(row)
    assert result["topology_class"] == "head_plus_separate_species_face_mask"
    assert result["topology_confidence"] >= 0.95


def test_standard_skull_print_is_not_dedicated_nonhuman_head() -> None:
    tool = load_tool()
    row = {
        "fig_num": "fig-test",
        "candidate_routes": ["head_print_or_decorated_head_only"],
        "head_components": [{"part_num": "3626cpr1732", "print_of": "3626c", "part_name": "Minifig Head Skeleton Guy, Skull Mask Print"}],
        "headgear_components": [],
    }
    result = tool.classify(row)
    assert result["topology_class"] == "standard_head_print_only"


def test_rock_monster_is_dedicated_head() -> None:
    tool = load_tool()
    row = {
        "fig_num": "fig-test",
        "candidate_routes": ["modified_or_nonhuman_head"],
        "head_components": [{"part_num": "64785", "print_of": None, "part_name": "Head Special, Rock Monster"}],
        "headgear_components": [],
    }
    result = tool.classify(row)
    assert result["topology_class"] == "dedicated_nonstandard_head_no_separate_headgear"


def test_cowl_classification_ignores_semantic_translation() -> None:
    tool = load_tool()
    row = {
        "fig_num": "fig-test",
        "candidate_routes": ["cowl_plus_head", "separate_mask_headgear"],
        "head_components": [{"part_num": "3626cpr1", "print_of": "3626c", "part_name": "Minifig Head"}],
        "headgear_components": [{"part_num": "10113", "part_name": "Mask, Batman Cowl [Plain]"}],
    }
    result = tool.classify(row)
    assert result["topology_class"] == "head_plus_separate_cowl"
    assert result["semantic_function_status"] == "manual_review_required"
    assert result["source_translation_status"] == "exact_source_appearance_pairing_required"


def test_welding_mask_plus_sports_helmet_is_not_sports_faceguard() -> None:
    tool = load_tool()
    row = {
        "fig_num": "fig-test",
        "candidate_routes": ["helmet_plus_head", "separate_mask_headgear"],
        "head_components": [{"part_num": "3626cpr1", "print_of": "3626c", "part_name": "Minifig Head"}],
        "headgear_components": [
            {"part_num": "93560", "part_name": "Helmet, Sports [Plain]"},
            {"part_num": "65195pr0004", "part_name": "Headwear Accessory Welding Mask with Visor"},
        ],
    }
    result = tool.classify(row)
    assert result["topology_class"] == "head_plus_separate_mask_untyped"
    assert result["topology_class"] != "head_plus_sports_helmet_plus_faceguard"


def test_printed_eye_mask_with_hair_is_printed_face_cover_topology() -> None:
    tool = load_tool()
    row = {
        "fig_num": "fig-test",
        "candidate_routes": ["head_print_plus_headgear"],
        "head_components": [
            {
                "part_num": "3626cpr9850",
                "print_of": "3626c",
                "part_name": "Minifig Head Winter Soldier, Black Eye Mask with Eye Holes Print",
            }
        ],
        "headgear_components": [
            {"part_num": "88283", "part_name": "Hair Mid-Length Tousled with Center Part"}
        ],
    }
    result = tool.classify(row)
    assert result["topology_class"] == "printed_face_cover_head_plus_nonmask_headgear"
    assert result["topology_confidence"] >= 0.95


def test_printed_breathing_mask_with_hair_is_printed_face_cover_topology() -> None:
    tool = load_tool()
    row = {
        "fig_num": "fig-test",
        "candidate_routes": ["head_print_plus_headgear"],
        "head_components": [
            {
                "part_num": "3626cpr2308",
                "print_of": "3626c",
                "part_name": "Minifig Head Leia, Smile / Breathing Mask Print",
            }
        ],
        "headgear_components": [
            {"part_num": "64807", "part_name": "Hair Short with Braid around Sides"}
        ],
    }
    result = tool.classify(row)
    assert result["topology_class"] == "printed_face_cover_head_plus_nonmask_headgear"


def test_printed_mask_plus_actual_cowl_does_not_use_nonmask_headgear_rule() -> None:
    tool = load_tool()
    row = {
        "fig_num": "fig-test",
        "candidate_routes": ["head_print_plus_headgear", "cowl_plus_head"],
        "head_components": [
            {
                "part_num": "3626cpr1",
                "print_of": "3626c",
                "part_name": "Minifig Head with Eye Mask Print",
            }
        ],
        "headgear_components": [
            {"part_num": "10113", "part_name": "Mask, Batman Cowl [Plain]"}
        ],
    }
    result = tool.classify(row)
    assert result["topology_class"] == "head_plus_separate_cowl"
