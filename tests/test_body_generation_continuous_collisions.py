from pathlib import Path

import pytest

from tools.geometry.validate_body_generation_continuous_collisions import (
    swept_point_bounds,
    validate_continuous_rotation_collisions,
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
        )+"\n",encoding="utf-8"
    )


def conditioning(angle_range=(0,90)):
    return {
        "architecture_id":"test",
        "skeleton_control":{
            "nodes":{
                "joint":{"position_mm_at_target_height":[0,0,0]}
            },
            "joints":[
                {
                    "joint_id":"joint","parent_node":"joint","child_node":"tip",
                    "axis":[0,0,1],"range_deg":list(angle_range),
                    "visual_envelope_ids":["moving_env"],
                }
            ],
        },
        "visual_envelopes":[
            {"envelope_id":"moving_env","component_slot_id":"moving_shell"},
            {"envelope_id":"static_env","component_slot_id":"static_shell"},
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


def contact_region():
    return {
        "joints":[
            {
                "joint_id":"joint",
                "component_pairs":[["moving_shell","static_shell"]],
                "allowed_contact_regions_mm":[
                    {
                        "region_id":"wide",
                        "shape":"aabb",
                        "min_mm":[-2,-2,-2],
                        "max_mm":[2,2,2],
                        "status":"validated_prototype",
                        "authority":"test",
                        "source_validation_id":"test",
                    }
                ],
            }
        ],
    }


def test_swept_point_bounds_quarter_circle():
    box=swept_point_bounds([1,0,0],[0,0,0],[0,0,1],0,90)
    assert box["min"][0]==pytest.approx(0,abs=1e-9)
    assert box["max"][0]==pytest.approx(1)
    assert box["min"][1]==pytest.approx(0,abs=1e-9)
    assert box["max"][1]==pytest.approx(1)
    assert box["min"][2]==pytest.approx(0)
    assert box["max"][2]==pytest.approx(0)


def test_far_static_triangle_is_continuously_proven_safe(tmp_path: Path):
    moving=tmp_path/"m.obj"; static=tmp_path/"s.obj"
    tri_obj(moving,[(1,0,0),(1,.1,0),(1,0,.1)])
    tri_obj(static,[(10,10,0),(11,10,0),(10,11,0)])
    result=validate_continuous_rotation_collisions(
        conditioning(),mapping(moving,static)
    )
    assert result["summary"]["continuous_rotation_collision_gate_passed"] is True
    assert result["summary"]["unresolved_interval_count"]==0


def test_sampled_disallowed_collision_fails_continuous_gate(tmp_path: Path):
    moving=tmp_path/"m.obj"; static=tmp_path/"s.obj"
    tri_obj(moving,[(-1,0,0),(1,0,0),(0,1,0)])
    tri_obj(static,[(0,-1,-1),(0,1,1),(0,1,-1)])
    result=validate_continuous_rotation_collisions(
        conditioning((0,0)),mapping(moving,static)
    )
    assert result["summary"]["continuous_rotation_collision_gate_passed"] is False
    assert result["summary"]["disallowed_collision_count"]>0


def test_full_possible_overlap_inside_validated_region_is_acceptable(tmp_path: Path):
    moving=tmp_path/"m.obj"; static=tmp_path/"s.obj"
    tri_obj(moving,[(-.5,0,0),(.5,0,0),(0,.5,0)])
    tri_obj(static,[(0,-.5,-.5),(0,.5,.5),(0,.5,-.5)])
    result=validate_continuous_rotation_collisions(
        conditioning((0,0)),mapping(moving,static),
        contact_regions=contact_region()
    )
    assert result["summary"]["continuous_rotation_collision_gate_passed"] is True
