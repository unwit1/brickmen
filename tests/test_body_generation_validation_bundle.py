from pathlib import Path

from tools.geometry.run_body_generation_validation_bundle import (
    run_validation_bundle,
)


IDENTITY=[
    1,0,0,0,
    0,1,0,0,
    0,0,1,0,
    0,0,0,1,
]


def cube_obj(path: Path, center):
    cx,cy,cz=center
    d=1
    v=[
        (cx-d,cy-d,cz-d),(cx+d,cy-d,cz-d),
        (cx+d,cy+d,cz-d),(cx-d,cy+d,cz-d),
        (cx-d,cy-d,cz+d),(cx+d,cy-d,cz+d),
        (cx+d,cy+d,cz+d),(cx-d,cy+d,cz+d),
    ]
    f=[
        (1,3,2),(1,4,3),
        (5,6,7),(5,7,8),
        (1,2,6),(1,6,5),
        (2,3,7),(2,7,6),
        (3,4,8),(3,8,7),
        (4,1,5),(4,5,8),
    ]
    path.write_text(
        "\n".join(
            [*(f"v {x} {y} {z}" for x,y,z in v),
             *(f"f {a} {b} {c}" for a,b,c in f)]
        )+"\n",encoding="utf-8"
    )


def conditioning():
    return {
        "architecture_id":"test",
        "skeleton_id":"test-skel",
        "target_height_mm":100,
        "skeleton_control":{
            "nodes":{
                "joint":{"position_mm_at_target_height":[0,0,0]},
                "moving_center":{"position_mm_at_target_height":[5,0,0]},
                "static_center":{"position_mm_at_target_height":[50,0,0]},
            },
            "joints":[
                {
                    "joint_id":"joint","parent_node":"joint","child_node":"moving_center",
                    "axis":[0,0,1],"range_deg":[0,10],
                    "visual_envelope_ids":["moving_env"],
                }
            ],
        },
        "visual_envelopes":[
            {
                "envelope_id":"moving_env","component_slot_id":"moving_shell",
                "shape":"box","center_node":"moving_center",
                "size_mm_at_target_height":[2,2,2],
            },
            {
                "envelope_id":"static_env","component_slot_id":"static_shell",
                "shape":"box","center_node":"static_center",
                "size_mm_at_target_height":[2,2,2],
            },
        ],
        "mechanical_constraints":[],
    }


def mapping(moving,static):
    return {
        "provider_id":"fake","provider_job_id":"j",
        "acceptance":{"structurally_complete":True},
        "components":[
            {
                "slot_id":"moving_shell","path":str(moving),
                "transform_status":"brickmen_mm_transform_supplied",
                "transform_matrix_to_brickmen_mm":IDENTITY,
            },
            {
                "slot_id":"static_shell","path":str(static),
                "transform_status":"brickmen_mm_transform_supplied",
                "transform_matrix_to_brickmen_mm":IDENTITY,
            },
        ],
    }


def test_complete_validation_bundle_for_separated_closed_components(tmp_path: Path):
    moving=tmp_path/"moving.obj"; static=tmp_path/"static.obj"
    cube_obj(moving,[5,0,0]); cube_obj(static,[50,0,0])
    out=tmp_path/"bundle"
    manifest=run_validation_bundle(
        conditioning(),mapping(moving,static),out
    )
    assert manifest["generated_geometry_validation_passed"] is True
    assert manifest["pipeline_production_ready"] is True
    for name in (
        "geometry-validation.json",
        "mesh-quality.json",
        "exact-keepout-validation.json",
        "pose-collision-validation.json",
        "continuous-collision-validation.json",
        "pipeline-state.json",
        "bundle-manifest.json",
    ):
        assert (out/name).exists()
