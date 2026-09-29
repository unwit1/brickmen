from __future__ import annotations

import importlib.util
import json
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "build_body_architecture_reference_acquisition_queue.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_body_architecture_reference_acquisition_queue",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_acquisition_queue_baseline() -> None:
    tool = load_tool()
    result = tool.build()
    summary = result["summary"]

    assert result["status"] == "reference_media_verified_materialization_pending"
    assert summary["total_cases"] == 27
    assert summary["byte_verified_cases"] == 27
    assert summary["ready_for_materialization_cases"] == 27
    assert summary["ready_for_image_url_resolution_cases"] == 0
    assert summary["blocked_cases"] == 0
    assert summary["action_status_counts"] == {
        "byte_verified": 27,
        "ready_for_reviewed_page_media_resolution": 12,
        "blocked_on_direct_release_locator": 1,
    }


def test_gh0304_preserves_indirect_locator_but_is_visually_resolved() -> None:
    tool = load_tool()
    result = tool.build()
    row = next(
        item for item in result["queue"]
        if item["source_record_id"] == "hulk_g2_gh0304_avengers"
    )

    assert row["status"] == "byte_verified_materialization_pending"
    assert any(
        action["locator_quality"] == "indirect_identity_graph"
        and action["status"] == "blocked_on_direct_release_locator"
        for action in row["locator_actions"]
    )
    assert any(
        action["source_id"] == "kongbricks_g2_hulk_gh0304_media"
        and action["status"] == "byte_verified"
        for action in row["locator_actions"]
    )


def test_queue_does_not_treat_page_urls_as_materialized_images() -> None:
    tool = load_tool()
    result = tool.build()

    resolved = [
        row for row in result["queue"]
        if row["required_output"]["exact_image_url"]
    ]
    unresolved = [
        row for row in result["queue"]
        if not row["required_output"]["exact_image_url"]
    ]

    assert len(resolved) == 27
    assert len(unresolved) == 0
    assert all(
        row["status"] == "byte_verified_materialization_pending"
        for row in resolved
    )
    assert all(
        len(row["required_output"]["source_file_sha256"]) == 64
        for row in result["queue"]
    )
    assert all(
        row["required_output"]["source_size_bytes"] > 0
        for row in result["queue"]
    )
    assert "Do not pass HTML catalog pages to the image materializer." in result["policy"]
    assert "Verified hashes and metadata may be stored in Git; raw reference image bytes must not be committed." in result["policy"]


def test_checked_in_queue_matches_generator() -> None:
    tool = load_tool()
    expected = tool.build()
    queue_path = (
        Path(__file__).resolve().parents[1]
        / "knowledge"
        / "libraries"
        / "lego-minifigure-customs"
        / "data"
        / "body-architecture-reference-acquisition-queue.json"
    )
    actual = json.loads(queue_path.read_text(encoding="utf-8"))

    assert actual == expected
