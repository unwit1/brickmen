import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_repo", ROOT / "tools/validate_repo.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def test_repository_integrity():
    report = VALIDATOR.validate(ROOT)
    assert not report["errors"], report


def test_missing_workflow_tool_and_invalid_backlog_pointer_are_reported(tmp_path):
    workflow = tmp_path / ".github/workflows/fixture.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("run: python tools/knowledge/missing.py", encoding="utf-8")
    data = tmp_path / "knowledge/libraries/lego-minifigure-customs/data"
    data.mkdir(parents=True)
    (data / "target.json").write_text('{"records":{}}', encoding="utf-8")
    (data / "alias.json").write_text(json.dumps({"record_ref": "target.json#/records/missing"}), encoding="utf-8")
    report = VALIDATOR.validate(tmp_path)
    assert len(report["errors"]) == 2
    assert any("missing tool" in error for error in report["errors"])
