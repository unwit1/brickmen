from tools.geometry.build_body_provider_mapping_review_ui import (
    build_mapping_review_html,
)


def proposal():
    box={"min":[-1,-1,-1],"max":[1,1,1]}
    return {
        "provider_id":"fake",
        "provider_job_id":"j",
        "architecture_id":"test",
        "automatic_promotion_allowed":False,
        "ambiguity":{
            "near_best_candidate_count":2,
            "distinct_near_best_mapping_count":2,
            "best_to_second_score_margin":0.001,
            "explanation":"symmetric",
        },
        "global_alignment_candidates":[
            {
                "total_score":.1,
                "union_shape_log_rmse":.01,
                "average_assignment_cost":.09,
                "axis_permutation_target_from_provider":[0,1,2],
                "axis_signs":[1,1,1],
                "uniform_scale_provider_units_to_mm":10,
                "complete_visual_slot_assignment":True,
                "assignments":[
                    {
                        "provider_part_path":"/tmp/part_00.glb",
                        "slot_id":"torso_shell",
                        "pair_cost":{"total":.1,"aabb_iou":.8},
                        "transformed_aabb_mm":box,
                        "target_aabb_mm":box,
                    }
                ],
                "missing_visual_target_slots":[],
                "missing_geometrically_mappable_slots":[],
                "unassigned_provider_parts":[],
            }
        ],
    }


def test_mapping_reviewer_embeds_metadata_not_mesh_bytes():
    page=build_mapping_review_html(proposal())
    assert "Brickmen Provider Part Mapping Review" in page
    assert "/tmp/part_00.glb" in page
    assert "promotion selection JSON" in page
    assert "data:model/" not in page
    assert "data:application/octet-stream" not in page
    assert "<model-viewer" not in page
