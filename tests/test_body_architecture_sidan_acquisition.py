from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
CANDIDATE = DATA / "body-architecture-sidan-acquisition-candidate-v1.json"


def test_sidan_candidate_uses_discovered_zoom_asset_not_thumbnail() -> None:
    doc = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    assert doc["status"] == "exact_url_pending_byte_verification"
    assert len(doc["cases"]) == 1
    row = doc["cases"][0]
    assert row["expected"]["architecture_id"] == "custom_sidan_full_balljoint_poseable"
    locator = row["input_asset"]["reference_locators"][0]
    assert ".500.500.jpg" in locator["exact_image_url"]
    assert ".50.50.jpg" not in locator["exact_image_url"]
    assert locator["source_file_sha256"] is None
    assert locator["image_resolution_status"] == (
        "exact_image_url_discovered_in_product_html_pending_byte_verification"
    )
