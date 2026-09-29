from __future__ import annotations

import importlib.util
import json
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "generate_body_architecture_sam2_candidates.py"
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
        "generate_body_architecture_sam2_candidates",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_segmentation_prompts_cover_exactly_current_blockers() -> None:
    prompts = json.loads(
        (
            DATA
            / "body-architecture-benchmark-segmentation-prompts.json"
        ).read_text(encoding="utf-8")
    )
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

    prompt_by_id = {
        row["source_record_id"]: row
        for row in prompts["prompts"]
    }
    blocker_ids = {
        row["source_record_id"]
        for row in candidates["blockers"]
    }
    queue_by_id = {
        row["source_record_id"]: row
        for row in queue["queue"]
    }

    assert len(prompt_by_id) == 8
    assert set(prompt_by_id) == blocker_ids

    for record_id, prompt in prompt_by_id.items():
        source = queue_by_id[record_id]["source"]
        assert prompt["source_file_sha256"] == source["source_file_sha256"]
        assert prompt["source_dimensions"] == [
            source["source_width"],
            source["source_height"],
        ]
        assert prompt["status"] == "prompt_seed_unvalidated"
        assert prompt["positive_points_norm"]


def test_normalized_prompt_conversion() -> None:
    tool = load_tool()

    assert tool.norm_box_to_pixels(
        [0.1, 0.2, 0.9, 0.8],
        1000,
        500,
    ) == [100.0, 100.0, 900.0, 400.0]

    points, labels = tool.norm_points_to_pixels(
        [[0.5, 0.5], [0.25, 0.75]],
        [[0.9, 0.1]],
        1000,
        500,
    )
    assert points == [
        [500.0, 250.0],
        [250.0, 375.0],
        [900.0, 50.0],
    ]
    assert labels == [1, 1, 0]


def test_invalid_normalized_box_is_rejected() -> None:
    tool = load_tool()

    for box in (
        [0.5, 0.5, 0.4, 0.9],
        [-0.1, 0.2, 0.8, 0.9],
        [0.1, 0.2, 1.1, 0.9],
    ):
        try:
            tool.norm_box_to_pixels(box, 100, 100)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected invalid box to fail: {box}")


def test_prompt_hash_or_dimensions_cannot_go_stale() -> None:
    tool = load_tool()
    row = {
        "source_record_id": "test",
        "status": "sanitization_required",
        "source": {
            "source_file_sha256": "a" * 64,
            "source_width": 100,
            "source_height": 200,
        },
    }
    prompt = {
        "source_file_sha256": "a" * 64,
        "source_dimensions": [100, 200],
    }

    tool.validate_prompt(prompt, row)

    stale_hash = dict(prompt)
    stale_hash["source_file_sha256"] = "b" * 64
    try:
        tool.validate_prompt(stale_hash, row)
    except ValueError as exc:
        assert "hash is stale" in str(exc)
    else:
        raise AssertionError("expected stale source hash to fail")

    stale_dimensions = dict(prompt)
    stale_dimensions["source_dimensions"] = [101, 200]
    try:
        tool.validate_prompt(stale_dimensions, row)
    except ValueError as exc:
        assert "dimensions are stale" in str(exc)
    else:
        raise AssertionError("expected stale dimensions to fail")


def test_sam2_wrapper_never_describes_generated_masks_as_approved() -> None:
    source = TOOL.read_text(encoding="utf-8")

    assert '"candidate_status": "generated_pending_visual_review"' in source
    assert '"model_input_allowed": False' in source
    assert "SAM2 score chooses a candidate mask only" in source
