from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
QUEUE_TOOL = ROOT / "tools" / "knowledge" / "build_body_architecture_benchmark_sanitization_queue.py"
MANIFEST_TOOL = ROOT / "tools" / "knowledge" / "build_body_architecture_model_input_manifest.py"
VALIDATOR = ROOT / "tools" / "knowledge" / "validate_body_architecture_sanitized_asset_reviews.py"

BENCHMARK = DATA / "body-architecture-custom-acquisition-candidates-v1.json"
SOURCE_REVIEWS = DATA / "body-architecture-custom-sanitization-reviews-v1.json"
QUEUE = DATA / "body-architecture-custom-sanitization-queue-v1.json"
CANDIDATES = DATA / "body-architecture-custom-sanitization-candidates-v1.json"
SANITIZED_REVIEWS = DATA / "body-architecture-custom-sanitized-asset-reviews-v1.jsonl"
MANIFEST = DATA / "body-architecture-custom-model-input-manifest-v1.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_jsonl(path: Path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_custom_source_queue_matches_generic_builder() -> None:
    tool = load_module(QUEUE_TOOL, "custom_queue")
    expected = tool.build(BENCHMARK, SOURCE_REVIEWS)
    actual = json.loads(QUEUE.read_text(encoding="utf-8"))
    assert actual == expected
    assert actual["created"] == "2026-09-28"
    assert actual["summary"] == {
        "total_cases": 3,
        "raw_model_input_allowed_cases": 2,
        "blocked_model_input_cases": 1,
        "status_counts": {
            "sanitization_required": 1,
            "approved_raw_model_input": 2,
        },
        "risk_counts": {"unknown_review_required": 3},
    }


def test_midfig_sanitized_review_is_exact_and_valid() -> None:
    validator = load_module(VALIDATOR, "custom_validator")
    candidates = validator.load_candidates(CANDIDATES)
    reviews = read_jsonl(SANITIZED_REVIEWS)
    assert len(reviews) == 1
    assert validator.validate_record(reviews[0], candidates) == []
    assert reviews[0]["review_id"] == validator.review_id(reviews[0])
    assert reviews[0]["decision"] == "approved"
    assert all(reviews[0]["checks"].values())


def test_custom_model_input_manifest_is_fully_runnable() -> None:
    tool = load_module(MANIFEST_TOOL, "custom_manifest")
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    reviews = read_jsonl(SANITIZED_REVIEWS)
    expected = tool.build(queue, candidates, reviews)
    actual = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert actual == expected
    assert actual["summary"] == {
        "total_cases": 3,
        "model_input_allowed_cases": 3,
        "approved_raw_cases": 2,
        "approved_sanitized_cases": 1,
        "blocked_cases": 0,
    }
    assert {
        row["source_record_id"]: row["status"]
        for row in actual["entries"]
    } == {
        "custom_midfig_balljoint_upper_titanic": "approved_sanitized",
        "custom_sidan_full_balljoint_poseable_sidan": "approved_raw",
        "custom_standard_four_arm_single_torso_titanic": "approved_raw",
    }
