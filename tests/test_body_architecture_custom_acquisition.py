from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
PLAN = DATA / "body-architecture-custom-acquisition-candidates-v1.json"

EXPECTED_HASHES = {
    "custom_midfig_balljoint_upper": "c79fc80eba86f18b155c358bfc900923f5743777bdd215a51b9828142b8d08b2",
    "custom_standard_four_arm_single_torso": "eb3649ca3c8c331bec1e42f15b6326bb47253b4bba8ec13ae57e2db0d3c2af14",
}


def test_custom_acquisition_plan_preserves_media_quality_gate() -> None:
    doc = json.loads(PLAN.read_text(encoding="utf-8"))

    assert doc["status"] == "byte_verified_pending_visual_sanitization_and_sidan_media_resolution"
    assert {
        row["expected"]["architecture_id"]
        for row in doc["cases"]
    } == set(EXPECTED_HASHES)

    hashes = []
    for row in doc["cases"]:
        locator = row["input_asset"]["reference_locators"][0]
        architecture_id = row["expected"]["architecture_id"]
        assert locator["exact_image_url"].startswith("https://titanicbricks.com/")
        assert locator["source_file_sha256"] == EXPECTED_HASHES[architecture_id]
        assert locator["verification_run_id"] == 36630907484
        assert locator["verification_artifact_id"] == 11061773814
        assert row["input_asset"]["status"] == "byte_verified_pending_sanitization"
        hashes.append(locator["source_file_sha256"])

    assert len(set(hashes)) == 2
    assert doc["verification_snapshot"]["verified_cases"] == 2
    assert doc["verification_snapshot"]["error_cases"] == 0
    assert doc["verification_snapshot"]["raw_media_committed"] is False

    unresolved = doc["unresolved_media"]
    assert len(unresolved) == 1
    assert unresolved[0]["architecture_id"] == "custom_sidan_full_balljoint_poseable"
    assert unresolved[0]["status"] == "high_resolution_exact_media_unresolved"
    assert ".50.50.jpg" in unresolved[0]["observed_thumbnail_example"]
