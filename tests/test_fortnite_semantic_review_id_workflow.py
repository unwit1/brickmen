from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "canonicalize-fortnite-semantic-review-ids.yml"


def test_review_id_workflow_is_fail_safe_and_reusable() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "contents: write" in source
    assert "canonicalize_fortnite_semantic_review_ids.py" in source
    assert "fortnite-first-review-batch-*-gpt56sol-submitted.jsonl" in source
    assert 'if git diff --quiet' in source
    assert "git pull --rebase origin main" in source
    assert "git push origin HEAD:main" in source
