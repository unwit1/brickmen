from pathlib import Path

import pytest

from tools.geometry.propose_body_provider_output_mapping import (
    propose_output_mapping,
)


def box_obj(path: Path, center, size):
    cx,cy,cz=center
    sx,sy,sz=[v/2 for v in size]
    pts=[
        (x,y,z)
        for x in (cx-sx,cx+sx)
        for y in (cy-sy,cy+sy)
        for z in (cz-sz,cz+sz)
    ]
    path.write_text(
        "\n".join(f"v {x} {y} {z}" for x,y,z in pts)+"\n",
        encoding="utf-8",
    )


def conditioning():
    return {
        "architecture_id":"test",
        "skeleton_control":{
            "nodes":{
                "torso_center":{"position_mm_at_target_height":[0,0,20]},
                "head_center":{"position_mm_at_target_height":[0,0,40]},
            }
        },
        "visual_envelopes":[
            {
                "envelope_id":"torso","component_slot_id":"torso_shell",
                "shape":"box","center_node":"torso_center",
                "size_mm_at_target_height":[20,10,20],
            },
            {
                "envelope_id":"head","component_slot_id":"head_shell",
                "shape":"box","center_node":"head_center",
                "size_mm_at_target_height":[10,10,10],
            },
        ],
        "component_plan":{
            "generated_component_slots":[
                {"slot_id":"torso_shell","required":True},
                {"slot_id":"head_shell","required":True},
            ]
        },
    }


def run(paths):
    return {
        "provider_id":"fake",
        "provider_job_id":"job",
        "output_classification":{
            "component_candidates":[str(p) for p in paths]
        },
    }


def job(stage="primary_generator"):
    return {
        "provider_id":"fake",
        "provider_job_id":"job",
        "pipeline_stage":stage,
        "requires_component_slot_mapping":stage!="post_generation_critic",
        "component_slots":{
            "required":[
                {"slot_id":"torso_shell","required":True},
                {"slot_id":"head_shell","required":True},
            ]
        },
    }


def test_geometry_mapper_assigns_large_and_small_parts_by_shape_position(tmp_path: Path):
    # Put provider geometry in a different scale/translation. Anonymous ordering
    # is deliberately reversed: head first, torso second.
    head=tmp_path/"part_00.obj"
    torso=tmp_path/"part_01.obj"
    box_obj(head,[10,0,8],[2,2,2])
    box_obj(torso,[10,0,4],[4,2,4])
    result=propose_output_mapping(
        conditioning(),run([head,torso]),provider_job=job()
    )
    best=result["global_alignment_candidates"][0]
    mapping={
        item["provider_part_path"]:item["slot_id"]
        for item in best["assignments"]
    }
    assert mapping[str(head)]=="head_shell"
    assert mapping[str(torso)]=="torso_shell"
    assert best["complete_visual_slot_assignment"] is True
    assert result["production_geometry_authority"] is False


def test_extra_part_remains_explicitly_unassigned(tmp_path: Path):
    head=tmp_path/"h.obj"; torso=tmp_path/"t.obj"; extra=tmp_path/"e.obj"
    box_obj(head,[0,0,8],[2,2,2])
    box_obj(torso,[0,0,4],[4,2,4])
    box_obj(extra,[20,20,20],[.5,.5,.5])
    result=propose_output_mapping(
        conditioning(),run([head,torso,extra]),provider_job=job()
    )
    best=result["global_alignment_candidates"][0]
    assert len(best["assignments"])==2
    assert len(best["unassigned_provider_parts"])==1


def test_critic_output_is_rejected_from_primary_slot_mapper(tmp_path: Path):
    mesh=tmp_path/"critic.obj"; box_obj(mesh,[0,0,0],[1,1,1])
    with pytest.raises(ValueError,match="critic outputs"):
        propose_output_mapping(
            conditioning(),run([mesh]),provider_job=job("post_generation_critic")
        )


def test_zero_extent_dummy_part_is_not_silently_mapped(tmp_path: Path):
    good=tmp_path/"good.obj"; dummy=tmp_path/"dummy.obj"
    box_obj(good,[0,0,0],[2,2,2])
    dummy.write_text("v 0 0 0\n",encoding="utf-8")
    result=propose_output_mapping(conditioning(),run([good,dummy]),provider_job=job())
    assert any(
        item["path"]==str(dummy)
        for item in result["invalid_or_degenerate_outputs"]
    )


def test_mapping_proposal_preserves_provider_part_provenance(tmp_path: Path):
    head=tmp_path/"part_03.obj"
    torso=tmp_path/"part_07.obj"
    box_obj(head,[10,0,8],[2,2,2])
    box_obj(torso,[10,0,4],[4,2,4])
    provider_run={
        "provider_id":"fake",
        "provider_job_id":"job",
        "output_classification":{
            "component_candidates":[str(head),str(torso)],
            "component_records":[
                {
                    "path":str(head),
                    "provider_part_id":"part_03",
                    "provider_part_index":3,
                    "provider_manifest":"/tmp/manifest.json",
                    "source_role":"generated_component",
                },
                {
                    "path":str(torso),
                    "provider_part_id":"part_07",
                    "provider_part_index":7,
                    "provider_manifest":"/tmp/manifest.json",
                    "source_role":"generated_component",
                },
            ],
        },
    }
    result=propose_output_mapping(
        conditioning(),provider_run,provider_job=job()
    )
    assigned={
        item["provider_part_path"]:item
        for item in result["global_alignment_candidates"][0]["assignments"]
    }
    assert assigned[str(head)]["provider_part_id"]=="part_03"
    assert assigned[str(head)]["provider_part_index"]==3
    assert assigned[str(torso)]["provider_part_id"]=="part_07"
    assert assigned[str(torso)]["provider_manifest"]=="/tmp/manifest.json"
