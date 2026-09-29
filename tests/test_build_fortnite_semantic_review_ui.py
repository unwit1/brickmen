from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "build_fortnite_semantic_review_ui.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_fortnite_semantic_review_ui",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def batch() -> dict:
    pair_id = "fortnitepair-test"
    return {
        "schema": "fortnite-semantic-review-work-batch/v1",
        "processor_version": "fortnite-semantic-review-work-batch/v1",
        "batch_id": "batch-test",
        "mode": "first_review",
        "offset": 0,
        "limit": 1,
        "min_priority_score": 6.0,
        "selected_records": 1,
        "reviewer_id": "unassigned",
        "reviewer_type": "human",
        "items": [
            {
                "translation_pair_id": pair_id,
                "review_priority_score": 10,
                "lego_image_resolution": "direct_pair",
                "source_image_url": "https://example.test/source.png",
                "lego_image_url": "https://example.test/lego.png",
                "measurement_signals": [
                    {
                        "signal": "palette_reduction",
                        "region": "torso",
                        "value": -2,
                    }
                ],
                "measurement_signal_policy": (
                    "Signals only prioritize review and must not be copied into semantic "
                    "labels without direct visual evidence."
                ),
                "review_template": {
                    "schema": "fortnite-semantic-review/v1",
                    "review_id": None,
                    "translation_pair_id": pair_id,
                    "reviewer": {
                        "reviewer_type": "human",
                        "reviewer_id": "unassigned",
                        "model_id": None,
                        "model_revision": None,
                        "review_role": "reviewer",
                    },
                    "evidence": {
                        "source_image_url": "https://example.test/source.png",
                        "lego_image_url": "https://example.test/lego.png",
                        "source_image_sha256": None,
                        "lego_image_sha256": None,
                        "evidence_scope": "front_pair",
                        "claims_unobserved_surfaces": False,
                    },
                    "annotations": {
                        "regions": {
                            "head": [],
                            "torso": [],
                            "lower_body": [],
                            "accessory_or_silhouette": [],
                        },
                        "identity_critical_features": [],
                        "mask_headgear_route": None,
                        "expression_translation": None,
                    },
                    "limitations": [],
                    "measurement_signal_refs": [
                        {
                            "signal": "palette_reduction",
                            "region": "torso",
                            "value": -2,
                            "role": "review_prioritization_only",
                        }
                    ],
                    "review_status": "draft",
                    "adjudicates_review_ids": [],
                    "created_at": None,
                    "provenance": [],
                },
            }
        ],
        "policy": [],
    }


def test_valid_batch_builds_standalone_review_html() -> None:
    tool = load_tool()
    value = batch()

    html = tool.build_review_html(value)

    assert "Brickmen Semantic Review" in html
    assert "https://example.test/source.png" in html
    assert "https://example.test/lego.png" in html
    assert "localStorage" in html
    assert "Export JSONL" in html
    assert "claims_unobserved_surfaces=false" in html
    assert "Measurement signals" in html
    assert "prioritization only" in html


def test_batch_validation_rejects_missing_items() -> None:
    tool = load_tool()
    value = batch()
    value["items"] = []
    value["selected_records"] = 0

    try:
        tool.validate_batch(value)
    except ValueError as exc:
        assert "at least one item" in str(exc)
    else:
        raise AssertionError("expected empty batch to be rejected")


def test_batch_validation_rejects_record_count_drift() -> None:
    tool = load_tool()
    value = batch()
    value["selected_records"] = 2

    try:
        tool.validate_batch(value)
    except ValueError as exc:
        assert "selected_records" in str(exc)
    else:
        raise AssertionError("expected selected_records mismatch to be rejected")


def test_batch_validation_rejects_unobserved_surface_claims() -> None:
    tool = load_tool()
    value = batch()
    value["items"][0]["review_template"]["evidence"][
        "claims_unobserved_surfaces"
    ] = True

    try:
        tool.validate_batch(value)
    except ValueError as exc:
        assert "claims_unobserved_surfaces" in str(exc)
    else:
        raise AssertionError("expected hidden-surface claims to be rejected")


def test_script_json_prevents_script_breakout() -> None:
    tool = load_tool()
    encoded = tool._script_json({"x": "</script><!--"})

    assert "</script>" not in encoded
    assert "<!--" not in encoded
    assert "<\\/script>" in encoded


def test_checked_in_first_batch_builds_ui() -> None:
    tool = load_tool()
    root = Path(__file__).resolve().parents[1]
    batch_path = (
        root
        / "knowledge"
        / "libraries"
        / "lego-minifigure-customs"
        / "data"
        / "semantic-review-batches"
        / "fortnite-first-review-batch-0001.json"
    )
    import json

    value = json.loads(batch_path.read_text(encoding="utf-8"))
    html = tool.build_review_html(value)

    assert value["selected_records"] == 25
    assert value["batch_id"] in html
    assert html.count("review_prioritization_only") >= 25
