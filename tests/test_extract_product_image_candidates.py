from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "extract_product_image_candidates.py"


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "extract_product_image_candidates",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extracts_srcset_and_json_escaped_urls() -> None:
    tool = load_tool()
    page = "https://example.com/product"
    doc = r"""
    <img srcset="//cdn.example.com/a.50.50.jpg 50w,
                 //cdn.example.com/a.500.500.jpg 500w">
    <script>
      {"zoom":"https:\/\/cdn.example.com\/a.original.jpg"}
    </script>
    """
    rows = tool.extract_candidates(page, doc, contains=["a."])
    urls = {row["url"] for row in rows}
    assert "https://cdn.example.com/a.50.50.jpg" in urls
    assert "https://cdn.example.com/a.500.500.jpg" in urls
    assert "https://cdn.example.com/a.original.jpg" in urls


def test_relative_image_url_is_normalized() -> None:
    tool = load_tool()
    rows = tool.extract_candidates(
        "https://example.com/items/1",
        '<img data-zoom-image="/images/large.jpg">',
        contains=["large.jpg"],
    )
    assert [row["url"] for row in rows] == [
        "https://example.com/images/large.jpg"
    ]
