import json
from pathlib import Path

import pytest

from tools.geometry.run_body_generation_provider import (
    build_execution_plan,
    execute_plan,
    load_json,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"knowledge"/"libraries"/"lego-minifigure-customs"/"data"


def registry():
    return load_json(BASE/"body-generation-provider-registry.json")


def providers():
    return {p["provider_id"]:p for p in registry()["providers"]}


def job(provider_id):
    return load_json(
        BASE/"provider-jobs"/"brickmen-giant-official-cad-v0"/f"{provider_id}.json"
    )


def fake_repo(tmp_path: Path, provider_id: str) -> Path:
    repo=tmp_path/provider_id
    provider=providers()[provider_id]
    entry=repo/provider["execution"]["entrypoint"]
    entry.parent.mkdir(parents=True)
    entry.write_text("print('fake')\n",encoding="utf-8")
    return repo


def test_partcrafter_plan_uses_architecture_part_count(tmp_path: Path):
    image=tmp_path/"source.png"; image.write_bytes(b"x")
    repo=fake_repo(tmp_path,"partcrafter")
    plan=build_execution_plan(
        job("partcrafter"),providers()["partcrafter"],
        provider_repo=repo,source_image=image,output_dir=tmp_path/"out"
    )
    assert plan["execution_supported"] is True
    assert "--num_parts" in plan["command"]
    i=plan["command"].index("--num_parts")
    assert plan["command"][i+1]=="7"
    assert plan["mode"]=="dry_run"
    assert not (tmp_path/"out").exists()


def test_partpacker_plan_stages_single_image_directory(tmp_path: Path):
    image=tmp_path/"source image.png"; image.write_bytes(b"x")
    repo=fake_repo(tmp_path,"partpacker")
    plan=build_execution_plan(
        job("partpacker"),providers()["partpacker"],
        provider_repo=repo,source_image=image,output_dir=tmp_path/"out"
    )
    assert plan["staging"]["strategy"]=="single_image_directory"
    assert plan["staging"]["staged_path"].endswith("source_image.png")
    assert "--input" in plan["command"]


def test_pact_plan_uses_batch_one_and_glb(tmp_path: Path):
    image=tmp_path/"source.png"; image.write_bytes(b"x")
    repo=fake_repo(tmp_path,"pact")
    plan=build_execution_plan(
        job("pact"),providers()["pact"],
        provider_repo=repo,source_image=image,output_dir=tmp_path/"out"
    )
    assert "--batch_size" in plan["command"]
    assert "1" in plan["command"]
    assert "--save_glb" in plan["command"]
    assert "--export_arti_objects" in plan["command"]


def test_particulate_requires_mesh_and_uses_up_z(tmp_path: Path):
    mesh=tmp_path/"mesh.glb"; mesh.write_bytes(b"x")
    repo=fake_repo(tmp_path,"particulate")
    plan=build_execution_plan(
        job("particulate"),providers()["particulate"],
        provider_repo=repo,input_mesh=mesh,output_dir=tmp_path/"out"
    )
    assert "--input_mesh" in plan["command"]
    assert plan["command"][-2:]==["--up_dir","Z"]


def test_sam_remains_plan_only_without_invented_cli(tmp_path: Path):
    plan=build_execution_plan(
        job("sam_3d_objects"),providers()["sam_3d_objects"],
        provider_repo=None,output_dir=tmp_path/"out"
    )
    assert plan["execution_supported"] is False
    assert plan["mode"]=="plan_only"
    assert plan["command"] is None
    with pytest.raises(ValueError,match="no executable verified adapter"):
        execute_plan(plan)


def test_missing_verified_entrypoint_is_rejected(tmp_path: Path):
    image=tmp_path/"source.png"; image.write_bytes(b"x")
    repo=tmp_path/"empty"; repo.mkdir()
    with pytest.raises(ValueError,match="entrypoint not found"):
        build_execution_plan(
            job("partcrafter"),providers()["partcrafter"],
            provider_repo=repo,source_image=image,output_dir=tmp_path/"out"
        )
