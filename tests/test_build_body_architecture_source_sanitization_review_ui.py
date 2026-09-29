from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = (
    ROOT
    / "tools"
    / "knowledge"
    / "build_body_architecture_source_sanitization_review_ui.py"
)
DATA = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_body_architecture_source_sanitization_review_ui",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_challenge_payload_is_hash_pinned_and_complete() -> None:
    tool = load_tool()
    queue = json.loads(
        (
            DATA
            / "body-architecture-recognition-challenge-sanitization-queue-v1.json"
        ).read_text(encoding="utf-8")
    )
    payload = tool.build_payload(queue)

    assert payload["candidate_count"] == 8
    assert len(payload["items"]) == 8
    assert len(
        {row["source_file_sha256"] for row in payload["items"]}
    ) == 8
    assert all(
        row["exact_image_url"].startswith("https://")
        for row in payload["items"]
    )


def test_canonical_payload_covers_all_source_review_cases() -> None:
    tool = load_tool()
    queue = json.loads(
        (
            DATA / "body-architecture-benchmark-sanitization-queue.json"
        ).read_text(encoding="utf-8")
    )
    payload = tool.build_payload(queue)

    assert payload["candidate_count"] == 27


def test_payload_rejects_unverified_source_hash() -> None:
    tool = load_tool()
    queue = {
        "queue": [
            {
                "source_record_id": "test",
                "case_id": "arch::test",
                "source": {
                    "source_id": "source-test",
                    "exact_image_url": "https://example.test/image.png",
                    "source_file_sha256": None,
                },
            }
        ]
    }

    try:
        tool.build_payload(queue)
    except ValueError as exc:
        assert "source SHA-256 is required" in str(exc)
    else:
        raise AssertionError("expected missing source hash to fail")


def test_html_is_metadata_only_and_fail_closed() -> None:
    tool = load_tool()
    payload = {
        "schema": "body-architecture-source-sanitization-review-ui-payload/v1",
        "processor_version": tool.VERSION,
        "queue_status": "visual_sanitization_in_progress",
        "candidate_count": 1,
        "items": [
            {
                "source_record_id": "test",
                "source_id": "source-test",
                "exact_image_url": "https://example.test/image.png",
                "source_file_sha256": "a" * 64,
                "source_width": 100,
                "source_height": 200,
                "case_id": "arch::test",
                "split": "test",
                "expected": {"architecture_id": "test_arch"},
                "source_risk": "medium_review_required",
                "risk_reasons": [],
                "required_checks": [],
                "recommended_actions": [],
            }
        ],
        "policy": [],
    }

    output = tool.build_review_html(payload)

    assert "data:image" not in output
    assert "source_file_sha256" in output
    assert "Raw approval checks not satisfied." in output
    assert "sanitization_required" in output
    assert "body-architecture-source-sanitization-review-set/v1" in output
