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

CHALLENGE = DATA / "body-architecture-recognition-challenge-cases-v3.json"
REVIEWS = DATA / "body-architecture-recognition-challenge-sanitization-reviews-v3.json"
QUEUE = DATA / "body-architecture-recognition-challenge-sanitization-queue-v3.json"
CANDIDATES = DATA / "body-architecture-recognition-challenge-sanitization-candidates-v3.json"
MANIFEST = DATA / "body-architecture-recognition-challenge-model-input-manifest-v3.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_challenge_v3_is_fully_byte_verified() -> None:
    challenge = json.loads(CHALLENGE.read_text(encoding="utf-8"))

    assert challenge["status"] == "byte_verified_pending_sanitization"
    assert challenge["summary"]["total_cases"] == 22
    assert challenge["summary"]["byte_verified_cases"] == 22

    hashes = []
    for case in challenge["cases"]:
        locators = [
            locator
            for locator in case["input_asset"]["reference_locators"]
            if locator.get("source_file_sha256")
        ]
        assert locators
        hashes.append(locators[0]["source_file_sha256"])

    assert len(hashes) == 22
    assert len(set(hashes)) == 22


def test_challenge_v3_sanitization_queue_has_one_explicit_raw_review_blocker() -> None:
    tool = load_module(
        QUEUE_TOOL,
        "build_body_architecture_benchmark_sanitization_queue_v3",
    )
    result = tool.build(CHALLENGE, REVIEWS)

    assert result["summary"] == {
        "total_cases": 22,
        "raw_model_input_allowed_cases": 21,
        "blocked_model_input_cases": 1,
        "status_counts": {
            "approved_raw_model_input": 21,
            "blocked_pending_visual_sanitization_review": 1,
        },
        "risk_counts": {"medium_review_required": 22},
    }

    blocked = [
        row
        for row in result["queue"]
        if not row["raw_model_input_allowed"]
    ]
    assert [row["source_record_id"] for row in blocked] == [
        "challenge_woody_toy003_long_limb"
    ]
    assert blocked[0]["status"] == "blocked_pending_visual_sanitization_review"


def test_checked_in_challenge_v3_queue_matches_generic_builder() -> None:
    tool = load_module(
        QUEUE_TOOL,
        "build_body_architecture_benchmark_sanitization_queue_v3_drift",
    )
    expected = tool.build(CHALLENGE, REVIEWS)
    actual = json.loads(QUEUE.read_text(encoding="utf-8"))

    assert actual == expected


def test_challenge_v3_model_input_manifest_is_partially_runnable() -> None:
    tool = load_module(
        MANIFEST_TOOL,
        "build_body_architecture_model_input_manifest_v3",
    )
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    result = tool.build(queue, candidates)

    assert result["summary"] == {
        "total_cases": 22,
        "model_input_allowed_cases": 21,
        "approved_raw_cases": 21,
        "approved_sanitized_cases": 0,
        "blocked_cases": 1,
    }
    assert all(row["split"] == "challenge_test" for row in result["entries"])

    blocked = [
        row
        for row in result["entries"]
        if not row["model_input_allowed"]
    ]
    assert blocked == [
        {
            "source_record_id": "challenge_woody_toy003_long_limb",
            "case_id": "archchallenge::challenge_woody_toy003_long_limb",
            "split": "challenge_test",
            "scoring_track": "core",
            "status": "blocked",
            "model_input_allowed": False,
            "asset_kind": None,
            "asset_sha256": None,
            "source_file_sha256": "777fd93e31997b912debb734bf0be461c6795210649370bd6be92717f948e7c9",
            "expected_local_asset": None,
            "approval_review_ids": [],
            "blocked_reason": "pending_visual_sanitization_review",
        }
    ]


def test_checked_in_challenge_v3_model_input_matches_generic_builder() -> None:
    tool = load_module(
        MANIFEST_TOOL,
        "build_body_architecture_model_input_manifest_v3_drift",
    )
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    expected = tool.build(queue, candidates)
    actual = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert actual == expected
