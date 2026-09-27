import json
from pathlib import Path

from tools.geometry.build_body_reference_reviewers import build_reviewers


def test_batch_reviewer_builder(tmp_path: Path):
    refs = tmp_path / "refs"
    refs.mkdir()
    ref = {
        "schema_version": "0.1",
        "reference_id": "one",
        "source": {"title": "One"},
        "view": "front",
        "evidence_class": "catalog_manual_estimate",
        "image_size_px": [100, 100],
        "body_bbox_px": [10, 10, 90, 90],
        "landmark_coordinate_mode": "pixel",
        "landmarks": {"neck": {"position": [50, 30], "confidence": 0.5}},
    }
    (refs / "one.json").write_text(json.dumps(ref), encoding="utf-8")
    manifest = {
        "references": [{"reference": "one.json", "skeleton": "../unused.json"}]
    }
    (refs / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    out = tmp_path / "out"
    result = build_reviewers(refs / "manifest.json", out)
    assert result["reviewers"][0]["source_image_embedded"] is False
    assert (out / "one.html").exists()
    assert (out / "index.json").exists()
    assert "data:image/" not in (out / "one.html").read_text(encoding="utf-8")
