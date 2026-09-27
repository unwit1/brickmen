#!/usr/bin/env python3
"""Plan or execute a verified Brickmen 3D-provider wrapper.

Default mode is dry-run. --execute is required to launch upstream provider code.

Supported verified adapters:
- PartCrafter CLI
- PartPacker CLI
- PAct through Brickmen's non-destructive dataset-root redirect wrapper
- Particulate CLI critic
- SAM 3D Objects published Python API through a Brickmen visual-baseline wrapper

Unknown or unverified providers are never guessed.

The wrapper does not install dependencies, download repositories, accept
licenses, or promote generated geometry to manufacturing authority.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
from typing import Any, Mapping


RUNNABLE = {"partcrafter", "partpacker", "pact", "particulate", "sam_3d_objects"}
RUNNABLE_STATUSES = {
    "runnable_cli_verified",
    "runnable_brickmen_python_api_visual_baseline",
    "runnable_brickmen_dataset_redirect_wrapper_verified",
}


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _safe_name(path: str | Path) -> str:
    name = Path(path).name
    return name.replace(" ", "_")


def _require_file(path: str | Path, label: str) -> Path:
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"{label} does not exist or is not a file: {p}")
    return p.resolve()


def _provider_entrypoint(provider: Mapping[str, Any]) -> str:
    execution = provider.get("execution") or {}
    entrypoint = execution.get("entrypoint")
    if not entrypoint:
        raise ValueError(
            f"Provider {provider.get('provider_id')} has no verified execution entrypoint"
        )
    return str(entrypoint)


def build_execution_plan(
    job: Mapping[str, Any],
    provider: Mapping[str, Any],
    *,
    provider_repo: str | Path | None,
    output_dir: str | Path,
    source_image: str | Path | None = None,
    mask_path: str | Path | None = None,
    semantic_mask: str | Path | None = None,
    semantic_mask_exr: str | Path | None = None,
    input_mesh: str | Path | None = None,
    python_executable: str = "python",
) -> dict[str, Any]:
    provider_id = str(job["provider_id"])
    if provider_id != provider.get("provider_id"):
        raise ValueError("Provider job and registry provider_id do not match")

    execution = provider.get("execution") or {}
    status = str(execution.get("adapter_status", "unverified"))
    runnable = provider_id in RUNNABLE and status in RUNNABLE_STATUSES
    out = Path(output_dir).resolve()

    if not runnable:
        return {
            "schema_version": "0.1",
            "provider_id": provider_id,
            "provider_job_id": job["provider_job_id"],
            "mode": "plan_only",
            "execution_supported": False,
            "adapter_status": status,
            "pipeline_stage": provider.get("pipeline_stage"),
            "output_contract": provider.get("output_contract"),
            "command": None,
            "working_directory": (
                str(Path(provider_repo).resolve()) if provider_repo else None
            ),
            "staging": {},
            "output_directory": str(out),
            "reason": (
                "No verified Brickmen CLI adapter exists for this provider. "
                "Use the provider job/guide pack manually or add a verified API adapter."
            ),
            "production_geometry_authority": False,
        }

    if provider_repo is None:
        raise ValueError("--provider-repo is required for runnable providers")
    repo = Path(provider_repo).resolve()
    entrypoint = repo / _provider_entrypoint(provider)
    if not entrypoint.is_file():
        raise ValueError(
            f"Verified provider entrypoint not found: {entrypoint}"
        )

    staging: dict[str, Any] = {}
    command: list[str]

    if provider_id == "partcrafter":
        image_path = _require_file(
            source_image or job.get("source_image") or "",
            "PartCrafter source image",
        )
        native = job.get("native_arguments", {})
        num_parts = int(
            native.get("num_parts")
            or job.get("component_slots", {})
            .get("expected_part_count", {})
            .get("min", 1)
        )
        tag = (
            native.get("tag")
            or job.get("architecture_id")
            or "brickmen"
        )
        command = [
            python_executable,
            str(entrypoint),
            "--image_path",
            str(image_path),
            "--num_parts",
            str(num_parts),
            "--output_dir",
            str(out),
            "--tag",
            str(tag),
            "--render",
        ]
        staging = {
            "source_image": str(image_path),
            "strategy": "direct_file",
        }

    elif provider_id == "partpacker":
        image_path = _require_file(
            source_image or job.get("source_image") or "",
            "PartPacker source image",
        )
        stage_dir = out / "_input_images"
        staged = stage_dir / _safe_name(image_path)
        command = [
            python_executable,
            str(entrypoint),
            "--ckpt_path",
            "pretrained/flow.pt",
            "--input",
            str(stage_dir),
            "--output_dir",
            str(out),
        ]
        staging = {
            "source_image": str(image_path),
            "staging_directory": str(stage_dir),
            "staged_path": str(staged),
            "strategy": "single_image_directory",
        }

    elif provider_id == "pact":
        image_path = _require_file(
            source_image or job.get("source_image") or "",
            "PAct source image",
        )
        semantic_mask_path = _require_file(
            semantic_mask or semantic_mask_exr or "",
            "PAct semantic part mask",
        )
        if semantic_mask_path.suffix.lower() not in {".exr",".png",".tif",".tiff"}:
            raise ValueError(
                "PAct semantic part mask must use .exr, .png, .tif, or .tiff"
            )
        wrapper = (
            Path(__file__).resolve().parent
            / "provider_wrappers"
            / "run_pact_arbitrary_input.py"
        )
        if not wrapper.is_file():
            raise ValueError(f"Brickmen PAct wrapper not found: {wrapper}")
        metadata = out / "brickmen-pact-wrapper.json"
        command = [
            python_executable,
            str(wrapper),
            "--provider-repo",
            str(repo),
            "--image",
            str(image_path),
            "--semantic-mask",
            str(semantic_mask_path),
            "--output-dir",
            str(out),
            "--metadata",
            str(metadata),
        ]
        staging = {
            "source_image": str(image_path),
            "semantic_mask": str(semantic_mask_path),
            "strategy": "wrapper_stages_rgba_and_semantic_label_mask",
        }

    elif provider_id == "sam_3d_objects":
        image_path = _require_file(
            source_image or job.get("source_image") or "",
            "SAM 3D source image",
        )
        mask = _require_file(mask_path or "", "SAM 3D binary mask")
        config = repo / "checkpoints" / "hf" / "pipeline.yaml"
        if not config.is_file():
            raise ValueError(
                "SAM 3D config not found: expected checkpoints/hf/pipeline.yaml"
            )
        wrapper = (
            Path(__file__).resolve().parent
            / "provider_wrappers"
            / "run_sam3d_objects_baseline.py"
        )
        if not wrapper.is_file():
            raise ValueError(f"Brickmen SAM 3D wrapper not found: {wrapper}")
        splat = out / "sam3d-splat.ply"
        metadata = out / "sam3d-metadata.json"
        command = [
            python_executable,
            str(wrapper),
            "--provider-repo",
            str(repo),
            "--image",
            str(image_path),
            "--mask",
            str(mask),
            "--output",
            str(splat),
            "--metadata",
            str(metadata),
            "--config",
            str(config),
        ]
        staging = {
            "source_image": str(image_path),
            "source_mask": str(mask),
            "strategy": "direct_image_and_mask",
        }

    elif provider_id == "particulate":
        mesh = _require_file(input_mesh or "", "Particulate input mesh")
        command = [
            python_executable,
            str(entrypoint),
            "--input_mesh",
            str(mesh),
            "--eval",
            "--output_dir",
            str(out),
            "--up_dir",
            "Z",
        ]
        staging = {
            "input_mesh": str(mesh),
            "strategy": "direct_mesh",
        }

    else:
        raise AssertionError("RUNNABLE set and adapter implementation diverged")

    return {
        "schema_version": "0.1",
        "provider_id": provider_id,
        "provider_job_id": job["provider_job_id"],
        "mode": "dry_run",
        "execution_supported": True,
        "adapter_status": status,
        "pipeline_stage": provider.get("pipeline_stage"),
        "output_contract": provider.get("output_contract"),
        "command": command,
        "working_directory": str(repo),
        "staging": staging,
        "output_directory": str(out),
        "return_code": None,
        "stdout_log": None,
        "stderr_log": None,
        "discovered_outputs": [],
        "production_geometry_authority": False,
        "warning": (
            "Provider output is visual/generated evidence only. Brickmen deterministic "
            "interfaces, collision/DFM checks and physical validation remain required."
        ),
    }


def _stage_inputs(plan: Mapping[str, Any]) -> None:
    staging = plan.get("staging") or {}
    if staging.get("strategy") != "single_image_directory":
        return
    src = Path(staging["source_image"])
    dst = Path(staging["staged_path"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _discover_outputs(output_dir: str | Path) -> list[str]:
    root = Path(output_dir)
    if not root.exists():
        return []
    return sorted(
        str(path)
        for path in root.rglob("*")
        if path.is_file()
        and "_input_images" not in path.parts
        and path.suffix.lower()
        in {".obj", ".glb", ".gltf", ".ply", ".stl", ".fbx", ".json", ".npz"}
    )


def _classify_outputs(
    provider_id: str,
    output_dir: str | Path,
) -> dict[str, Any]:
    root = Path(output_dir)
    all_outputs = _discover_outputs(root)
    result = {
        "component_candidates": [],
        "component_records": [],
        "composite_outputs": [],
        "critic_outputs": [],
        "baseline_outputs": [],
        "auxiliary_outputs": [],
        "manifest_files": [],
        "unclassified_outputs": [],
    }
    if provider_id == "partcrafter":
        manifests = sorted(root.rglob("manifest.json")) if root.exists() else []
        for manifest_path in manifests:
            try:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            result["manifest_files"].append(str(manifest_path))
            parent = manifest_path.parent
            for item in payload.get("parts", []):
                file = parent / str(item.get("file", ""))
                if file.is_file():
                    result["component_candidates"].append(str(file))
                    index=item.get("index")
                    result["component_records"].append({
                        "path":str(file),
                        "provider_part_id":(
                            f"part_{int(index):02d}"
                            if index is not None else file.stem
                        ),
                        "provider_part_index":(
                            int(index) if index is not None else None
                        ),
                        "provider_manifest":str(manifest_path),
                        "source_role":"generated_component",
                    })
            composite = parent / str(payload.get("composite_file", ""))
            if composite.is_file():
                result["composite_outputs"].append(str(composite))
    elif provider_id == "partpacker":
        for path in map(Path, all_outputs):
            name = path.name
            if path.suffix.lower() == ".glb" and "_part" in name:
                result["component_candidates"].append(str(path))
                match=re.search(r"_part(\d+)\.glb$",name)
                result["component_records"].append({
                    "path":str(path),
                    "provider_part_id":(
                        f"part_{int(match.group(1)):02d}"
                        if match else path.stem
                    ),
                    "provider_part_index":(
                        int(match.group(1)) if match else None
                    ),
                    "provider_manifest":None,
                    "source_role":"generated_component",
                })
            elif path.suffix.lower() == ".glb" and (
                "_vol0.glb" in name or "_vol1.glb" in name
            ):
                result["auxiliary_outputs"].append(str(path))
            elif path.suffix.lower() == ".glb":
                result["composite_outputs"].append(str(path))
    elif provider_id == "pact":
        manifests = sorted(root.rglob("object.json")) if root.exists() else []
        seen=set()
        for manifest_path in manifests:
            try:
                payload=json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            result["manifest_files"].append(str(manifest_path))
            parent=manifest_path.parent
            for item in payload.get("diffuse_tree",[]):
                part_id=item.get("id")
                glbs=item.get("glb") or []
                plys=item.get("plys") or []
                candidates=[*glbs,*plys]
                chosen=None
                for rel in candidates:
                    candidate=parent/str(rel)
                    if candidate.is_file():
                        chosen=candidate
                        break
                if chosen is None:
                    continue
                path_str=str(chosen)
                if path_str in seen:
                    continue
                seen.add(path_str)
                result["component_candidates"].append(path_str)
                result["component_records"].append({
                    "path":path_str,
                    "provider_part_id":(
                        f"part_{int(part_id)}"
                        if part_id is not None else chosen.stem
                    ),
                    "provider_part_index":(
                        int(part_id) if part_id is not None else None
                    ),
                    "provider_manifest":str(manifest_path),
                    "source_role":"generated_articulated_component",
                })
        for path in map(Path, all_outputs):
            if str(path) in seen or str(path) in result["manifest_files"]:
                continue
            result["auxiliary_outputs"].append(str(path))
    elif provider_id == "sam_3d_objects":
        for path in map(Path, all_outputs):
            if path.name == "sam3d-splat.ply":
                result["baseline_outputs"].append(str(path))
            elif path.name == "sam3d-metadata.json":
                result["manifest_files"].append(str(path))
            else:
                result["auxiliary_outputs"].append(str(path))
    elif provider_id == "particulate":
        for path in map(Path, all_outputs):
            if (
                path.name.startswith("mesh_parts_with_axes_")
                or path.name.startswith("animated_textured_")
                or path.name in {"pred.obj", "pred.npz"}
            ):
                result["critic_outputs"].append(str(path))
            else:
                result["auxiliary_outputs"].append(str(path))
    else:
        result["unclassified_outputs"] = all_outputs

    classified = set(
        result["component_candidates"]
        + result["composite_outputs"]
        + result["critic_outputs"]
        + result["baseline_outputs"]
        + result["auxiliary_outputs"]
        + result["manifest_files"]
    )
    result["unclassified_outputs"].extend(
        path for path in all_outputs if path not in classified
    )
    for key, values in list(result.items()):
        if key == "component_records":
            by_path = {}
            for item in values:
                path = str(item.get("path", ""))
                if not path:
                    continue
                by_path[path] = item
            result[key] = [by_path[path] for path in sorted(by_path)]
        else:
            result[key] = sorted(set(values))
    return result


def execute_plan(
    plan: Mapping[str, Any],
    *,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    if not plan.get("execution_supported"):
        raise ValueError(
            f"Provider {plan.get('provider_id')} has no executable verified adapter"
        )
    command = plan.get("command")
    if not command:
        raise ValueError("Execution plan has no command")

    output_dir = Path(plan["output_directory"])
    output_dir.mkdir(parents=True, exist_ok=True)
    _stage_inputs(plan)

    completed = subprocess.run(
        list(command),
        cwd=plan["working_directory"],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        env=os.environ.copy(),
    )
    stdout_path = output_dir / "brickmen-provider-stdout.log"
    stderr_path = output_dir / "brickmen-provider-stderr.log"
    stdout_path.write_text(completed.stdout or "", encoding="utf-8")
    stderr_path.write_text(completed.stderr or "", encoding="utf-8")

    result = dict(plan)
    result.update(
        {
            "mode": "executed",
            "return_code": int(completed.returncode),
            "stdout_log": str(stdout_path),
            "stderr_log": str(stderr_path),
            "discovered_outputs": _discover_outputs(output_dir),
            "output_classification": _classify_outputs(
                str(plan.get("provider_id")), output_dir
            ),
            "execution_succeeded": completed.returncode == 0,
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("job")
    parser.add_argument("registry")
    parser.add_argument("--provider-repo", default=None)
    parser.add_argument("--source-image", default=None)
    parser.add_argument("--mask", default=None)
    parser.add_argument("--semantic-mask", default=None)
    parser.add_argument("--semantic-mask-exr", default=None)
    parser.add_argument("--input-mesh", default=None)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--python", default="python")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=None)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    job = load_json(args.job)
    registry = load_json(args.registry)
    providers = {p["provider_id"]: p for p in registry["providers"]}
    if job["provider_id"] not in providers:
        raise SystemExit(f"Provider not present in registry: {job['provider_id']}")

    plan = build_execution_plan(
        job,
        providers[job["provider_id"]],
        provider_repo=args.provider_repo,
        output_dir=args.output_dir,
        source_image=args.source_image,
        mask_path=args.mask,
        semantic_mask=args.semantic_mask,
        semantic_mask_exr=args.semantic_mask_exr,
        input_mesh=args.input_mesh,
        python_executable=args.python,
    )
    result = (
        execute_plan(plan, timeout_seconds=args.timeout_seconds)
        if args.execute
        else plan
    )
    Path(args.report).write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )

    if args.execute and result.get("return_code", 0) != 0:
        return int(result["return_code"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
