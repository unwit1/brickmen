from pathlib import Path

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


def test_mapping_reviewer_embeds_bounded_wireframe_metadata(tmp_path: Path):
    mesh=tmp_path/"part.obj"
    mesh.write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n",
        encoding="utf-8",
    )
    p=proposal()
    assignment=p["global_alignment_candidates"][0]["assignments"][0]
    assignment["provider_part_path"]=str(mesh)
    p["global_alignment_candidates"][0]["global_transform_matrix_to_brickmen_mm"]=[
        1,0,0,0,
        0,1,0,0,
        0,0,1,0,
        0,0,0,1,
    ]
    page=build_mapping_review_html(p)
    assert '"wireframe_segment_count":3' in page
    assert '"source_triangle_count":1' in page
    assert 'class:"wire"' in page
    assert "data:model/" not in page


def test_mapping_reviewer_tolerates_missing_mesh_for_wireframe():
    page=build_mapping_review_html(proposal())
    assert '"status":"unavailable"' in page
    assert "Brickmen Provider Part Mapping Review" in page
