#!/usr/bin/env python3
"""Render canonical multi-view images from an indexed local LDraw minifigure-pattern manifest.

Input manifest is the output of index_ldraw_minifig_patterns.py. Every rendered image
inherits source file hash, author and license metadata.

Requires a local LDView executable. This tool renders individual parts/patterned parts;
it does not invent full minifigure assembly transforms.

Profiles:
- physical_like: LDView artificial edge lines disabled
- structural_edges: edge lines enabled
- both

The manifest output is suitable for detection/view/geometry/style-measurement experiments,
but authority remains community_structured rather than LEGO-primary.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path

VERSION="ldraw-pattern-multiview-render/v1"

VIEWS=[
 ("front",0,0),
 ("front_right_3q",0,45),
 ("right",0,90),
 ("rear_right_3q",0,135),
 ("rear",0,180),
 ("rear_left_3q",0,225),
 ("left",0,270),
 ("front_left_3q",0,315),
 ("elevated_front_right",25,45),
]

def now_iso(): return datetime.now(timezone.utc).isoformat()
def sha256(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()

def load(path):
 with path.open("r",encoding="utf-8") as f:
  for line in f:
   if line.strip():yield json.loads(line)

def render(exe,source,out,lat,lon,width,height,edges,zoom):
 cmd=[
  str(exe),str(source),
  f"-SaveSnapshot={out}",
  f"-SaveWidth={width}",
  f"-SaveHeight={height}",
  f"-DefaultLatLong={lat},{lon}",
  "-SaveAlpha=1",
  "-SaveZoomToFit=1",
  f"-DefaultZoom={zoom}",
  f"-ShowHighlightLines={1 if edges else 0}",
 ]
 p=subprocess.run(cmd,capture_output=True,text=True,check=False)
 return p.returncode,(p.stderr or p.stdout)[-2000:]

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--manifest",type=Path,required=True)
 ap.add_argument("--ldraw-root",type=Path,required=True)
 ap.add_argument("--ldview",type=Path,required=True)
 ap.add_argument("--output-dir",type=Path,required=True)
 ap.add_argument("--profile",choices=["physical_like","structural_edges","both"],default="both")
 ap.add_argument("--width",type=int,default=1024)
 ap.add_argument("--height",type=int,default=1024)
 ap.add_argument("--zoom",type=float,default=0.92)
 ap.add_argument("--limit",type=int)
 args=ap.parse_args()
 root=args.ldraw_root.resolve(); exe=args.ldview.resolve(); out=args.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
 profiles=[]
 if args.profile in ("physical_like","both"):profiles.append(("physical_like",False))
 if args.profile in ("structural_edges","both"):profiles.append(("structural_edges",True))
 records=[];failures=0;source_count=0
 for rec in load(args.manifest.resolve()):
  if args.limit is not None and source_count>=args.limit:break
  source=root/rec["source_path"]
  if not source.is_file():continue
  source_count+=1
  stem=Path(rec.get("ldraw_name") or source.name).stem.replace(" ","_")
  for profile,edges in profiles:
   for view,lat,lon in VIEWS:
    target=out/profile/stem/f"{view}.png";target.parent.mkdir(parents=True,exist_ok=True)
    rc,detail=render(exe,source,target,lat,lon,args.width,args.height,edges,args.zoom)
    if rc!=0 or not target.exists():
     failures+=1;continue
    records.append({
      "derived_asset_id":"ldrawrender-"+hashlib.sha256((rec["reference_asset_id"]+"|"+profile+"|"+view+"|"+VERSION).encode()).hexdigest()[:24],
      "source_reference_asset_id":rec["reference_asset_id"],
      "source_path":rec["source_path"],
      "source_sha256":rec.get("sha256"),
      "source_author":rec.get("author"),
      "source_license":rec.get("license"),
      "authority":"community_structured",
      "component_type":rec.get("component_type"),
      "render_profile":profile,
      "view":view,
      "latitude":lat,
      "longitude":lon,
      "width":args.width,
      "height":args.height,
      "edge_lines":edges,
      "local_path":str(target),
      "sha256":sha256(target),
      "training_rights_status":"allowed_with_attribution" if "CC BY" in str(rec.get("license") or "") else "allowed_open" if "CC0" in str(rec.get("license") or "") else "requires_permission",
      "processor_version":VERSION,
      "created_at":now_iso()
    })
 manifest=out/"render_manifest.jsonl"
 with manifest.open("w",encoding="utf-8") as f:
  for r in records:f.write(json.dumps(r,ensure_ascii=False)+"\n")
 report={"schema":"ldraw-pattern-multiview-render-report/v1","version":VERSION,"sources_rendered":source_count,"renders":len(records),"failures":failures,"profiles":[p[0] for p in profiles],"views":[v[0] for v in VIEWS],"manifest":str(manifest)}
 (out/"import_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print(json.dumps(report,indent=2))

if __name__=="__main__":main()
