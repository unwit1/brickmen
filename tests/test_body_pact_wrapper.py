from pathlib import Path

import pytest

from tools.geometry.provider_wrappers.run_pact_arbitrary_input import preflight


def test_pact_wrapper_preflight_requires_upstream_entry_and_exr(tmp_path: Path):
    repo=tmp_path/"PAct"; repo.mkdir()
    (repo/"infer_imgs.py").write_text("# stub\n",encoding="utf-8")
    image=tmp_path/"image.png"; image.write_bytes(b"x")
    mask=tmp_path/"parts.exr"; mask.write_bytes(b"x")
    plan=preflight(repo,image,mask,tmp_path/"out")
    assert plan["entrypoint"]==str((repo/"infer_imgs.py").resolve())
    assert plan["staged_image"].endswith("case_000/brickmen_processed.png")
    assert plan["staged_mask"].endswith("case_000/brickmen_mask.exr")
    assert plan["production_geometry_authority"] is False


def test_pact_wrapper_rejects_non_exr_semantic_mask(tmp_path: Path):
    repo=tmp_path/"PAct"; repo.mkdir()
    (repo/"infer_imgs.py").write_text("# stub\n",encoding="utf-8")
    image=tmp_path/"image.png"; image.write_bytes(b"x")
    mask=tmp_path/"parts.png"; mask.write_bytes(b"x")
    with pytest.raises(ValueError,match="must be an upstream-compatible .exr"):
        preflight(repo,image,mask,tmp_path/"out")
