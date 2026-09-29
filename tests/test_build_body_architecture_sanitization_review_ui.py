from __future__ import annotations

import importlib.util
import json
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "build_body_architecture_sanitization_review_ui.py"
)
DATA = (
    Path(__file__).resolve().parents[1]
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_body_architecture_sanitization_review_ui",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_live_payload_contains_only_generated_candidates() -> None:
    tool = load_tool()
    candidates = json.loads(
        (
            DATA
            / "body-architecture-benchmark-sanitization-candidates.json"
        ).read_text(encoding="utf-8")
    )
    queue = json.loads(
        (
            DATA
            / "body-architecture-benchmark-sanitization-queue.json"
        ).read_text(encoding="utf-8")
    )

    payload = tool.build_payload(candidates, queue)

    assert payload["candidate_count"] == 13
    assert len(payload["items"]) == 13
    assert {
        row["source_record_id"] for row in payload["items"]
    }.isdisjoint(
        {
            row["source_record_id"]
            for row in candidates["blockers"]
        }
    )
    tool.validate_payload(payload)


def test_expected_filename_is_hash_bound() -> None:
    tool = load_tool()
    candidates = {
        "records": [
            {
                "source_record_id": "test",
                "case_id": "archrec::test",
                "split": "test",
                "source_id": "source-test",
                "source_file_sha256": "a" * 64,
                "source_dimensions": [100, 200],
                "output_dimensions": [80, 160],
                "sanitized_pixel_sha256": "b" * 64,
                "sanitized_png_sha256": "c" * 64,
                "operations": [],
            }
        ]
    }
    queue = {
        "queue": [
            {
                "source_record_id": "test",
                "status": "sanitization_required",
                "source": {
                    "exact_image_url": "https://example.test/source.png",
                    "source_file_sha256": "a" * 64,
                },
                "review": {
                    "visible_text_leakage": [],
                    "visual_confounders": [],
                    "sanitization_action": "tight_figure_crop",
                    "notes": [],
                },
            }
        ]
    }

    payload = tool.build_payload(candidates, queue)
    item = payload["items"][0]

    assert item["expected_derivative_filename"] == (
        "test--bbbbbbbbbbbbbbbb.png"
    )


def test_payload_rejects_stale_source_hash() -> None:
    tool = load_tool()
    candidates = {
        "records": [
            {
                "source_record_id": "test",
                "source_file_sha256": "a" * 64,
                "sanitized_pixel_sha256": "b" * 64,
                "sanitized_png_sha256": "c" * 64,
                "operations": [],
            }
        ]
    }
    queue = {
        "queue": [
            {
                "source_record_id": "test",
                "status": "sanitization_required",
                "source": {
                    "exact_image_url": "https://example.test/source.png",
                    "source_file_sha256": "d" * 64,
                },
                "review": {},
            }
        ]
    }

    try:
        tool.build_payload(candidates, queue)
    except ValueError as exc:
        assert "source hash mismatch" in str(exc)
    else:
        raise AssertionError("expected stale candidate source hash to fail")


def test_html_does_not_embed_derivative_image_bytes() -> None:
    tool = load_tool()
    payload = {
        "schema": "body-architecture-sanitization-review-ui-payload/v1",
        "processor_version": tool.VERSION,
        "candidate_count": 1,
        "items": [
            {
                "source_record_id": "test",
                "source_url": "https://example.test/source.png",
                "source_file_sha256": "a" * 64,
                "sanitized_pixel_sha256": "b" * 64,
                "sanitized_png_sha256": "c" * 64,
                "expected_derivative_filename": "test--bbbbbbbbbbbbbbbb.png",
                "operations": [],
                "review_context": {},
            }
        ],
        "policy": [],
    }

    output = tool.build_review_html(payload)

    assert "data:image/png;base64" not in output
    assert 'type="file"' in output
    assert "crypto.subtle.digest" in output
    assert "Exact derivative hash must be verified first." in output
    assert "body-architecture-sanitized-asset-review/v1" in output
