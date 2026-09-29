from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = (
    ROOT
    / "tools"
    / "knowledge"
    / "build_body_architecture_model_input_manifest.py"
)
DATA = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
)
QUEUE = (
    DATA
    / "body-architecture-recognition-challenge-sanitization-queue-v1.json"
)
CANDIDATES = (
    DATA
    / "body-architecture-recognition-challenge-sanitization-candidates-v1.json"
)
MANIFEST = (
    DATA
    / "body-architecture-recognition-challenge-model-input-manifest-v1.json"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_body_architecture_model_input_manifest",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_inputs() -> tuple[dict, dict]:
    return (
        json.loads(QUEUE.read_text(encoding="utf-8")),
        json.loads(CANDIDATES.read_text(encoding="utf-8")),
    )


def test_challenge_model_input_gate_allows_seven_clean_raw_cases() -> None:
    tool = load_tool()
    queue, candidates = live_inputs()

    result = tool.build(queue, candidates)

    assert result["summary"] == {
        "total_cases": 8,
        "model_input_allowed_cases": 7,
        "approved_raw_cases": 7,
        "approved_sanitized_cases": 0,
        "blocked_cases": 1,
    }
    assert all(
        row["split"] == "challenge_test"
        for row in result["entries"]
    )


def test_centaur_remains_fail_closed_until_sanitized() -> None:
    tool = load_tool()
    queue, candidates = live_inputs()
    result = tool.build(queue, candidates)

    row = next(
        entry
        for entry in result["entries"]
        if entry["source_record_id"] == "challenge_centaur_col379"
    )
    assert row["model_input_allowed"] is False
    assert row["status"] == "blocked"
    assert row["blocked_reason"] == (
        "requires_segmentation_or_manual_cleanup"
    )
    assert row["source_file_sha256"] == (
        "9c6ab60d4b94f6f8544625eac122865b248bd05661cf94a93fd7e7e0085f73c5"
    )


def test_checked_in_challenge_model_input_manifest_matches_generic_builder() -> None:
    tool = load_tool()
    queue, candidates = live_inputs()
    expected = tool.build(queue, candidates)
    actual = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert actual == expected
