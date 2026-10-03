from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "build-fortnite-semantic-review-ui.yml"


def test_push_materializes_the_numeric_batch_that_changed() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "fortnite-first-review-batch-[0-9][0-9][0-9][0-9].json" in source
    assert ".github/fortnite-semantic-review-trigger" in source
    assert "RESOLVED_BATCH_PATH" in source
    assert 'fetch-depth: 2' in source
    assert 'git diff --name-only "$GITHUB_SHA^" "$GITHUB_SHA"' in source
    assert 'BATCH_INDEX="$(tr -d \'[:space:]\' < .github/fortnite-semantic-review-trigger)"' in source
    assert "resolve_fortnite_review_batch_from_event.py --paths-stdin" in source
    assert 'cp "$RESOLVED_BATCH_PATH" .agent-local/review-ui/review-batch.json' in source
    assert "contents: write" in source
    assert "TRIGGER_REQUESTED=1" in source
    assert "build_fortnite_semantic_review_batch_plan.py" in source
    assert "build_fortnite_semantic_review_progress.py" in source
    assert "fortnite-semantic-review-progress.json" in source
    assert 'git push origin HEAD:main' in source


def test_manual_dispatch_can_prepare_blind_independent_second_review() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "review_mode:" in source
    assert "second_review" in source
    assert "reviewer_id:" in source
    assert "reviewer_type:" in source
    assert 'REVIEW_MODE: ${{ inputs.review_mode || \'first_review\' }}' in source
    assert "prepare_fortnite_semantic_second_review.py" in source
    assert "-name '*-submitted.jsonl'" in source
    assert 'REVIEW_ARGS+=(--existing-reviews "$review_file")' in source
    assert '--reviewer-id "$REVIEWER_ID"' in source
    assert '--reviewer-type "$REVIEWER_TYPE"' in source
    assert 'OFFSET=$(( (BATCH_INDEX - 1) * 25 ))' in source


def test_pull_request_bundle_generation_cannot_persist_a_new_batch() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    pr_block = source.split(
        'if [[ "$GITHUB_EVENT_NAME" == "pull_request" ]]; then',
        1,
    )[1].split(
        'elif [[ "$GITHUB_EVENT_NAME" == "push" ]]; then',
        1,
    )[0]

    assert 'BATCH_INDEX="$(tr -d \'[:space:]\' < .github/fortnite-semantic-review-trigger)"' in pr_block
    assert "TRIGGER_REQUESTED=1" not in pr_block
    assert "git push" not in pr_block
