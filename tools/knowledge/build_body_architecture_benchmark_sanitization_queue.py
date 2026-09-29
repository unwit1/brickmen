#!/usr/bin/env python3
"""Build the leakage-sanitization review queue for architecture benchmark images.

Verified source media remains reference evidence only. This queue prevents catalog
labels, maker marks, SKU codes, composite panels, or similar shortcuts from entering
benchmark model inputs before explicit visual sanitization approval.
"""
from __future__ import annotations

import argparse
import json
import urllib.parse
from collections import Counter
from pathlib import Path
from typing import Any

VERSION = "body-architecture-benchmark-sanitization-queue/v1"
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
DEFAULT_BENCHMARK = DATA / "body-architecture-recognition-benchmark-cases.json"
DEFAULT_REVIEWS = DATA / "body-architecture-benchmark-sanitization-reviews.json"
DEFAULT_OUTPUT = DATA / "body-architecture-benchmark-sanitization-queue.json"

HIGH_RISK_HOSTS = {
    "static.herobloks.com",
    "kongbricks.com",
    "kongbricks.myshopify.com",
    "cdn.shopify.com",
}
MEDIUM_RISK_HOSTS = {"img.bricklink.com"}


def path_label(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def url_host(url: str | None) -> str:
    return (
        urllib.parse.urlparse(str(url or "")).hostname or ""
    ).lower()


def select_verified_locator(case: dict[str, Any]) -> dict[str, Any]:
    locators = [
        locator
        for locator in (case.get("input_asset") or {}).get(
            "reference_locators", []
        )
        if locator.get("source_file_sha256")
        and locator.get("exact_image_url")
    ]
    if not locators:
        raise ValueError(
            f"case has no byte-verified exact image: {case.get('source_record_id')}"
        )
    locators.sort(
        key=lambda locator: (
            str(locator.get("source_id") or ""),
            str(locator.get("source_file_sha256") or ""),
        )
    )
    return locators[0]


def source_risk(locator: dict[str, Any]) -> tuple[str, list[str]]:
    host = url_host(locator.get("exact_image_url"))
    if host in HIGH_RISK_HOSTS:
        return (
            "high",
            [
                "product_media_may_include_text_or_branding",
                "product_media_may_be_multi_panel_or_composite",
            ],
        )
    if host in MEDIUM_RISK_HOSTS:
        return (
            "medium_review_required",
            [
                "catalog_image_may_include_insets_or_auxiliary_panels",
            ],
        )
    return (
        "unknown_review_required",
        ["source_host_has_no_sanitization_prior"],
    )


def build(
    benchmark_path: Path = DEFAULT_BENCHMARK,
    reviews_path: Path = DEFAULT_REVIEWS,
) -> dict[str, Any]:
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    reviews_doc = (
        json.loads(reviews_path.read_text(encoding="utf-8"))
        if reviews_path.exists()
        else {"reviews": [], "reviewer": None}
    )
    reviews_by_record = {
        row["source_record_id"]: row
        for row in reviews_doc.get("reviews", [])
    }
    queue: list[dict[str, Any]] = []

    for case in benchmark.get("cases", []):
        locator = select_verified_locator(case)
        risk, reasons = source_risk(locator)
        recommended = (
            [
                "tight_figure_crop",
                "mask_text_or_logo_regions",
                "segment_primary_figure",
                "replace_with_cleaner_exact_release_source",
                "manual_composite_cleanup",
            ]
            if risk == "high"
            else [
                "approve_raw_only_if_visually_clean",
                "tight_figure_crop",
                "mask_auxiliary_insets",
            ]
        )
        stored_review = reviews_by_record.get(case["source_record_id"])
        review_stale = bool(
            stored_review
            and stored_review.get("source_file_sha256")
            != locator.get("source_file_sha256")
        )
        if stored_review and not review_stale:
            stored_status = stored_review.get("status")
            if stored_status == "approved_raw":
                status = "approved_raw_model_input"
                raw_allowed = True
                sanitized_status = "approved"
                sanitized_hash = locator.get("source_file_sha256")
            elif stored_status == "sanitization_required":
                status = "sanitization_required"
                raw_allowed = False
                sanitized_status = "pending"
                sanitized_hash = None
            else:
                status = "blocked_pending_visual_sanitization_review"
                raw_allowed = False
                sanitized_status = "pending"
                sanitized_hash = None
        elif review_stale:
            status = "review_stale_source_hash_changed"
            raw_allowed = False
            sanitized_status = "stale"
            sanitized_hash = None
        else:
            status = "blocked_pending_visual_sanitization_review"
            raw_allowed = False
            sanitized_status = "pending"
            sanitized_hash = None

        review_payload = {
            "identity_match": None,
            "primary_view": None,
            "primary_figure_complete": None,
            "visible_text_leakage": [],
            "visual_confounders": [],
            "sanitization_action": None,
            "sanitized_asset_sha256": sanitized_hash,
            "sanitized_asset_status": sanitized_status,
            "reviewer_id": None,
            "reviewer_type": None,
            "review_confidence": None,
            "notes": [],
            "review_source_sha256": (
                stored_review.get("source_file_sha256")
                if stored_review
                else None
            ),
            "review_stale": review_stale,
        }
        if stored_review and not review_stale:
            for key in (
                "identity_match",
                "primary_view",
                "primary_figure_complete",
                "visible_text_leakage",
                "visual_confounders",
                "sanitization_action",
                "review_confidence",
                "notes",
            ):
                review_payload[key] = stored_review.get(key)
            reviewer = reviews_doc.get("reviewer") or {}
            review_payload["reviewer_id"] = reviewer.get("reviewer_id")
            review_payload["reviewer_type"] = reviewer.get("reviewer_type")

        queue.append(
            {
                "case_id": case["case_id"],
                "source_record_id": case["source_record_id"],
                "split": case["split"],
                "scoring_track": case["scoring_track"],
                "task": case["task"],
                "expected": case["expected"],
                "source": {
                    "source_id": locator["source_id"],
                    "exact_image_url": locator["exact_image_url"],
                    "source_file_sha256": locator["source_file_sha256"],
                    "source_size_bytes": locator.get("source_size_bytes"),
                    "source_width": locator.get("source_width"),
                    "source_height": locator.get("source_height"),
                    "source_content_type": locator.get("source_content_type"),
                    "source_image_format": locator.get("source_image_format"),
                    "verification_run_id": locator.get("verification_run_id"),
                },
                "source_risk": risk,
                "risk_reasons": reasons,
                "status": status,
                "raw_model_input_allowed": raw_allowed,
                "required_checks": [
                    "identity_matches_source_record",
                    "primary_view_classified",
                    "primary_figure_complete",
                    "release_or_sku_text_absent_or_removed",
                    "character_name_text_absent_or_removed",
                    "maker_or_brand_logo_absent_or_removed",
                    "architecture_or_market_label_absent_or_removed",
                    "task_confounding_secondary_panels_absent_or_removed",
                ],
                "recommended_actions": recommended,
                "review": review_payload,
                "policy": (
                    "Byte verification proves file identity, not benchmark suitability. "
                    "Raw media remains blocked from model input until visual sanitization "
                    "is explicitly approved."
                ),
                "processor_version": VERSION,
            }
        )

    counts = Counter(row["source_risk"] for row in queue)
    status_counts = Counter(row["status"] for row in queue)
    return {
        "schema_version": "0.1",
        "created": "2026-09-28",
        "status": "visual_sanitization_in_progress",
        "processor_version": VERSION,
        "benchmark_manifest": path_label(benchmark_path),
        "policy": "data/body-architecture-benchmark-input-sanitization-policy.json",
        "reviews": path_label(reviews_path),
        "summary": {
            "total_cases": len(queue),
            "raw_model_input_allowed_cases": sum(
                row["raw_model_input_allowed"] for row in queue
            ),
            "blocked_model_input_cases": sum(
                not row["raw_model_input_allowed"] for row in queue
            ),
            "status_counts": dict(status_counts),
            "risk_counts": dict(counts),
        },
        "queue": queue,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--reviews", type=Path, default=DEFAULT_REVIEWS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    result = build(args.benchmark, args.reviews)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
