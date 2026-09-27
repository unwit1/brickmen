from pathlib import Path

import pytest

from tools.geometry.promote_body_provider_output_mapping import (
    promote_mapping_candidate,
)


def job():
    return {
        "provider_id":"fake",
        "provider_job_id":"j",
        "requires_component_slot_mapping":True,
        "component_slots":{
            "required":[
                {"slot_id":"torso_shell","required":True},
                {"slot_id":"head_shell","required":True},
            ],
            "optional":[],
        },
    }


def run(torso,head):
    return {
        "provider_id":"fake",
        "provider_job_id":"j",
        "mode":"executed",
        "return_code":0,
        "execution_succeeded":True,
        "discovered_outputs":[str(torso),str(head)],
    }


def proposal(torso,head,complete=True):
    matrix=[
        1,0,0,0,
        0,1,0,0,
        0,0,1,0,
        0,0,0,1,
    ]
    return {
        "schema_version":"0.1",
        "provider_id":"fake",
        "provider_job_id":"j",
        "automatic_promotion_allowed":False,
        "ambiguity":{"near_best_candidate_count":2},
        "global_alignment_candidates":[
            {
                "total_score":.12,
                "union_shape_log_rmse":.02,
                "average_assignment_cost":.10,
                "global_transform_matrix_to_brickmen_mm":matrix,
                "complete_visual_slot_assignment":complete,
                "assignments":[
                    {
                        "provider_part_path":str(torso),
                        "slot_id":"torso_shell",
                    },
                    {
                        "provider_part_path":str(head),
                        "slot_id":"head_shell",
                    },
                ],
            }
        ],
    }


def test_explicit_promotion_records_review_provenance(tmp_path: Path):
    torso=tmp_path/"torso.glb"; head=tmp_path/"head.glb"
    torso.write_bytes(b"x"); head.write_bytes(b"x")
    result=promote_mapping_candidate(
        proposal(torso,head),job(),run(torso,head),0,
        reviewer="reviewer",review_note="checked against guide",
    )
    assert result["acceptance"]["structurally_complete"] is True
    assert result["mapping_promotion"]["promotion_is_explicit"] is True
    assert result["mapping_promotion"]["reviewer"]=="reviewer"
    assert result["mapping_promotion"]["proposal_automatic_promotion_allowed"] is False
    assert all(
        c["transform_source"]=="reviewed_global_mapping_proposal"
        for c in result["components"]
    )
    assert result["production_geometry_authority"] is False


def test_incomplete_candidate_cannot_be_promoted(tmp_path: Path):
    torso=tmp_path/"torso.glb"; head=tmp_path/"head.glb"
    torso.write_bytes(b"x"); head.write_bytes(b"x")
    with pytest.raises(ValueError,match="does not resolve every required"):
        promote_mapping_candidate(
            proposal(torso,head,complete=False),job(),run(torso,head),0
        )


def test_critic_job_cannot_be_promoted_as_components(tmp_path: Path):
    torso=tmp_path/"torso.glb"; head=tmp_path/"head.glb"
    torso.write_bytes(b"x"); head.write_bytes(b"x")
    critic=job()
    critic["requires_component_slot_mapping"]=False
    with pytest.raises(ValueError,match="not a primary"):
        promote_mapping_candidate(
            proposal(torso,head),critic,run(torso,head),0
        )
