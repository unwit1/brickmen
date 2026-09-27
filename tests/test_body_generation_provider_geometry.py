from pathlib import Path

import pytest

from tools.geometry.validate_body_generation_provider_geometry import (
    slot_target_box,
    transform_box,
    validate_provider_geometry,
)


IDENTITY=[
    1,0,0,0,
    0,1,0,0,
    0,0,1,0,
    0,0,0,1,
]


def conditioning():
    return {
        "architecture_id":"test",
        "skeleton_control":{
            "nodes":{
                "chest":{"position_mm_at_target_height":[0,0,20]},
                "shoulder":{"position_mm_at_target_height":[10,0,20]},
            }
        },
        "visual_envelopes":[
            {
                "envelope_id":"torso",
                "component_slot_id":"torso_shell",
                "shape":"box",
                "center_node":"chest",
                "size_mm_at_target_height":[20,10,20],
            }
        ],
        "mechanical_constraints":[
            {
                "joint_profile_id":"pin",
                "authority_class":"reference_only_not_manufacturing_authority",
                "placements":[
                    {
                        "placement_id":"left",
                        "anchor_mm_at_target_height":[10,0,20],
                        "reference_keepout_local_min_mm":[-2,-2,-2],
                        "reference_keepout_local_max_mm":[2,2,2],
                        "affected_component_slot_ids":["torso_shell"],
                        "boolean_subtraction_required_before_mechanical_validation":True,
                    }
                ],
            }
        ],
    }


def write_box_obj(path: Path, mn, mx):
    points=[
        (x,y,z)
        for x in (mn[0],mx[0])
        for y in (mn[1],mx[1])
        for z in (mn[2],mx[2])
    ]
    path.write_text(
        "\n".join(f"v {x} {y} {z}" for x,y,z in points)+"\n",
        encoding="utf-8",
    )


def mapping(path: Path, matrix=IDENTITY):
    return {
        "provider_id":"fake",
        "provider_job_id":"job",
        "components":[
            {
                "slot_id":"torso_shell",
                "path":str(path),
                "transform_status":"brickmen_mm_transform_supplied",
                "transform_matrix_to_brickmen_mm":matrix,
            }
        ],
    }


def test_slot_target_box_from_visual_envelope():
    box=slot_target_box(conditioning(),"torso_shell")
    assert box["min"]==pytest.approx([-10,-5,10])
    assert box["max"]==pytest.approx([10,5,30])


def test_transformed_provider_box_can_match_visual_target(tmp_path: Path):
    mesh=tmp_path/"torso.obj"
    write_box_obj(mesh,[-10,-5,10],[10,5,30])
    result=validate_provider_geometry(conditioning(),mapping(mesh))
    comp=result["components"][0]
    assert comp["visual_conformance"]["plausible"] is True
    assert result["summary"]["bbox_geometry_gate_passed"] is True
    # The torso bbox overlaps the shoulder hardware bbox, which is only a
    # potential material conflict until exact mesh/boolean analysis.
    assert comp["mechanical_keepout_checks"][0]["bbox_intersection"] is True
    assert result["summary"]["exact_collision_or_boolean_review_required"] is True


def test_missing_transform_blocks_geometry_gate(tmp_path: Path):
    mesh=tmp_path/"torso.obj"
    write_box_obj(mesh,[-10,-5,10],[10,5,30])
    out=mapping(mesh)
    out["components"][0]["transform_matrix_to_brickmen_mm"]=None
    out["components"][0]["transform_status"]="unreconciled_provider_frame"
    result=validate_provider_geometry(conditioning(),out)
    assert result["components"][0]["status"]=="transform_required"
    assert result["summary"]["bbox_geometry_gate_passed"] is False


def test_transform_box_converts_provider_units_to_mm():
    box={"min":[0,0,0],"max":[1,2,3]}
    scale_translate=[
        10,0,0,5,
        0,10,0,6,
        0,0,10,7,
        0,0,0,1,
    ]
    out=transform_box(box,scale_translate)
    assert out["min"]==pytest.approx([5,6,7])
    assert out["max"]==pytest.approx([15,26,37])
