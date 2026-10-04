#!/usr/bin/env python3
"""Materialize exact-release multiview source candidates into byte-pinned review evidence.

This tool deliberately does not promote anything to canonical supervision. It:
- tries one or more declared source strategies in order;
- resolves representative image URLs from direct URLs or page metadata;
- downloads the image bytes;
- records SHA-256, content type, byte size, provenance, and failed attempts;
- leaves every result pending visual review and training-ineligible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

VERSION = "exact-release-multiview-candidate-materializer/v2"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "exact-release-multiview-source-candidates-v1.json"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_image_urls(html: str, base_url: str) -> list[str]:
    values: list[str] = []
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image(?::src)?["\']',
        r'<img[^>]+(?:data-zoom-image|data-image|data-src|src)=["\']([^"\']+)["\']',
        r'<a[^>]+href=["\']([^"\']+\.(?:png|jpe?g|webp)(?:\?[^"\']*)?)["\']',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, html, flags=re.IGNORECASE):
            value = urllib.parse.urljoin(base_url, match.group(1).strip())
            if value not in values:
                values.append(value)
    if not values:
        raise ValueError(f"could not resolve image URL from {base_url}")
    return values


def extract_image_url(html: str, base_url: str) -> str:
    return extract_image_urls(html, base_url)[0]


def default_fetch(url: str) -> tuple[bytes, str | None, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "BrickmenResearchBot/1.0 "
                "(evidence acquisition; contact repository owner)"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return (
            response.read(),
            response.headers.get_content_type(),
            response.geturl(),
        )


def extension_for(image_url: str, content_type: str | None) -> str:
    suffix = Path(urllib.parse.urlparse(image_url).path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return suffix
    if content_type:
        guess = mimetypes.guess_extension(content_type)
        if guess in {".png", ".jpg", ".jpeg", ".webp"}:
            return guess
    return ".bin"


def source_options(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    raw = candidate.get("source_options")
    if raw is not None:
        if not isinstance(raw, list) or not raw:
            raise ValueError("source_options must be a non-empty list")
        options: list[dict[str, Any]] = []
        for index, option in enumerate(raw):
            if not isinstance(option, dict):
                raise ValueError(f"source_options[{index}] must be an object")
            page_url = option.get("source_page_url")
            direct_image_url = option.get("direct_image_url")
            if not (
                isinstance(page_url, str)
                and page_url
                or isinstance(direct_image_url, str)
                and direct_image_url
            ):
                raise ValueError(
                    f"source_options[{index}] requires source_page_url or direct_image_url"
                )
            options.append(dict(option))
        return options

    page_url = candidate.get("source_page_url")
    direct_image_url = candidate.get("direct_image_url")
    if not (
        isinstance(page_url, str)
        and page_url
        or isinstance(direct_image_url, str)
        and direct_image_url
    ):
        raise ValueError("candidate requires source_page_url or direct_image_url")
    return [
        {
            "source_provider": candidate.get("source_provider"),
            "source_page_url": page_url,
            "direct_image_url": direct_image_url,
        }
    ]


def _source_metadata(option: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "option_index": index,
        "source_provider": option.get("source_provider"),
        "source_identifier": option.get("source_identifier"),
        "declared_source_page_url": option.get("source_page_url"),
        "declared_direct_image_url": option.get("direct_image_url"),
        "image_candidate_index": option.get("image_candidate_index"),
        "expected_image_sha256": option.get("expected_image_sha256"),
        "identity_match_basis": option.get("identity_match_basis"),
    }


def materialize(
    doc: dict[str, Any],
    output_dir: Path,
    *,
    fetcher: Callable[[str], tuple[bytes, str | None, str]] = default_fetch,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for candidate in doc.get("candidates") or []:
        candidate_id = str(candidate["candidate_id"])
        options = source_options(candidate)
        base = {
            "candidate_id": candidate_id,
            "reference_set_id": candidate["reference_set_id"],
            "subject": candidate.get("subject"),
            "identifiers": candidate.get("identifiers") or {},
            "observed_view": candidate.get("observed_view"),
            "canonical_eligible": False,
            "training_eligible": False,
        }
        attempts: list[dict[str, Any]] = []
        success: dict[str, Any] | None = None

        for index, option in enumerate(options):
            metadata = _source_metadata(option, index)
            page_url = option.get("source_page_url")
            direct_image_url = option.get("direct_image_url")
            try:
                if isinstance(direct_image_url, str) and direct_image_url:
                    resolved_page_url = (
                        page_url if isinstance(page_url, str) and page_url else None
                    )
                    page_type = None
                    image_url = direct_image_url
                else:
                    assert isinstance(page_url, str) and page_url
                    page_bytes, page_type, resolved_page_url = fetcher(page_url)
                    html = page_bytes.decode("utf-8", errors="replace")
                    image_candidates = extract_image_urls(html, resolved_page_url)
                    candidate_index = option.get("image_candidate_index", 0)
                    if not isinstance(candidate_index, int) or candidate_index < 0:
                        raise ValueError("image_candidate_index must be a non-negative integer")
                    if candidate_index >= len(image_candidates):
                        raise ValueError(
                            f"image_candidate_index {candidate_index} out of range "
                            f"for {len(image_candidates)} discovered image candidates"
                        )
                    image_url = image_candidates[candidate_index]

                if isinstance(direct_image_url, str) and direct_image_url:
                    image_candidates = [direct_image_url]
                    candidate_index = 0

                image_bytes, image_type, resolved_image_url = fetcher(image_url)
                image_sha256 = sha256_bytes(image_bytes)
                expected_sha256 = option.get("expected_image_sha256")
                if expected_sha256 is not None:
                    if not (
                        isinstance(expected_sha256, str)
                        and re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256)
                    ):
                        raise ValueError("expected_image_sha256 must be a 64-character hex digest")
                    if image_sha256.lower() != expected_sha256.lower():
                        raise ValueError(
                            "image SHA-256 mismatch: "
                            f"expected {expected_sha256.lower()}, got {image_sha256.lower()}"
                        )

                suffix = extension_for(resolved_image_url, image_type)
                output_path = output_dir / f"{candidate_id}{suffix}"
                output_path.write_bytes(image_bytes)

                attempt = {
                    **metadata,
                    "status": "materialized",
                    "resolved_source_page_url": resolved_page_url,
                    "resolved_image_url": resolved_image_url,
                    "resolved_image_candidates": image_candidates,
                    "selected_image_candidate_index": candidate_index,
                    "image_content_type": image_type,
                    "image_sha256": image_sha256,
                    "image_bytes": len(image_bytes),
                }
                attempts.append(attempt)
                success = {
                    **base,
                    "source_provider": option.get("source_provider"),
                    "source_identifier": option.get("source_identifier"),
                    "declared_source_page_url": page_url,
                    "materialization_status": "materialized",
                    "selected_source_option": index,
                    "selected_source": metadata,
                    "acquisition_attempts": attempts,
                    "resolved_source_page_url": resolved_page_url,
                    "source_page_content_type": page_type,
                    "resolved_image_url": resolved_image_url,
                    "resolved_image_candidates": image_candidates,
                    "selected_image_candidate_index": candidate_index,
                    "image_content_type": image_type,
                    "local_path": output_path.name,
                    "image_sha256": image_sha256,
                    "image_bytes": len(image_bytes),
                    "byte_materialized": True,
                    "visual_review_status": "pending",
                    "exact_release_visual_identity_verified": False,
                    "limitations": [
                        "Byte materialization alone does not prove the image depicts the declared exact release.",
                        "A reviewer must visually verify exact-release identity and the claimed view before promotion.",
                        "Hidden surfaces remain unknown even after a successful download.",
                    ],
                }
                break
            except Exception as exc:
                attempts.append(
                    {
                        **metadata,
                        "status": "blocked",
                        "blocker": {
                            "error_type": type(exc).__name__,
                            "message": str(exc)[:500],
                        },
                    }
                )

        if success is not None:
            results.append(success)
            continue

        last_blocker = attempts[-1]["blocker"] if attempts else {
            "error_type": "ValueError",
            "message": "no source options were attempted",
        }
        results.append(
            {
                **base,
                "source_provider": candidate.get("source_provider"),
                "declared_source_page_url": candidate.get("source_page_url"),
                "materialization_status": "blocked",
                "byte_materialized": False,
                "visual_review_status": "blocked_on_acquisition",
                "exact_release_visual_identity_verified": False,
                "acquisition_attempts": attempts,
                "blocker": last_blocker,
                "limitations": [
                    "All declared source options failed to materialize in this run.",
                    "No image bytes were accepted or hashed.",
                    "Provider blocking must not be treated as evidence about the unseen view.",
                ],
            }
        )

    materialized_count = sum(
        row["materialization_status"] == "materialized" for row in results
    )
    blocked_count = sum(
        row["materialization_status"] == "blocked" for row in results
    )
    return {
        "schema": "exact-release-multiview-materialization-manifest/v1",
        "processor_version": VERSION,
        "source_schema": doc.get("schema"),
        "candidate_count": len(doc.get("candidates") or []),
        "materialized_count": materialized_count,
        "blocked_count": blocked_count,
        "results": results,
        "policy": [
            "Downloaded bytes are review evidence only and are never canonicalized automatically.",
            "Ordered source fallbacks may recover evidence from a different provider but do not prove exact-release identity.",
            "Exact-release identity requires explicit visual review after byte materialization.",
            "Training eligibility remains false until downstream review and promotion gates pass.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    doc = json.loads(args.input.read_text(encoding="utf-8"))
    result = materialize(doc, args.output_dir)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "results"},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
