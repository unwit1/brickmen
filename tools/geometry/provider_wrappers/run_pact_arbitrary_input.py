#!/usr/bin/env python3
"""Run PAct on an arbitrary Brickmen image + semantic part mask without editing PAct.

Current upstream infer_imgs.py parses --data_dir but constructs
ImageConditioned_dataset("assets/real_world_examples") directly. This wrapper
redirects only that dataset constructor in-process, then executes the published
upstream script unchanged.

Input contract:
- image: any PIL-readable image; staged as RGBA *_processed.png
- semantic mask: upstream-compatible EXR, or a lossless integer-label PNG/TIFF.
  PNG/TIFF is read through a narrowly scoped in-process imageio redirect while
  preserving PAct's expected *_mask.exr path contract.

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
    semantic_mask: str | Path,
    output_dir: str | Path,
) -> dict[str,Any]:
    repo=Path(provider_repo).resolve()
    entry=repo/"infer_imgs.py"
    if not entry.is_file():
        raise ValueError(f"PAct infer_imgs.py not found: {entry}")
    image_path=Path(image).resolve()
    if not image_path.is_file():
        raise ValueError(f"PAct image not found: {image_path}")
    mask=Path(semantic_mask).resolve()
    if not mask.is_file():
        raise ValueError(f"PAct semantic mask not found: {mask}")
    supported={".exr",".png",".tif",".tiff"}
    if mask.suffix.lower() not in supported:
        raise ValueError(
            "PAct semantic part mask must be .exr, .png, .tif, or .tiff"
        )
    out=Path(output_dir).resolve()
    stage=out/"_brickmen_pact_input"
    case=stage/"case_000"
    return {
        "provider_repo":str(repo),
        "entrypoint":str(entry),
        "source_image":str(image_path),
        "semantic_mask":str(mask),
        "semantic_mask_format":mask.suffix.lower().lstrip("."),
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
    # PAct discovers a case only when *_mask.exr exists. For PNG/TIFF input,
    # this placeholder is never decoded as EXR: run_pact installs an exact-path
    # read redirect before upstream dataset iteration.
    shutil.copy2(plan["semantic_mask"],plan["staged_mask"])


def _load_integer_label_mask(path: str | Path):
    """Load/validate a lossless raster semantic label map for PAct."""
    import numpy as np
    from PIL import Image

    p=Path(path)
    with Image.open(p) as image:
        array=np.asarray(image)
    if array.ndim==3:
        if array.shape[2] == 1:
            array=array[...,0]
        elif array.shape[2] in (3,4):
            rgb=array[...,:3]
            if not (
                np.array_equal(rgb[...,0],rgb[...,1])
                and np.array_equal(rgb[...,0],rgb[...,2])
            ):
                raise ValueError(
                    "Semantic PNG/TIFF must be grayscale labels or RGB with identical channels"
                )
            array=rgb[...,0]
        else:
            raise ValueError("Unsupported semantic mask channel count")
    if array.ndim!=2:
        raise ValueError("Semantic mask must be a 2D label image")
    if not np.issubdtype(array.dtype,np.integer):
        raise ValueError("Semantic PNG/TIFF labels must use an integer pixel type")
    values=np.unique(array.astype(np.int64))
    if values.size==0 or values[0] < 0:
        raise ValueError("Semantic mask labels must be non-negative")
    positive=[int(v) for v in values if int(v)>0]
    if positive:
        expected=list(range(1,max(positive)+1))
        if positive!=expected:
            raise ValueError(
                "Semantic mask positive labels must be contiguous 1..N with 0 as background"
            )
    return array, [int(v) for v in values]


def run_pact(
    provider_repo: str | Path,
    image: str | Path,
    semantic_mask: str | Path,
    output_dir: str | Path,
    *,
    model: str="PAct000/PAct",
    revision: str="main",
) -> dict[str,Any]:
    plan=preflight(provider_repo,image,semantic_mask,output_dir)
    stage_inputs(plan)
    repo=Path(plan["provider_repo"])
    entry=Path(plan["entrypoint"])
    out=Path(plan["output_dir"])
    out.mkdir(parents=True,exist_ok=True)

    sys.path.insert(0,str(repo))
    old_cwd=Path.cwd()
    old_argv=list(sys.argv)
    original_dataset=None
    original_imread=None
    try:
        os.chdir(repo)
        from modules.pact import datasets
        from modules.pact.datasets import components as dataset_components

        original_dataset=datasets.ImageConditioned_dataset
        original_imread=dataset_components.iio.imread
        stage_root=plan["stage_root"]

        class BrickmenRedirectDataset(original_dataset):
            def __init__(self, roots, *args, **kwargs):
                super().__init__(stage_root,*args,**kwargs)

        datasets.ImageConditioned_dataset=BrickmenRedirectDataset

        semantic_labels=None
        if plan["semantic_mask_format"] != "exr":
            label_array,semantic_labels=_load_integer_label_mask(
                plan["semantic_mask"]
            )
            staged_mask=Path(plan["staged_mask"]).resolve()
            def brickmen_mask_read(path,*args,**kwargs):
                if Path(path).resolve()==staged_mask:
                    # Upstream accesses mask[...,0].
                    return label_array[...,None]
                return original_imread(path,*args,**kwargs)
            dataset_components.iio.imread=brickmen_mask_read

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
        if original_imread is not None:
            try:
                from modules.pact.datasets import components as dataset_components
                dataset_components.iio.imread=original_imread
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
        "semantic_labels":(
            semantic_labels
            if 'semantic_labels' in locals() else None
        ),
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
    parser.add_argument(
        "--semantic-mask",
        "--semantic-mask-exr",
        dest="semantic_mask",
        required=True,
        help="PAct semantic part-label mask (.exr, or lossless label .png/.tif/.tiff)",
    )
    parser.add_argument("--output-dir",required=True)
    parser.add_argument("--model",default="PAct000/PAct")
    parser.add_argument("--revision",default="main")
    parser.add_argument("--metadata",required=True)
    args=parser.parse_args()
    result=run_pact(
        args.provider_repo,args.image,args.semantic_mask,args.output_dir,
        model=args.model,revision=args.revision,
    )
    Path(args.metadata).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
