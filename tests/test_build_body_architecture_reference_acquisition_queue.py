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
    assert summary["ready_for_materialization_cases"] == 4
    assert summary["ready_for_image_url_resolution_cases"] == 22
    assert summary["blocked_cases"] == 1
    assert summary["action_status_counts"] == {
        "resolved_exact_image_url": 4,
        "ready_for_reviewed_page_media_resolution": 21,
        "blocked_on_direct_release_locator": 1,
        "ready_for_catalog_image_resolution": 1,
    }


def test_only_gh0304_is_indirectly_blocked() -> None:
    tool = load_tool()
    result = tool.build()
    blocked = [row for row in result["queue"] if row["status"].startswith("blocked")]

    assert len(blocked) == 1
    assert blocked[0]["source_record_id"] == "hulk_g2_gh0304_avengers"
    assert blocked[0]["locator_actions"][0]["locator_quality"] == "indirect_identity_graph"


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

    assert len(resolved) == 4
    assert len(unresolved) == 23
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
