#!/usr/bin/env python3
"""Build the visual-reference acquisition queue for architecture benchmark cases.

This queue converts provenance page locators into explicit next acquisition actions.
It does not crawl catalog pages and does not pretend an HTML page URL is an image URL.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VERSION = "body-architecture-reference-acquisition/v1"
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"
DEFAULT_BENCHMARK = DATA / "body-architecture-recognition-benchmark-cases.json"
DEFAULT_OUTPUT = DATA / "body-architecture-reference-acquisition-queue.json"


def classify_locator(locator: dict[str, Any]) -> tuple[str, str]:
    quality = locator.get("locator_quality")
    authority = locator.get("authority")
    url = str(locator.get("url") or "")
    exact_image_url = locator.get("exact_image_url")

    if exact_image_url:
        return (
            "resolved_exact_image_url",
            "already_resolved_source_media",
        )
    if quality == "indirect_identity_graph":
        return (
            "blocked_on_direct_release_locator",
            "resolve_direct_release_page_before_image_acquisition",
        )
    if authority == "structured_catalog" and "bricklink.com" in url:
        return (
            "ready_for_catalog_image_resolution",
            "bricklink_catalog_adapter_or_reviewed_image_endpoint",
        )
    return (
        "ready_for_reviewed_page_media_resolution",
        "reviewed_page_to_exact_image_url",
    )


def build(benchmark_path: Path = DEFAULT_BENCHMARK) -> dict[str, Any]:
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    queue: list[dict[str, Any]] = []

    for case in benchmark["cases"]:
        locators = case["input_asset"].get("reference_locators") or []
        actions = []
        for locator in locators:
            status, strategy = classify_locator(locator)
            actions.append(
                {
                    "source_id": locator["source_id"],
                    "page_url": locator["url"],
                    "authority": locator.get("authority"),
                    "locator_quality": locator.get("locator_quality"),
                    "status": status,
                    "strategy": strategy,
                    "exact_image_url": locator.get("exact_image_url"),
                    "image_resolution_status": locator.get("image_resolution_status"),
                }
            )

        if not actions:
            case_status = "blocked_missing_reference_locator"
        elif any(action["status"] == "resolved_exact_image_url" for action in actions):
            case_status = "ready_for_materialization"
        elif all(
            action["status"] == "blocked_on_direct_release_locator"
            for action in actions
        ):
            case_status = "blocked_on_direct_release_locator"
        else:
            case_status = "ready_for_image_url_resolution"

        queue.append(
            {
                "case_id": case["case_id"],
                "source_record_id": case["source_record_id"],
                "split": case["split"],
                "scoring_track": case["scoring_track"],
                "architecture_target": case["expected"],
                "status": case_status,
                "locator_actions": actions,
                "required_output": {
                    "exact_image_url": next(
                        (
                            action.get("exact_image_url")
                            for action in actions
                            if action.get("exact_image_url")
                        ),
                        None,
                    ),
                    "source_occurrence_id": None,
                    "source_file_sha256": None,
                    "view": "canonical_or_best_available_full_figure",
                    "rights_provenance_status": "preserve_source_permission_overlay",
                },
            }
        )

    action_status_counts: dict[str, int] = {}
    strategy_counts: dict[str, int] = {}
    for row in queue:
        for action in row["locator_actions"]:
            action_status_counts[action["status"]] = (
                action_status_counts.get(action["status"], 0) + 1
            )
            strategy_counts[action["strategy"]] = (
                strategy_counts.get(action["strategy"], 0) + 1
            )

    summary_ready_for_materialization = sum(
        row["status"] == "ready_for_materialization" for row in queue
    )
    summary_ready_for_image_resolution = sum(
        row["status"] == "ready_for_image_url_resolution" for row in queue
    )
    summary_blocked = sum(row["status"].startswith("blocked") for row in queue)

    return {
        "schema_version": "0.1",
        "created": "2026-09-28",
        "status": (
            "exact_image_urls_complete_materialization_pending"
            if summary_ready_for_materialization == len(queue)
            and summary_ready_for_image_resolution == 0
            and summary_blocked == 0
            else "ready_for_resolution"
        ),
        "processor_version": VERSION,
        "objective": (
            "Resolve every architecture benchmark case from a provenance page locator "
            "to an exact reviewed image URL before content-addressed materialization."
        ),
        "policy": [
            "Do not pass HTML catalog pages to the image materializer.",
            "Do not crawl a source merely because a page locator exists.",
            "Prefer supported catalog/API adapters when available.",
            "Preserve source occurrence, rights/provenance metadata, and exact image URL.",
            "Indirect identity-graph evidence may remain as provenance even when a separate exact media source resolves the visual asset.",
        ],
        "benchmark_manifest": benchmark_path.relative_to(ROOT).as_posix(),
        "summary": {
            "total_cases": len(queue),
            "ready_for_materialization_cases": summary_ready_for_materialization,
            "ready_for_image_url_resolution_cases": summary_ready_for_image_resolution,
            "blocked_cases": summary_blocked,
            "action_status_counts": action_status_counts,
            "strategy_counts": strategy_counts,
        },
        "queue": queue,
        "downstream": {
            "materializer": "tools/knowledge/materialize_lego_reference_images.py",
            "materializer_requirement": "exact HTTPS image URLs plus explicit allowed hosts",
            "post_materialization": [
                "checksum and content-addressed dedupe",
                "canonical-view validation",
                "low-resolution and occlusion derivative generation",
                "benchmark manifest asset binding",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build(args.benchmark)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
