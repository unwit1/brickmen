#!/usr/bin/env python3
"""Compile a machine-readable readiness view of Brickmen body 3D providers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


RUNNABLE_STATUSES={
    "runnable_cli_verified",
    "runnable_brickmen_python_api_visual_baseline",
    "runnable_brickmen_dataset_redirect_wrapper_verified",
}


PROVIDER_HELPERS={
    "partcrafter":{
        "execution":"tools/geometry/run_body_generation_provider.py",
        "post_run":"tools/geometry/continue_body_generator_run.py",
        "mapping_review":"tools/geometry/build_body_provider_mapping_review_ui.py",
    },
    "partpacker":{
        "execution":"tools/geometry/run_body_generation_provider.py",
        "post_run":"tools/geometry/continue_body_generator_run.py",
        "mapping_review":"tools/geometry/build_body_provider_mapping_review_ui.py",
    },
    "pact":{
        "execution":"tools/geometry/run_body_generation_provider.py",
        "provider_wrapper":"tools/geometry/provider_wrappers/run_pact_arbitrary_input.py",
        "semantic_mask_editor":"tools/geometry/build_pact_semantic_mask_editor.py",
        "post_run":"tools/geometry/continue_body_generator_run.py",
        "mapping_review":"tools/geometry/build_body_provider_mapping_review_ui.py",
    },
    "particulate":{
        "execution":"tools/geometry/run_body_generation_provider.py",
        "critic_normalization":"tools/geometry/normalize_particulate_critic.py",
        "architecture_comparison":"tools/geometry/compare_particulate_to_body_architecture.py",
    },
    "sam_3d_objects":{
        "execution":"tools/geometry/run_body_generation_provider.py",
        "provider_wrapper":"tools/geometry/provider_wrappers/run_sam3d_objects_baseline.py",
    },
}


def load_json(path: str | Path | None) -> dict[str,Any] | None:
    if path is None:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _state_by_provider(paths):
    out={}
    for path in paths:
        payload=load_json(path)
        if payload and payload.get("provider_id"):
            out[str(payload["provider_id"])]={
                "path":str(path),
                "payload":payload,
            }
    return out


def _input_requirements(provider: Mapping[str,Any]) -> list[str]:
    pid=provider["provider_id"]
    requirements=[]
    stage=provider.get("pipeline_stage")
    if pid in {"partcrafter","partpacker"}:
        requirements.append("source_or_control_image")
    elif pid=="pact":
        requirements.extend([
            "source_or_control_image",
            "semantic_part_label_mask_exr_or_lossless_png_tiff",
        ])
    elif pid=="particulate":
        requirements.append("generated_triangle_mesh")
    elif pid=="sam_3d_objects":
        requirements.extend(["source_image","binary_object_mask"])
    if stage=="post_generation_critic":
        requirements.append("primary_generator_output_dependency")
    return requirements


def compile_readiness(
    registry: Mapping[str,Any],
    conditioning: Mapping[str,Any],
    *,
    pipeline_states: Mapping[str,Any] | None=None,
    contact_regions: Mapping[str,Any] | None=None,
) -> dict[str,Any]:
    pipeline_states=pipeline_states or {}
    providers=[]
    for provider in registry.get("providers",[]):
        pid=str(provider["provider_id"])
        execution=provider.get("execution") or {}
        status=str(execution.get("adapter_status","unverified"))
        state_entry=pipeline_states.get(pid)
        state=(state_entry or {}).get("payload") or {}
        run_gate=next(
            (
                gate for gate in state.get("gates",[])
                if gate.get("gate_id")=="provider_run"
            ),
            None,
        )
        providers.append({
            "provider_id":pid,
            "display_name":provider.get("display_name") or provider.get("name"),
            "pipeline_stage":provider.get("pipeline_stage"),
            "provider_role":provider.get("provider_role"),
            "adapter_status":status,
            "brickmen_execution_runnable":status in RUNNABLE_STATUSES,
            "entrypoint":execution.get("entrypoint"),
            "input_requirements":_input_requirements(provider),
            "output_contract":provider.get("output_contract"),
            "requires_component_slot_mapping":provider.get(
                "requires_component_slot_mapping"
            ),
            "helpers":PROVIDER_HELPERS.get(pid,{}),
            "canonical_pipeline_state_path":(
                state_entry.get("path") if state_entry else None
            ),
            "canonical_provider_run_status":(
                run_gate.get("status") if run_gate else "state_unavailable"
            ),
            "canonical_provider_run_detail":(
                run_gate.get("detail") if run_gate else None
            ),
            "execution_has_been_performed_in_canonical_fixture":False,
            "limitations":provider.get("limitations",[]),
            "production_geometry_authority":False,
        })

    mechanical=[]
    for item in conditioning.get("mechanical_constraints",[]):
        if item.get("manufacturing_authority",False):
            continue
        mechanical.append({
            "kind":"mechanical_interface_validation",
            "joint_profile_id":item.get("joint_profile_id"),
            "authority_class":item.get("authority_class"),
            "required_validation":item.get("required_validation",[]),
        })

    contact=[]
    if contact_regions:
        for joint in contact_regions.get("joints",[]):
            validated=[
                region for region in joint.get("allowed_contact_regions_mm",[])
                if region.get("status") in {
                    "validated_prototype","production_approved"
                }
            ]
            if not validated:
                contact.append({
                    "kind":"joint_contact_region_validation",
                    "joint_id":joint.get("joint_id"),
                    "status":joint.get("status"),
                    "source_validation_plan_id":joint.get(
                        "source_validation_plan_id"
                    ),
                    "blocker":joint.get("blocker"),
                })

    return {
        "schema_version":"0.1",
        "architecture_id":conditioning.get("architecture_id"),
        "skeleton_id":conditioning.get("skeleton_id"),
        "target_height_mm":conditioning.get("target_height_mm"),
        "providers":providers,
        "shared_pipeline":{
            "conditioning":"implemented",
            "structural_guides":"implemented",
            "articulation_sweeps":"implemented",
            "provider_job_compilation":"implemented",
            "provider_dry_run_and_execution":"implemented_for_verified_adapters",
            "provider_output_classification":"provider_specific",
            "provider_part_provenance":"preserved",
            "semantic_slot_mapping_proposal":"implemented",
            "mapping_wireframe_reviewer":"implemented",
            "strict_unambiguous_auto_promotion":"opt_in_only",
            "transform_reconciliation":"implemented",
            "coarse_geometry_validation":"implemented",
            "mesh_topology_preflight":"implemented",
            "exact_fixed_keepout_validation":"implemented",
            "sampled_pose_collision":"implemented",
            "conservative_continuous_rotation_collision":"implemented",
            "validation_bundle":"implemented",
            "pipeline_state":"implemented",
        },
        "physical_blockers":[*mechanical,*contact],
        "canonical_generated_geometry_available":False,
        "canonical_gpu_provider_execution_performed":False,
        "next_system_milestone":(
            "Run at least one verified primary generator on real/reference input, "
            "continue it through mapping/validation, and retain the resulting "
            "provider-run/output/validation bundle as a non-production experiment."
        ),
        "production_geometry_authority":False,
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("registry")
    parser.add_argument("conditioning")
    parser.add_argument("--pipeline-state",action="append",default=[])
    parser.add_argument("--contact-regions",default=None)
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    result=compile_readiness(
        load_json(args.registry),
        load_json(args.conditioning),
        pipeline_states=_state_by_provider(args.pipeline_state),
        contact_regions=load_json(args.contact_regions),
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
