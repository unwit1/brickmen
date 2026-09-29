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

    assert summary["total_cases"] == 27
    assert summary["ready_for_materialization_cases"] == 20
    assert summary["ready_for_image_url_resolution_cases"] == 7
    assert summary["blocked_cases"] == 0
    assert summary["action_status_counts"] == {
        "resolved_exact_image_url": 20,
        "ready_for_reviewed_page_media_resolution": 19,
        "blocked_on_direct_release_locator": 1,
            }


def test_gh0304_preserves_indirect_locator_but_is_visually_resolved() -> None:
    tool = load_tool()
    result = tool.build()
    row = next(
        item for item in result["queue"]
        if item["source_record_id"] == "hulk_g2_gh0304_avengers"
    )

    assert row["status"] == "ready_for_materialization"
    assert any(
        action["locator_quality"] == "indirect_identity_graph"
        and action["status"] == "blocked_on_direct_release_locator"
        for action in row["locator_actions"]
    )
    assert any(
        action["source_id"] == "kongbricks_g2_hulk_gh0304_media"
        and action["status"] == "resolved_exact_image_url"
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

    assert len(resolved) == 20
    assert len(unresolved) == 7
    assert all(row["status"] == "ready_for_materialization" for row in resolved)
    assert all(row["required_output"]["source_file_sha256"] is None for row in result["queue"])
    assert "Do not pass HTML catalog pages to the image materializer." in result["policy"]


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
