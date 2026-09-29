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

    assert result["status"] == "visual_sanitization_in_progress"
    assert summary["total_cases"] == 27
    assert summary["raw_model_input_allowed_cases"] == 4
    assert summary["blocked_model_input_cases"] == 23
    assert summary["status_counts"] == {
        "sanitization_required": 9,
        "approved_raw_model_input": 4,
        "blocked_pending_visual_sanitization_review": 14,
    }
    assert summary["risk_counts"] == {
        "high": 22,
        "medium_review_required": 5,
    }

    for row in result["queue"]:
        assert len(row["source"]["source_file_sha256"]) == 64
        assert row["source"]["verification_run_id"] == 36513502605
        if row["raw_model_input_allowed"]:
            assert row["status"] == "approved_raw_model_input"
            assert row["review"]["sanitized_asset_status"] == "approved"
            assert (
                row["review"]["sanitized_asset_sha256"]
                == row["source"]["source_file_sha256"]
            )
        else:
            assert row["status"] in {
                "sanitization_required",
                "blocked_pending_visual_sanitization_review",
            }


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
    assert sum(row["raw_model_input_allowed"] for row in bricklink) == 4
    assert next(
        row for row in bricklink
        if row["source_record_id"] == "hulk_lego_sh0037_standard"
    )["status"] == "sanitization_required"


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


def test_review_hash_change_invalidates_approval(tmp_path: Path) -> None:
    tool = load_tool()
    benchmark = json.loads(tool.DEFAULT_BENCHMARK.read_text(encoding="utf-8"))
    reviews = json.loads(tool.DEFAULT_REVIEWS.read_text(encoding="utf-8"))

    approved = next(
        row for row in reviews["reviews"]
        if row["status"] == "approved_raw"
    )
    approved["source_file_sha256"] = "0" * 64

    reviews_path = tmp_path / "reviews.json"
    reviews_path.write_text(json.dumps(reviews), encoding="utf-8")
    result = tool.build(tool.DEFAULT_BENCHMARK, reviews_path)
    row = next(
        item for item in result["queue"]
        if item["source_record_id"] == approved["source_record_id"]
    )

    assert row["status"] == "review_stale_source_hash_changed"
    assert row["raw_model_input_allowed"] is False
    assert row["review"]["review_stale"] is True
    assert row["review"]["sanitized_asset_status"] == "stale"
