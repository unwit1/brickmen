from pathlib import Path

import pytest

from tools.geometry.build_body_reference_review_ui import (
    build_review_html,
    validate_editable_reference,
)


def sample_reference():
    return {
        "schema_version": "0.1",
        "reference_id": "sample",
        "source": {"title": "Sample", "catalog_url": "https://example.com/page"},
        "view": "front",
        "evidence_class": "catalog_manual_estimate",
        "image_size_px": [512, 512],
        "body_bbox_px": [100, 50, 400, 450],
        "landmark_coordinate_mode": "pixel",
        "landmarks": {
            "neck": {"position": [250, 120], "confidence": 0.7},
            "waist": {"position": [250, 300], "confidence": 0.7},
        },
        "silhouette_pairs_px": {
            "chest_outer_width": {
                "left_x": 160,
                "right_x": 340,
                "y_px": 180,
                "confidence": 0.8,
            }
        },
        "exclude_from_production_dimensions": True,
    }


def test_reviewer_embeds_annotations_not_source_image_bytes():
    ref = sample_reference()
    html = build_review_html(ref)
    assert "sample" in html
    assert '"catalog_url":"https://example.com/page"' in html
    assert "source image is not embedded" in html.lower()
    assert "data:image/" not in html
    assert "Add chest at torso midpoint" in html
    assert "silhouette-line" in html
    assert "brickmen_body_reference_reviewer_v0" in html


def test_default_image_url_is_reference_only():
    html = build_review_html(
        sample_reference(),
        default_image_url="https://images.example.com/sample.png",
    )
    assert 'href="https://images.example.com/sample.png"' in html


def test_normalized_cad_reference_is_rejected():
    ref = sample_reference()
    ref["landmark_coordinate_mode"] = "normalized_body_height"
    with pytest.raises(ValueError, match="pixel-coordinate"):
        validate_editable_reference(ref)


def test_missing_bbox_is_rejected():
    ref = sample_reference()
    del ref["body_bbox_px"]
    with pytest.raises(ValueError, match="body_bbox_px"):
        validate_editable_reference(ref)
