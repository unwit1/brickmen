from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "build_body_architecture_benchmark_cases.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_body_architecture_benchmark_cases",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_populated_case_manifest_baseline() -> None:
    tool = load_tool()
    result = tool.build()
    summary = result["summary"]

    assert summary["total_cases"] == 27
    assert summary["closed_set_cases"] == 18
    assert summary["open_set_unknown_cases"] == 9
    assert summary["core_scoring_cases"] == 11
    assert summary["provisional_scoring_cases"] == 7
    assert summary["cases_with_reference_locators"] == 27
    assert summary["indirect_only_locator_cases"] == 0
    assert summary["cases_with_exact_image_urls"] == 27
    assert summary["cases_with_verified_image_hashes"] == 27
    assert summary["unique_verified_image_hashes"] == 27
    assert result["status"] == "populated_case_manifest_reference_media_verified_materialization_pending"
    assert summary["split_counts"] == {
        "development": 11,
        "validation": 6,
        "test": 10,
    }

    assert {row["source_corpus"] for row in result["cases"] if row["split"] == "development"} == {"hulk"}
    assert {row["source_corpus"] for row in result["cases"] if row["split"] == "validation"} == {"venom"}
    assert {row["source_corpus"] for row in result["cases"] if row["split"] == "test"} == {"thing"}


def test_label_leakage_is_forbidden() -> None:
    tool = load_tool()
    result = tool.build()

    forbidden = set(result["input_policy"]["forbidden_model_inputs"])
    assert "maker_name" in forbidden
    assert "release_code" in forbidden
    assert "character_name_or_label" in forbidden
    assert "record_id" in forbidden

    for case in result["cases"]:
        guard = case["leakage_guard"]
        assert guard["allow_release_maker_as_model_input"] is False
        assert guard["allow_release_code_as_model_input"] is False
        assert guard["allow_character_label_as_model_input"] is False
        assert guard["allow_source_corpus_name_as_model_input"] is False


def test_open_set_cases_are_not_coerced_into_known_architectures() -> None:
    tool = load_tool()
    result = tool.build()
    unknown = [
        row for row in result["cases"]
        if row["task"] == "architecture_unknown_rejection"
    ]

    assert unknown
    assert all(row["expected"]["architecture_id"] is None for row in unknown)
    assert all(row["expected"]["unresolved_candidate"] for row in unknown)
    assert all(row["scoring_track"] == "open_set" for row in unknown)


def test_target_classification_tracks_evidence_strength() -> None:
    tool = load_tool()
    registry = {
        "canonical": {"status": "canonical_existing"},
        "strong": {"status": "strong_catalog_evidence_physical_measurement_pending"},
        "official": {"status": "official_architecture_variant"},
        "provisional": {"status": "provisional_visual_family_metrology_pending"},
        "umbrella": {"status": "umbrella_candidate_not_a_mechanical_standard"},
    }

    assert tool.classify_target("canonical", registry) == ("canonical", "core", False)
    assert tool.classify_target("strong", registry) == ("strong_evidence", "core", False)
    assert tool.classify_target("official", registry) == ("official_evidence", "core", False)
    assert tool.classify_target("provisional", registry) == (
        "provisional",
        "provisional",
        False,
    )
    assert tool.classify_target("umbrella", registry) == (
        "open_set_unknown",
        "open_set",
        True,
    )
    assert tool.classify_target("missing", registry) == (
        "open_set_unknown",
        "open_set",
        True,
    )

def test_checked_in_manifest_matches_generator() -> None:
    tool = load_tool()
    expected = tool.build()
    manifest_path = (
        Path(__file__).resolve().parents[1]
        / "knowledge"
        / "libraries"
        / "lego-minifigure-customs"
        / "data"
        / "body-architecture-recognition-benchmark-cases.json"
    )
    actual = __import__("json").loads(manifest_path.read_text(encoding="utf-8"))

    assert actual == expected


def test_every_case_has_resolved_reference_locator() -> None:
    tool = load_tool()
    result = tool.build()

    indirect = []
    for case in result["cases"]:
        locators = case["input_asset"]["reference_locators"]
        assert locators
        assert case["provenance"]["source_refs"]
        for locator in locators:
            assert locator["source_id"]
            assert locator["url"]
            assert locator["authority"]
            if locator["locator_quality"] == "indirect_identity_graph":
                indirect.append(case["source_record_id"])

    assert indirect == ["hulk_g2_gh0304_avengers"]


def test_resolved_exact_image_urls_are_source_backed() -> None:
    tool = load_tool()
    result = tool.build()
    resolved = []

    for case in result["cases"]:
        for locator in case["input_asset"]["reference_locators"]:
            if locator.get("exact_image_url"):
                resolved.append((case["source_record_id"], locator))
                assert locator["exact_image_url"].startswith("https://")
                assert locator["image_resolution_status"] == "verified_exact_image_url"

    assert {record_id for record_id, _ in resolved} == {
        "hulk_lego_sh0037_standard",
        "hulk_lego_sh0252_mighty_micros",
        "hulk_lego_sh0371_giant",
        "hulk_alpha_af344_avengers",
        "hulk_alpha_af345_comics",
        "hulk_g2_gh0304_avengers",
        "hulk_bigguy_ragnarok",
        "hulk_mrj_heart_comics",
        "red_hulk_alpha_af364_bnw",
        "red_hulk_g2_gh0303_bnw",
        "red_hulk_bigguy_bnw",
        "venom_lego_sh0542_standard",
        "venom_alpha_af321_movie",
        "venom_alpha_af325",
        "venom_alpha_af328_ancient",
        "venom_xinh_xh1829_movie_bigfig",
        "venom_xinh_xh1911_bigfig",
        "thing_lego_sh1051_first_steps",
        "thing_alpha_af336_first_steps",
        "thing_kdl_k2302_first_steps",
        "thing_tp_tp178_first_steps",
        "thing_tp_tp349_first_steps_bigfig",
        "thing_g2_gh0348",
        "thing_g2_gh0435_bigfig",
        "thing_g2_gh0440_bigfig",
        "thing_shengyuan_sy288_bigfig",
        "thing_xinh_1421_bigfig",
    }


def test_verified_reference_media_has_hash_metadata() -> None:
    tool = load_tool()
    result = tool.build()
    hashes = set()

    for case in result["cases"]:
        verified = [
            locator
            for locator in case["input_asset"]["reference_locators"]
            if locator.get("source_file_sha256")
        ]
        assert verified
        assert case["input_asset"]["status"] == (
            "reference_media_byte_verified_materialization_pending"
        )
        for locator in verified:
            digest = locator["source_file_sha256"]
            assert len(digest) == 64
            assert locator["byte_verification_status"] == "verified"
            assert locator["source_size_bytes"] > 0
            assert locator["source_content_type"].startswith("image/")
            assert locator["source_image_format"] in {"png", "jpeg", "webp", "gif", "bmp", "tiff"}
            assert isinstance(locator["verification_run_id"], int)
            assert locator["verification_run_id"] > 0
            assert locator["source_width"] > 0
            assert locator["source_height"] > 0
            assert locator["raw_media_committed"] is False
            hashes.add(digest)

    assert len(hashes) == 27


def test_character_specific_official_architecture_is_core() -> None:
    tool = load_tool()
    registry = {
        "jabba": {
            "status": "official_character_specific_architecture",
        }
    }

    assert tool.classify_target("jabba", registry) == (
        "official_evidence",
        "core",
        False,
    )
