#!/usr/bin/env python3
"""Dependency-free mesh bounding-box inspection for provider outputs.

Supported:
- OBJ vertex records;
- STL (ASCII and binary);
- PLY (ASCII vertex tables);
- glTF/GLB using POSITION accessor min/max metadata.

The inspector returns geometry bounds only. It does not infer units, orientation,
semantic part identity, or manufacturing validity.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any, Iterable, Sequence


def _bounds(points: Iterable[Sequence[float]]) -> dict[str, Any]:
    pts=[tuple(map(float,p[:3])) for p in points]
    if not pts:
        raise ValueError("Mesh contains no readable 3D positions")
    mn=[min(p[i] for p in pts) for i in range(3)]
    mx=[max(p[i] for p in pts) for i in range(3)]
    return {
        "min":mn,
        "max":mx,
        "size":[mx[i]-mn[i] for i in range(3)],
        "center":[(mn[i]+mx[i])/2.0 for i in range(3)],
        "point_count_used":len(pts),
    }


def inspect_obj(path: Path) -> dict[str, Any]:
    points=[]
    for raw in path.read_text(encoding="utf-8",errors="replace").splitlines():
        line=raw.strip()
        if not line.startswith("v "):
            continue
        fields=line.split()
        if len(fields)>=4:
            points.append(tuple(map(float,fields[1:4])))
    result=_bounds(points)
    result.update({"format":"obj","bounds_source":"vertex_records"})
    return result


def inspect_stl(path: Path) -> dict[str, Any]:
    data=path.read_bytes()
    # Binary STL: 80-byte header + uint32 triangle count + 50 bytes per triangle.
    if len(data)>=84:
        tri_count=struct.unpack_from("<I",data,80)[0]
        expected=84+50*tri_count
        if expected==len(data):
            points=[]
            off=84
            for _ in range(tri_count):
                off+=12  # normal
                for _ in range(3):
                    points.append(struct.unpack_from("<3f",data,off))
                    off+=12
                off+=2
            result=_bounds(points)
            result.update({
                "format":"stl",
                "stl_encoding":"binary",
                "triangle_count":tri_count,
                "bounds_source":"triangle_vertices",
            })
            return result

    text=data.decode("utf-8",errors="replace")
    points=[]
    triangles=0
    for raw in text.splitlines():
        line=raw.strip()
        if line.startswith("vertex "):
            fields=line.split()
            if len(fields)>=4:
                points.append(tuple(map(float,fields[1:4])))
        elif line.startswith("facet normal"):
            triangles+=1
    result=_bounds(points)
    result.update({
        "format":"stl",
        "stl_encoding":"ascii",
        "triangle_count":triangles,
        "bounds_source":"triangle_vertices",
    })
    return result


def inspect_ply(path: Path) -> dict[str, Any]:
    data=path.read_bytes()
    marker=b"end_header"
    idx=data.find(marker)
    if idx<0:
        raise ValueError("PLY header missing end_header")
    line_end=data.find(b"\n",idx)
    if line_end<0:
        line_end=len(data)-1
    header=data[:line_end+1].decode("ascii",errors="replace").splitlines()
    fmt=None
    vertex_count=None
    props=[]
    in_vertex=False
    for line in header:
        fields=line.strip().split()
        if not fields:
            continue
        if fields[0]=="format":
            fmt=fields[1]
        elif fields[:2]==["element","vertex"]:
            vertex_count=int(fields[2]); in_vertex=True; props=[]
        elif fields[0]=="element" and fields[1]!="vertex":
            in_vertex=False
        elif fields[0]=="property" and in_vertex:
            if len(fields)>=3 and fields[1]!="list":
                props.append(fields[2])
    if fmt!="ascii":
        raise ValueError(
            f"PLY format {fmt!r} not supported without optional binary parser"
        )
    if vertex_count is None:
        raise ValueError("PLY has no vertex element")
    try:
        xi,yi,zi=(props.index("x"),props.index("y"),props.index("z"))
    except ValueError as exc:
        raise ValueError("PLY vertex element needs x/y/z properties") from exc
    body=data[line_end+1:].decode("utf-8",errors="replace").splitlines()
    points=[]
    for raw in body[:vertex_count]:
        fields=raw.strip().split()
        if len(fields)>max(xi,yi,zi):
            points.append((float(fields[xi]),float(fields[yi]),float(fields[zi])))
    result=_bounds(points)
    result.update({
        "format":"ply",
        "ply_encoding":"ascii",
        "declared_vertex_count":vertex_count,
        "bounds_source":"vertex_records",
    })
    return result


def _gltf_position_accessor_indices(doc: dict[str, Any]) -> list[int]:
    result=[]
    for mesh in doc.get("meshes",[]):
        for primitive in mesh.get("primitives",[]):
            attrs=primitive.get("attributes",{})
            if "POSITION" in attrs:
                result.append(int(attrs["POSITION"]))
    return result


def _gltf_bounds_from_accessors(doc: dict[str, Any]) -> dict[str, Any]:
    points=[]
    used=[]
    accessors=doc.get("accessors",[])
    for index in _gltf_position_accessor_indices(doc):
        if index<0 or index>=len(accessors):
            continue
        accessor=accessors[index]
        mn=accessor.get("min")
        mx=accessor.get("max")
        if (
            isinstance(mn,list) and len(mn)>=3
            and isinstance(mx,list) and len(mx)>=3
        ):
            points.append(mn[:3]); points.append(mx[:3]); used.append(index)
    if not points:
        raise ValueError(
            "glTF/GLB POSITION accessors do not expose min/max metadata"
        )
    result=_bounds(points)
    result["point_count_used"]=len(points)
    result["position_accessor_indices"]=used
    result["bounds_source"]="position_accessor_minmax"
    return result


def inspect_gltf(path: Path) -> dict[str, Any]:
    doc=json.loads(path.read_text(encoding="utf-8"))
    result=_gltf_bounds_from_accessors(doc)
    result["format"]="gltf"
    return result


def inspect_glb(path: Path) -> dict[str, Any]:
    data=path.read_bytes()
    if len(data)<20 or data[:4]!=b"glTF":
        raise ValueError("Invalid GLB header")
    version,total=struct.unpack_from("<II",data,4)
    if version!=2:
        raise ValueError(f"Unsupported GLB version {version}")
    if total>len(data):
        raise ValueError("GLB declared length exceeds file size")
    offset=12
    doc=None
    while offset+8<=total:
        length,chunk_type=struct.unpack_from("<II",data,offset)
        offset+=8
        chunk=data[offset:offset+length]
        offset+=length
        if chunk_type==0x4E4F534A:  # JSON
            doc=json.loads(chunk.decode("utf-8").rstrip(" \t\r\n\x00"))
            break
    if doc is None:
        raise ValueError("GLB has no JSON chunk")
    result=_gltf_bounds_from_accessors(doc)
    result.update({"format":"glb","glb_version":version})
    return result


def inspect_mesh_bounds(path: str | Path) -> dict[str, Any]:
    p=Path(path)
    if not p.is_file():
        raise ValueError(f"Mesh path is not a file: {p}")
    ext=p.suffix.lower()
    if ext==".obj":
        result=inspect_obj(p)
    elif ext==".stl":
        result=inspect_stl(p)
    elif ext==".ply":
        result=inspect_ply(p)
    elif ext==".gltf":
        result=inspect_gltf(p)
    elif ext==".glb":
        result=inspect_glb(p)
    else:
        raise ValueError(f"Unsupported mesh format for bounds: {ext}")
    result["path"]=str(p)
    result["units"]="unknown_provider_units"
    result["coordinate_frame"]="unknown_provider_frame"
    result["production_geometry_authority"]=False
    return result


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("mesh")
    parser.add_argument("-o","--output",default=None)
    args=parser.parse_args()
    result=inspect_mesh_bounds(args.mesh)
    payload=json.dumps(result,indent=2)+"\n"
    if args.output:
        Path(args.output).write_text(payload,encoding="utf-8")
    else:
        print(payload,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
