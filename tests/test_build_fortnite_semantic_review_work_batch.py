from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "build_fortnite_semantic_review_work_batch.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_fortnite_semantic_review_work_batch",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def queue_record(pair_id: str, score: float) -> dict:
    return {
        "translation_pair_id": pair_id,
        "source_image_url": f"https://example.test/{pair_id}-source.png",
        "lego_image_url": f"https://example.test/{pair_id}-lego.png",
        "lego_image_resolution": "direct_pair",
        "review_priority_score": score,
        "measurement_signals": [
            {
                "signal": "palette_reduction",
                "region": "torso",
                "value": -3,
            }
        ],
        "processor_version": "fortnite-semantic-review-queue/v1",
    }


def existing_review(
    pair_id: str,
    status: str = "submitted",
    reviewer_id: str = "reviewer-a",
) -> dict:
    return {
        "translation_pair_id": pair_id,
        "review_status": status,
        "reviewer": {
            "reviewer_id": reviewer_id,
        },
    }


def adjudication(pair_id: str, status: str) -> dict:
    return {
        "translation_pair_id": pair_id,
        "status": status,
    }


def test_first_review_selects_highest_priority_unreviewed_pairs() -> None:
    tool = load_tool()
    queue = [
        queue_record("pair-a", 7),
        queue_record("pair-b", 10),
        queue_record("pair-c", 8),
    ]

    selected = tool.select(
        queue,
        mode="first_review",
        limit=2,
        min_priority_score=6,
        existing_reviews=[existing_review("pair-b")],
    )

    assert [row["translation_pair_id"] for row in selected] == [
        "pair-c",
        "pair-a",
    ]


def test_first_review_offset_is_deterministic() -> None:
    tool = load_tool()
    queue = [
        queue_record("pair-a", 10),
        queue_record("pair-b", 9),
        queue_record("pair-c", 8),
    ]

    selected = tool.select(
        queue,
        mode="first_review",
        limit=1,
        offset=1,
    )

    assert [row["translation_pair_id"] for row in selected] == ["pair-b"]


def test_second_review_uses_adjudication_status() -> None:
    tool = load_tool()
    queue = [queue_record("pair-a", 10), queue_record("pair-b", 9)]

    selected = tool.select(
        queue,
        mode="second_review",
        limit=10,
        adjudication_rows=[
            adjudication("pair-a", "needs_second_review"),
            adjudication("pair-b", "agreement_candidate"),
        ],
    )

    assert [row["translation_pair_id"] for row in selected] == ["pair-a"]


def test_second_review_accepts_needs_independent_second_review_status() -> None:
    tool = load_tool()
    queue = [queue_record("pair-a", 10)]

    selected = tool.select(
        queue,
        mode="second_review",
        limit=10,
        reviewer_id="reviewer-b",
        existing_reviews=[existing_review("pair-a", reviewer_id="reviewer-a")],
        adjudication_rows=[
            adjudication("pair-a", "needs_independent_second_review"),
        ],
    )

    assert [row["translation_pair_id"] for row in selected] == ["pair-a"]


def test_second_review_excludes_pairs_already_reviewed_by_assigned_reviewer() -> None:
    tool = load_tool()
    queue = [queue_record("pair-a", 10)]
    existing = [existing_review("pair-a", reviewer_id="reviewer-a")]
    rows = [adjudication("pair-a", "needs_second_review")]

    duplicate = tool.select(
        queue,
        mode="second_review",
        limit=10,
        reviewer_id="REVIEWER-A",
        existing_reviews=existing,
        adjudication_rows=rows,
    )
    independent = tool.select(
        queue,
        mode="second_review",
        limit=10,
        reviewer_id="reviewer-b",
        existing_reviews=existing,
        adjudication_rows=rows,
    )

    assert duplicate == []
    assert [row["translation_pair_id"] for row in independent] == ["pair-a"]


def test_adjudication_mode_targets_conflict_states() -> None:
    tool = load_tool()
    queue = [
        queue_record("pair-a", 10),
        queue_record("pair-b", 9),
        queue_record("pair-c", 8),
        queue_record("pair-d", 7),
    ]

    selected = tool.select(
        queue,
        mode="adjudication",
        limit=10,
        adjudication_rows=[
            adjudication("pair-a", "needs_adjudication"),
            adjudication("pair-b", "adjudicator_conflict"),
            adjudication("pair-c", "invalid_adjudicator_references"),
            adjudication("pair-d", "agreement_candidate"),
        ],
    )

    assert [row["translation_pair_id"] for row in selected] == [
        "pair-a",
        "pair-b",
        "pair-c",
    ]


def test_work_item_keeps_measurement_signals_nonsemantic() -> None:
    tool = load_tool()
    result = tool.build(
        [queue_record("pair-a", 10)],
        mode="first_review",
        limit=1,
        reviewer_id="reviewer-a",
    )

    item = result["items"][0]
    template = item["review_template"]

    assert item["measurement_signals"]
    assert "prioritize review" in item["measurement_signal_policy"]
    assert template["annotations"]["regions"]["torso"] == []
    assert template["measurement_signal_refs"][0]["role"] == "review_prioritization_only"
    assert template["review_status"] == "draft"
    assert template["evidence"]["claims_unobserved_surfaces"] is False


def test_second_review_requires_explicit_reviewer_assignment() -> None:
    tool = load_tool()

    try:
        tool.build(
            [queue_record("pair-a", 10)],
            mode="second_review",
            limit=1,
            existing_reviews=[existing_review("pair-a", reviewer_id="reviewer-a")],
            adjudication_rows=[adjudication("pair-a", "needs_second_review")],
        )
    except ValueError as exc:
        assert "explicit independent reviewer_id" in str(exc)
    else:
        raise AssertionError("expected unassigned second-review batch to be rejected")


def test_adjudication_batch_uses_adjudicator_role() -> None:
    tool = load_tool()
    result = tool.build(
        [queue_record("pair-a", 10)],
        mode="adjudication",
        limit=1,
        adjudication_rows=[adjudication("pair-a", "needs_adjudication")],
        reviewer_id="adjudicator-a",
    )

    assert (
        result["items"][0]["review_template"]["reviewer"]["review_role"]
        == "adjudicator"
    )


def test_batch_id_is_stable_for_same_selection() -> None:
    tool = load_tool()
    queue = [queue_record("pair-a", 10), queue_record("pair-b", 9)]

    first = tool.build(queue, mode="first_review", limit=2)
    second = tool.build(queue, mode="first_review", limit=2)

    assert first["batch_id"] == second["batch_id"]


def test_invalid_limit_or_mode_is_rejected() -> None:
    tool = load_tool()
    queue = [queue_record("pair-a", 10)]

    for kwargs in (
        {"mode": "bad", "limit": 1},
        {"mode": "first_review", "limit": 0},
        {"mode": "first_review", "limit": 1, "offset": -1},
    ):
        try:
            tool.select(queue, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {kwargs}")


def test_checked_in_first_batch_matches_builder() -> None:
    tool = load_tool()
    root = Path(__file__).resolve().parents[1]
    queue_path = (
        root
        / "knowledge"
        / "libraries"
        / "lego-minifigure-customs"
        / "data"
        / "semantic-review-batches"
        / "fortnite-first-review-queue-v1.jsonl.gz"
    )
    batch_path = (
        root
        / "knowledge"
        / "libraries"
        / "lego-minifigure-customs"
        / "data"
        / "semantic-review-batches"
        / "fortnite-first-review-batch-0001.json"
    )

    expected = tool.build(
        tool.iter_jsonl([queue_path]),
        mode="first_review",
        limit=25,
        offset=0,
        min_priority_score=6.0,
        reviewer_id="unassigned",
        reviewer_type="human",
    )
    actual = __import__("json").loads(batch_path.read_text(encoding="utf-8"))

    assert actual == expected
