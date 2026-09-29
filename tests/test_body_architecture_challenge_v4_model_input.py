from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
QUEUE_TOOL = ROOT / "tools" / "knowledge" / "build_body_architecture_benchmark_sanitization_queue.py"
MANIFEST_TOOL = ROOT / "tools" / "knowledge" / "build_body_architecture_model_input_manifest.py"

CHALLENGE = DATA / "body-architecture-recognition-challenge-cases-v4.json"
REVIEWS = DATA / "body-architecture-recognition-challenge-sanitization-reviews-v4.json"
QUEUE = DATA / "body-architecture-recognition-challenge-sanitization-queue-v4.json"
CANDIDATES = DATA / "body-architecture-recognition-challenge-sanitization-candidates-v4.json"
MANIFEST = DATA / "body-architecture-recognition-challenge-model-input-manifest-v4.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_challenge_v4_is_fully_byte_verified() -> None:
    challenge = json.loads(CHALLENGE.read_text(encoding="utf-8"))
    assert challenge["status"] == "byte_verified_pending_sanitization"
    assert challenge["summary"]["total_cases"] == 23
    assert challenge["summary"]["byte_verified_cases"] == 23

    hashes = []
    for case in challenge["cases"]:
        locators = [
            locator
            for locator in case["input_asset"]["reference_locators"]
            if locator.get("source_file_sha256")
        ]
        assert locators
        hashes.append(locators[0]["source_file_sha256"])

    assert len(hashes) == 23
    assert len(set(hashes)) == 23
    assert "2385f7c7627bb1b5b7412f107d6a2b15ec727e1a13bef8b920809d3504e7a737" in hashes


def test_challenge_v4_sanitization_queue_is_fully_raw_approved() -> None:
    tool = load_module(QUEUE_TOOL, "build_body_architecture_benchmark_sanitization_queue_v4")
    result = tool.build(CHALLENGE, REVIEWS)

    assert result["summary"] == {
        "total_cases": 23,
        "raw_model_input_allowed_cases": 23,
        "blocked_model_input_cases": 0,
        "status_counts": {
            "approved_raw_model_input": 23,
        },
        "risk_counts": {
            "medium_review_required": 22,
            "unknown_review_required": 1,
        },
    }

    assert all(row["raw_model_input_allowed"] for row in result["queue"])


def test_checked_in_challenge_v4_queue_matches_generic_builder() -> None:
    tool = load_module(QUEUE_TOOL, "build_body_architecture_benchmark_sanitization_queue_v4_drift")
    expected = tool.build(CHALLENGE, REVIEWS)
    actual = json.loads(QUEUE.read_text(encoding="utf-8"))
    assert actual == expected


def test_challenge_v4_model_input_manifest_is_fully_runnable() -> None:
    tool = load_module(MANIFEST_TOOL, "build_body_architecture_model_input_manifest_v4")
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    result = tool.build(queue, candidates)

    assert result["summary"] == {
        "total_cases": 23,
        "model_input_allowed_cases": 23,
        "approved_raw_cases": 23,
        "approved_sanitized_cases": 0,
        "blocked_cases": 0,
    }
    assert all(row["split"] == "challenge_test" for row in result["entries"])

    assert all(row["model_input_allowed"] for row in result["entries"])


def test_checked_in_challenge_v4_model_input_matches_generic_builder() -> None:
    tool = load_module(MANIFEST_TOOL, "build_body_architecture_model_input_manifest_v4_drift")
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    expected = tool.build(queue, candidates)
    actual = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert actual == expected
