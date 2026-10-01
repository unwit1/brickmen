from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "knowledge" / "resolve_fortnite_review_batch_from_event.py"


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "resolve_fortnite_review_batch_from_event",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolves_one_numeric_batch_and_ignores_plan_or_reviews() -> None:
    tool = load_tool()
    event = {
        "commits": [
            {
                "added": [
                    "knowledge/libraries/lego-minifigure-customs/data/"
                    "semantic-review-batches/fortnite-first-review-batch-0002.json",
                    "knowledge/libraries/lego-minifigure-customs/data/"
                    "semantic-review-batches/fortnite-first-review-batch-plan.json",
                ],
                "modified": [
                    "knowledge/libraries/lego-minifigure-customs/data/"
                    "semantic-review-batches/"
                    "fortnite-first-review-batch-0001-gpt56sol-summary.json"
                ],
            }
        ]
    }
    assert tool.resolve(event) == (
        "knowledge/libraries/lego-minifigure-customs/data/"
        "semantic-review-batches/fortnite-first-review-batch-0002.json"
    )


def test_no_numeric_batch_returns_none() -> None:
    tool = load_tool()
    assert tool.resolve({"commits": [{"added": [], "modified": ["README.md"]}]}) is None


def test_multiple_numeric_batches_fail_closed() -> None:
    tool = load_tool()
    with pytest.raises(ValueError, match="multiple numeric Fortnite review batches"):
        tool.resolve(
            {
                "commits": [
                    {
                        "added": [
                            "knowledge/libraries/lego-minifigure-customs/data/"
                            "semantic-review-batches/fortnite-first-review-batch-0002.json",
                            "knowledge/libraries/lego-minifigure-customs/data/"
                            "semantic-review-batches/fortnite-first-review-batch-0003.json",
                        ],
                        "modified": [],
                    }
                ]
            }
        )


def test_resolve_paths_matches_git_diff_input() -> None:
    tool = load_tool()
    assert tool.resolve_paths(
        [
            ".github/workflows/build-fortnite-semantic-review-ui.yml",
            "knowledge/libraries/lego-minifigure-customs/data/"
            "semantic-review-batches/fortnite-first-review-batch-0002.json",
        ]
    ) == (
        "knowledge/libraries/lego-minifigure-customs/data/"
        "semantic-review-batches/fortnite-first-review-batch-0002.json"
    )
