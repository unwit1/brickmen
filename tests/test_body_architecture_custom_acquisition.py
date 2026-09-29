from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
PLAN = DATA / "body-architecture-custom-acquisition-candidates-v1.json"

EXPECTED_HASHES = {
    "custom_midfig_balljoint_upper": "c79fc80eba86f18b155c358bfc900923f5743777bdd215a51b9828142b8d08b2",
    "custom_standard_four_arm_single_torso": "eb3649ca3c8c331bec1e42f15b6326bb47253b4bba8ec13ae57e2db0d3c2af14",
    "custom_sidan_full_balljoint_poseable": "2ac7f9ba8793107e58892205ea56cc772b876cd63cd2fda08e51e1a0ec8e831e",
}


def test_custom_acquisition_cohort_is_fully_byte_verified() -> None:
    doc = json.loads(PLAN.read_text(encoding="utf-8"))

    assert doc["status"] == "byte_verified_visual_review_complete"
    assert {
        row["expected"]["architecture_id"]
        for row in doc["cases"]
    } == set(EXPECTED_HASHES)
    assert doc["unresolved_media"] == []

    hashes = []
    for row in doc["cases"]:
        locator = row["input_asset"]["reference_locators"][0]
        architecture_id = row["expected"]["architecture_id"]
        assert locator["source_file_sha256"] == EXPECTED_HASHES[architecture_id]
        assert row["input_asset"]["status"] == "byte_verified_pending_sanitization"
        assert locator["source_width"] > 0
        assert locator["source_height"] > 0
        hashes.append(locator["source_file_sha256"])

    assert len(hashes) == 3
    assert len(set(hashes)) == 3
    assert sum(
        snapshot["verified_cases"]
        for snapshot in doc["verification_snapshots"]
    ) == 3
    assert all(
        snapshot["error_cases"] == 0
        for snapshot in doc["verification_snapshots"]
    )
    assert all(
        snapshot["raw_media_committed"] is False
        for snapshot in doc["verification_snapshots"]
    )
