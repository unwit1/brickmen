import json
import struct
from pathlib import Path

import pytest

from tools.geometry.inspect_mesh_bounds import inspect_mesh_bounds


def test_obj_bounds(tmp_path: Path):
    p=tmp_path/"x.obj"
    p.write_text("v -1 2 3\nv 4 -5 6\nv 0 1 -2\nf 1 2 3\n",encoding="utf-8")
    result=inspect_mesh_bounds(p)
    assert result["min"]==pytest.approx([-1,-5,-2])
    assert result["max"]==pytest.approx([4,2,6])
    assert result["units"]=="unknown_provider_units"


def test_ascii_stl_bounds(tmp_path: Path):
    p=tmp_path/"x.stl"
    p.write_text(
        "solid x\nfacet normal 0 0 1\nouter loop\n"
        "vertex 0 0 0\nvertex 2 0 0\nvertex 0 3 4\n"
        "endloop\nendfacet\nendsolid x\n",encoding="utf-8"
    )
    result=inspect_mesh_bounds(p)
    assert result["size"]==pytest.approx([2,3,4])


def test_ascii_ply_bounds(tmp_path: Path):
    p=tmp_path/"x.ply"
    p.write_text(
        "ply\nformat ascii 1.0\nelement vertex 2\n"
        "property float x\nproperty float y\nproperty float z\n"
        "end_header\n-2 0 1\n5 3 -4\n",encoding="utf-8"
    )
    result=inspect_mesh_bounds(p)
    assert result["min"]==pytest.approx([-2,0,-4])
    assert result["max"]==pytest.approx([5,3,1])


def test_glb_uses_position_accessor_minmax(tmp_path: Path):
    doc={
        "asset":{"version":"2.0"},
        "accessors":[
            {"componentType":5126,"count":3,"type":"VEC3",
             "min":[-1,-2,-3],"max":[4,5,6]}
        ],
        "meshes":[{"primitives":[{"attributes":{"POSITION":0}}]}],
    }
    raw=json.dumps(doc,separators=(",",":")).encode("utf-8")
    pad=(-len(raw))%4
    raw+=b" "*pad
    total=12+8+len(raw)
    data=b"glTF"+struct.pack("<II",2,total)+struct.pack("<II",len(raw),0x4E4F534A)+raw
    p=tmp_path/"x.glb"; p.write_bytes(data)
    result=inspect_mesh_bounds(p)
    assert result["min"]==pytest.approx([-1,-2,-3])
    assert result["max"]==pytest.approx([4,5,6])
    assert result["bounds_source"]=="position_accessor_minmax"


def test_unsupported_extension_rejected(tmp_path: Path):
    p=tmp_path/"x.fbx"; p.write_bytes(b"x")
    with pytest.raises(ValueError,match="Unsupported mesh format"):
        inspect_mesh_bounds(p)
