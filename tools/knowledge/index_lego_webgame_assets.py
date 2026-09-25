#!/usr/bin/env python3
"""Index locally preserved LEGO browser-game files and route formats to extractors."""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
PROCESSOR_VERSION="lego-webgame-asset-index/v1"
ROUTES={
 ".swf":("flash_swf","JPEXS Free Flash Decompiler"),".dcr":("director_shockwave","ProjectorRays"),".dxr":("director_shockwave","ProjectorRays"),".dir":("director_shockwave","Director-compatible inspection / ProjectorRays outputs"),
 ".jar":("java_jar","ZIP/JAR extraction"),".unity3d":("unity","UnityPy or Unity WebExtract"),".assets":("unity","UnityPy"),".resource":("unity","UnityPy"),".resS":("unity","UnityPy"),".bundle":("unity","UnityPy"),
 ".png":("image","direct image"),".jpg":("image","direct image"),".jpeg":("image","direct image"),".gif":("image","direct image"),".webp":("image","direct image"),".svg":("vector_image","SVG parser/render"),
 ".dds":("texture","texture decoder"),".tga":("texture","texture decoder"),".obj":("model","3D renderer"),".fbx":("model","3D renderer"),".dae":("model","3D renderer"),".gltf":("model","3D renderer"),".glb":("model","3D renderer"),
 ".json":("metadata","JSON inspection"),".xml":("metadata","XML inspection"),".js":("code_metadata","JS/resource path inspection"),".html":("code_metadata","HTML/resource path inspection"),".htm":("code_metadata","HTML/resource path inspection")
}
def now_iso(): return datetime.now(timezone.utc).isoformat()
def sha256(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--game-id",required=True); ap.add_argument("--title",required=True); ap.add_argument("--source-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); args=ap.parse_args()
 root=args.source_root.resolve()
 if not root.is_dir(): raise SystemExit(f"Not a directory: {root}")
 args.output.parent.mkdir(parents=True,exist_ok=True); counts=Counter(); records=[]
 for path in sorted(p for p in root.rglob("*") if p.is_file()):
  rel=path.relative_to(root).as_posix(); suffix=path.suffix; key=suffix if suffix==".resS" else suffix.lower(); family,tool=ROUTES.get(key,("unknown","research_needed")); digest=sha256(path); counts[family]+=1
  records.append({"asset_id":f"webasset-{hashlib.sha256((args.game_id+'|'+rel+'|'+digest).encode()).hexdigest()[:24]}","game_id":args.game_id,"title":args.title,"relative_path":rel,"extension":suffix,"size_bytes":path.stat().st_size,"sha256":digest,"format_family":family,"recommended_extractor":tool,"source_root":str(root),"storage_policy":"local_only_raw_asset","character_id":None,"appearance_id":None,"review_status":"unprocessed","processor_version":PROCESSOR_VERSION})
 with args.output.open("w",encoding="utf-8") as f:
  for r in records: f.write(json.dumps(r,ensure_ascii=False)+"\n")
 report={"schema":"lego-webgame-asset-index-report/v1","created_at":now_iso(),"processor_version":PROCESSOR_VERSION,"game_id":args.game_id,"title":args.title,"source_root":str(root),"asset_count":len(records),"counts_by_format_family":dict(counts),"output":str(args.output)}
 args.output.with_suffix(".report.json").write_text(json.dumps(report,indent=2),encoding="utf-8"); print(json.dumps(report,indent=2))
if __name__=="__main__": main()
