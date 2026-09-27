from tools.geometry.compile_body_provider_readiness import compile_readiness


def test_readiness_distinguishes_generator_baseline_and_critic():
    registry={
        "providers":[
            {
                "provider_id":"partcrafter",
                "pipeline_stage":"primary_generator",
                "provider_role":"part_aware_generator",
                "execution":{"adapter_status":"runnable_cli_verified","entrypoint":"x.py"},
                "requires_component_slot_mapping":True,
            },
            {
                "provider_id":"sam_3d_objects",
                "pipeline_stage":"baseline_generator",
                "provider_role":"visual_baseline",
                "execution":{
                    "adapter_status":"runnable_brickmen_python_api_visual_baseline",
                    "entrypoint":"notebook/inference.py",
                },
                "requires_component_slot_mapping":False,
            },
            {
                "provider_id":"particulate",
                "pipeline_stage":"post_generation_critic",
                "provider_role":"critic",
                "execution":{"adapter_status":"runnable_cli_verified","entrypoint":"infer.py"},
                "requires_component_slot_mapping":False,
            },
        ]
    }
    conditioning={
        "architecture_id":"giant",
        "mechanical_constraints":[
            {
                "joint_profile_id":"pin",
                "manufacturing_authority":False,
                "required_validation":["measure"],
            }
        ],
    }
    result=compile_readiness(registry,conditioning)
    by_id={p["provider_id"]:p for p in result["providers"]}
    assert by_id["partcrafter"]["brickmen_execution_runnable"] is True
    assert by_id["sam_3d_objects"]["pipeline_stage"]=="baseline_generator"
    assert "generated_triangle_mesh" in by_id["particulate"]["input_requirements"]
    assert result["shared_pipeline"]["mapping_wireframe_reviewer"]=="implemented"
    assert result["physical_blockers"][0]["joint_profile_id"]=="pin"
    assert result["canonical_gpu_provider_execution_performed"] is False


def test_pact_readiness_exposes_mask_editor():
    registry={
        "providers":[
            {
                "provider_id":"pact",
                "pipeline_stage":"primary_generator",
                "execution":{
                    "adapter_status":"runnable_brickmen_dataset_redirect_wrapper_verified",
                    "entrypoint":"infer_imgs.py",
                },
                "requires_component_slot_mapping":True,
            }
        ]
    }
    result=compile_readiness(registry,{"architecture_id":"giant"})
    pact=result["providers"][0]
    assert pact["brickmen_execution_runnable"] is True
    assert "semantic_part_label_mask_exr_or_lossless_png_tiff" in pact["input_requirements"]
    assert pact["helpers"]["semantic_mask_editor"].endswith(
        "build_pact_semantic_mask_editor.py"
    )
