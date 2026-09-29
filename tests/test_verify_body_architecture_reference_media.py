from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "verify_body_architecture_reference_media.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "verify_body_architecture_reference_media",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def benchmark_fixture() -> dict:
    return {
        "cases": [
            {
                "case_id": "archrec::a",
                "source_record_id": "a",
                "split": "development",
                "scoring_track": "core",
                "input_asset": {
                    "reference_locators": [
                        {
                            "source_id": "page-only",
                            "url": "https://example.test/page",
                            "exact_image_url": None,
                            "image_resolution_status": None,
                        },
                        {
                            "source_id": "media-a",
                            "url": "https://example.test/a",
                            "exact_image_url": "https://images.example.test/a.png",
                            "image_resolution_status": "verified_exact_image_url",
                        },
                    ]
                },
            },
            {
                "case_id": "archrec::b",
                "source_record_id": "b",
                "split": "test",
                "scoring_track": "open_set",
                "input_asset": {
                    "reference_locators": [
                        {
                            "source_id": "media-b",
                            "url": "https://example.test/b",
                            "exact_image_url": "https://images.example.test/b.webp",
                            "image_resolution_status": "verified_exact_image_url",
                        }
                    ]
                },
            },
        ]
    }


def test_sniff_image_format() -> None:
    tool = load_tool()

    assert tool.sniff_image_format(b"\x89PNG\r\n\x1a\nrest") == "png"
    assert tool.sniff_image_format(b"\xff\xd8\xffrest") == "jpeg"
    assert tool.sniff_image_format(b"GIF89arest") == "gif"
    assert tool.sniff_image_format(b"RIFFxxxxWEBPrest") == "webp"
    assert tool.sniff_image_format(b"BMrest") == "bmp"
    assert tool.sniff_image_format(b"II*\x00rest") == "tiff"
    assert tool.sniff_image_format(b"not-an-image") is None


def test_validate_https_url_enforces_reviewed_hosts() -> None:
    tool = load_tool()
    allowed = {"images.example.test"}

    assert (
        tool.validate_https_url(
            "https://images.example.test/a.png",
            allowed,
        )
        == "images.example.test"
    )

    for url in (
        "http://images.example.test/a.png",
        "https://other.example.test/a.png",
    ):
        try:
            tool.validate_https_url(url, allowed)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected rejected URL: {url}")


def test_select_exact_images_requires_every_case() -> None:
    tool = load_tool()
    selected = tool.select_exact_images(benchmark_fixture())

    assert [row["source_record_id"] for row in selected] == ["a", "b"]
    assert selected[0]["source_id"] == "media-a"
    assert selected[0]["exact_image_url"].endswith("/a.png")

    broken = benchmark_fixture()
    broken["cases"][0]["input_asset"]["reference_locators"][1][
        "exact_image_url"
    ] = None
    try:
        tool.select_exact_images(broken)
    except ValueError as exc:
        assert "lacks exact image URL" in str(exc)
    else:
        raise AssertionError("expected missing exact image URL to fail")


def test_verify_records_hashes_without_raw_bytes(monkeypatch) -> None:
    tool = load_tool()
    calls: list[str] = []

    def fake_fetch(url: str, **kwargs):
        calls.append(url)
        digest = "a" * 64 if url.endswith("a.png") else "b" * 64
        return {
            "initial_host": "images.example.test",
            "final_url": url,
            "final_host": "images.example.test",
            "content_type": "image/png",
            "image_format": "png",
            "size_bytes": 123,
            "sha256": digest,
        }

    monkeypatch.setattr(tool, "fetch_image_metadata", fake_fetch)
    monkeypatch.setattr(tool.time, "sleep", lambda _: None)

    result = tool.verify(
        benchmark_fixture(),
        allowed_hosts={"images.example.test"},
        retries=0,
        delay_seconds=0,
    )

    assert result["total_cases"] == 2
    assert result["verified_cases"] == 2
    assert result["error_cases"] == 0
    assert result["unique_verified_hashes"] == 2
    assert result["duplicate_hashes"] == []
    assert len(calls) == 2
    assert all("raw_bytes" not in row for row in result["records"])
    assert all(row["status"] == "verified" for row in result["records"])


def test_verify_reports_duplicate_hashes(monkeypatch) -> None:
    tool = load_tool()

    def fake_fetch(url: str, **kwargs):
        return {
            "initial_host": "images.example.test",
            "final_url": url,
            "final_host": "images.example.test",
            "content_type": "image/png",
            "image_format": "png",
            "size_bytes": 123,
            "sha256": "c" * 64,
        }

    monkeypatch.setattr(tool, "fetch_image_metadata", fake_fetch)
    monkeypatch.setattr(tool.time, "sleep", lambda _: None)

    result = tool.verify(
        benchmark_fixture(),
        allowed_hosts={"images.example.test"},
        retries=0,
        delay_seconds=0,
    )

    assert result["verified_cases"] == 2
    assert result["unique_verified_hashes"] == 1
    assert result["duplicate_hashes"] == ["c" * 64]


def test_verify_preserves_errors_as_metadata(monkeypatch) -> None:
    tool = load_tool()

    def fake_fetch(url: str, **kwargs):
        if url.endswith("a.png"):
            raise ValueError("bad image")
        return {
            "initial_host": "images.example.test",
            "final_url": url,
            "final_host": "images.example.test",
            "content_type": "image/webp",
            "image_format": "webp",
            "size_bytes": 456,
            "sha256": "d" * 64,
        }

    monkeypatch.setattr(tool, "fetch_image_metadata", fake_fetch)
    monkeypatch.setattr(tool.time, "sleep", lambda _: None)

    result = tool.verify(
        benchmark_fixture(),
        allowed_hosts={"images.example.test"},
        retries=0,
        delay_seconds=0,
    )

    assert result["verified_cases"] == 1
    assert result["error_cases"] == 1
    failed = next(row for row in result["records"] if row["status"] == "error")
    assert failed["source_record_id"] == "a"
    assert failed["error"] == "bad image"
