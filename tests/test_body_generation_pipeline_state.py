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


def test_bbox_pass_still_requires_exact_collision():
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
    assert "exact_collision_boolean_validation" in state["production_readiness"]["blocking_gates"]
