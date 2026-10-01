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
    assert 'git push origin HEAD:main' in source
