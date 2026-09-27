from pathlib import Path

import pytest

from tools.geometry.continue_body_generator_run import (
    automatic_mapping_selection,
    continue_generator_run,
)


def box_obj(path: Path,center,size):
    cx,cy,cz=center; hx,hy,hz=[v/2 for v in size]
    pts=[
        (x,y,z)
        for x in (cx-hx,cx+hx)
        for y in (cy-hy,cy+hy)
        for z in (cz-hz,cz+hz)
    ]
    path.write_text(
        "\n".join(f"v {x} {y} {z}" for x,y,z in pts)+"\n",
        encoding="utf-8",
    )


def conditioning():
    return {
        "architecture_id":"test",
        "skeleton_id":"s",
        "target_height_mm":50,
        "skeleton_control":{
            "nodes":{
                "torso":{"position_mm_at_target_height":[0,0,10]},
                "head":{"position_mm_at_target_height":[0,0,25]},
            },
            "joints":[],
        },
        "visual_envelopes":[
            {
                "envelope_id":"torso","component_slot_id":"torso_shell",
                "shape":"box","center_node":"torso",
                "size_mm_at_target_height":[20,10,20],
            },
            {
                "envelope_id":"head","component_slot_id":"head_shell",
                "shape":"box","center_node":"head",
                "size_mm_at_target_height":[10,10,10],
            },
        ],
        "component_plan":{
            "generated_component_slots":[
                {"slot_id":"torso_shell","required":True},
                {"slot_id":"head_shell","required":True},
            ]
        },
        "mechanical_constraints":[],
    }


def job():
    return {
        "provider_id":"fake",
        "provider_job_id":"j",
        "pipeline_stage":"primary_generator",
        "requires_component_slot_mapping":True,
        "component_slots":{
            "required":[
                {"slot_id":"torso_shell","required":True},
                {"slot_id":"head_shell","required":True},
            ],
            "optional":[],
        },
    }


def run(paths):
    return {
        "provider_id":"fake",
        "provider_job_id":"j",
        "mode":"executed",
        "return_code":0,
        "execution_succeeded":True,
        "discovered_outputs":[str(p) for p in paths],
        "output_classification":{
            "component_candidates":[str(p) for p in paths]
        },
    }


def test_generator_continuation_stops_at_explicit_review_boundary(tmp_path: Path):
    head=tmp_path/"p0.obj"; torso=tmp_path/"p1.obj"
    box_obj(head,[0,0,5],[2,2,2])
    box_obj(torso,[0,0,2],[4,2,4])
    workspace=tmp_path/"work"
    manifest=continue_generator_run(
        conditioning(),job(),run([head,torso]),workspace
    )
    assert manifest["status"]=="mapping_review_required"
    assert manifest["mapping_review_required"] is True
    assert (workspace/"mapping-proposal.json").exists()
    assert (workspace/"mapping-review.html").exists()
    assert not (workspace/"output-mapping.json").exists()


def test_generator_continuation_rejects_critic_job(tmp_path: Path):
    head=tmp_path/"p0.obj"; torso=tmp_path/"p1.obj"
    box_obj(head,[0,0,5],[2,2,2])
    box_obj(torso,[0,0,2],[4,2,4])
    critic=job()
    critic["pipeline_stage"]="post_generation_critic"
    critic["requires_component_slot_mapping"]=False
    with pytest.raises(ValueError,match="critic runs"):
        continue_generator_run(
            conditioning(),critic,run([head,torso]),tmp_path/"work"
        )


def test_auto_mapping_selection_requires_strict_unique_proposal():
    proposal={
        "provider_id":"fake",
        "provider_job_id":"j",
        "architecture_id":"test",
        "automatic_promotion_allowed":True,
        "ambiguity":{
            "near_best_candidate_count":1,
            "distinct_near_best_mapping_count":1,
        },
        "global_alignment_candidates":[
            {
                "complete_visual_slot_assignment":True,
                "total_score":0.1,
            }
        ],
    }
    selection=automatic_mapping_selection(proposal,enabled=True)
    assert selection is not None
    assert selection["selected_candidate_index"]==0
    assert selection["automatic_selection"] is True
    assert selection["explicit_review_selection"] is True


def test_auto_mapping_selection_refuses_ambiguous_proposal():
    proposal={
        "provider_id":"fake",
        "provider_job_id":"j",
        "architecture_id":"test",
        "automatic_promotion_allowed":True,
        "ambiguity":{
            "near_best_candidate_count":2,
            "distinct_near_best_mapping_count":2,
        },
        "global_alignment_candidates":[
            {"complete_visual_slot_assignment":True,"total_score":0.1}
        ],
    }
    assert automatic_mapping_selection(proposal,enabled=True) is None
