#!/usr/bin/env python3
"""Dependency-free triangle extraction for common provider mesh formats.

Supported:
- OBJ;
- STL (ASCII/binary);
- PLY ASCII;
- glTF 2.0 / GLB 2.0 uncompressed primitives.

glTF support reads accessor buffers and applies scene-node transforms. Draco or
other compressed primitive extensions are intentionally rejected rather than
silently approximated.
"""

from __future__ import annotations

import argparse
import base64
import json
import math
from pathlib import Path
import struct
from typing import Any, Iterable, Sequence


Triangle = tuple[
    tuple[float,float,float],
    tuple[float,float,float],
    tuple[float,float,float],
]


def _tri(a,b,c) -> Triangle:
    return (
        tuple(map(float,a[:3])),
        tuple(map(float,b[:3])),
        tuple(map(float,c[:3])),
    )


def load_obj_triangles(path: Path) -> list[Triangle]:
    vertices=[]
    triangles=[]
    for raw in path.read_text(encoding="utf-8",errors="replace").splitlines():
        line=raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("v "):
            f=line.split()
            vertices.append(tuple(map(float,f[1:4])))
        elif line.startswith("f "):
            refs=line.split()[1:]
            idx=[]
            for ref in refs:
                raw_i=int(ref.split("/")[0])
                i=raw_i-1 if raw_i>0 else len(vertices)+raw_i
                idx.append(i)
            for k in range(1,len(idx)-1):
                triangles.append(_tri(vertices[idx[0]],vertices[idx[k]],vertices[idx[k+1]]))
    return triangles


def load_stl_triangles(path: Path) -> list[Triangle]:
    data=path.read_bytes()
    if len(data)>=84:
        count=struct.unpack_from("<I",data,80)[0]
        if 84+50*count==len(data):
            out=[]
            off=84
            for _ in range(count):
                off+=12
                pts=[]
                for _ in range(3):
                    pts.append(struct.unpack_from("<3f",data,off)); off+=12
                off+=2
                out.append(_tri(*pts))
            return out
    points=[]
    out=[]
    for raw in data.decode("utf-8",errors="replace").splitlines():
        line=raw.strip()
        if line.startswith("vertex "):
            f=line.split()
            points.append(tuple(map(float,f[1:4])))
            if len(points)==3:
                out.append(_tri(*points)); points=[]
    return out


def _parse_ply_header(data: bytes) -> tuple[list[str],int,int,int]:
    marker=b"end_header"
    idx=data.find(marker)
    if idx<0:
        raise ValueError("PLY header missing end_header")
    end=data.find(b"\n",idx)
    if end<0: end=len(data)-1
    header=data[:end+1].decode("ascii",errors="replace").splitlines()
    return header,end+1,idx,end


def load_ply_triangles(path: Path) -> list[Triangle]:
    data=path.read_bytes()
    header,body_offset,_,_=_parse_ply_header(data)
    fmt=None
    vertex_count=0
    face_count=0
    vertex_props=[]
    current=None
    for line in header:
        f=line.strip().split()
        if not f: continue
        if f[0]=="format": fmt=f[1]
        elif f[0]=="element":
            current=f[1]
            if current=="vertex": vertex_count=int(f[2])
            elif current=="face": face_count=int(f[2])
        elif f[0]=="property" and current=="vertex" and len(f)>=3 and f[1]!="list":
            vertex_props.append(f[2])
    if fmt!="ascii":
        raise ValueError("Triangle extraction supports ASCII PLY only")
    try:
        xi,yi,zi=(vertex_props.index("x"),vertex_props.index("y"),vertex_props.index("z"))
    except ValueError as exc:
        raise ValueError("PLY vertices require x/y/z") from exc
    lines=data[body_offset:].decode("utf-8",errors="replace").splitlines()
    vertices=[]
    for raw in lines[:vertex_count]:
        f=raw.split()
        vertices.append((float(f[xi]),float(f[yi]),float(f[zi])))
    out=[]
    face_lines=lines[vertex_count:vertex_count+face_count]
    for raw in face_lines:
        f=raw.split()
        if not f: continue
        n=int(f[0])
        idx=list(map(int,f[1:1+n]))
        for k in range(1,len(idx)-1):
            out.append(_tri(vertices[idx[0]],vertices[idx[k]],vertices[idx[k+1]]))
    return out


COMPONENT_FORMAT={
    5120:"b",5121:"B",5122:"h",5123:"H",5125:"I",5126:"f"
}
TYPE_COUNT={
    "SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,
    "MAT2":4,"MAT3":9,"MAT4":16
}


def _load_gltf(path: Path) -> tuple[dict[str,Any],list[bytes]]:
    if path.suffix.lower()==".glb":
        data=path.read_bytes()
        if len(data)<12 or data[:4]!=b"glTF":
            raise ValueError("Invalid GLB header")
        version,total=struct.unpack_from("<II",data,4)
        if version!=2:
            raise ValueError(f"Unsupported GLB version {version}")
        off=12; doc=None; bins=[]
        while off+8<=total:
            length,kind=struct.unpack_from("<II",data,off); off+=8
            chunk=data[off:off+length]; off+=length
            if kind==0x4E4F534A:
                doc=json.loads(chunk.decode("utf-8").rstrip(" \t\r\n\x00"))
            elif kind==0x004E4942:
                bins.append(chunk)
        if doc is None:
            raise ValueError("GLB has no JSON chunk")
        buffers=[]
        bin_iter=iter(bins)
        for buf in doc.get("buffers",[]):
            uri=buf.get("uri")
            if uri is None:
                try: buffers.append(next(bin_iter))
                except StopIteration:
                    raise ValueError("GLB missing BIN chunk")
            else:
                buffers.append(_load_uri(path.parent,uri))
        return doc,buffers

    doc=json.loads(path.read_text(encoding="utf-8"))
    return doc,[_load_uri(path.parent,b.get("uri")) for b in doc.get("buffers",[])]


def _load_uri(base: Path, uri: str | None) -> bytes:
    if not uri:
        raise ValueError("glTF external buffer URI missing")
    if uri.startswith("data:"):
        if ";base64," not in uri:
            raise ValueError("Only base64 data URIs supported")
        return base64.b64decode(uri.split(";base64,",1)[1])
    return (base/uri).read_bytes()


def _accessor_values(
    doc: Mapping[str,Any],
    buffers: Sequence[bytes],
    index: int,
) -> list[tuple[Any,...]]:
    accessor=doc["accessors"][index]
    if accessor.get("sparse"):
        raise ValueError("Sparse glTF accessors are not supported")
    if "bufferView" not in accessor:
        raise ValueError("glTF accessor has no bufferView")
    view=doc["bufferViews"][accessor["bufferView"]]
    buffer=buffers[view["buffer"]]
    component_type=int(accessor["componentType"])
    if component_type not in COMPONENT_FORMAT:
        raise ValueError(f"Unsupported glTF componentType {component_type}")
    fmt=COMPONENT_FORMAT[component_type]
    component_size=struct.calcsize("<"+fmt)
    count=TYPE_COUNT[accessor["type"]]
    item_size=component_size*count
    stride=int(view.get("byteStride",item_size))
    start=int(view.get("byteOffset",0))+int(accessor.get("byteOffset",0))
    unpack="<"+fmt*count
    out=[]
    for i in range(int(accessor["count"])):
        off=start+i*stride
        out.append(struct.unpack_from(unpack,buffer,off))
    return out


def _mat_mul(a: Sequence[float],b: Sequence[float]) -> list[float]:
    return [
        sum(float(a[r*4+k])*float(b[k*4+c]) for k in range(4))
        for r in range(4) for c in range(4)
    ]


def _trs_matrix(node: Mapping[str,Any]) -> list[float]:
    if "matrix" in node:
        # glTF stores matrices column-major; transpose into row-major.
        m=list(map(float,node["matrix"]))
        return [m[c*4+r] for r in range(4) for c in range(4)]
    t=list(map(float,node.get("translation",[0,0,0])))
    s=list(map(float,node.get("scale",[1,1,1])))
    x,y,z,w=map(float,node.get("rotation",[0,0,0,1]))
    n=math.sqrt(x*x+y*y+z*z+w*w)
    if n<=1e-15: x=y=z=0; w=1
    else: x/=n; y/=n; z/=n; w/=n
    r=[
        1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w), 0,
        2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w), 0,
        2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y), 0,
        0,0,0,1,
    ]
    sm=[s[0],0,0,0, 0,s[1],0,0, 0,0,s[2],0, 0,0,0,1]
    tm=[1,0,0,t[0], 0,1,0,t[1], 0,0,1,t[2], 0,0,0,1]
    return _mat_mul(tm,_mat_mul(r,sm))


def _transform(p: Sequence[float],m: Sequence[float]) -> tuple[float,float,float]:
    x,y,z=map(float,p)
    return (
        m[0]*x+m[1]*y+m[2]*z+m[3],
        m[4]*x+m[5]*y+m[6]*z+m[7],
        m[8]*x+m[9]*y+m[10]*z+m[11],
    )


IDENTITY=[1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]


def _mesh_triangles(
    doc: Mapping[str,Any],
    buffers: Sequence[bytes],
    mesh_index: int,
    transform: Sequence[float],
) -> list[Triangle]:
    out=[]
    mesh=doc["meshes"][mesh_index]
    for primitive in mesh.get("primitives",[]):
        if "KHR_draco_mesh_compression" in primitive.get("extensions",{}):
            raise ValueError("Draco-compressed glTF primitive unsupported")
        if int(primitive.get("mode",4))!=4:
            raise ValueError("Only glTF TRIANGLES primitive mode is supported")
        pos_idx=primitive.get("attributes",{}).get("POSITION")
        if pos_idx is None:
            continue
        positions=_accessor_values(doc,buffers,int(pos_idx))
        positions=[_transform(p,transform) for p in positions]
        if "indices" in primitive:
            raw=_accessor_values(doc,buffers,int(primitive["indices"]))
            indices=[int(v[0]) for v in raw]
        else:
            indices=list(range(len(positions)))
        for i in range(0,len(indices)-2,3):
            out.append(_tri(
                positions[indices[i]],
                positions[indices[i+1]],
                positions[indices[i+2]],
            ))
    return out


def load_gltf_triangles(path: Path) -> list[Triangle]:
    doc,buffers=_load_gltf(path)
    nodes=doc.get("nodes",[])
    out=[]
    referenced=set()

    def walk(index: int,parent: Sequence[float]):
        node=nodes[index]
        world=_mat_mul(parent,_trs_matrix(node))
        if "mesh" in node:
            referenced.add(int(node["mesh"]))
            out.extend(_mesh_triangles(doc,buffers,int(node["mesh"]),world))
        for child in node.get("children",[]):
            walk(int(child),world)

    if doc.get("scenes"):
        scene_index=int(doc.get("scene",0))
        for root in doc["scenes"][scene_index].get("nodes",[]):
            walk(int(root),IDENTITY)
    elif nodes:
        child_set={int(c) for n in nodes for c in n.get("children",[])}
        roots=[i for i in range(len(nodes)) if i not in child_set]
        for root in roots:
            walk(root,IDENTITY)

    for i in range(len(doc.get("meshes",[]))):
        if i not in referenced:
            out.extend(_mesh_triangles(doc,buffers,i,IDENTITY))
    return out


def load_mesh_triangles(path: str | Path) -> list[Triangle]:
    p=Path(path)
    ext=p.suffix.lower()
    if ext==".obj": out=load_obj_triangles(p)
    elif ext==".stl": out=load_stl_triangles(p)
    elif ext==".ply": out=load_ply_triangles(p)
    elif ext in {".gltf",".glb"}: out=load_gltf_triangles(p)
    else: raise ValueError(f"Unsupported triangle mesh format: {ext}")
    if not out:
        raise ValueError("Mesh contains no readable triangles")
    return out


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("mesh")
    args=parser.parse_args()
    triangles=load_mesh_triangles(args.mesh)
    print(json.dumps({
        "path":args.mesh,
        "triangle_count":len(triangles),
        "production_geometry_authority":False,
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
