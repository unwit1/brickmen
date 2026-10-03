from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "materialize_exact_release_multiview_candidates.py"


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "materialize_exact_release_multiview_candidates",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extract_image_url_prefers_open_graph() -> None:
    tool = load_tool()
    html = (
        '<html><head>'
        '<meta property="og:image" content="/media/exact/rear.jpg">'
        '</head><body><img src="/wrong/front.jpg"></body></html>'
    )
    assert (
        tool.extract_image_url(html, "https://example.test/minifig/1")
        == "https://example.test/media/exact/rear.jpg"
    )


def test_materializer_hashes_bytes_but_keeps_result_noncanonical(tmp_path: Path) -> None:
    tool = load_tool()
    page_url = "https://example.test/minifig/fig-1/"
    image_url = "https://cdn.example.test/rear.png"
    page = (
        f'<html><head><meta property="og:image" content="{image_url}"></head></html>'
    ).encode()
    image = b"not-a-real-png-but-stable-test-bytes"

    def fetcher(url: str):
        if url == page_url:
            return page, "text/html", page_url
        if url == image_url:
            return image, "image/png", image_url
        raise AssertionError(url)

    doc = {
        "schema": "exact-release-multiview-source-candidates/v1",
        "candidates": [
            {
                "candidate_id": "candidate-1",
                "reference_set_id": "refset-1",
                "subject": "Subject",
                "identifiers": {
                    "bricklink_minifigure_id": "m1",
                    "rebrickable_fig_num": "fig-1",
                },
                "source_provider": "Example",
                "source_page_url": page_url,
                "observed_view": "rear",
            }
        ],
    }

    result = tool.materialize(doc, tmp_path, fetcher=fetcher)
    row = result["results"][0]

    assert result["candidate_count"] == 1
    assert result["materialized_count"] == 1
    assert row["image_sha256"] == tool.sha256_bytes(image)
    assert (tmp_path / row["local_path"]).read_bytes() == image
    assert row["byte_materialized"] is True
    assert row["visual_review_status"] == "pending"
    assert row["exact_release_visual_identity_verified"] is False
    assert row["canonical_eligible"] is False
    assert row["training_eligible"] is False


def test_fallback_img_resolution_is_relative() -> None:
    tool = load_tool()
    html = '<html><body><img data-src="../images/rear.webp"></body></html>'
    assert (
        tool.extract_image_url(html, "https://example.test/a/b/page")
        == "https://example.test/a/images/rear.webp"
    )


def test_materializer_records_provider_block_without_promoting(tmp_path: Path) -> None:
    tool = load_tool()
    page_url = "https://blocked.example.test/minifig/fig-1/"

    def fetcher(url: str):
        raise PermissionError("provider denied automated page access")

    doc = {
        "schema": "exact-release-multiview-source-candidates/v1",
        "candidates": [
            {
                "candidate_id": "candidate-blocked",
                "reference_set_id": "refset-1",
                "subject": "Subject",
                "identifiers": {
                    "bricklink_minifigure_id": "m1",
                    "rebrickable_fig_num": "fig-1",
                },
                "source_provider": "BlockedProvider",
                "source_page_url": page_url,
                "observed_view": "rear",
            }
        ],
    }

    result = tool.materialize(doc, tmp_path, fetcher=fetcher)
    row = result["results"][0]

    assert result["materialized_count"] == 0
    assert result["blocked_count"] == 1
    assert row["materialization_status"] == "blocked"
    assert row["byte_materialized"] is False
    assert row["visual_review_status"] == "blocked_on_acquisition"
    assert row["exact_release_visual_identity_verified"] is False
    assert row["canonical_eligible"] is False
    assert row["training_eligible"] is False
    assert row["blocker"]["error_type"] == "PermissionError"
    assert list(tmp_path.iterdir()) == []


def test_direct_image_url_bypasses_blocked_page_layer(tmp_path: Path) -> None:
    tool = load_tool()
    page_url = "https://blocked.example.test/minifig/fig-1/"
    image_url = "https://cdn.example.test/exact-rear.webp"
    image = b"stable-rear-evidence-bytes"

    def fetcher(url: str):
        if url == image_url:
            return image, "image/webp", image_url
        raise AssertionError(f"page fetch should have been bypassed: {url}")

    doc = {
        "schema": "exact-release-multiview-source-candidates/v1",
        "candidates": [
            {
                "candidate_id": "candidate-direct",
                "reference_set_id": "refset-1",
                "subject": "Subject",
                "identifiers": {
                    "bricklink_minifigure_id": "m1",
                    "rebrickable_fig_num": "fig-1",
                },
                "source_provider": "Example",
                "source_page_url": page_url,
                "direct_image_url": image_url,
                "observed_view": "rear",
            }
        ],
    }

    result = tool.materialize(doc, tmp_path, fetcher=fetcher)
    row = result["results"][0]

    assert result["materialized_count"] == 1
    assert result["blocked_count"] == 0
    assert row["materialization_status"] == "materialized"
    assert row["resolved_image_url"] == image_url
    assert row["image_sha256"] == tool.sha256_bytes(image)
    assert row["canonical_eligible"] is False
    assert row["training_eligible"] is False
