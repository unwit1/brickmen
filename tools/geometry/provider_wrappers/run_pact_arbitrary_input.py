#!/usr/bin/env python3
"""Run PAct on an arbitrary Brickmen image + semantic part mask without editing PAct.

Current upstream infer_imgs.py parses --data_dir but constructs
ImageConditioned_dataset("assets/real_world_examples") directly. This wrapper
redirects only that dataset constructor in-process, then executes the published
upstream script unchanged.

Input contract:
- image: any PIL-readable image; staged as RGBA *_processed.png
- semantic mask: upstream-compatible EXR semantic-part mask, copied as *_mask.exr

The semantic mask must follow PAct's own label convention. Brickmen does not
invent or relabel part IDs here.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
from typing import Any


def preflight(
    provider_repo: str | Path,
    image: str | Path,
    semantic_mask_exr: str | Path,
    output_dir: str | Path,
) -> dict[str,Any]:
    repo=Path(provider_repo).resolve()
    entry=repo/"infer_imgs.py"
    if not entry.is_file():
        raise ValueError(f"PAct infer_imgs.py not found: {entry}")
    image_path=Path(image).resolve()
    if not image_path.is_file():
        raise ValueError(f"PAct image not found: {image_path}")
    mask=Path(semantic_mask_exr).resolve()
    if not mask.is_file():
        raise ValueError(f"PAct semantic mask not found: {mask}")
    if mask.suffix.lower()!=".exr":
        raise ValueError(
            "PAct semantic part mask must be an upstream-compatible .exr file"
        )
    out=Path(output_dir).resolve()
    stage=out/"_brickmen_pact_input"
    case=stage/"case_000"
    return {
        "provider_repo":str(repo),
        "entrypoint":str(entry),
        "source_image":str(image_path),
        "semantic_mask_exr":str(mask),
        "output_dir":str(out),
        "stage_root":str(stage),
        "stage_case":str(case),
        "staged_image":str(case/"brickmen_processed.png"),
        "staged_mask":str(case/"brickmen_mask.exr"),
        "production_geometry_authority":False,
    }


def stage_inputs(plan: dict[str,Any]) -> None:
    # PIL is an upstream PAct dependency; import it only for actual execution so
    # Brickmen preflight/tests remain dependency-free.
    from PIL import Image

    case=Path(plan["stage_case"])
    case.mkdir(parents=True,exist_ok=True)
    with Image.open(plan["source_image"]) as image:
        image.convert("RGBA").save(plan["staged_image"])
    shutil.copy2(plan["semantic_mask_exr"],plan["staged_mask"])


def run_pact(
    provider_repo: str | Path,
    image: str | Path,
    semantic_mask_exr: str | Path,
    output_dir: str | Path,
    *,
    model: str="PAct000/PAct",
    revision: str="main",
) -> dict[str,Any]:
    plan=preflight(provider_repo,image,semantic_mask_exr,output_dir)
    stage_inputs(plan)
    repo=Path(plan["provider_repo"])
    entry=Path(plan["entrypoint"])
    out=Path(plan["output_dir"])
    out.mkdir(parents=True,exist_ok=True)

    sys.path.insert(0,str(repo))
    old_cwd=Path.cwd()
    old_argv=list(sys.argv)
    original_dataset=None
    try:
        os.chdir(repo)
        from modules.pact import datasets

        original_dataset=datasets.ImageConditioned_dataset
        stage_root=plan["stage_root"]

        class BrickmenRedirectDataset(original_dataset):
            def __init__(self, roots, *args, **kwargs):
                super().__init__(stage_root,*args,**kwargs)

        datasets.ImageConditioned_dataset=BrickmenRedirectDataset
        sys.argv=[
            str(entry),
            "--data_dir",stage_root,
            "--outdir",str(out),
            "--batch_size","1",
            "--save_glb",
            "--export_arti_objects",
            "--model",model,
            "--revision",revision,
        ]
        runpy.run_path(str(entry),run_name="__main__")
    finally:
        if original_dataset is not None:
            try:
                from modules.pact import datasets
                datasets.ImageConditioned_dataset=original_dataset
            except Exception:
                pass
        sys.argv=old_argv
        os.chdir(old_cwd)
        if sys.path and sys.path[0]==str(repo):
            sys.path.pop(0)

    manifests=sorted(out.rglob("object.json"))
    result={
        **plan,
        "model":model,
        "revision":revision,
        "object_manifests":[str(p) for p in manifests],
        "wrapper_status":"completed",
        "production_geometry_authority":False,
        "warning":(
            "PAct geometry/articulation is generated candidate evidence only. "
            "Brickmen mapping, collision, deterministic interfaces and physical "
            "validation remain authoritative downstream gates."
        ),
    }
    return result


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--provider-repo",required=True)
    parser.add_argument("--image",required=True)
    parser.add_argument("--semantic-mask-exr",required=True)
    parser.add_argument("--output-dir",required=True)
    parser.add_argument("--model",default="PAct000/PAct")
    parser.add_argument("--revision",default="main")
    parser.add_argument("--metadata",required=True)
    args=parser.parse_args()
    result=run_pact(
        args.provider_repo,args.image,args.semantic_mask_exr,args.output_dir,
        model=args.model,revision=args.revision,
    )
    Path(args.metadata).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
