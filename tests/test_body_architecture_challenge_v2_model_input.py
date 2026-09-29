from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
QUEUE_TOOL = (
    ROOT
    / "tools"
    / "knowledge"
    / "build_body_architecture_benchmark_sanitization_queue.py"
)
MANIFEST_TOOL = (
    ROOT
    / "tools"
    / "knowledge"
    / "build_body_architecture_model_input_manifest.py"
)

CHALLENGE = DATA / "body-architecture-recognition-challenge-cases-v2.json"
REVIEWS = DATA / "body-architecture-recognition-challenge-sanitization-reviews-v2.json"
QUEUE = DATA / "body-architecture-recognition-challenge-sanitization-queue-v2.json"
CANDIDATES = DATA / "body-architecture-recognition-challenge-sanitization-candidates-v2.json"
MANIFEST = DATA / "body-architecture-recognition-challenge-model-input-manifest-v2.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_challenge_v2_sanitization_queue_is_fully_raw_approved() -> None:
    tool = load_module(
        QUEUE_TOOL,
        "build_body_architecture_benchmark_sanitization_queue_v2",
    )
    result = tool.build(CHALLENGE, REVIEWS)

    assert result["summary"] == {
        "total_cases": 16,
        "raw_model_input_allowed_cases": 16,
        "blocked_model_input_cases": 0,
        "status_counts": {"approved_raw_model_input": 16},
        "risk_counts": {"medium_review_required": 16},
    }
    assert all(row["raw_model_input_allowed"] is True for row in result["queue"])
    assert all(row["review"]["review_stale"] is False for row in result["queue"])
    assert len(
        {
            row["source"]["source_file_sha256"]
            for row in result["queue"]
        }
    ) == 16


def test_checked_in_challenge_v2_queue_matches_generic_builder() -> None:
    tool = load_module(
        QUEUE_TOOL,
        "build_body_architecture_benchmark_sanitization_queue_v2_drift",
    )
    expected = tool.build(CHALLENGE, REVIEWS)
    actual = json.loads(QUEUE.read_text(encoding="utf-8"))

    assert actual == expected


def test_challenge_v2_model_input_manifest_is_fully_runnable() -> None:
    tool = load_module(
        MANIFEST_TOOL,
        "build_body_architecture_model_input_manifest_v2",
    )
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    result = tool.build(queue, candidates)

    assert result["summary"] == {
        "total_cases": 16,
        "model_input_allowed_cases": 16,
        "approved_raw_cases": 16,
        "approved_sanitized_cases": 0,
        "blocked_cases": 0,
    }
    assert all(row["split"] == "challenge_test" for row in result["entries"])
    assert all(row["model_input_allowed"] is True for row in result["entries"])
    assert all(row["asset_kind"] == "verified_raw_reference" for row in result["entries"])


def test_checked_in_challenge_v2_model_input_matches_generic_builder() -> None:
    tool = load_module(
        MANIFEST_TOOL,
        "build_body_architecture_model_input_manifest_v2_drift",
    )
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    expected = tool.build(queue, candidates)
    actual = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert actual == expected
