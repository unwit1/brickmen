from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "materialize_fortnite_semantic_review_media.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "materialize_fortnite_semantic_review_media",
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
        "batch_id": "batch-test",
        "items": [
            {
                "translation_pair_id": pair_id,
                "source_image_url": "https://fortnite-api.com/source.png",
                "lego_image_url": "https://fortnite-api.com/lego.png",
                "review_template": {
                    "schema": "fortnite-semantic-review/v1",
                    "translation_pair_id": pair_id,
                    "evidence": {
                        "source_image_url": "https://fortnite-api.com/source.png",
                        "lego_image_url": "https://fortnite-api.com/lego.png",
                        "source_image_sha256": None,
                        "lego_image_sha256": None,
                    },
                    "provenance": [],
                },
            }
        ],
    }


def test_materialization_hashes_exact_bytes_and_updates_review_evidence(
    tmp_path: Path,
) -> None:
    tool = load_tool()
    payloads = {
        "https://fortnite-api.com/source.png": b"source-image-bytes",
        "https://fortnite-api.com/lego.png": b"lego-image-bytes",
    }

    def fake_fetch(url: str):
        return payloads[url], "image/png", url

    output, manifest = tool.materialize_batch(
        batch(),
        tmp_path / "media",
        fetcher=fake_fetch,
    )

    item = output["items"][0]
    evidence = item["review_template"]["evidence"]
    source_sha = hashlib.sha256(payloads[item["source_image_url"]]).hexdigest()
    lego_sha = hashlib.sha256(payloads[item["lego_image_url"]]).hexdigest()

    assert evidence["source_image_sha256"] == source_sha
    assert evidence["lego_image_sha256"] == lego_sha
    assert item["source_image_sha256"] == source_sha
    assert item["lego_image_sha256"] == lego_sha
    assert item["source_image_local_asset"].startswith("media/")
    assert item["lego_image_local_asset"].startswith("media/")
    assert (tmp_path / item["source_image_local_asset"]).read_bytes() == payloads[
        item["source_image_url"]
    ]
    assert (tmp_path / item["lego_image_local_asset"]).read_bytes() == payloads[
        item["lego_image_url"]
    ]
    assert manifest["records"][0]["source"]["sha256"] == source_sha
    assert manifest["records"][0]["lego"]["sha256"] == lego_sha
    assert output["media_materialization"]["records"] == 1


def test_disallowed_review_media_host_is_rejected(tmp_path: Path) -> None:
    tool = load_tool()
    value = batch()
    value["items"][0]["source_image_url"] = "https://example.test/source.png"

    try:
        tool.materialize_batch(value, tmp_path / "media")
    except ValueError as exc:
        assert "host is not allowed" in str(exc)
    else:
        raise AssertionError("expected disallowed media host to fail")


def test_empty_batch_is_rejected(tmp_path: Path) -> None:
    tool = load_tool()

    try:
        tool.materialize_batch({"items": []}, tmp_path / "media")
    except ValueError as exc:
        assert "at least one review item" in str(exc)
    else:
        raise AssertionError("expected empty batch to fail")
