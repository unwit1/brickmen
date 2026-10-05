from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools/knowledge" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REFERENCES = load_tool("build_minifigure_reference_sets")
SPLITS = load_tool("build_minifigure_training_splits")
COMPILER = load_tool("compile_generation_brief")
RENDERER = load_tool("render_ldraw_pattern_training_views")


def asset(asset_id="a", **overrides):
    return {"sample_id": "sample", "derived_asset_id": asset_id,
            "source_reference_asset_id": "source-" + asset_id, **overrides}


def test_zero_confidence_is_not_replaced_by_defaults():
    low = asset(authority="lego_primary", identity_confidence=0, view_confidence=0,
                segmentation_confidence=0, quality={"identity_confidence": 1})
    high = {**low, "identity_confidence": 1}
    assert REFERENCES.score(high) - REFERENCES.score(low) == 20
    assert REFERENCES.score(asset()) == 0


@pytest.mark.parametrize("component,view,expected", [
    ("head", "left", "head_left"), ("head", None, "head_unknown"),
    ("torso", "right", "torso_right"), ("hips_legs", "back", "hips_legs_rear"),
    ("head", "rear", "head_reverse"), ("helmet", "rear", "mask_or_headgear_rear"),
    ("helmet", None, "mask_or_headgear_unknown"), ("helmet", "left", "mask_or_headgear_side"),
    (None, "front_right_3q", "full_front_3q"),
])
def test_views_are_not_mislabeled_as_front(component, view, expected):
    assert REFERENCES.role(asset(component_type=component, view=view)) == expected


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.1, 1.1, True])
def test_invalid_confidence_is_rejected(value):
    with pytest.raises(ValueError):
        REFERENCES.score(asset(identity_confidence=value))


def test_reference_sets_deduplicate_without_losing_source_occurrences():
    records = [asset("a", view="front", sha256="same"), asset("b", view="front", sha256="same"),
               asset("c", view="front", unresolved_conflicts=["wrong outfit"], authority="lego_primary")]
    output = REFERENCES.build_reference_sets(records + [records[0]])[0]
    slot = output["slots"]["full_front"]
    assert slot["preferred_asset_id"] == "a"
    assert slot["alternate_asset_ids"] == []
    assert slot["occurrence_asset_ids"] == ["a", "b"]
    assert slot["source_reference_asset_id"] == "source-a"
    assert output["asset_count"] == 3
    assert output["unresolved_conflicts"]
    assert "full_rear" in output["missing_roles"]


def test_part_coverage_has_no_minifigure_body_requirements():
    output = REFERENCES.build_reference_sets([asset(view="back")], "part")[0]
    assert output["completeness"]["part_rear"]
    assert set(output["missing_roles"]) == {"part_front", "part_left", "part_right"}


def test_missing_provenance_and_conflicting_ids_fail():
    with pytest.raises(ValueError, match="source_reference_asset_id"):
        REFERENCES.build_reference_sets([{"sample_id": "s", "derived_asset_id": "a"}])
    with pytest.raises(ValueError, match="Conflicting duplicate"):
        REFERENCES.build_reference_sets([asset(view="front"), asset(view="rear")])


def test_duplicate_groups_join_transitively_and_ignore_input_order():
    records = [
        {"derived_asset_id": "a", "outfit_design_id": "A", "sha256": "h1"},
        {"derived_asset_id": "b", "outfit_design_id": "B", "sha256": "h1"},
        {"derived_asset_id": "c", "outfit_design_id": "B", "duplicate_cluster_id": "cluster"},
        {"derived_asset_id": "d", "outfit_design_id": "C", "duplicate_cluster_id": "cluster"},
    ]
    output = SPLITS.build_splits(records)
    assert len({r["component_id"] for r in output}) == 1
    assert len({r["split"] for r in output}) == 1
    assert sorted(output, key=lambda r: r["record_id"]) == sorted(SPLITS.build_splits(records[::-1]), key=lambda r: r["record_id"])


def test_new_occurrence_does_not_move_existing_group():
    a = {"derived_asset_id": "a", "outfit_design_id": "A"}
    b = {"derived_asset_id": "b", "outfit_design_id": "A"}
    assert SPLITS.build_splits([a])[0] == SPLITS.build_splits([a, b])[0]


def test_missing_identity_requires_explicit_fallback():
    records = [{"sample_id": "s", "derived_asset_id": "a"}]
    with pytest.raises(ValueError, match="resolve identity"):
        SPLITS.build_splits(records)
    assert SPLITS.build_splits(records, allow_fallback=True)[0]["used_fallback"] is True


def test_perceptual_similarity_is_not_duplicate_identity():
    records = [{"derived_asset_id": "a", "outfit_design_id": "A", "perceptual_hash": "same"},
               {"derived_asset_id": "b", "outfit_design_id": "B", "perceptual_hash": "same"}]
    assert len({r["component_id"] for r in SPLITS.build_splits(records)}) == 2


def valid_brief(kind="minifigure"):
    brief = COMPILER.new_brief(kind)
    brief["brief_id"] = "synthetic-test-only"
    packet = brief["generation_packet"]
    packet["target_identity"] = {"subject": "original test design", "source_appearance": "test-design-v1",
                                 "incarnation_version": "v1", "outfit": "test uniform", "expression": "neutral", "mask_headgear_state": "none"}
    packet["references"] = [{"reference_id": view, "provenance_id": "test-provenance",
                             "semantic_role": "identity_primary" if view == "front" else "side_reference", "view": view}
                            for view in brief["required_views"]]
    packet["references"].append({"reference_id": "geometry", "semantic_role": "geometry_template", "provenance_id": "test-geometry"})
    packet["critical_features"] = [{"feature": "asymmetric red left sleeve", "priority": "P0", "source_reference_ids": ["front"]}]
    packet["structural_locks"].update({"geometry_profile": "synthetic-test", "geometry_revision": "v1", "pose": "neutral", "camera_view": "front"})
    for part in packet["structural_locks"]["canonical_parts"]:
        part.update({"namespace": "test", "part_id": "test-part-" + part["slot"], "color_id": "test-red", "geometry_revision": "v1"})
    packet.setdefault("official_style", {})["profile"] = "test-style"
    packet.setdefault("mask_translation", {})["route"] = "not_applicable"
    packet["transformation"]["target"] = "test concept"
    packet["rendering"] = {"view": "front", "projection": "orthographic", "lighting": "neutral", "background": "white", "framing": "whole object"}
    return brief


@pytest.mark.parametrize("kind", ["minifigure", "part"])
def test_compilation_is_deterministic_and_provider_neutral(kind):
    brief = valid_brief(kind)
    first = COMPILER.compile_brief(brief)
    assert first == COMPILER.compile_brief(deepcopy(brief))
    report, prompt = first
    assert report["status"] == "ready_for_metadata_review"
    assert report["warnings"]  # No local assets means evidence is still unverified.
    assert report["feature_checklist"][0]["result"] == "unreviewed"
    assert "asymmetric red left sleeve" in prompt
    assert "canonical_part_id" in report["required_output_fields"] if kind == "part" else "canonical_assembly_id" in report["required_output_fields"]


def test_scaffold_does_not_claim_readiness():
    report, prompt = COMPILER.compile_brief(COMPILER.new_brief("minifigure"))
    assert report["status"] == "blocked"
    assert report["errors"]
    assert prompt is None


@pytest.mark.parametrize("mutation,error", [
    (lambda b: b["generation_packet"]["references"].pop(1), "Missing reference view: rear"),
    (lambda b: b["generation_packet"]["critical_features"][0].update(source_reference_ids=["absent"]), "cites missing reference"),
    (lambda b: b["generation_packet"]["structural_locks"]["canonical_parts"].pop(0), "Missing canonical part slot: head"),
    (lambda b: b["generation_packet"]["rendering"].update(view="rear"), "must match"),
    (lambda b: b.update(unresolved_conflicts=["two outfits"]), "Resolve evidence conflicts"),
    (lambda b: b["generation_packet"].update(allowed_changes=["eye"], forbidden_changes=["eye"]), "both allowed and forbidden"),
])
def test_incomplete_or_contradictory_briefs_block(mutation, error):
    brief = valid_brief()
    mutation(brief)
    report, prompt = COMPILER.compile_brief(brief)
    assert any(error in message for message in report["errors"])
    assert prompt is None


def test_local_reference_bytes_are_verified(tmp_path):
    brief = valid_brief()
    path = tmp_path / "reference.txt"
    path.write_text("test reference", encoding="utf-8")
    ref = brief["generation_packet"]["references"][0]
    ref.update(local_path=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    report, _ = COMPILER.compile_brief(brief, base_dir=tmp_path)
    assert report["verified_local_attachments"][0]["reference_id"] == "front"
    path.write_text("changed bytes", encoding="utf-8")
    report, prompt = COMPILER.compile_brief(brief, base_dir=tmp_path)
    assert any("mismatched" in message for message in report["errors"])
    assert prompt is None


def test_cli_clears_stale_prompt_on_blocked_rerun(tmp_path):
    path = tmp_path / "brief.json"
    out = tmp_path / "compiled"
    path.write_text(json.dumps(valid_brief()), encoding="utf-8")
    command = [sys.executable, "-B", str(ROOT / "tools/knowledge/compile_generation_brief.py"), "--input", str(path), "--output-dir", str(out)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (out / "prompt.txt").exists()
    brief = valid_brief()
    brief["generation_packet"]["references"] = []
    path.write_text(json.dumps(brief), encoding="utf-8")
    assert subprocess.run(command, capture_output=True).returncode == 2
    assert not (out / "prompt.txt").exists()
    assert json.loads((out / "preflight.json").read_text())["status"] == "blocked"


def test_render_identity_tracks_source_and_configuration():
    record = {"reference_asset_id": "reference", "sha256": "source-hash"}
    config = {"width": 1024, "library_revision": "library-v1"}
    original = RENDERER.render_identity(record, "physical_like", "front", config)
    assert original != RENDERER.render_identity(record, "physical_like", "front", {**config, "width": 512})
    assert original != RENDERER.render_identity(record, "physical_like", "front", {**config, "library_revision": "library-v2"})


def test_render_manifest_feeds_part_reference_sets(tmp_path, monkeypatch):
    source = tmp_path / "library/parts/test.dat"
    source.parent.mkdir(parents=True)
    source.write_text("0 Synthetic fixture only\n3 16 0 0 0 5 0 0 0 5 0\n", encoding="utf-8")
    executable = tmp_path / "fake-ldview.exe"
    executable.write_bytes(b"test executable identity")
    manifest = tmp_path / "source.jsonl"
    record = {"reference_asset_id": "test-reference", "source_path": "parts/test.dat", "sha256": RENDERER.sha256(source), "license": "CC0"}
    manifest.write_text(json.dumps(record) + "\n", encoding="utf-8")
    output = tmp_path / "renders"
    monkeypatch.setattr(sys, "argv", ["renderer", "--manifest", str(manifest), "--ldraw-root", str(source.parent.parent), "--ldview", str(executable), "--library-revision", "test-library-v1", "--output-dir", str(output), "--profile", "physical_like"])

    def fake_render(exe, source_path, target, *args):
        target.write_bytes(b"synthetic render; no real image or LDView invocation")
        return 0, ""

    monkeypatch.setattr(RENDERER, "render", fake_render)
    assert RENDERER.main() == 0
    records = [json.loads(line) for line in (output / "render_manifest.jsonl").read_text().splitlines()]
    refset = REFERENCES.build_reference_sets(records, "part")[0]
    assert all(refset["completeness"].values())
    source.write_text("0 Changed source", encoding="utf-8")
    assert RENDERER.main() == 2
    assert json.loads((output / "import_report.json").read_text())["failures"] == 1


def test_output_contract_and_target_type_must_agree():
    brief = valid_brief()
    brief["output_contract"] = "print_art"
    report, prompt = COMPILER.compile_brief(brief)
    assert any("target_type" in error for error in report["errors"])
    assert any("production_template" in error for error in report["errors"])
    assert any("production_process" in error for error in report["errors"])
    assert prompt is None


@pytest.mark.parametrize("payload", ["{broken", '{"schema_version": "brickmen-generation-brief/v1", "generation_packet": "wrong-type"}'])
def test_malformed_rerun_clears_stale_prompt(tmp_path, payload):
    path = tmp_path / "brief.json"
    path.write_text(payload, encoding="utf-8")
    out = tmp_path / "compiled"
    out.mkdir()
    (out / "prompt.txt").write_text("old usable prompt", encoding="utf-8")
    command = [sys.executable, "-B", str(ROOT / "tools/knowledge/compile_generation_brief.py"), "--input", str(path), "--output-dir", str(out)]
    assert subprocess.run(command, capture_output=True).returncode == 2
    assert not (out / "prompt.txt").exists()
    assert json.loads((out / "preflight.json").read_text())["status"] == "blocked"


def test_geometry_templates_do_not_replace_missing_appearance_views():
    brief = valid_brief()
    for ref in brief["generation_packet"]["references"]:
        if ref.get("view") in {"rear", "left", "right"}:
            ref["semantic_role"] = "geometry_template"
    report, prompt = COMPILER.compile_brief(brief)
    assert report["status"] == "blocked"
    assert report["view_coverage"]["appearance"] == ["front"]
    assert report["view_coverage"]["geometry"] == ["left", "rear", "right"]
    assert all(f"Missing reference view: {view}" in report["errors"] for view in ("rear", "left", "right"))
    assert prompt is None


@pytest.mark.parametrize("field", ["part_id", "slot", "namespace", "geometry_revision"])
def test_part_identity_fields_cannot_be_lists(field):
    brief = valid_brief()
    brief["generation_packet"]["structural_locks"]["canonical_parts"][0][field] = ["ambiguous", "identity"]
    report, prompt = COMPILER.compile_brief(brief)
    assert report["status"] == "blocked"
    assert prompt is None


@pytest.mark.parametrize("field,value", [("view", ["front"]), ("local_path", ["asset.png"]), ("provenance_id", ["source"]), ("reference_id", {"id": "source"})])
def test_malformed_reference_fields_return_blocked_api_results(field, value):
    brief = valid_brief()
    brief["generation_packet"]["references"][0][field] = value
    report, prompt = COMPILER.compile_brief(brief)
    assert report["status"] == "blocked"
    assert report["errors"]
    assert prompt is None


def test_dependency_snapshot_tracks_changed_child_bytes_and_enforces_pins(tmp_path):
    root = tmp_path / "ldraw"
    parts = root / "parts"
    parts.mkdir(parents=True)
    parent = parts / "parent.dat"
    child = parts / "child.dat"
    parent.write_bytes(b"0 Parent\n1 16 0 0 0 1 0 0 0 1 0 0 0 1 child.dat\n")
    child.write_bytes(b"0 Child\n3 16 0 0 0 5 0 0 0 5 0\n")
    record = {"source_path": "parts/parent.dat", "reference_asset_id": "parent", "sha256": RENDERER.sha256(parent)}
    dependencies, original = RENDERER.dependency_snapshot(root, record)
    assert len(dependencies) == 2
    pinned = {**record, "dependencies_sha256": original}
    assert RENDERER.dependency_snapshot(root, pinned)[1] == original
    child.write_bytes(child.read_bytes().replace(b"5 0 0", b"6 0 0"))
    assert RENDERER.sha256(parent) == record["sha256"]
    assert RENDERER.dependency_snapshot(root, record)[1] != original
    with pytest.raises(ValueError, match="pinned"):
        RENDERER.dependency_snapshot(root, pinned)
    child.unlink()
    with pytest.raises(FileNotFoundError):
        RENDERER.dependency_snapshot(root, record)


def test_render_dependencies_cannot_escape_declared_library(tmp_path):
    from tools.knowledge.render_ldraw_pattern_training_views import dependency_snapshot
    library = tmp_path / "library"
    library.mkdir()
    (tmp_path / "outside.dat").write_text("3 16 0 0 0 1 0 0 0 1 0\n")
    (library / "parent.dat").write_text("1 16 0 0 0 1 0 0 0 1 0 0 0 1 ../outside.dat\n")
    with pytest.raises(ValueError, match="outside library"):
        dependency_snapshot(library, {"source_path": "parent.dat"})


@pytest.mark.parametrize("mutation,error", [
    (lambda p: (p["transformation"].update(change_only=["change geometry"]), p.update(forbidden_changes=["change geometry"])), "contradicts"),
    (lambda p: p["transformation"].update(change_only="change geometry"), "list of resolved strings"),
    (lambda p: p["references"][1].update(unresolved_conflicts=["wrong outfit"]), "unresolved conflicts"),
    (lambda p: p["references"][1].update(source_appearance="another outfit"), "different source appearance"),
    (lambda p: p["critical_features"][0].update(source_reference_ids=["geometry"]), "lacks appearance evidence"),
])
def test_explicit_conflicts_and_geometry_only_appearance_claims_block(mutation, error):
    brief = valid_brief()
    mutation(brief["generation_packet"])
    report, prompt = COMPILER.compile_brief(brief)
    assert any(error in e for e in report["errors"])
    assert prompt is None


def print_brief():
    brief = valid_brief()
    brief["output_contract"] = "print_art"
    packet = brief["generation_packet"]
    packet["output"].update(target_type="torso_front", production_process="UV", dimensions_or_aspect="synthetic fixture", dimensions_mm={"width": 12.0, "height": 15.0}, template_revision="test-template-v1")
    packet["structural_locks"]["template_boundaries"] = ["test safe zone"]
    packet["references"].append({"reference_id": "production", "semantic_role": "production_template", "provenance_id": "synthetic test only", "scale_status": "calibrated", "calibration_provenance_id": "test-calibration", "template_revision": "test-template-v1"})
    return brief


@pytest.mark.parametrize("mutation,error", [
    (lambda p: p["output"].pop("dimensions_mm"), "positive finite dimensions_mm"),
    (lambda p: p["output"].update(dimensions_mm={"width": 0, "height": -3}), "positive finite dimensions_mm"),
    (lambda p: p["structural_locks"].update(template_boundaries=[None]), "resolved surface constraints"),
    (lambda p: p["structural_locks"].update(template_boundaries=["unknown"]), "resolved surface constraints"),
    (lambda p: p["references"][-1].update(scale_status="unknown"), "must be calibrated"),
    (lambda p: p["references"][-1].update(template_revision="old-v0"), "revision must match"),
])
def test_print_brief_requires_resolved_scale_and_template(mutation, error):
    brief = print_brief()
    mutation(brief["generation_packet"])
    report, prompt = COMPILER.compile_brief(brief)
    assert any(error in e for e in report["errors"])
    assert prompt is None


def test_prompt_contains_selected_contract_policies():
    report, prompt = COMPILER.compile_brief(print_brief())
    assert report["status"] == "ready_for_metadata_review"
    assert "WHITE" in prompt and "keepout_check" in prompt
    assert "template scale unknown" in prompt and "first physical prototype" in prompt
    brief = valid_brief("part")
    brief["output_contract"] = "resin_concept"
    brief["generation_packet"]["output"]["target_type"] = "new_part_concept"
    report, prompt = COMPILER.compile_brief(brief)
    assert report["status"] == "ready_for_metadata_review"
    assert "concept mesh is nonfunctional until connector engineering/validation" in prompt
