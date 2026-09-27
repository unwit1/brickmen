#!/usr/bin/env python3
"""Thin Brickmen wrapper around SAM 3D Objects' published Python API.

This script must run in an environment where the SAM 3D Objects repository and
its dependencies/checkpoints are installed. It exports the public quick-start
Gaussian splat PLY plus small pose/scale metadata.

It does not request internal mesh postprocessing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


def _jsonable(value: Any):
    if value is None or isinstance(value,(str,int,float,bool)):
        return value
    if isinstance(value,(list,tuple)):
        return [_jsonable(x) for x in value]
    if isinstance(value,dict):
        return {str(k):_jsonable(v) for k,v in value.items()}
    if hasattr(value,"detach"):
        value=value.detach()
    if hasattr(value,"cpu"):
        value=value.cpu()
    if hasattr(value,"tolist"):
        try:
            return value.tolist()
        except Exception:
            pass
    return str(type(value).__name__)


def run_sam3d_baseline(
    provider_repo: str | Path,
    image_path: str | Path,
    mask_path: str | Path,
    output_path: str | Path,
    metadata_path: str | Path,
    *,
    seed: int=42,
    config_path: str | Path | None=None,
) -> dict[str,Any]:
    repo=Path(provider_repo).resolve()
    image=Path(image_path).resolve()
    mask=Path(mask_path).resolve()
    output=Path(output_path).resolve()
    metadata=Path(metadata_path).resolve()

    if not (repo/"notebook"/"inference.py").is_file():
        raise ValueError("SAM 3D provider repo missing notebook/inference.py")
    if not image.is_file():
        raise ValueError(f"Image not found: {image}")
    if not mask.is_file():
        raise ValueError(f"Mask not found: {mask}")
    config=(
        Path(config_path).resolve()
        if config_path is not None
        else repo/"checkpoints"/"hf"/"pipeline.yaml"
    )
    if not config.is_file():
        raise ValueError(
            "SAM 3D config not found. Expected checkpoints/hf/pipeline.yaml "
            "or supply --config."
        )

    sys.path.insert(0,str(repo))
    sys.path.insert(0,str(repo/"notebook"))
    from inference import Inference,load_image,load_mask  # type: ignore

    inference=Inference(str(config),compile=False)
    rgb=load_image(str(image))
    binary_mask=load_mask(str(mask))
    result=inference(rgb,binary_mask,seed=int(seed))
    if "gs" not in result:
        raise RuntimeError("SAM 3D output did not contain published 'gs' result")

    output.parent.mkdir(parents=True,exist_ok=True)
    result["gs"].save_ply(str(output))

    payload={
        "schema_version":"0.1",
        "provider_id":"sam_3d_objects",
        "pipeline_stage":"baseline_generator",
        "source_image":str(image),
        "source_mask":str(mask),
        "config_path":str(config),
        "seed":int(seed),
        "gaussian_splat_ply":str(output),
        "published_result_fields":sorted(str(k) for k in result.keys()),
        "pose_scale_metadata":{
            key:_jsonable(result.get(key))
            for key in ("rotation","translation","scale")
            if key in result
        },
        "triangle_mesh_exported":False,
        "production_geometry_authority":False,
        "warning":(
            "This wrapper uses the published SAM 3D quick-start inference path, "
            "which disables mesh postprocessing and exports Gaussian splat evidence."
        ),
    }
    metadata.parent.mkdir(parents=True,exist_ok=True)
    metadata.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    return payload


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--provider-repo",required=True)
    parser.add_argument("--image",required=True)
    parser.add_argument("--mask",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--metadata",required=True)
    parser.add_argument("--seed",type=int,default=42)
    parser.add_argument("--config",default=None)
    args=parser.parse_args()
    run_sam3d_baseline(
        args.provider_repo,args.image,args.mask,args.output,args.metadata,
        seed=args.seed,config_path=args.config,
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
