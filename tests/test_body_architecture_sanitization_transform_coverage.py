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
        "candidate_transform": 15,
        "requires_segmentation": 8,
    }
