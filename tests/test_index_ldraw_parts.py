"""Synthetic catalog and rendering integration fixtures, not accuracy evidence."""
import hashlib
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.knowledge import index_ldraw_minifig_patterns as INDEX
from tools.knowledge import render_ldraw_pattern_training_views as RENDER


def part(root, name, description, kind="Part", extra="", newline="\n"):
    path = root / "parts" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (f"0 {description}\n0 Name: {name}\n0 Author: Synthetic fixture\n"
           f"0 !LDRAW_ORG {kind}\n0 !LICENSE CC0\n{extra}"
           "3 16 0 0 0 1 0 0 0 1 0\n").replace("\n", newline).encode()
    path.write_bytes(raw)
    return path


def args(root, out, catalog="minifig_patterns"):
    return ["--ldraw-root", str(root), "--output-dir", str(out), "--catalog", catalog]


def records(out):
    report = json.loads((out / "import_report.json").read_text())
    return report, [json.loads(line) for line in Path(report["manifest"]).read_text().splitlines()]


@pytest.mark.parametrize("catalog,expected", [
    ("minifig_patterns", {"face"}),
    ("patterned_parts", {"face", "tile", "torso"}),
    ("all_parts", {"face", "tile", "torso", "brick", "assembly"}),
])
def test_catalog_selection_preserves_default_and_excludes_fragments(tmp_path, catalog, expected):
    root = tmp_path / "library"
    for name, desc, kind in [
        ("face", "Minifig Head with Smile Pattern", "Part"),
        ("tile", "Tile with Printed Map", "Part"),
        ("torso", "Torso Pattern", "Unofficial_Part"),
        ("brick", "Brick 2 x 4", "Part"),
        ("assembly", "Wheel Assembly", "Shortcut"),
        ("fragment", "Tile Pattern Fragment", "Subpart"),
        ("primitive", "Pattern Primitive", "48_Primitive"),
        ("unknown", "Tile Pattern", ""),
    ]:
        part(root, name + ".DAT", desc, kind)
    out = tmp_path / "out"
    assert INDEX.main(args(root, out, catalog)) == 0
    report, entries = records(out)
    assert {r["part_id"] for r in entries} == expected
    assert Path(report["manifest"]).name == INDEX.CATALOG_FILES[catalog]
    assert all(r["part_namespace"] == "ldraw" and r["authority"] == "community_structured" for r in entries)
    assert all(r["render_status"] == "not_requested" for r in entries)


def test_exact_bytes_header_category_and_legacy_identity(tmp_path):
    root = tmp_path / "library"
    path = part(root, "3626p-test.dat", "Minifig Head with Test Pattern", extra="0 !CATEGORY Minifig Head\n0 !KEYWORDS first, second\n", newline="\r\n")
    raw = path.read_bytes()
    header = INDEX.parse_header(path, raw)
    path.write_bytes(b"changed after capture")
    assert INDEX.parse_header(path, raw) == header
    path.write_bytes(raw)
    out = tmp_path / "out"
    INDEX.main(args(root, out))
    _, entries = records(out)
    row = entries[0]
    digest = hashlib.sha256(raw).hexdigest()
    assert row["sha256"] == digest
    assert row["reference_asset_id"] == f"ldraw-3626p-test-{digest[:16]}"
    assert row["category"] == "Minifig Head" and row["category_source"] == "header"
    assert row["keywords"] == ["first", "second"]
    assert row["license"] == "!LICENSE CC0"


def test_geometry_comments_do_not_override_catalog_header(tmp_path):
    root = tmp_path / "library"
    path = part(root, "brick.dat", "Brick", extra="\n")
    path.write_bytes(path.read_bytes() + b"0 !CATEGORY Invented\n0 !LDRAW_ORG Subpart\n")
    header = INDEX.parse_header(path)
    assert header["category"] == "" and header["part_type"] == "Part"


@pytest.mark.parametrize("write_output,expected_status", [(True, "rendered"), (False, "error")])
def test_preview_uses_shared_inventory_and_rejects_stale_images(tmp_path, monkeypatch, capsys, write_output, expected_status):
    root = tmp_path / "library"
    path = part(root, "tile.dat", "Tile with Pattern")
    # Untrusted Name header cannot control the output directory.
    path.write_bytes(path.read_bytes().replace(b"Name: tile.dat", b"Name: ../../escape.dat"))
    exe = tmp_path / "renderer.exe"
    exe.write_bytes(b"synthetic renderer fixture")
    out = tmp_path / "out"
    stale = out / "previews/tile.png"
    stale.parent.mkdir(parents=True)
    Image.new("RGBA", (8, 8)).save(stale)
    calls = []

    def fake_render(exe, source, target, lat, lon, width, height, edges, zoom, library, settings):
        calls.append(target)
        assert library == root and not edges and (lat, lon) == (0, 0)
        assert target.resolve().is_relative_to(out.resolve())
        if write_output:
            Image.new("RGBA", (width, height), "red").save(target)
        return 0, "synthetic fixture"

    monkeypatch.setattr(RENDER, "render", fake_render)
    result = INDEX.main(args(root, out, "patterned_parts") + [
        "--ldview", str(exe), "--library-revision", "synthetic-library",
        "--render-width", "8", "--render-height", "8"])
    report, entries = records(out)
    assert result == (0 if write_output else 2)
    assert len(calls) == 1 and entries[0]["render_status"] == expected_status
    assert json.loads(capsys.readouterr().out)["catalog"] == "patterned_parts"
    if write_output:
        rendered = [json.loads(line) for line in Path(report["render_manifest"]).read_text().splitlines()]
        assert rendered[0]["view"] == "front"
        assert rendered[0]["geometry_dependencies"][0]["path"] == "parts/tile.dat"
        assert entries[0]["preview_sha256"] == rendered[0]["sha256"]
        assert entries[0]["preview_path"] != str(stale)
    else:
        assert entries[0]["preview_path"] is None
        assert Path(report["render_manifest"]).read_text() == ""


def test_preview_rejects_changed_child_after_rendering(tmp_path, monkeypatch):
    root = tmp_path / "library"
    child = part(root, "s/child.dat", "Fragment", "Subpart")
    parent = part(root, "tile.dat", "Tile Pattern")
    parent.write_bytes(parent.read_bytes() + b"1 16 0 0 0 1 0 0 0 1 0 0 0 1 s/child.dat\n")
    exe = tmp_path / "renderer.exe"
    exe.write_bytes(b"fixture")

    def fake_render(exe, source, target, lat, lon, width, height, *rest):
        Image.new("RGBA", (width, height)).save(target)
        child.write_bytes(child.read_bytes() + b"0 changed\n")
        return 0, ""

    monkeypatch.setattr(RENDER, "render", fake_render)
    out = tmp_path / "out"
    assert INDEX.main(args(root, out, "all_parts") + ["--ldview", str(exe), "--library-revision", "fixture"]) == 2
    _, entries = records(out)
    assert entries[0]["preview_path"] is None and entries[0]["render_status"] == "error"


def test_preview_requires_revision_before_writing_output(tmp_path):
    root = tmp_path / "library"
    part(root, "tile.dat", "Tile Pattern")
    exe = tmp_path / "renderer.exe"
    exe.write_bytes(b"fixture")
    out = tmp_path / "out"
    with pytest.raises(SystemExit) as exc:
        INDEX.main(args(root, out) + ["--ldview", str(exe)])
    assert exc.value.code == 2 and not out.exists()


def test_duplicate_views_rejected_before_render(tmp_path):
    with pytest.raises(SystemExit) as exc:
        RENDER.main(["--manifest", "unused", "--ldraw-root", str(tmp_path), "--ldview", "unused",
                     "--library-revision", "fixture", "--output-dir", str(tmp_path / "out"),
                     "--view", "front", "--view", "front"], quiet=True)
    assert exc.value.code == 2 and not (tmp_path / "out").exists()


def test_duplicate_asset_ids_cannot_silently_cross_link_previews(tmp_path):
    root = tmp_path / "library"
    path = part(root, "tile.dat", "Tile Pattern")
    duplicate = root / "parts/alternate/tile.dat"
    duplicate.parent.mkdir()
    duplicate.write_bytes(path.read_bytes())
    out = tmp_path / "out"
    with pytest.raises(SystemExit) as exc:
        INDEX.main(args(root, out, "all_parts"))
    assert exc.value.code == 2 and not (out / "ldraw_parts.jsonl").exists()
