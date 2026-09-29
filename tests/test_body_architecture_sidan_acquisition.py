from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
CANDIDATE = DATA / "body-architecture-sidan-acquisition-candidate-v1.json"


def test_sidan_candidate_is_byte_verified_zoom_asset() -> None:
    doc = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    assert doc["status"] == "byte_verified_pending_sanitization"
    assert len(doc["cases"]) == 1
    row = doc["cases"][0]
    assert row["expected"]["architecture_id"] == "custom_sidan_full_balljoint_poseable"
    locator = row["input_asset"]["reference_locators"][0]
    assert ".500.500.jpg" in locator["exact_image_url"]
    assert ".50.50.jpg" not in locator["exact_image_url"]
    assert locator["source_file_sha256"] == (
        "2ac7f9ba8793107e58892205ea56cc772b876cd63cd2fda08e51e1a0ec8e831e"
    )
    assert (locator["source_width"], locator["source_height"]) == (301, 500)
    assert locator["verification_run_id"] == 36634149308
    assert locator["verification_artifact_id"] == 11062873338
    assert row["input_asset"]["status"] == "byte_verified_pending_sanitization"
    assert doc["verification_snapshot"]["verified_cases"] == 1
    assert doc["verification_snapshot"]["error_cases"] == 0
    assert doc["verification_snapshot"]["raw_media_committed"] is False
