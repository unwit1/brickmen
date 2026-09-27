from pathlib import Path

from tools.geometry.validate_body_generation_exact_keepouts import (
    mesh_topology_summary,
    triangle_intersects_aabb,
    validate_exact_keepouts,
)


IDENTITY=[
    1,0,0,0,
    0,1,0,0,
    0,0,1,0,
    0,0,0,1,
]


def cube_obj(path: Path, mn, mx):
    x0,y0,z0=mn; x1,y1,z1=mx
    verts=[
        (x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
        (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1),
    ]
    faces=[
        (1,2,3),(1,3,4),
        (5,7,6),(5,8,7),
        (1,5,6),(1,6,2),
        (2,6,7),(2,7,3),
        (3,7,8),(3,8,4),
        (4,8,5),(4,5,1),
    ]
    path.write_text(
        "\n".join(
            [*(f"v {x} {y} {z}" for x,y,z in verts),
             *(f"f {a} {b} {c}" for a,b,c in faces)]
        )+"\n",encoding="utf-8"
    )


def conditioning(box_min,box_max):
    # Encode desired keepout via anchor=0 and local min/max.
    return {
        "architecture_id":"test",
        "mechanical_constraints":[
            {
                "joint_profile_id":"pin",
                "authority_class":"reference_only_not_manufacturing_authority",
                "placements":[
                    {
                        "placement_id":"k",
                        "anchor_mm_at_target_height":[0,0,0],
                        "reference_keepout_local_min_mm":box_min,
                        "reference_keepout_local_max_mm":box_max,
                        "affected_component_slot_ids":["torso_shell"],
                    }
                ],
            }
        ],
    }


def mapping(path: Path):
    return {
        "provider_id":"fake",
        "provider_job_id":"j",
        "components":[
            {
                "slot_id":"torso_shell",
                "path":str(path),
                "transform_matrix_to_brickmen_mm":IDENTITY,
            }
        ],
    }


def test_triangle_box_sat():
    tri=[(-1,0,0),(1,0,0),(0,1,0)]
    assert triangle_intersects_aabb(
        tri,{"min":[-.2,-.2,-.2],"max":[.2,.2,.2]}
    )
    assert not triangle_intersects_aabb(
        tri,{"min":[5,5,5],"max":[6,6,6]}
    )


def test_keepout_fully_inside_closed_solid_is_detected(tmp_path: Path):
    mesh=tmp_path/"cube.obj"; cube_obj(mesh,[-5,-5,-5],[5,5,5])
    result=validate_exact_keepouts(
        conditioning([-1,-1,-1],[1,1,1]),mapping(mesh)
    )
    keep=result["components"][0]["keepouts"][0]
    assert keep["status"]=="keepout_inside_solid_material"
    assert keep["inside_sample_count"]>0
    assert result["summary"]["exact_keepout_gate_passed"] is False


def test_keepout_outside_closed_mesh_passes(tmp_path: Path):
    mesh=tmp_path/"cube.obj"; cube_obj(mesh,[-1,-1,-1],[1,1,1])
    result=validate_exact_keepouts(
        conditioning([5,5,5],[6,6,6]),mapping(mesh)
    )
    keep=result["components"][0]["keepouts"][0]
    assert keep["status"]=="keepout_geometrically_empty"
    assert result["summary"]["exact_keepout_gate_passed"] is True


def test_keepout_crossing_surface_is_detected(tmp_path: Path):
    mesh=tmp_path/"cube.obj"; cube_obj(mesh,[-1,-1,-1],[1,1,1])
    result=validate_exact_keepouts(
        conditioning([.5,-.2,-.2],[1.5,.2,.2]),mapping(mesh)
    )
    keep=result["components"][0]["keepouts"][0]
    assert keep["surface_intersection_triangle_count"]>0
    assert keep["status"]=="keepout_surface_intersection"
