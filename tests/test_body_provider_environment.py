from pathlib import Path

from tools.geometry.check_body_provider_environment import (
    check_provider_environment,
)


def provider(pid="partcrafter"):
    return {
        "provider_id":pid,
        "execution":{
            "adapter_status":"runnable_cli_verified",
            "entrypoint":"entry.py",
            "environment":{
                "cuda_required":True,
                "minimum_vram_gb":8,
                "minimum_vram_authority":"upstream_documented_minimum",
            },
        },
        "upstream_verification":{
            "verified_commit_sha":"abc123",
            "interface_files":["entry.py"],
            "version_policy":"exact_verified_revision_preferred_reverify_adapter_on_mismatch",
        },
    }


def test_environment_ready_on_exact_revision_files_modules_and_gpu(tmp_path: Path):
    (tmp_path/"entry.py").write_text("# stub\n",encoding="utf-8")
    result=check_provider_environment(
        provider(),tmp_path,
        detected_git_head="abc123",
        detected_gpus=[{
            "name":"GPU","memory_total_gb_decimal":12,
            "memory_total_mib":11444,"memory_total_gib":11.18,
        }],
        module_status={
            "torch":True,"numpy":True,"trimesh":True,
            "huggingface_hub":True,"PIL":True,
        },
        detect_runtime=False,
    )
    assert result["ready_to_attempt_inference"] is True
    assert result["version"]["status"]=="exact_verified_revision"
    assert result["gpu"]["vram_satisfies_documented_minimum"] is True


def test_revision_mismatch_blocks_attempt(tmp_path: Path):
    (tmp_path/"entry.py").write_text("# stub\n",encoding="utf-8")
    result=check_provider_environment(
        provider(),tmp_path,
        detected_git_head="newer",
        detected_gpus=[{"name":"GPU","memory_total_gb_decimal":12}],
        module_status={
            "torch":True,"numpy":True,"trimesh":True,
            "huggingface_hub":True,"PIL":True,
        },
        detect_runtime=False,
    )
    assert result["ready_to_attempt_inference"] is False
    assert "provider_revision_not_verified" in result["blockers"]


def test_documented_vram_floor_is_not_guessed_when_unknown(tmp_path: Path):
    p=provider("pact")
    p["execution"]["environment"]["minimum_vram_gb"]=None
    p["execution"]["environment"]["minimum_vram_authority"]="not_verified"
    (tmp_path/"entry.py").write_text("# stub\n",encoding="utf-8")
    result=check_provider_environment(
        p,tmp_path,
        detected_git_head="abc123",
        detected_gpus=[{"name":"GPU","memory_total_gb_decimal":6}],
        module_status={
            "torch":True,"numpy":True,"PIL":True,
            "imageio":True,"easydict":True,
        },
        detect_runtime=False,
    )
    assert result["gpu"]["vram_status"]=="minimum_not_verified"
    assert result["gpu"]["vram_satisfies_documented_minimum"] is None
    assert result["ready_to_attempt_inference"] is True
