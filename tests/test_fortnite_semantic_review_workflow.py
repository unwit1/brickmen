from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "build-fortnite-semantic-review-ui.yml"


def test_push_materializes_the_numeric_batch_that_changed() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "fortnite-first-review-batch-[0-9][0-9][0-9][0-9].json" in source
    assert "RESOLVED_BATCH_PATH" in source
    assert "GITHUB_EVENT_PATH" in source
    assert "push changed multiple numeric Fortnite review batches" in source
    assert 'cp "$RESOLVED_BATCH_PATH" .agent-local/review-ui/review-batch.json' in source
