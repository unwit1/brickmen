from copy import deepcopy

import pytest

from tools.knowledge.sync_autonomous_state import synchronize


def sample():
    state = {
        "known_gaps": [{"id": "fortnite_semantic_review_labels", "description": "old counts"}],
        "highest_value_tasks": [{"task": "Continue Fortnite first-review batch 0004"}],
        "continuation": {"instruction": "batch 0006"},
        "completed_batches": [{"id": "historical", "details": {"submitted_pairs": 75}}],
    }
    progress = {
        "invalid_review_records": 0, "eligible_pairs": 744,
        "submitted_first_review_pairs": 250, "remaining_first_review_pairs": 494,
        "submitted_semantic_annotations": 1017, "complete_first_review_batch_count": 10,
        "independently_double_reviewed_pairs": 0, "adjudicated_pairs": 0,
        "next_materialized_incomplete_batch": {"batch_index": 11},
        "next_planned_batch": {"batch_index": 12},
    }
    return state, progress


def test_frontier_replaces_stale_instructions_and_preserves_history():
    state, progress = sample()
    before = deepcopy(state)
    result = synchronize(state, progress)
    assert state == before
    assert result["completed_batches"] == state["completed_batches"]
    assert "0011" in result["current_workstream"]
    assert "494 remain" in result["continuation"]["instruction"]
    assert "0004" not in result["highest_value_tasks"][0]["task"]
    assert synchronize(result, progress) == result


@pytest.mark.parametrize("mutation", [
    {"invalid_review_records": 1}, {"remaining_first_review_pairs": 493},
    {"submitted_first_review_pairs": -1}, {"eligible_pairs": True},
])
def test_inconsistent_or_invalid_progress_cannot_become_continuation(mutation):
    state, progress = sample()
    progress.update(mutation)
    with pytest.raises(ValueError):
        synchronize(state, progress)


def test_completed_first_reviews_do_not_claim_canonical_completion():
    state, progress = sample()
    progress.update(submitted_first_review_pairs=744, remaining_first_review_pairs=0,
                    next_materialized_incomplete_batch=None, next_planned_batch=None)
    result = synchronize(state, progress)
    assert "independent_second_review" in result["current_workstream"]
    assert "explicit adjudication" in result["continuation"]["instruction"]
