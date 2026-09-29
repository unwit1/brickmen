from __future__ import annotations

import importlib.util
import json
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "build_body_architecture_benchmark_sanitization_queue.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_body_architecture_benchmark_sanitization_queue",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sanitization_queue_blocks_all_raw_model_inputs() -> None:
    tool = load_tool()
    result = tool.build()
    summary = result["summary"]

    assert result["status"] == "visual_sanitization_review_required"
    assert summary["total_cases"] == 27
    assert summary["raw_model_input_allowed_cases"] == 0
    assert summary["blocked_pending_visual_sanitization_review"] == 27
    assert summary["risk_counts"] == {
        "high": 22,
        "medium_review_required": 5,
    }

    for row in result["queue"]:
        assert row["raw_model_input_allowed"] is False
        assert row["status"] == "blocked_pending_visual_sanitization_review"
        assert row["review"]["sanitized_asset_status"] == "pending"
        assert len(row["source"]["source_file_sha256"]) == 64
        assert row["source"]["verification_run_id"] == 36513502605


def test_custom_product_media_is_high_leakage_risk() -> None:
    tool = load_tool()
    result = tool.build()
    by_record = {
        row["source_record_id"]: row
        for row in result["queue"]
    }

    assert by_record["hulk_bigguy_ragnarok"]["source_risk"] == "high"
    assert by_record["hulk_g2_gh0304_avengers"]["source_risk"] == "high"
    assert by_record["venom_xinh_xh1911_bigfig"]["source_risk"] == "high"
    assert by_record["thing_g2_gh0435_bigfig"]["source_risk"] == "high"


def test_bricklink_catalog_images_still_require_review() -> None:
    tool = load_tool()
    result = tool.build()
    bricklink = [
        row for row in result["queue"]
        if row["source"]["exact_image_url"].startswith(
            "https://img.bricklink.com/"
        )
    ]

    assert len(bricklink) == 5
    assert all(
        row["source_risk"] == "medium_review_required"
        for row in bricklink
    )
    assert all(row["raw_model_input_allowed"] is False for row in bricklink)


def test_verified_locator_is_required() -> None:
    tool = load_tool()
    case = {
        "source_record_id": "broken",
        "input_asset": {
            "reference_locators": [
                {
                    "source_id": "page-only",
                    "exact_image_url": "https://example.test/image.png",
                    "source_file_sha256": None,
                }
            ]
        },
    }

    try:
        tool.select_verified_locator(case)
    except ValueError as exc:
        assert "no byte-verified exact image" in str(exc)
    else:
        raise AssertionError("expected missing byte verification to fail")


def test_checked_in_sanitization_queue_matches_generator() -> None:
    tool = load_tool()
    expected = tool.build()
    path = (
        Path(__file__).resolve().parents[1]
        / "knowledge"
        / "libraries"
        / "lego-minifigure-customs"
        / "data"
        / "body-architecture-benchmark-sanitization-queue.json"
    )
    actual = json.loads(path.read_text(encoding="utf-8"))

    assert actual == expected
