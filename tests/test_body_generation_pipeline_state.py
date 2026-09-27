from tools.geometry.summarize_body_generation_pipeline_state import (
    summarize_pipeline_state,
)


def conditioning():
    return {
        "architecture_id":"giant",
        "skeleton_id":"giant-skel",
        "target_height_mm":62,
        "mechanical_constraints":[
            {
                "joint_profile_id":"pin",
                "manufacturing_authority":False,
                "required_validation":["measure pin","cycle test"],
                "placements":[
                    {
                        "placement_id":"shoulder_keepout",
                        "affected_component_slot_ids":["torso"],
                        "anchor_mm_at_target_height":[0,0,0],
                        "reference_keepout_local_min_mm":[-1,-1,-1],
                        "reference_keepout_local_max_mm":[1,1,1],
                    }
                ],
            }
        ],
    }


def test_state_exposes_provider_and_physical_blockers():
    state=summarize_pipeline_state(
        conditioning(),
        sweeps={"joint_sweeps":[{"joint_id":"shoulder"}]},
        guide_manifest={"source_image_embedded":False},
        provider_job={"provider_id":"partcrafter"},
    )
    assert state["provider_id"]=="partcrafter"
    assert "provider_run" in state["production_readiness"]["blocking_gates"]
    assert "mechanical_interface_validation" in state["production_readiness"]["blocking_gates"]
    assert any("measure pin" in x for x in state["next_actions"])
    assert state["production_geometry_authority"] is False


def test_executed_mapping_without_transforms_exposes_alignment_gate():
    state=summarize_pipeline_state(
        conditioning(),
        provider_job={"provider_id":"fake"},
        provider_run={
            "provider_id":"fake",
            "mode":"executed",
            "return_code":0,
            "execution_succeeded":True,
        },
        output_mapping={
            "acceptance":{"structurally_complete":True},
            "components":[
                {"slot_id":"torso","transform_matrix_to_brickmen_mm":None}
            ],
        },
    )
    assert "frame_alignment" in state["production_readiness"]["blocking_gates"]
    assert any("alignment candidates" in x for x in state["next_actions"])


def test_bbox_pass_still_requires_topology_keepout_and_pose_collision():
    state=summarize_pipeline_state(
        conditioning(),
        provider_job={"provider_id":"fake"},
        provider_run={
            "provider_id":"fake","mode":"executed","return_code":0,
            "execution_succeeded":True,
        },
        output_mapping={
            "acceptance":{"structurally_complete":True},
            "components":[
                {"slot_id":"torso","transform_matrix_to_brickmen_mm":[1]*16}
            ],
        },
        geometry_validation={
            "summary":{
                "bbox_geometry_gate_passed":True,
                "status":"bbox_geometry_plausible_requires_exact_collision_validation",
            }
        },
    )
    assert "mesh_topology_preflight" in state["production_readiness"]["blocking_gates"]
    assert "exact_fixed_keepout_validation" in state["production_readiness"]["blocking_gates"]
    assert "sampled_pose_collision_validation" in state["production_readiness"]["blocking_gates"]


def test_sampled_pose_pass_exposes_continuous_motion_blocker():
    state=summarize_pipeline_state(
        conditioning(),
        provider_job={"provider_id":"fake"},
        provider_run={
            "provider_id":"fake","mode":"executed","return_code":0,
            "execution_succeeded":True,
        },
        output_mapping={
            "acceptance":{"structurally_complete":True},
            "components":[
                {"slot_id":"torso","transform_matrix_to_brickmen_mm":[1]*16}
            ],
        },
        geometry_validation={
            "summary":{"bbox_geometry_gate_passed":True,"status":"ok"}
        },
        mesh_quality={
            "summary":{"mesh_quality_gate_passed":True,"status":"ok"}
        },
        exact_keepout={
            "summary":{"exact_keepout_gate_passed":True,"status":"ok"}
        },
        pose_collision={
            "summary":{
                "sampled_pose_collision_gate_passed":True,
                "status":"sampled_pose_collision_gate_passed",
            }
        },
    )
    assert "sampled_pose_collision_validation" not in state["production_readiness"]["blocking_gates"]
    assert "continuous_motion_collision_validation" in state["production_readiness"]["blocking_gates"]
    assert any("continuous collision" in x for x in state["next_actions"])


def test_critic_state_cannot_masquerade_as_primary_generator():
    state=summarize_pipeline_state(
        conditioning(),
        provider_job={
            "provider_id":"particulate",
            "pipeline_stage":"post_generation_critic",
            "execution_interface":{"adapter_status":"runnable_cli_verified"},
        },
    )
    assert state["state_scope"]=="auxiliary_post_generation_critic"
    assert state["provider_pipeline_stage"]=="post_generation_critic"
    assert "primary_generator_output_dependency" in state["production_readiness"]["blocking_gates"]
    mapping_gate=next(
        g for g in state["gates"] if g["gate_id"]=="component_mapping"
    )
    assert mapping_gate["status"]=="not_applicable_to_critic_provider"
    assert "component_mapping" not in state["production_readiness"]["blocking_gates"]


def test_wrapper_verified_provider_run_is_pending_not_blocked():
    state=summarize_pipeline_state(
        conditioning(),
        provider_job={
            "provider_id":"pact",
            "pipeline_stage":"articulated_generator",
            "requires_component_slot_mapping":True,
            "execution_interface":{
                "adapter_status":"runnable_brickmen_dataset_redirect_wrapper_verified"
            },
        },
    )
    run_gate=next(g for g in state["gates"] if g["gate_id"]=="provider_run")
    assert run_gate["status"]=="pending"
    assert "dry-run the pact adapter" in " ".join(state["next_actions"])
