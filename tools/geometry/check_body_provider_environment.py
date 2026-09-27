#!/usr/bin/env python3
"""Preflight a local external 3D-provider environment without loading model weights."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Mapping


PYTHON_MODULES={
    "partcrafter":["torch","numpy","trimesh","huggingface_hub","PIL"],
    "partpacker":["torch","numpy","cv2","trimesh","rembg"],
    "pact":["torch","numpy","PIL","imageio","easydict"],
    "particulate":["torch","numpy","trimesh","omegaconf","huggingface_hub"],
    "sam_3d_objects":["torch","numpy","PIL"],
}

RUNTIME_FILES={
    "partpacker":["pretrained/flow.pt"],
    "sam_3d_objects":["checkpoints/hf/pipeline.yaml"],
}


def load_json(path: str | Path) -> dict[str,Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def detect_git_head(repo: Path) -> str | None:
    if not (repo/".git").exists() or shutil.which("git") is None:
        return None
    try:
        completed=subprocess.run(
            ["git","-C",str(repo),"rev-parse","HEAD"],
            check=False,capture_output=True,text=True,timeout=10,
        )
    except Exception:
        return None
    if completed.returncode!=0:
        return None
    value=(completed.stdout or "").strip()
    return value or None


def detect_gpus() -> list[dict[str,Any]]:
    exe=shutil.which("nvidia-smi")
    if not exe:
        return []
    try:
        completed=subprocess.run(
            [
                exe,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=False,capture_output=True,text=True,timeout=10,
        )
    except Exception:
        return []
    if completed.returncode!=0:
        return []
    out=[]
    for raw in (completed.stdout or "").splitlines():
        fields=[x.strip() for x in raw.split(",")]
        if len(fields)<2:
            continue
        try:
            mib=float(fields[-1])
        except ValueError:
            continue
        out.append({
            "name":",".join(fields[:-1]).strip(),
            "memory_total_mib":mib,
            "memory_total_gb_decimal":mib*1024*1024/1_000_000_000,
            "memory_total_gib":mib/1024,
        })
    return out


def _module_status(
    names: list[str],
    *,
    python_executable: str | None=None,
) -> dict[str,bool]:
    python_executable=python_executable or sys.executable
    if not names:
        return {}
    code=(
        "import importlib.util,json;"
        "names="+repr(names)+";"
        "print(json.dumps({n:importlib.util.find_spec(n) is not None for n in names}))"
    )
    try:
        completed=subprocess.run(
            [python_executable,"-c",code],
            check=False,capture_output=True,text=True,timeout=20,
        )
        if completed.returncode==0:
            payload=json.loads((completed.stdout or "{}").strip() or "{}")
            return {name:bool(payload.get(name)) for name in names}
    except Exception:
        pass
    # Fallback is valid only for the current interpreter.
    if python_executable in {sys.executable,"python","python3"}:
        return {
            name:importlib.util.find_spec(name) is not None
            for name in names
        }
    return {name:False for name in names}


def check_provider_environment(
    provider: Mapping[str,Any],
    provider_repo: str | Path,
    *,
    detected_git_head: str | None=None,
    detected_gpus: list[dict[str,Any]] | None=None,
    module_status: Mapping[str,bool] | None=None,
    python_executable: str | None=None,
    detect_runtime: bool=True,
) -> dict[str,Any]:
    pid=str(provider["provider_id"])
    repo=Path(provider_repo).resolve()
    execution=provider.get("execution") or {}
    verification=provider.get("upstream_verification") or {}
    environment=execution.get("environment") or {}

    if detected_git_head is None and detect_runtime:
        detected_git_head=detect_git_head(repo)
    if detected_gpus is None:
        detected_gpus=detect_gpus() if detect_runtime else []
    modules=PYTHON_MODULES.get(pid,[])
    if module_status is None:
        module_status=_module_status(
            modules,python_executable=python_executable
        ) if detect_runtime else {
            name:False for name in modules
        }

    expected_sha=verification.get("verified_commit_sha")
    if not expected_sha:
        version_status="no_verified_revision_recorded"
        version_match=False
    elif detected_git_head is None:
        version_status="git_revision_unavailable"
        version_match=False
    elif str(detected_git_head)==str(expected_sha):
        version_status="exact_verified_revision"
        version_match=True
    else:
        version_status="revision_mismatch_reverification_required"
        version_match=False

    interface_files=list(verification.get("interface_files") or [])
    entrypoint=execution.get("entrypoint")
    if entrypoint and entrypoint not in interface_files:
        interface_files.append(str(entrypoint))
    runtime_files=RUNTIME_FILES.get(pid,[])
    file_status={
        rel:(repo/rel).is_file()
        for rel in [*interface_files,*runtime_files]
    }
    interface_ok=all(
        file_status.get(rel,False) for rel in interface_files
    ) if interface_files else bool(entrypoint and (repo/str(entrypoint)).is_file())
    runtime_files_ok=all(
        file_status.get(rel,False) for rel in runtime_files
    )

    modules_ok=all(bool(module_status.get(name)) for name in modules)
    cuda_required=bool(environment.get("cuda_required",False))
    gpu_visible=bool(detected_gpus)
    min_vram=environment.get("minimum_vram_gb")
    if min_vram is None:
        vram_status="minimum_not_verified"
        vram_satisfies=None
    elif not detected_gpus:
        vram_status="no_gpu_visible"
        vram_satisfies=False
    else:
        best=max(float(g.get("memory_total_gb_decimal",0)) for g in detected_gpus)
        vram_satisfies=best>=float(min_vram)
        vram_status=(
            "documented_minimum_satisfied"
            if vram_satisfies else "below_documented_minimum"
        )

    gpu_ok=(
        True
        if not cuda_required
        else gpu_visible and (vram_satisfies is not False)
    )
    ready=bool(
        repo.is_dir()
        and version_match
        and interface_ok
        and runtime_files_ok
        and modules_ok
        and gpu_ok
    )
    blockers=[]
    if not repo.is_dir(): blockers.append("provider_repo_missing")
    if not version_match: blockers.append("provider_revision_not_verified")
    if not interface_ok: blockers.append("verified_interface_files_missing")
    if not runtime_files_ok: blockers.append("required_runtime_files_missing")
    if not modules_ok: blockers.append("python_dependencies_missing")
    if not gpu_ok: blockers.append("gpu_environment_not_ready")

    return {
        "schema_version":"0.1",
        "provider_id":pid,
        "provider_repo":str(repo),
        "adapter_status":execution.get("adapter_status"),
        "version":{
            "expected_verified_commit_sha":expected_sha,
            "detected_commit_sha":detected_git_head,
            "status":version_status,
            "exact_match":version_match,
            "version_policy":verification.get("version_policy"),
        },
        "files":{
            "interface_files":interface_files,
            "runtime_files":runtime_files,
            "status_by_relative_path":file_status,
            "interface_files_ready":interface_ok,
            "runtime_files_ready":runtime_files_ok,
        },
        "python_modules":{
            "python_executable":python_executable or sys.executable,
            "required":modules,
            "status":dict(module_status),
            "all_available":modules_ok,
            "note":"Checks module discoverability only; it does not import or initialize models.",
        },
        "gpu":{
            "cuda_required":cuda_required,
            "visible_gpus":detected_gpus,
            "gpu_visible":gpu_visible,
            "documented_minimum_vram_gb":min_vram,
            "minimum_vram_authority":environment.get(
                "minimum_vram_authority"
            ),
            "vram_status":vram_status,
            "vram_satisfies_documented_minimum":vram_satisfies,
        },
        "ready_to_attempt_inference":ready,
        "blockers":blockers,
        "warning":(
            "Environment readiness means Brickmen can attempt the verified inference "
            "interface. It does not establish model quality, output validity, licensing "
            "fitness for a specific use, or production geometry authority."
        ),
        "production_geometry_authority":False,
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("registry")
    parser.add_argument("provider_id")
    parser.add_argument("provider_repo")
    parser.add_argument("--python",default=sys.executable)
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    registry=load_json(args.registry)
    providers={p["provider_id"]:p for p in registry.get("providers",[])}
    if args.provider_id not in providers:
        raise SystemExit(f"Unknown provider: {args.provider_id}")
    result=check_provider_environment(
        providers[args.provider_id],args.provider_repo,
        python_executable=args.python,
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0 if result["ready_to_attempt_inference"] else 2


if __name__=="__main__":
    raise SystemExit(main())
