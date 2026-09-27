import io
from pathlib import Path
import struct
import zipfile

import pytest

from tools.geometry.ingest_particulate_critic import ingest_particulate
from tools.geometry.read_numeric_npz import read_npy_bytes,read_npz


def npy_bytes(descr,shape,values):
    header=str({
        "descr":descr,
        "fortran_order":False,
        "shape":tuple(shape),
    })
    header=(header+" "*(64-len(header)%64-1)+"\n").encode("latin1")
    magic=b"\x93NUMPY"+bytes([1,0])+struct.pack("<H",len(header))
    fmts={"<i8":"q","<f4":"f","|b1":"?"}
    payload=b"".join(struct.pack("<"+fmts[descr],v) for v in values)
    return magic+header+payload


def write_npz(path: Path):
    arrays={
        "face_part_ids":("<i8",[2],[0,1]),
        "motion_hierarchy":("<i8",[1,2],[0,1]),
        "is_part_revolute":("|b1",[2],[True,False]),
        "is_part_prismatic":("|b1",[2],[False,True]),
        "revolute_plucker":("<f4",[2,6],[1,0,0,0,0,0, 0,1,0,0,0,0]),
        "revolute_range":("<f4",[2,2],[-1,1, 0,0]),
        "prismatic_axis":("<f4",[2,3],[0,0,0, 0,0,1]),
        "prismatic_range":("<f4",[2,2],[0,0, -.2,.3]),
    }
    with zipfile.ZipFile(path,"w") as z:
        for key,(descr,shape,values) in arrays.items():
            z.writestr(key+".npy",npy_bytes(descr,shape,values))


def test_dependency_free_npy_reader():
    arr=read_npy_bytes(npy_bytes("<i8",[2,2],[1,2,3,4]))
    assert arr["shape"]==[2,2]
    assert arr["values"]==[[1,2],[3,4]]


def test_particulate_npz_normalizes_motion_evidence(tmp_path: Path):
    npz=tmp_path/"pred.npz"; write_npz(npz)
    obj=tmp_path/"pred.obj"
    obj.write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\n"
        "v 2 0 0\nv 3 0 0\nv 2 1 0\n"
        "f 1 2 3\nf 4 5 6\n",
        encoding="utf-8",
    )
    result=ingest_particulate(npz,pred_obj=obj)
    assert result["part_count"]==2
    assert result["motion_hierarchy"]==[[0,1]]
    assert result["parts"][0]["motion_class"]=="revolute"
    assert result["parts"][1]["motion_class"]=="prismatic"
    assert result["parts"][0]["revolute_axis_direction"]==pytest.approx([1,0,0])
    assert result["parts"][1]["predicted_part_bounds"]["center"]==pytest.approx([2.5,.5,0])
    assert result["production_geometry_authority"] is False
