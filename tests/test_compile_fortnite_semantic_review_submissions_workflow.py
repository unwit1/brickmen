from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (
    ROOT
    / ".github"
    / "workflows"
    / "compile-fortnite-semantic-review-submissions.yml"
)


def test_submission_compiler_accepts_plain_and_gzip_decision_bundles() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "*-decisions.json.gz" in source
    assert "*-decisions.json" in source
    assert 'DECISION_FILES=("$REVIEW_DIR"/*-decisions.json "$REVIEW_DIR"/*-decisions.json.gz)' in source
    assert r'-decisions\.json(\.gz)?$' in source


def test_submission_compiler_persists_only_generated_review_state() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "build_fortnite_semantic_review_submission.py" in source
    assert "build_fortnite_semantic_review_progress.py" in source
    assert "git add knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/" in source
    assert 'git push origin "HEAD:$GITHUB_REF_NAME"' in source
