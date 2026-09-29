from __future__ import annotations

import importlib.util
import json
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "prepare_body_architecture_sanitization_review.py"
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
        "prepare_body_architecture_sanitization_review",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_candidate_metadata_is_self_consistent() -> None:
    tool = load_tool()
    canonical = json.loads(
        (
            DATA
            / "body-architecture-benchmark-sanitization-candidates.json"
        ).read_text(encoding="utf-8")
    )

    synthetic_generated = {
        "records": [
            {
                **row,
                "candidate_status": "generated_pending_visual_review",
                "model_input_allowed": False,
            }
            for row in canonical["records"]
        ],
        "blockers": canonical["blockers"],
        "errors": 0,
    }

    result = tool.verify_generated_against_canonical(
        synthetic_generated,
        canonical,
    )
    assert result == {
        "verified_candidates": 15,
        "verified_blockers": 8,
        "candidate_hash_drift": 0,
    }


def test_candidate_hash_drift_fails_closed() -> None:
    tool = load_tool()
    canonical = {
        "records": [
            {
                "source_record_id": "test",
                "source_file_sha256": "a" * 64,
                "source_dimensions": [100, 100],
                "operations": [],
                "output_dimensions": [90, 90],
                "sanitized_pixel_sha256": "b" * 64,
                "sanitized_png_sha256": "c" * 64,
            }
        ],
        "blockers": [],
    }
    generated = json.loads(json.dumps(canonical))
    generated["records"][0]["sanitized_png_sha256"] = "d" * 64
    generated["errors"] = 0

    try:
        tool.verify_generated_against_canonical(generated, canonical)
    except ValueError as exc:
        assert "candidate drift" in str(exc)
    else:
        raise AssertionError("expected derivative hash drift to fail")


def test_candidate_error_fails_closed() -> None:
    tool = load_tool()
    canonical = {"records": [], "blockers": []}
    generated = {
        "records": [],
        "blockers": [],
        "errors": 1,
    }

    try:
        tool.verify_generated_against_canonical(generated, canonical)
    except ValueError as exc:
        assert "candidate errors" in str(exc)
    else:
        raise AssertionError("expected candidate generation errors to fail")


def test_default_reviewed_hosts_match_canonical_source_families() -> None:
    tool = load_tool()

    assert tool.REVIEWED_HOSTS == {
        "img.bricklink.com",
        "kongbricks.com",
        "kongbricks.myshopify.com",
        "cdn.shopify.com",
        "static.herobloks.com",
    }
