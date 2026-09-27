#!/usr/bin/env python3
"""Minimal dependency-free reader for numeric .npy/.npz arrays.

Supported dtype families are intentionally narrow and cover Brickmen's current
critic-ingestion needs: booleans and little/native-endian integer/float scalars.
Object arrays, structured dtypes and Fortran-order arrays are rejected.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
from pathlib import Path
import struct
import zipfile
from typing import Any


STRUCT_FORMATS={
    "|b1":"?",
    "|?":"?",
    "|u1":"B",
    "|i1":"b",
    "<u1":"B",
    "<i1":"b",
    "<u2":"H",
    "<i2":"h",
    "<u4":"I",
    "<i4":"i",
    "<u8":"Q",
    "<i8":"q",
    "<f4":"f",
    "<f8":"d",
    "=u1":"B",
    "=i1":"b",
    "=u2":"H",
    "=i2":"h",
    "=u4":"I",
    "=i4":"i",
    "=u8":"Q",
    "=i8":"q",
    "=f4":"f",
    "=f8":"d",
}


def _reshape(values,shape):
    if shape==():
        return values[0] if values else None
    if len(shape)==1:
        return values[:shape[0]]
    step=math.prod(shape[1:])
    return [
        _reshape(values[i*step:(i+1)*step],shape[1:])
        for i in range(shape[0])
    ]


def read_npy_bytes(data: bytes) -> dict[str,Any]:
    if len(data)<10 or data[:6]!=b"\x93NUMPY":
        raise ValueError("Invalid NPY magic")
    major,minor=data[6],data[7]
    if major==1:
        header_len=struct.unpack_from("<H",data,8)[0]
        start=10
    elif major in {2,3}:
        header_len=struct.unpack_from("<I",data,8)[0]
        start=12
    else:
        raise ValueError(f"Unsupported NPY version {major}.{minor}")
    header=ast.literal_eval(
        data[start:start+header_len].decode("latin1").strip()
    )
    descr=str(header["descr"])
    if header.get("fortran_order"):
        raise ValueError("Fortran-order NPY arrays are not supported")
    if descr not in STRUCT_FORMATS:
        raise ValueError(f"Unsupported NPY dtype {descr}")
    shape=tuple(int(v) for v in header["shape"])
    count=math.prod(shape) if shape else 1
    fmt=STRUCT_FORMATS[descr]
    size=struct.calcsize("<"+fmt)
    payload=data[start+header_len:]
    if len(payload)<count*size:
        raise ValueError("NPY payload shorter than declared array")
    values=[
        struct.unpack_from("<"+fmt,payload,i*size)[0]
        for i in range(count)
    ]
    return {
        "dtype":descr,
        "shape":list(shape),
        "values":_reshape(values,shape),
    }


def read_npz(path: str | Path) -> dict[str,dict[str,Any]]:
    result={}
    with zipfile.ZipFile(path,"r") as archive:
        for name in archive.namelist():
            if not name.endswith(".npy"):
                continue
            key=Path(name).stem
            result[key]=read_npy_bytes(archive.read(name))
    return result


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("npz")
    args=parser.parse_args()
    print(json.dumps(read_npz(args.npz),indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
