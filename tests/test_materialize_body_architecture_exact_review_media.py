from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "materialize_body_architecture_exact_review_media.py"
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
CHALLENGE = DATA / "body-architecture-recognition-challenge-cases-v4.json"


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "materialize_body_architecture_exact_review_media",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_review_selection_is_explicit_and_hash_pinned() -> None:
    tool = load_tool()
    selected = tool.load_selected(
        CHALLENGE,
        {
            "challenge_homemaker_276_nurse",
            "challenge_woody_toy003_long_limb",
        },
    )
    assert {row["source_record_id"] for row in selected} == {
        "challenge_homemaker_276_nurse",
        "challenge_woody_toy003_long_limb",
    }
    for row in selected:
        locator = row["source"]
        assert locator["exact_image_url"].startswith("https://")
        assert len(locator["source_file_sha256"]) == 64
        assert locator["source_width"] > 0
        assert locator["source_height"] > 0


def test_unknown_review_record_is_rejected() -> None:
    tool = load_tool()
    with pytest.raises(ValueError, match="unknown source_record_id"):
        tool.load_selected(CHALLENGE, {"does_not_exist"})
