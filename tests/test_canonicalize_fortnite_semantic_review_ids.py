from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "canonicalize_fortnite_semantic_review_ids.py"


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "canonicalize_fortnite_semantic_review_ids",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record(review_id: str | None) -> dict:
    return {
        "schema": "fortnite-semantic-review/v1",
        "review_id": review_id,
        "translation_pair_id": "pair-1",
        "reviewer": {
            "reviewer_type": "model",
            "reviewer_id": "reviewer",
            "model_id": "model",
            "model_revision": "rev",
            "review_role": "reviewer",
        },
        "evidence": {
            "source_image_url": "https://example.com/source.png",
            "lego_image_url": "https://example.com/lego.png",
            "source_image_sha256": "a" * 64,
            "lego_image_sha256": "b" * 64,
            "evidence_scope": "front_pair",
            "claims_unobserved_surfaces": False,
        },
        "annotations": {
            "regions": {
                "head": [{
                    "feature": "feature",
                    "decision": "preserved",
                    "confidence": 1.0,
                    "evidence_basis": "observed_in_both",
                    "notes": None,
                }],
                "torso": [],
                "lower_body": [],
                "accessory_or_silhouette": [],
            },
            "identity_critical_features": ["feature"],
            "mask_headgear_route": None,
            "expression_translation": None,
        },
        "limitations": ["front only"],
        "measurement_signal_refs": [],
        "review_status": "submitted",
        "adjudicates_review_ids": [],
        "created_at": "2026-10-01T00:00:00Z",
        "provenance": [],
    }


def test_canonicalizer_repairs_stale_id_without_changing_payload(tmp_path: Path) -> None:
    tool = load_tool()
    path = tmp_path / "reviews.jsonl"
    original = record("semreview-stale")
    path.write_text(json.dumps(original) + "\n", encoding="utf-8")

    result = tool.canonicalize_file(path)
    repaired = json.loads(path.read_text(encoding="utf-8"))

    assert result == {"records": 1, "changed": 1}
    assert repaired["review_id"] == tool.canonical_review_id(repaired)
    expected = dict(original)
    expected["review_id"] = repaired["review_id"]
    assert repaired == expected


def test_canonicalizer_is_idempotent(tmp_path: Path) -> None:
    tool = load_tool()
    path = tmp_path / "reviews.jsonl"
    row = record(None)
    row["review_id"] = tool.canonical_review_id(row)
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    before = path.read_bytes()
    result = tool.canonicalize_file(path)

    assert result == {"records": 1, "changed": 0}
    assert path.read_bytes() == before
