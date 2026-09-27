from pathlib import Path

import pytest

from tools.geometry.provider_wrappers.run_sam3d_objects_baseline import (
    run_sam3d_baseline,
)


def test_sam_wrapper_validates_repo_before_importing_heavy_dependencies(tmp_path: Path):
    image=tmp_path/"image.png"; mask=tmp_path/"mask.png"
    image.write_bytes(b"x"); mask.write_bytes(b"x")
    repo=tmp_path/"sam"; repo.mkdir()
    with pytest.raises(ValueError,match="missing notebook/inference.py"):
        run_sam3d_baseline(
            repo,image,mask,tmp_path/"out.ply",tmp_path/"meta.json"
        )


def test_sam_wrapper_requires_public_quickstart_config_before_import(tmp_path: Path):
    image=tmp_path/"image.png"; mask=tmp_path/"mask.png"
    image.write_bytes(b"x"); mask.write_bytes(b"x")
    repo=tmp_path/"sam"; (repo/"notebook").mkdir(parents=True)
    (repo/"notebook"/"inference.py").write_text("# stub\n",encoding="utf-8")
    with pytest.raises(ValueError,match="config not found"):
        run_sam3d_baseline(
            repo,image,mask,tmp_path/"out.ply",tmp_path/"meta.json"
        )
