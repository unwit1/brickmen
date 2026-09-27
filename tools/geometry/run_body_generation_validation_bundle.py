#!/usr/bin/env python3
"""Run the complete Brickmen generated-body validation bundle.

This is the orchestration layer for already-generated/mapped component meshes.
It intentionally does not run the external 3D provider itself.

Artifacts:
- coarse geometry validation;
- mesh topology preflight;
- exact fixed keep-out validation;
- pose-sampled collision validation;
- conservative continuous rotation collision validation;
- refreshed pipeline-state manifest;
- bundle manifest.

Generation validation and production readiness remain separate concepts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.geometry.summarize_body_generation_pipeline_state import (
    summarize_pipeline_state,
)
from tools.geometry.validate_body_generation_continuous_collisions import (
    validate_continuous_rotation_collisions,
)
from tools.geometry.validate_body_generation_exact_keepouts import (
    validate_exact_keepouts,
)
from tools.geometry.validate_body_generation_mesh_quality import (
    validate_mesh_quality,
)
from tools.geometry.validate_body_generation_pose_collisions import (
    validate_pose_collisions,
)
from tools.geometry.validate_body_generation_provider_geometry import (
    validate_provider_geometry,
)


def load_json(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_validation_bundle(
    conditioning: dict[str, Any],
    output_mapping: dict[str, Any],
    output_dir: str | Path,
    *,
    conditioning_path: str | None=None,
    output_mapping_path: str | None=None,
    sweeps: dict[str, Any] | None=None,
    sweeps_path: str | None=None,
    guide_manifest: dict[str, Any] | None=None,
    guide_manifest_path: str | None=None,
    provider_job: dict[str, Any] | None=None,
    provider_job_path: str | None=None,
    provider_run: dict[str, Any] | None=None,
    provider_run_path: str | None=None,
    contact_regions: dict[str, Any] | None=None,
    contact_regions_path: str | None=None,
    sampled_pose_count: int=9,
    continuous_min_interval_deg: float=.25,
    continuous_max_depth: int=14,
    continuous_max_candidate_pairs: int=200000,
) -> dict[str, Any]:
    out=Path(output_dir)
    out.mkdir(parents=True,exist_ok=True)

    geometry=validate_provider_geometry(
        conditioning,output_mapping,sweeps=sweeps
    )
    geometry_path=out/"geometry-validation.json"
    _write(geometry_path,geometry)

    mesh_quality=validate_mesh_quality(output_mapping)
    mesh_quality_path=out/"mesh-quality.json"
    _write(mesh_quality_path,mesh_quality)

    keepout=validate_exact_keepouts(conditioning,output_mapping)
    keepout_path=out/"exact-keepout-validation.json"
    _write(keepout_path,keepout)

    pose=validate_pose_collisions(
        conditioning,output_mapping,
        contact_regions=contact_regions,
        samples_per_joint=sampled_pose_count,
    )
    pose_path=out/"pose-collision-validation.json"
    _write(pose_path,pose)

    continuous=validate_continuous_rotation_collisions(
        conditioning,output_mapping,
        contact_regions=contact_regions,
        min_interval_deg=continuous_min_interval_deg,
        max_depth=continuous_max_depth,
        max_candidate_triangle_pairs=continuous_max_candidate_pairs,
    )
    continuous_path=out/"continuous-collision-validation.json"
    _write(continuous_path,continuous)

    state=summarize_pipeline_state(
        conditioning,
        conditioning_path=conditioning_path,
        sweeps=sweeps,
        sweeps_path=sweeps_path,
        guide_manifest=guide_manifest,
        guide_manifest_path=guide_manifest_path,
        provider_job=provider_job,
        provider_job_path=provider_job_path,
        provider_run=provider_run,
        provider_run_path=provider_run_path,
        output_mapping=output_mapping,
        output_mapping_path=output_mapping_path,
        geometry_validation=geometry,
        geometry_validation_path=str(geometry_path),
        mesh_quality=mesh_quality,
        mesh_quality_path=str(mesh_quality_path),
        exact_keepout=keepout,
        exact_keepout_path=str(keepout_path),
        contact_regions=contact_regions,
        contact_regions_path=contact_regions_path,
        pose_collision=pose,
        pose_collision_path=str(pose_path),
        continuous_collision=continuous,
        continuous_collision_path=str(continuous_path),
    )
    state_path=out/"pipeline-state.json"
    _write(state_path,state)

    gates={
        "bbox_geometry":bool(
            geometry.get("summary",{}).get("bbox_geometry_gate_passed")
        ),
        "mesh_topology":bool(
            mesh_quality.get("summary",{}).get("mesh_quality_gate_passed")
        ),
        "exact_fixed_keepout":bool(
            keepout.get("summary",{}).get("exact_keepout_gate_passed")
        ),
        "sampled_pose_collision":bool(
            pose.get("summary",{}).get(
                "sampled_pose_collision_gate_passed"
            )
        ),
        "continuous_rotation_collision":bool(
            continuous.get("summary",{}).get(
                "continuous_rotation_collision_gate_passed"
            )
        ),
    }
    generated_geometry_passed=all(gates.values())

    manifest={
        "schema_version":"0.1",
        "architecture_id":conditioning.get("architecture_id"),
        "provider_id":output_mapping.get("provider_id"),
        "provider_job_id":output_mapping.get("provider_job_id"),
        "artifacts":{
            "geometry_validation":str(geometry_path),
            "mesh_quality":str(mesh_quality_path),
            "exact_keepout_validation":str(keepout_path),
            "pose_collision_validation":str(pose_path),
            "continuous_collision_validation":str(continuous_path),
            "pipeline_state":str(state_path),
        },
        "generation_validation_gates":gates,
        "generated_geometry_validation_passed":generated_geometry_passed,
        "pipeline_production_ready":bool(
            state.get("production_readiness",{}).get("ready")
        ),
        "production_blocking_gates":state.get(
            "production_readiness",{}
        ).get("blocking_gates",[]),
        "production_geometry_authority":False,
        "warning":(
            "Generated-geometry validation success is not equivalent to production "
            "approval. Mechanical interface qualification and other production gates "
            "remain explicit in pipeline-state.json."
        ),
    }
    manifest_path=out/"bundle-manifest.json"
    _write(manifest_path,manifest)
    return manifest


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("output_mapping")
    parser.add_argument("output_dir")
    parser.add_argument("--sweeps",default=None)
    parser.add_argument("--guide-manifest",default=None)
    parser.add_argument("--provider-job",default=None)
    parser.add_argument("--provider-run",default=None)
    parser.add_argument("--contact-regions",default=None)
    parser.add_argument("--sampled-pose-count",type=int,default=9)
    parser.add_argument("--continuous-min-interval-deg",type=float,default=.25)
    parser.add_argument("--continuous-max-depth",type=int,default=14)
    parser.add_argument("--continuous-max-candidate-pairs",type=int,default=200000)
    args=parser.parse_args()

    manifest=run_validation_bundle(
        load_json(args.conditioning),
        load_json(args.output_mapping),
        args.output_dir,
        conditioning_path=args.conditioning,
        output_mapping_path=args.output_mapping,
        sweeps=load_json(args.sweeps),
        sweeps_path=args.sweeps,
        guide_manifest=load_json(args.guide_manifest),
        guide_manifest_path=args.guide_manifest,
        provider_job=load_json(args.provider_job),
        provider_job_path=args.provider_job,
        provider_run=load_json(args.provider_run),
        provider_run_path=args.provider_run,
        contact_regions=load_json(args.contact_regions),
        contact_regions_path=args.contact_regions,
        sampled_pose_count=args.sampled_pose_count,
        continuous_min_interval_deg=args.continuous_min_interval_deg,
        continuous_max_depth=args.continuous_max_depth,
        continuous_max_candidate_pairs=args.continuous_max_candidate_pairs,
    )
    return 0 if manifest["generated_geometry_validation_passed"] else 2


if __name__=="__main__":
    raise SystemExit(main())
