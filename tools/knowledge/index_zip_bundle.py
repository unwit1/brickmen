#!/usr/bin/env python3
"""Index a locally downloaded ZIP bundle with per-entry hashes and media classification."""
from __future__ import annotations
import argparse,hashlib,json,mimetypes,zipfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

VERSION="zip-bundle-index/v1"

def now_iso():return datetime.now(timezone.utc).isoformat()
def sha256_bytes(data):return hashlib.sha256(data).hexdigest()
def sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def cls(name):
    ext=Path(name).suffix.lower()
    if ext in {".png",".jpg",".jpeg",".webp",".gif",".bmp",".tif",".tiff"}:return "raster_image"
    if ext in {".svg",".ai",".eps"}:return "vector_art"
    if ext in {".json",".csv",".xml",".txt",".md",".yaml",".yml"}:return "structured_or_text"
    if ext in {".fbx",".obj",".dae",".gltf",".glb",".blend",".ldr",".dat"}:return "3d_or_cad"
    if ext in {".mp4",".mov",".avi",".webm",".mkv"}:return "video"
    return "other"
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--zip",type=Path,required=True)
    ap.add_argument("--bundle-id",required=True)
    ap.add_argument("--source-url",required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    ap.add_argument("--hash-max-bytes",type=int,default=50_000_000)
    args=ap.parse_args()
    rows=[];classes=Counter();exts=Counter();total_uncompressed=0;total_compressed=0
    with zipfile.ZipFile(args.zip) as z:
        for info in z.infolist():
            if info.is_dir():continue
            kind=cls(info.filename);classes[kind]+=1;exts[Path(info.filename).suffix.lower() or "<none>"]+=1
            total_uncompressed+=info.file_size;total_compressed+=info.compress_size
            digest=None
            if info.file_size<=args.hash_max_bytes:
                digest=sha256_bytes(z.read(info))
            rows.append({
              "bundle_id":args.bundle_id,
              "path":info.filename,
              "basename":Path(info.filename).name,
              "extension":Path(info.filename).suffix.lower() or None,
              "asset_class":kind,
              "file_size":info.file_size,
              "compressed_size":info.compress_size,
              "crc32":f"{info.CRC:08x}",
              "sha256":digest,
              "hash_status":"complete" if digest else "skipped_large_entry",
              "processor_version":VERSION
            })
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"zip-bundle-index-summary/v1","created_at":now_iso(),"processor_version":VERSION,
      "bundle_id":args.bundle_id,"source_url":args.source_url,
      "zip_sha256":sha256_file(args.zip),"zip_bytes":args.zip.stat().st_size,
      "entry_count":len(rows),"total_uncompressed_bytes":total_uncompressed,
      "total_compressed_bytes":total_compressed,
      "asset_class_counts":dict(classes),"extension_counts":dict(exts),
      "hashed_entries":sum(bool(r["sha256"]) for r in rows),
      "unhashed_large_entries":sum(not bool(r["sha256"]) for r in rows),
      "status":"bundle_index_complete"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
