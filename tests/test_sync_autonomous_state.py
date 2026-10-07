from copy import deepcopy
import hashlib
import json
import sys

import pytest

from tools.knowledge.sync_autonomous_state import synchronize
from tools.knowledge import sync_autonomous_state as tool
from tools.knowledge.build_fortnite_semantic_critic_hardcase_queue import build as build_queue


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


def test_priority_moves_again_after_generated_task_text_replaces_original():
    state, progress = sample()
    first = synchronize(state, progress)
    progress.update(submitted_first_review_pairs=275, remaining_first_review_pairs=469,
                    next_materialized_incomplete_batch=None)
    second = synchronize(first, progress)
    assert second["highest_value_tasks"][0]["id"] == "fortnite_semantic_first_review"
    assert "0012" in second["highest_value_tasks"][0]["task"]
    assert "0011" not in second["highest_value_tasks"][0]["task"]


def test_existing_generated_priority_is_migrated_without_duplicate_tasks():
    state, progress = sample()
    state["highest_value_tasks"][0]["task"] = "Review first-review batch 0010; obtain independent second reviews."
    result = synchronize(state, progress)
    assert len(result["highest_value_tasks"]) == 1
    assert result["highest_value_tasks"][0]["id"] == "fortnite_semantic_first_review"
    assert "0011" in result["highest_value_tasks"][0]["task"]


def test_current_critic_snapshot_replaces_stale_counts_without_changing_history():
    state, progress = sample()
    state["semantic_evidence_gate"] = {"hardcase_priority": {"unique_critic_items": 900, "policy": "Keep explicit provisional policy."}}
    before = deepcopy(state)
    queue = build_queue([])
    result = synchronize(state, progress, queue)
    snapshot = result["semantic_evidence_gate"]["hardcase_priority"]
    assert snapshot["unique_critic_items"] == 0
    assert snapshot["unpaired_uncertainty_items"] == 0
    assert snapshot["duplicates_ignored"] == 0
    assert snapshot["queue_sha256"] == hashlib.sha256((json.dumps(queue, indent=2, ensure_ascii=False) + "\n").encode()).hexdigest()
    assert snapshot["policy"] == "Keep explicit provisional policy."
    assert result["completed_batches"] == state["completed_batches"]
    assert state == before
    assert synchronize(result, progress, queue) == result


def test_critic_snapshot_can_be_created_without_previous_gate():
    state, progress = sample()
    result = synchronize(state, progress, build_queue([]))
    assert result["semantic_evidence_gate"]["hardcase_priority"]["processor_version"].endswith("/v2")
    assert "no eligibility promotion" in result["semantic_evidence_gate"]["hardcase_priority"]["policy"]


def test_check_detects_stale_critic_artifact_without_rewriting_it(tmp_path, monkeypatch):
    state, progress = sample()
    state.update(updated_date="2026-10-07", status="active", latest_validated_test_commit="synthetic")
    data = tmp_path / "knowledge/libraries/lego-minifigure-customs/data"
    batches = data / "semantic-review-batches"
    batches.mkdir(parents=True)
    (tmp_path / "data").mkdir()
    (tmp_path / "data/autonomous-state.json").write_text(json.dumps(state))
    for filename in ("body-architecture-benchmark-model-input-manifest.json", "body-architecture-recognition-challenge-model-input-manifest-v4.json", "body-architecture-custom-model-input-manifest-v1.json"):
        (data / filename).write_text(json.dumps({"summary": {"model_input_allowed_cases": 1, "total_cases": 1, "blocked_cases": 0}}))
    monkeypatch.setattr(tool, "ROOT", tmp_path)
    monkeypatch.setattr(tool, "DATA", data)
    monkeypatch.setattr(tool, "DEFAULT_BATCH_DIR", batches)
    monkeypatch.setattr(tool, "build_progress", lambda *_: deepcopy(progress))
    monkeypatch.setattr(tool, "build_critic_evidence", lambda *_: ([], {"synthetic_summary": True}))
    monkeypatch.setattr(sys, "argv", ["sync"])
    assert tool.main() == 0
    monkeypatch.setattr(sys, "argv", ["sync", "--check"])
    assert tool.main() == 0
    path = data / "fortnite-semantic-critic-hardcase-queue-v1.json"
    path.write_text("{}\n")
    assert tool.main() == 2
    assert path.read_text() == "{}\n"
    monkeypatch.setattr(sys, "argv", ["sync"])
    assert tool.main() == 0
    assert json.loads(path.read_text())["unique_critic_items"] == 0
