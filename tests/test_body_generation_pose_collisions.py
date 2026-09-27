from pathlib import Path

from tools.geometry.validate_body_generation_pose_collisions import (
    triangle_intersection_witness,
    validate_pose_collisions,
)


IDENTITY=[
    1,0,0,0,
    0,1,0,0,
    0,0,1,0,
    0,0,0,1,
]


def tri_obj(path: Path, points):
    path.write_text(
        "\n".join(
            [*(f"v {x} {y} {z}" for x,y,z in points),"f 1 2 3"]
        )+"\n",
        encoding="utf-8",
    )


def conditioning():
    return {
        "architecture_id":"test",
        "skeleton_control":{
            "nodes":{
                "joint":{"position_mm_at_target_height":[0,0,0]}
            },
            "joints":[
                {
                    "joint_id":"joint",
                    "parent_node":"joint",
                    "child_node":"tip",
                    "axis":[0,0,1],
                    "range_deg":[0,0],
                    "visual_envelope_ids":["moving_env"],
                }
            ],
        },
        "visual_envelopes":[
            {
                "envelope_id":"moving_env",
                "component_slot_id":"moving_shell",
            },
            {
                "envelope_id":"static_env",
                "component_slot_id":"static_shell",
            },
        ],
    }


def mapping(moving,static):
    return {
        "provider_id":"fake","provider_job_id":"j",
        "components":[
            {
                "slot_id":"moving_shell","path":str(moving),
                "transform_matrix_to_brickmen_mm":IDENTITY,
            },
            {
                "slot_id":"static_shell","path":str(static),
                "transform_matrix_to_brickmen_mm":IDENTITY,
            },
        ],
    }


def validated_contact(status="validated_prototype"):
    return {
        "architecture_id":"test",
        "joints":[
            {
                "joint_id":"joint",
                "component_pairs":[["moving_shell","static_shell"]],
                "allowed_contact_regions_mm":[
                    {
                        "region_id":"r",
                        "shape":"aabb",
                        "min_mm":[-.2,-.2,-.2],
                        "max_mm":[.2,.2,.2],
                        "status":status,
                        "authority":"physical_test",
                        "source_validation_id":"v1",
                    }
                ],
            }
        ],
    }


def test_triangle_witness_for_crossing_triangles():
    a=[(-1,0,0),(1,0,0),(0,1,0)]
    b=[(0,-1,-1),(0,1,1),(0,1,-1)]
    hit=triangle_intersection_witness(a,b)
    assert hit is not None
    assert abs(hit[0])<1e-8


def test_disallowed_collision_fails_without_validated_region(tmp_path: Path):
    moving=tmp_path/"m.obj"
    static=tmp_path/"s.obj"
    tri_obj(moving,[(-1,0,0),(1,0,0),(0,1,0)])
    tri_obj(static,[(0,-1,-1),(0,1,1),(0,1,-1)])
    result=validate_pose_collisions(
        conditioning(),mapping(moving,static),samples_per_joint=1
    )
    assert result["summary"]["sampled_pose_collision_gate_passed"] is False
    assert result["summary"]["disallowed_collision_count"]>0


def test_candidate_contact_region_does_not_suppress(tmp_path: Path):
    moving=tmp_path/"m.obj"
    static=tmp_path/"s.obj"
    tri_obj(moving,[(-1,0,0),(1,0,0),(0,1,0)])
    tri_obj(static,[(0,-1,-1),(0,1,1),(0,1,-1)])
    result=validate_pose_collisions(
        conditioning(),mapping(moving,static),
        contact_regions=validated_contact("candidate"),
        samples_per_joint=1,
    )
    assert result["summary"]["sampled_pose_collision_gate_passed"] is False


def test_validated_contact_region_can_suppress_joint_local_contact(tmp_path: Path):
    moving=tmp_path/"m.obj"
    static=tmp_path/"s.obj"
    tri_obj(moving,[(-1,0,0),(1,0,0),(0,1,0)])
    tri_obj(static,[(0,-1,-1),(0,1,1),(0,1,-1)])
    result=validate_pose_collisions(
        conditioning(),mapping(moving,static),
        contact_regions=validated_contact(),
        samples_per_joint=1,
    )
    assert result["summary"]["sampled_pose_collision_gate_passed"] is True
    assert result["summary"]["allowed_collision_count"]>0
    assert result["summary"]["disallowed_collision_count"]==0


def test_contact_region_cannot_suppress_unrelated_pair(tmp_path: Path):
    moving=tmp_path/"m.obj"
    static=tmp_path/"s.obj"
    tri_obj(moving,[(-1,0,0),(1,0,0),(0,1,0)])
    tri_obj(static,[(0,-1,-1),(0,1,1),(0,1,-1)])
    contact=validated_contact()
    contact["joints"][0]["component_pairs"]=[["moving_shell","other_shell"]]
    result=validate_pose_collisions(
        conditioning(),mapping(moving,static),
        contact_regions=contact,samples_per_joint=1,
    )
    assert result["summary"]["sampled_pose_collision_gate_passed"] is False
