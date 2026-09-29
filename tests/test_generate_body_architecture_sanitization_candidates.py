from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "generate_body_architecture_sanitization_candidates.py"
)


def load_tool():
    sys.path.insert(0, str(TOOL.parent))
    spec = importlib.util.spec_from_file_location(
        "generate_body_architecture_sanitization_candidates",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_normalized_box_rounding_and_validation() -> None:
    tool = load_tool()

    assert tool.normalized_box([0.1, 0.2, 0.9, 0.8], 101, 99) == (
        10,
        19,
        91,
        80,
    )

    for bounds in (
        [-0.1, 0, 1, 1],
        [0, 0, 1.1, 1],
        [0.5, 0, 0.4, 1],
        [0, 0, 1],
    ):
        try:
            tool.normalized_box(bounds, 100, 100)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected invalid bounds: {bounds}")


def test_apply_operations_masks_then_crops() -> None:
    tool = load_tool()
    from PIL import Image

    image = Image.new("RGB", (100, 100), "white")
    operations = [
        {
            "op": "mask_rect_norm",
            "bounds": [0.8, 0.0, 1.0, 0.2],
            "fill_mode": "white",
        },
        {
            "op": "crop_norm",
            "bounds": [0.1, 0.1, 0.9, 0.9],
        },
    ]

    result, applied = tool.apply_operations(image, operations)

    assert result.size == (80, 80)
    assert [row["op"] for row in applied] == [
        "mask_rect_norm",
        "crop_norm",
    ]
    assert applied[0]["fill_rgba"] == [255, 255, 255, 255]


def test_generate_candidate_is_hash_pinned_and_metadata_only(monkeypatch) -> None:
    tool = load_tool()
    from PIL import Image

    image = Image.new("RGB", (100, 80), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    source_bytes = buffer.getvalue()
    source_sha = hashlib.sha256(source_bytes).hexdigest()

    monkeypatch.setattr(
        tool,
        "fetch_source_bytes",
        lambda *args, **kwargs: (
            source_bytes,
            "https://images.example.test/source.png",
        ),
    )

    queue_row = {
        "case_id": "archrec::test",
        "source_record_id": "test",
        "split": "development",
        "source": {
            "source_id": "test-source",
            "exact_image_url": "https://images.example.test/source.png",
            "source_file_sha256": source_sha,
            "source_width": 100,
            "source_height": 80,
        },
    }
    transform = {
        "source_record_id": "test",
        "source_file_sha256": source_sha,
        "source_dimensions": [100, 80],
        "status": "candidate_transform",
        "operations": [
            {
                "op": "crop_norm",
                "bounds": [0.1, 0.1, 0.9, 0.9],
            }
        ],
    }

    result = tool.generate_candidate(
        queue_row,
        transform,
        allowed_hosts={"images.example.test"},
        timeout_seconds=1,
        max_bytes=1024 * 1024,
    )

    assert result["source_file_sha256"] == source_sha
    assert result["source_dimensions"] == [100, 80]
    assert result["output_dimensions"] == [80, 64]
    assert len(result["sanitized_pixel_sha256"]) == 64
    assert len(result["sanitized_png_sha256"]) == 64
    assert result["candidate_status"] == "generated_pending_visual_review"
    assert result["model_input_allowed"] is False
    assert result["written_derivative_path"] is None


def test_generate_candidate_rejects_stale_source_hash(monkeypatch) -> None:
    tool = load_tool()
    queue_row = {
        "case_id": "archrec::test",
        "source_record_id": "test",
        "split": "development",
        "source": {
            "source_id": "test-source",
            "exact_image_url": "https://images.example.test/source.png",
            "source_file_sha256": "a" * 64,
            "source_width": 100,
            "source_height": 80,
        },
    }
    transform = {
        "source_record_id": "test",
        "source_file_sha256": "b" * 64,
        "source_dimensions": [100, 80],
        "status": "candidate_transform",
        "operations": [
            {
                "op": "crop_norm",
                "bounds": [0.1, 0.1, 0.9, 0.9],
            }
        ],
    }

    try:
        tool.generate_candidate(
            queue_row,
            transform,
            allowed_hosts={"images.example.test"},
            timeout_seconds=1,
            max_bytes=1024,
        )
    except ValueError as exc:
        assert "source hash is stale" in str(exc)
    else:
        raise AssertionError("expected stale transform source hash to fail")


def test_build_keeps_segmentation_blockers_separate(tmp_path: Path, monkeypatch) -> None:
    tool = load_tool()
    from PIL import Image

    image = Image.new("RGB", (20, 20), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    source_bytes = buffer.getvalue()
    source_sha = hashlib.sha256(source_bytes).hexdigest()

    queue_path = tmp_path / "queue.json"
    transform_path = tmp_path / "transforms.json"

    queue_path.write_text(
        json.dumps(
            {
                "queue": [
                    {
                        "case_id": "archrec::a",
                        "source_record_id": "a",
                        "split": "development",
                        "source": {
                            "source_id": "source-a",
                            "exact_image_url": "https://images.example.test/a.png",
                            "source_file_sha256": source_sha,
                            "source_width": 20,
                            "source_height": 20,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    transform_path.write_text(
        json.dumps(
            {
                "transforms": [
                    {
                        "source_record_id": "a",
                        "source_file_sha256": source_sha,
                        "source_dimensions": [20, 20],
                        "status": "candidate_transform",
                        "operations": [
                            {
                                "op": "crop_norm",
                                "bounds": [0, 0, 1, 1],
                            }
                        ],
                    },
                    {
                        "source_record_id": "b",
                        "source_file_sha256": "c" * 64,
                        "source_dimensions": [20, 20],
                        "status": "requires_segmentation",
                        "operations": [],
                        "rationale": "overlapping inset",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        tool,
        "fetch_source_bytes",
        lambda *args, **kwargs: (
            source_bytes,
            "https://images.example.test/a.png",
        ),
    )
    monkeypatch.setattr(tool.time, "sleep", lambda _: None)

    result = tool.build(
        queue_path,
        transform_path,
        allowed_hosts={"images.example.test"},
        delay_seconds=0,
    )

    assert result["generated_candidates"] == 1
    assert result["segmentation_or_manual_blockers"] == 1
    assert result["errors"] == 0
    assert result["metadata_only"] is True
    assert result["raw_source_media_persisted"] is False
    assert result["candidate_derivative_media_persisted"] is False
