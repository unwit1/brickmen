from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "prepare_body_architecture_contrast_review.py"
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
CORPUS = DATA / "body-architecture-same-character-contrast-v1.json"


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "prepare_body_architecture_contrast_review", TOOL
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_live_contrast_has_four_unique_hash_pinned_assets() -> None:
    tool = load_tool()
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    assets = tool.unique_assets(corpus)

    assert len(assets) == 4
    assert len({row["source_file_sha256"] for row in assets}) == 4
    assert all(row["exact_image_url"].startswith("https://") for row in assets)


def test_fetch_asset_rejects_hash_mismatch(tmp_path: Path, monkeypatch) -> None:
    tool = load_tool()

    class Response:
        headers = {"Content-Type": "image/png"}
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def geturl(self): return "https://img.bricklink.com/test.png"
        def read(self, n): return b"wrong"

    monkeypatch.setattr(tool.urllib.request, "urlopen", lambda *a, **k: Response())
    asset = {
        "source_record_id": "test",
        "exact_image_url": "https://img.bricklink.com/test.png",
        "source_file_sha256": "0" * 64,
        "dimensions": [1, 1],
    }
    try:
        tool.fetch_asset(
            asset,
            output_dir=tmp_path,
            allowed_hosts={"img.bricklink.com"},
            timeout_seconds=1,
            max_bytes=1024,
        )
    except ValueError as exc:
        assert "SHA-256 mismatch" in str(exc)
    else:
        raise AssertionError("expected hash mismatch")


def test_fetch_asset_writes_only_after_exact_verification(
    tmp_path: Path, monkeypatch
) -> None:
    tool = load_tool()
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (2, 3), "white").save(buf, format="PNG")
    data = buf.getvalue()
    sha = hashlib.sha256(data).hexdigest()

    class Response:
        headers = {"Content-Type": "image/png"}
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def geturl(self): return "https://img.bricklink.com/test.png"
        def read(self, n): return data

    monkeypatch.setattr(tool.urllib.request, "urlopen", lambda *a, **k: Response())
    asset = {
        "source_record_id": "test",
        "pair_id": "pair",
        "side": "left",
        "character_id": "x",
        "architecture_id": "a",
        "exact_image_url": "https://img.bricklink.com/test.png",
        "source_file_sha256": sha,
        "dimensions": [2, 3],
        "model_input_state": "pending_visual_sanitization",
    }
    result = tool.fetch_asset(
        asset,
        output_dir=tmp_path,
        allowed_hosts={"img.bricklink.com"},
        timeout_seconds=1,
        max_bytes=1024 * 1024,
    )

    assert result["observed_sha256"] == sha
    assert result["observed_dimensions"] == [2, 3]
    assert (tmp_path / result["local_review_filename"]).exists()
