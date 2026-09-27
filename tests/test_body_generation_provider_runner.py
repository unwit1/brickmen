import json
from pathlib import Path

import pytest

from tools.geometry.run_body_generation_provider import (
    build_execution_plan,
    _classify_outputs,
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
    assert "--output_dir" in plan["command"]
    oi=plan["command"].index("--output_dir")
    assert plan["command"][oi+1]==str((tmp_path/"out").resolve())
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


def test_pact_plan_uses_brickmen_dataset_redirect_wrapper(tmp_path: Path):
    image=tmp_path/"image.png"; image.write_bytes(b"x")
    mask=tmp_path/"parts.exr"; mask.write_bytes(b"x")
    repo=fake_repo(tmp_path,"pact")
    plan=build_execution_plan(
        job("pact"),providers()["pact"],
        provider_repo=repo,source_image=image,semantic_mask_exr=mask,
        output_dir=tmp_path/"out"
    )
    assert plan["execution_supported"] is True
    assert plan["adapter_status"]=="runnable_brickmen_dataset_redirect_wrapper_verified"
    assert "run_pact_arbitrary_input.py" in " ".join(plan["command"])
    assert "--semantic-mask-exr" in plan["command"]
    assert str(mask.resolve()) in plan["command"]


def test_particulate_requires_mesh_and_uses_up_z(tmp_path: Path):
    mesh=tmp_path/"mesh.glb"; mesh.write_bytes(b"x")
    repo=fake_repo(tmp_path,"particulate")
    plan=build_execution_plan(
        job("particulate"),providers()["particulate"],
        provider_repo=repo,input_mesh=mesh,output_dir=tmp_path/"out"
    )
    assert "--input_mesh" in plan["command"]
    assert plan["command"][-2:]==["--up_dir","Z"]


def test_sam_visual_baseline_plan_requires_image_mask_and_public_config(tmp_path: Path):
    image=tmp_path/"image.png"; mask=tmp_path/"mask.png"
    image.write_bytes(b"x"); mask.write_bytes(b"x")
    repo=tmp_path/"sam3d"
    (repo/"notebook").mkdir(parents=True)
    (repo/"notebook"/"inference.py").write_text("# stub\n",encoding="utf-8")
    (repo/"checkpoints"/"hf").mkdir(parents=True)
    (repo/"checkpoints"/"hf"/"pipeline.yaml").write_text("stub: true\n",encoding="utf-8")
    plan=build_execution_plan(
        job("sam_3d_objects"),providers()["sam_3d_objects"],
        provider_repo=repo,source_image=image,mask_path=mask,
        output_dir=tmp_path/"out"
    )
    assert plan["execution_supported"] is True
    assert plan["pipeline_stage"]=="baseline_generator"
    assert plan["adapter_status"]=="runnable_brickmen_python_api_visual_baseline"
    assert "--mask" in plan["command"]
    assert str(mask.resolve()) in plan["command"]
    assert str((tmp_path/"out"/"sam3d-splat.ply").resolve()) in plan["command"]
    assert "run_sam3d_objects_baseline.py" in " ".join(plan["command"])


def test_sam_output_classification_is_baseline_not_component_mesh(tmp_path: Path):
    out=tmp_path/"out"; out.mkdir()
    splat=out/"sam3d-splat.ply"; meta=out/"sam3d-metadata.json"
    splat.write_bytes(b"x")
    meta.write_text("{}",encoding="utf-8")
    classified=_classify_outputs("sam_3d_objects",out)
    assert classified["baseline_outputs"]==[str(splat)]
    assert classified["manifest_files"]==[str(meta)]
    assert classified["component_candidates"]==[]


def test_missing_verified_entrypoint_is_rejected(tmp_path: Path):
    image=tmp_path/"source.png"; image.write_bytes(b"x")
    repo=tmp_path/"empty"; repo.mkdir()
    with pytest.raises(ValueError,match="entrypoint not found"):
        build_execution_plan(
            job("partcrafter"),providers()["partcrafter"],
            provider_repo=repo,source_image=image,output_dir=tmp_path/"out"
        )


def test_partcrafter_output_classification_uses_upstream_manifest(tmp_path: Path):
    run=tmp_path/"out"/"tag"
    run.mkdir(parents=True)
    (run/"part_00.glb").write_bytes(b"x")
    (run/"part_01.glb").write_bytes(b"x")
    (run/"object.glb").write_bytes(b"x")
    (run/"manifest.json").write_text(
        json.dumps({
            "parts":[
                {"index":0,"file":"part_00.glb"},
                {"index":1,"file":"part_01.glb"},
            ],
            "composite_file":"object.glb",
        }),
        encoding="utf-8",
    )
    classified=_classify_outputs("partcrafter",tmp_path/"out")
    assert len(classified["component_candidates"])==2
    assert classified["composite_outputs"]==[str(run/"object.glb")]
    assert classified["manifest_files"]==[str(run/"manifest.json")]


def test_partpacker_output_classification_excludes_dual_volumes(tmp_path: Path):
    out=tmp_path/"out"; out.mkdir()
    for name in (
        "source_0_part0.glb","source_0_part1.glb",
        "source_0.glb","source_0_vol0.glb","source_0_vol1.glb",
    ):
        (out/name).write_bytes(b"x")
    classified=_classify_outputs("partpacker",out)
    assert len(classified["component_candidates"])==2
    assert classified["composite_outputs"]==[str(out/"source_0.glb")]
    assert len(classified["auxiliary_outputs"])==2


def test_pact_output_classification_uses_object_manifest(tmp_path: Path):
    root=tmp_path/"out"/"exported_arti_objects"/"case"
    glb=root/"glb"; glb.mkdir(parents=True)
    (glb/"part_0.glb").write_bytes(b"x")
    (glb/"part_1.glb").write_bytes(b"x")
    (root/"object.json").write_text(
        json.dumps({
            "diffuse_tree":[
                {"id":0,"glb":["glb/part_0.glb"],"plys":["ply/part_0.ply"]},
                {"id":1,"glb":["glb/part_1.glb"],"plys":["ply/part_1.ply"]},
            ]
        }),
        encoding="utf-8",
    )
    classified=_classify_outputs("pact",tmp_path/"out")
    assert len(classified["component_candidates"])==2
    assert [r["provider_part_id"] for r in classified["component_records"]]==[
        "part_0","part_1"
    ]
    assert classified["manifest_files"]==[str(root/"object.json")]


def test_partcrafter_component_records_preserve_manifest_indices(tmp_path: Path):
    run=tmp_path/"out"/"tag"; run.mkdir(parents=True)
    (run/"part_03.glb").write_bytes(b"x")
    (run/"object.glb").write_bytes(b"x")
    manifest=run/"manifest.json"
    manifest.write_text(
        json.dumps({
            "parts":[{"index":3,"file":"part_03.glb"}],
            "composite_file":"object.glb",
        }),
        encoding="utf-8",
    )
    classified=_classify_outputs("partcrafter",tmp_path/"out")
    assert classified["component_records"]==[
        {
            "path":str(run/"part_03.glb"),
            "provider_part_id":"part_03",
            "provider_part_index":3,
            "provider_manifest":str(manifest),
            "source_role":"generated_component",
        }
    ]


def test_pact_plan_accepts_lossless_label_png(tmp_path: Path):
    image=tmp_path/"image.png"; image.write_bytes(b"x")
    mask=tmp_path/"parts.png"; mask.write_bytes(b"x")
    repo=fake_repo(tmp_path,"pact")
    plan=build_execution_plan(
        job("pact"),providers()["pact"],
        provider_repo=repo,source_image=image,semantic_mask=mask,
        output_dir=tmp_path/"out"
    )
    assert plan["execution_supported"] is True
    assert "--semantic-mask" in plan["command"]
    assert str(mask.resolve()) in plan["command"]
    assert plan["staging"]["semantic_mask"]==str(mask.resolve())
