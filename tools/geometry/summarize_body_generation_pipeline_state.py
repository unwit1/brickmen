#!/usr/bin/env python3
"""Summarize Brickmen body-generation pipeline progress as explicit gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


def load_json(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _gate(
    gate_id: str,
    status: str,
    *,
    artifact: str | None=None,
    detail: str | None=None,
    blocking: bool=False,
) -> dict[str,Any]:
    return {
        "gate_id":gate_id,
        "status":status,
        "artifact":artifact,
        "detail":detail,
        "blocking":blocking,
    }


def summarize_pipeline_state(
    conditioning: Mapping[str,Any],
    *,
    conditioning_path: str | None=None,
    sweeps: Mapping[str,Any] | None=None,
    sweeps_path: str | None=None,
    guide_manifest: Mapping[str,Any] | None=None,
    guide_manifest_path: str | None=None,
    provider_job: Mapping[str,Any] | None=None,
    provider_job_path: str | None=None,
    provider_run: Mapping[str,Any] | None=None,
    provider_run_path: str | None=None,
    output_mapping: Mapping[str,Any] | None=None,
    output_mapping_path: str | None=None,
    geometry_validation: Mapping[str,Any] | None=None,
    geometry_validation_path: str | None=None,
    mesh_quality: Mapping[str,Any] | None=None,
    mesh_quality_path: str | None=None,
    exact_keepout: Mapping[str,Any] | None=None,
    exact_keepout_path: str | None=None,
) -> dict[str,Any]:
    gates=[]
    next_actions=[]

    gates.append(_gate(
        "conditioning",
        "complete",
        artifact=conditioning_path,
        detail="BodyGenerationConditioning exists and remains non-production."
    ))

    if sweeps:
        gates.append(_gate(
            "articulation_sweeps","complete",artifact=sweeps_path,
            detail=f"{len(sweeps.get('joint_sweeps',[]))} joint sweep records compiled."
        ))
    else:
        gates.append(_gate(
            "articulation_sweeps","pending",artifact=sweeps_path,
            detail="Compile conservative visual articulation sweeps."
        ))
        next_actions.append("compile articulation sweep conditioning")

    if guide_manifest:
        gates.append(_gate(
            "structural_guides","complete",artifact=guide_manifest_path,
            detail="Source-image-free front/side structural guides are available."
        ))
    else:
        gates.append(_gate(
            "structural_guides","pending",artifact=guide_manifest_path,
            detail="Render provider-facing structural guide pack."
        ))
        next_actions.append("render front/side structural generation guides")

    provider_id=provider_job.get("provider_id") if provider_job else None
    if provider_job:
        gates.append(_gate(
            "provider_job","complete",artifact=provider_job_path,
            detail=f"Provider job compiled for {provider_id}."
        ))
    else:
        gates.append(_gate(
            "provider_job","pending",artifact=provider_job_path,
            detail="Compile provider-specific orchestration job."
        ))
        next_actions.append("compile a provider job from the conditioning payload")

    if provider_job and not provider_run:
        adapter_status = str(
            (provider_job.get("execution_interface") or {}).get(
                "adapter_status", "unknown"
            )
        )
        if adapter_status == "runnable_cli_verified":
            run_status = "pending"
            detail = (
                "Verified CLI adapter exists, but no provider run report exists. "
                "External provider environment and source/guide image input are required."
            )
            next_actions.append(
                f"dry-run the {provider_id} adapter against an installed provider environment"
            )
            next_actions.append(
                f"execute {provider_id} inference only after the dry-run plan is reviewed"
            )
        else:
            run_status = "blocked"
            detail = (
                f"Provider execution interface is {adapter_status}; no verified runnable "
                "Brickmen execution adapter exists yet."
            )
            next_actions.append(
                f"implement/verify the {provider_id} execution adapter before inference"
            )
        gates.append(_gate(
            "provider_run",run_status,artifact=provider_run_path,
            detail=detail,
            blocking=True,
        ))
    elif provider_run:
        if not provider_run.get("execution_supported",True):
            status="blocked"
            blocking=True
            detail="Provider adapter is plan/API-only and cannot be executed yet."
            next_actions.append(
                f"implement/verify an executable adapter for {provider_run.get('provider_id')}"
            )
        elif provider_run.get("mode")=="dry_run":
            status="ready_for_execution"
            blocking=True
            detail="Provider invocation has been planned but not executed."
            next_actions.append("execute the reviewed provider plan")
        elif (
            provider_run.get("mode")=="executed"
            and provider_run.get("return_code") in (0,None)
            and provider_run.get("execution_succeeded",True)
        ):
            status="complete"
            blocking=False
            detail="Provider process completed successfully; output still needs Brickmen validation."
        else:
            status="failed"
            blocking=True
            detail="Provider execution did not complete successfully."
            next_actions.append("review provider stdout/stderr and rerun inference")
        gates.append(_gate(
            "provider_run",status,artifact=provider_run_path,
            detail=detail,blocking=blocking
        ))

    if output_mapping:
        acceptance=output_mapping.get("acceptance",{})
        if acceptance.get("structurally_complete"):
            gates.append(_gate(
                "component_mapping","complete",artifact=output_mapping_path,
                detail="Every required component slot is mapped exactly once."
            ))
        else:
            gates.append(_gate(
                "component_mapping","incomplete",artifact=output_mapping_path,
                detail=acceptance.get("status"),
                blocking=True,
            ))
            next_actions.append("resolve every required provider output to a Brickmen component slot")
    elif provider_run and provider_run.get("mode")=="executed":
        gates.append(_gate(
            "component_mapping","pending",artifact=output_mapping_path,
            detail="Provider outputs have not been mapped to component slots.",
            blocking=True,
        ))
        next_actions.append("map generated provider parts to Brickmen component slots")
    else:
        gates.append(_gate(
            "component_mapping","not_started",artifact=output_mapping_path,
            detail="Requires provider outputs first."
        ))

    if output_mapping and output_mapping.get("components"):
        missing_transform=[
            c["slot_id"] for c in output_mapping["components"]
            if c.get("transform_matrix_to_brickmen_mm") is None
        ]
        if missing_transform:
            gates.append(_gate(
                "frame_alignment","incomplete",artifact=output_mapping_path,
                detail="Missing provider->Brickmen-mm transforms: "+", ".join(missing_transform),
                blocking=True,
            ))
            next_actions.append(
                "propose/review provider-frame alignment candidates and record explicit transforms"
            )
        else:
            gates.append(_gate(
                "frame_alignment","complete",artifact=output_mapping_path,
                detail="All mapped components have explicit provider->Brickmen-mm transforms."
            ))
    else:
        gates.append(_gate(
            "frame_alignment","not_started",artifact=output_mapping_path,
            detail="Requires mapped provider components."
        ))

    if geometry_validation:
        summary=geometry_validation.get("summary",{})
        if summary.get("bbox_geometry_gate_passed"):
            gates.append(_gate(
                "bbox_geometry_validation","complete",artifact=geometry_validation_path,
                detail=summary.get("status")
            ))
        else:
            gates.append(_gate(
                "bbox_geometry_validation","review_required",artifact=geometry_validation_path,
                detail=summary.get("status"),blocking=True
            ))
            next_actions.append("repair scale/alignment/slot geometry until the coarse bbox gate passes")
    else:
        gates.append(_gate(
            "bbox_geometry_validation","not_started",artifact=geometry_validation_path,
            detail="Requires explicit transforms and mapped meshes."
        ))

    bbox_passed = bool(
        geometry_validation
        and geometry_validation.get("summary",{}).get(
            "bbox_geometry_gate_passed"
        )
    )

    if mesh_quality:
        quality_pass = bool(
            mesh_quality.get("summary",{}).get("mesh_quality_gate_passed")
        )
        gates.append(_gate(
            "mesh_topology_preflight",
            "complete" if quality_pass else "review_required",
            artifact=mesh_quality_path,
            detail=mesh_quality.get("summary",{}).get("status"),
            blocking=not quality_pass,
        ))
        if not quality_pass:
            next_actions.append(
                "repair open/nonmanifold/degenerate/disconnected generated meshes"
            )
    elif output_mapping and output_mapping.get("components"):
        gates.append(_gate(
            "mesh_topology_preflight","pending",artifact=mesh_quality_path,
            detail="Mapped provider meshes have not been audited for topology/closedness.",
            blocking=True,
        ))
        next_actions.append("run generated-mesh topology preflight")
    else:
        gates.append(_gate(
            "mesh_topology_preflight","not_started",artifact=mesh_quality_path,
            detail="Requires mapped provider meshes."
        ))

    has_mechanical_keepouts = any(
        constraint.get("placements")
        for constraint in conditioning.get("mechanical_constraints",[])
    )
    if exact_keepout:
        keepout_pass = bool(
            exact_keepout.get("summary",{}).get("exact_keepout_gate_passed")
        )
        gates.append(_gate(
            "exact_fixed_keepout_validation",
            "complete" if keepout_pass else "review_required",
            artifact=exact_keepout_path,
            detail=exact_keepout.get("summary",{}).get("status"),
            blocking=not keepout_pass,
        ))
        if not keepout_pass:
            next_actions.append(
                "repair generated shell material intersecting fixed mechanical keep-outs"
            )
    elif has_mechanical_keepouts and output_mapping and output_mapping.get("components"):
        gates.append(_gate(
            "exact_fixed_keepout_validation","pending",artifact=exact_keepout_path,
            detail="Run triangle/inside-solid validation for scoped mechanical keep-outs.",
            blocking=True,
        ))
        next_actions.append("run exact fixed mechanical keep-out validation")
    elif has_mechanical_keepouts:
        gates.append(_gate(
            "exact_fixed_keepout_validation","not_started",artifact=exact_keepout_path,
            detail="Requires mapped and transformed generated components."
        ))
    else:
        gates.append(_gate(
            "exact_fixed_keepout_validation","not_applicable",artifact=exact_keepout_path,
            detail="No scoped fixed mechanical keep-outs are present."
        ))

    if bbox_passed and output_mapping and output_mapping.get("components"):
        gates.append(_gate(
            "exact_pose_collision_validation","blocked",
            detail=(
                "Exact pose-wise component collision needs explicit joint-local allowed-contact "
                "regions so intended shoulder/wrist mating contact is not misclassified."
            ),
            blocking=True,
        ))
        next_actions.append(
            "define/review joint-local allowed-contact regions, then run exact pose-wise triangle collision"
        )
    else:
        gates.append(_gate(
            "exact_pose_collision_validation","not_started",
            detail="Requires mapped, aligned geometry and joint-local allowed-contact regions."
        ))

    mechanical=conditioning.get("mechanical_constraints",[])
    unapproved=[
        m for m in mechanical if not m.get("manufacturing_authority",False)
    ]
    validation_items=[]
    for item in unapproved:
        validation_items.extend(item.get("required_validation",[]))
    if unapproved:
        gates.append(_gate(
            "mechanical_interface_validation","blocked",
            detail=(
                f"{len(unapproved)} mechanical profile(s) remain non-production; "
                f"{len(validation_items)} validation item(s) are outstanding."
            ),
            blocking=True,
        ))
        next_actions.extend(
            f"physical validation: {text}" for text in validation_items
            if f"physical validation: {text}" not in next_actions
        )
    else:
        gates.append(_gate(
            "mechanical_interface_validation","complete",
            detail="All included mechanical profiles claim manufacturing authority."
        ))

    # De-duplicate while preserving order.
    dedup=[]
    for action in next_actions:
        if action not in dedup:
            dedup.append(action)

    blocking=[g["gate_id"] for g in gates if g.get("blocking")]
    return {
        "schema_version":"0.1",
        "architecture_id":conditioning["architecture_id"],
        "skeleton_id":conditioning.get("skeleton_id"),
        "provider_id":provider_id,
        "target_height_mm":conditioning.get("target_height_mm"),
        "gates":gates,
        "next_actions":dedup,
        "production_readiness":{
            "ready":not blocking,
            "blocking_gates":blocking,
            "note":(
                "Pipeline readiness requires all explicit gates; production authority "
                "still belongs only to separately validated deterministic interfaces."
            ),
        },
        "production_geometry_authority":False,
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("--sweeps",default=None)
    parser.add_argument("--guide-manifest",default=None)
    parser.add_argument("--provider-job",default=None)
    parser.add_argument("--provider-run",default=None)
    parser.add_argument("--output-mapping",default=None)
    parser.add_argument("--geometry-validation",default=None)
    parser.add_argument("--mesh-quality",default=None)
    parser.add_argument("--exact-keepout",default=None)
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()

    result=summarize_pipeline_state(
        load_json(args.conditioning),
        conditioning_path=args.conditioning,
        sweeps=load_json(args.sweeps),
        sweeps_path=args.sweeps,
        guide_manifest=load_json(args.guide_manifest),
        guide_manifest_path=args.guide_manifest,
        provider_job=load_json(args.provider_job),
        provider_job_path=args.provider_job,
        provider_run=load_json(args.provider_run),
        provider_run_path=args.provider_run,
        output_mapping=load_json(args.output_mapping),
        output_mapping_path=args.output_mapping,
        geometry_validation=load_json(args.geometry_validation),
        geometry_validation_path=args.geometry_validation,
        mesh_quality=load_json(args.mesh_quality),
        mesh_quality_path=args.mesh_quality,
        exact_keepout=load_json(args.exact_keepout),
        exact_keepout_path=args.exact_keepout,
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
