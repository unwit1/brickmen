import json
import struct
from pathlib import Path

import pytest

from tools.geometry.inspect_mesh_triangles import load_mesh_triangles


def test_obj_face_fan_triangulation(tmp_path: Path):
    p=tmp_path/"q.obj"
    p.write_text(
        "v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nf 1 2 3 4\n",
        encoding="utf-8"
    )
    tris=load_mesh_triangles(p)
    assert len(tris)==2


def test_ascii_stl_triangle(tmp_path: Path):
    p=tmp_path/"x.stl"
    p.write_text(
        "solid x\nfacet normal 0 0 1\nouter loop\n"
        "vertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\n"
        "endloop\nendfacet\nendsolid\n",encoding="utf-8"
    )
    tris=load_mesh_triangles(p)
    assert len(tris)==1


def test_ascii_ply_face(tmp_path: Path):
    p=tmp_path/"x.ply"
    p.write_text(
        "ply\nformat ascii 1.0\nelement vertex 3\n"
        "property float x\nproperty float y\nproperty float z\n"
        "element face 1\nproperty list uchar int vertex_indices\n"
        "end_header\n0 0 0\n1 0 0\n0 1 0\n3 0 1 2\n",
        encoding="utf-8"
    )
    assert len(load_mesh_triangles(p))==1


def test_glb_triangle_and_node_translation(tmp_path: Path):
    positions=struct.pack(
        "<9f",
        0,0,0,
        1,0,0,
        0,1,0,
    )
    indices=struct.pack("<3H",0,1,2)
    blob=positions+indices
    doc={
        "asset":{"version":"2.0"},
        "buffers":[{"byteLength":len(blob)}],
        "bufferViews":[
            {"buffer":0,"byteOffset":0,"byteLength":len(positions)},
            {"buffer":0,"byteOffset":len(positions),"byteLength":len(indices)},
        ],
        "accessors":[
            {"bufferView":0,"componentType":5126,"count":3,"type":"VEC3"},
            {"bufferView":1,"componentType":5123,"count":3,"type":"SCALAR"},
        ],
        "meshes":[{"primitives":[{"attributes":{"POSITION":0},"indices":1}]}],
        "nodes":[{"mesh":0,"translation":[5,6,7]}],
        "scenes":[{"nodes":[0]}],
        "scene":0,
    }
    raw=json.dumps(doc,separators=(",",":")).encode()
    raw+=b" "*((-len(raw))%4)
    blob+=b"\x00"*((-len(blob))%4)
    total=12+8+len(raw)+8+len(blob)
    data=(
        b"glTF"+struct.pack("<II",2,total)
        +struct.pack("<II",len(raw),0x4E4F534A)+raw
        +struct.pack("<II",len(blob),0x004E4942)+blob
    )
    p=tmp_path/"x.glb"; p.write_bytes(data)
    tri=load_mesh_triangles(p)[0]
    assert tri[0]==pytest.approx((5,6,7))
    assert tri[1]==pytest.approx((6,6,7))
    assert tri[2]==pytest.approx((5,7,7))
