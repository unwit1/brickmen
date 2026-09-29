from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
PLAN = DATA / "body-architecture-custom-acquisition-candidates-v1.json"


def test_custom_acquisition_plan_preserves_media_quality_gate() -> None:
    doc = json.loads(PLAN.read_text(encoding="utf-8"))

    assert doc["status"] == "mixed_exact_url_pending_byte_verification_and_media_resolution"
    assert {
        row["expected"]["architecture_id"]
        for row in doc["cases"]
    } == {
        "custom_midfig_balljoint_upper",
        "custom_standard_four_arm_single_torso",
    }

    for row in doc["cases"]:
        locator = row["input_asset"]["reference_locators"][0]
        assert locator["exact_image_url"].startswith("https://titanicbricks.com/")
        assert locator["source_file_sha256"] is None
        assert row["input_asset"]["status"] == "exact_url_pending_byte_verification"

    assert doc["unresolved_media"] == [
        {
            "architecture_id": "custom_sidan_full_balljoint_poseable",
            "source_id": "minifigworld_sidan_poseable_product",
            "source_page_url": "https://minifigworld.com/si-dan-toys-poseable-minifig/",
            "status": "high_resolution_exact_media_unresolved",
            "reason": doc["unresolved_media"][0]["reason"],
            "observed_thumbnail_example": doc["unresolved_media"][0]["observed_thumbnail_example"],
        }
    ]
    assert ".50.50.jpg" in doc["unresolved_media"][0]["observed_thumbnail_example"]
