from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
)
QUEUE = DATA / "body-architecture-benchmark-sanitization-queue.json"
TRANSFORMS = DATA / "body-architecture-benchmark-sanitization-transforms.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_every_sanitization_required_case_has_explicit_plan() -> None:
    queue = load(QUEUE)
    transforms = load(TRANSFORMS)

    required = {
        row["source_record_id"]: row
        for row in queue["queue"]
        if row["status"] == "sanitization_required"
    }
    planned = {
        row["source_record_id"]: row
        for row in transforms["transforms"]
    }

    assert set(required) == set(planned)
    assert len(required) == 23

    for record_id, plan in planned.items():
        source = required[record_id]["source"]
        assert plan["source_file_sha256"] == source["source_file_sha256"]
        assert plan["source_dimensions"] == [
            source["source_width"],
            source["source_height"],
        ]
        assert plan["status"] in {
            "candidate_transform",
            "requires_segmentation",
        }

        if plan["status"] == "candidate_transform":
            assert plan["operations"]
        else:
            assert plan["operations"] == []
            assert plan["rationale"]


def test_clean_raw_cases_do_not_need_derivative_plans() -> None:
    queue = load(QUEUE)
    transforms = load(TRANSFORMS)
    planned = {
        row["source_record_id"]
        for row in transforms["transforms"]
    }
    approved_raw = {
        row["source_record_id"]
        for row in queue["queue"]
        if row["status"] == "approved_raw_model_input"
    }

    assert len(approved_raw) == 4
    assert approved_raw.isdisjoint(planned)


def test_transform_plan_has_expected_candidate_blocker_split() -> None:
    transforms = load(TRANSFORMS)
    status_counts: dict[str, int] = {}
    for row in transforms["transforms"]:
        status = row["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    assert status_counts == {
        "candidate_transform": 13,
        "requires_segmentation": 10,
    }


def test_candidate_manifest_retains_source_and_transform_provenance() -> None:
    queue = load(QUEUE)
    transforms = load(TRANSFORMS)
    candidates = load(
        DATA / "body-architecture-benchmark-sanitization-candidates.json"
    )

    queue_by_id = {
        row["source_record_id"]: row
        for row in queue["queue"]
    }
    transform_by_id = {
        row["source_record_id"]: row
        for row in transforms["transforms"]
    }

    assert len(candidates["records"]) == 13
    for candidate in candidates["records"]:
        record_id = candidate["source_record_id"]
        source = queue_by_id[record_id]["source"]
        transform = transform_by_id[record_id]
        assert candidate["source_file_sha256"] == source["source_file_sha256"]
        assert candidate["source_dimensions"] == [
            source["source_width"],
            source["source_height"],
        ]
        assert candidate["operations"] == transform["operations"]
        assert candidate["transform_status"] == "candidate_transform"
        assert candidate["model_input_allowed"] is False


def test_candidate_hash_fields_are_sha256() -> None:
    candidates = load(
        DATA / "body-architecture-benchmark-sanitization-candidates.json"
    )

    for candidate in candidates["records"]:
        for key in (
            "source_file_sha256",
            "sanitized_pixel_sha256",
            "sanitized_png_sha256",
        ):
            value = candidate[key]
            assert len(value) == 64
            assert all(ch in "0123456789abcdef" for ch in value)
