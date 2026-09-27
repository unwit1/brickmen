from pathlib import Path

from tools.geometry.fit_body_skeleton_batch import run_manifest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "knowledge"
    / "libraries"
    / "lego-minifigure-customs"
    / "data"
    / "reference-landmarks"
    / "manifest.json"
)


def test_seed_reference_manifest_runs():
    result = run_manifest(MANIFEST)
    assert result["result_count"] >= 5
    assert result["production_geometry_authority"] is False
    ids = {item["reference_id"] for item in result["results"]}
    assert "alpha_af325_venom_front_seed" in ids
    assert "lego_sh0371_hulk_front_seed" in ids
