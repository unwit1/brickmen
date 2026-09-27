from pathlib import Path

from tools.geometry.validate_body_generation_mesh_quality import (
    audit_triangles,
    validate_mesh_quality,
)


IDENTITY=[
    1,0,0,0,
    0,1,0,0,
    0,0,1,0,
    0,0,0,1,
]


def cube(path: Path, open_top=False):
    v=[
        (-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
        (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1),
    ]
    f=[
        (1,3,2),(1,4,3),
        (5,6,7),(5,7,8),
        (1,2,6),(1,6,5),
        (2,3,7),(2,7,6),
        (3,4,8),(3,8,7),
        (4,1,5),(4,5,8),
    ]
    if open_top:
        f=f[:-2]
    path.write_text(
        "\n".join(
            [*(f"v {x} {y} {z}" for x,y,z in v),
             *(f"f {a} {b} {c}" for a,b,c in f)]
        )+"\n",encoding="utf-8"
    )


def mapping(path):
    return {
        "provider_id":"fake","provider_job_id":"j",
        "components":[
            {
                "slot_id":"torso_shell","path":str(path),
                "transform_status":"brickmen_mm_transform_supplied",
                "transform_matrix_to_brickmen_mm":IDENTITY,
            }
        ],
    }


def test_closed_cube_passes(tmp_path: Path):
    p=tmp_path/"cube.obj"; cube(p)
    result=validate_mesh_quality(mapping(p))
    audit=result["components"][0]["audit"]
    assert audit["closed_two_manifold_candidate"] is True
    assert audit["boundary_edge_count"]==0
    assert audit["nonmanifold_edge_count"]==0
    assert audit["absolute_volume"]>0
    assert result["summary"]["mesh_quality_gate_passed"] is True


def test_open_cube_fails(tmp_path: Path):
    p=tmp_path/"open.obj"; cube(p,open_top=True)
    result=validate_mesh_quality(mapping(p))
    assert result["summary"]["mesh_quality_gate_passed"] is False
    assert "open_boundary_edges" in result["components"][0]["errors"]


def test_duplicate_face_is_flagged():
    tri=((0,0,0),(1,0,0),(0,1,0))
    audit=audit_triangles([tri,tri])
    assert audit["duplicate_triangle_count"]==1
