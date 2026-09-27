from pathlib import Path

import pytest

from tools.geometry.ingest_ldraw_geometry import (
    LDU_TO_MM,
    flatten_ldraw,
    manifest_without_geometry,
    obj_from_triangles,
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def synthetic_library(tmp_path: Path) -> Path:
    root = tmp_path / "ldraw"
    write(
        root / "parts" / "root.dat",
        """0 Synthetic Root
0 Name: root.dat
0 Author: Test Author
0 !LDRAW_ORG Part
0 !LICENSE Licensed under CC BY 4.0 : see CAreadme.txt
0 BFC CERTIFY CCW
1 16 10 20 30 1 0 0 0 1 0 0 0 1 s\\child.dat
4 16 0 0 0 10 0 0 10 10 0 0 10 0
""",
    )
    write(
        root / "parts" / "s" / "child.dat",
        """0 ~Synthetic Child
0 Name: s/child.dat
0 Author: Child Author
0 !LDRAW_ORG Subpart
0 !LICENSE Redistributable under CCAL version 2.0 : see CAreadme.txt
0 BFC CERTIFY CCW
3 16 0 0 0 5 0 0 0 5 0
""",
    )
    return root


def test_recursive_subfile_transform_and_quad_triangulation(tmp_path):
    root = synthetic_library(tmp_path)
    result = flatten_ldraw(root, "root.dat")

    assert result["triangle_count"] == 3
    assert result["source_file_count"] == 2
    assert result["unresolved_references"] == []

    points = [p for tri in result["triangles_ldu"] for p in tri]
    assert (10.0, 20.0, 30.0) in points
    assert (15.0, 20.0, 30.0) in points
    assert result["bbox_ldu"]["max"][2] == pytest.approx(30.0)
    assert result["bbox_nominal_mm"]["max"][2] == pytest.approx(30.0 * LDU_TO_MM)


def test_manifest_preserves_per_file_license_and_hash(tmp_path):
    root = synthetic_library(tmp_path)
    result = manifest_without_geometry(flatten_ldraw(root, "root.dat"))

    deps = {item["path"]: item for item in result["dependencies"]}
    assert "CC BY 4.0" in deps["parts/root.dat"]["metadata"]["license"]
    assert "CCAL version 2.0" in deps["parts/s/child.dat"]["metadata"]["license"]
    assert len(deps["parts/root.dat"]["sha256"]) == 64
    assert "triangles_ldu" not in result


def test_missing_dependency_is_strict_by_default(tmp_path):
    root = tmp_path / "ldraw"
    write(
        root / "parts" / "broken.dat",
        "0 Broken\n1 16 0 0 0 1 0 0 0 1 0 0 0 1 missing.dat\n",
    )
    with pytest.raises(FileNotFoundError):
        flatten_ldraw(root, "broken.dat")

    result = flatten_ldraw(root, "broken.dat", strict_missing=False)
    assert result["unresolved_references"][0]["reference"] == "missing.dat"


def test_obj_export_deduplicates_shared_vertices(tmp_path):
    root = synthetic_library(tmp_path)
    result = flatten_ldraw(root, "root.dat")
    payload = obj_from_triangles(result["triangles_ldu"], scale=LDU_TO_MM)

    assert payload.count("\nv ") < result["triangle_count"] * 3
    assert payload.count("\nf ") == result["triangle_count"]
