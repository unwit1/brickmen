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
import argparse,hashlib,json,math,subprocess,sys,uuid
from PIL import Image
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.geometry.ingest_ldraw_geometry import flatten_ldraw

VERSION="ldraw-pattern-multiview-render/v4"

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

def render_identity(rec, profile, view, configuration):
 """Pin a derived asset to both its source revision and render configuration."""
 payload={"source_reference_asset_id":rec["reference_asset_id"],
          "source_sha256":rec["sha256"],"profile":profile,"view":view,
          "configuration":configuration,"version":VERSION}
 return "ldrawrender-"+hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()[:24]

def dependency_snapshot(root,rec):
 """Reuse hierarchy ingestion to bind every resolved source file, not just the root."""
 result=flatten_ldraw(root,rec["source_path"],strict_missing=True,confine_to_library=True)
 dependencies=[{"path":d["path"],"sha256":d["sha256"],"license":d["metadata"].get("license")}
               for d in result["dependencies"]]
 payload={"schema":"ldraw-dependency-snapshot/v1","files":[{"path":d["path"],"sha256":d["sha256"]} for d in dependencies]}
 digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 root_path=(root/rec["source_path"]).resolve()
 if sha256(root_path)!=rec.get("sha256"):
  raise ValueError("Root bytes changed during dependency inventory")
 for dependency in dependencies:
  text=(root/dependency["path"]).read_text(encoding="utf-8",errors="replace")
  if any(line.strip().upper().startswith("0 !TEXMAP") for line in text.splitlines()):
   raise ValueError("Texture-mapped parts require a texture dependency inventory before rendering")
 color_config=root/"LDConfig.ldr"
 if color_config.is_file():
  if not color_config.resolve().is_relative_to(root.resolve()):
   raise ValueError("Color configuration outside library")
  dependencies.append({"path":"LDConfig.ldr","sha256":sha256(color_config),"license":None})
 dependencies.sort(key=lambda d:d["path"])
 payload["files"]=[{"path":d["path"],"sha256":d["sha256"]} for d in dependencies]
 digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 if rec.get("dependencies_sha256") and rec["dependencies_sha256"]!=digest:
  raise ValueError("Dependency snapshot does not match the pinned dependencies_sha256")
 return dependencies,digest

def render(exe,source,out,lat,lon,width,height,edges,zoom,root,settings):
 cmd=[
  str(exe),str(source),
  f"-LDrawDir={root}",
  "-LDrawZip=",
  f"-IniFile={settings}",
  "-AllowPrimitiveSubstitution=0",
  "-AutoCrop=0",
  f"-ProcessLDConfig={1 if (root/'LDConfig.ldr').is_file() else 0}",
  f"-LDConfig={root/'LDConfig.ldr'}",
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
 ap.add_argument("--library-revision",required=True,help="Pinned library archive hash or commit, including dependencies")
 ap.add_argument("--output-dir",type=Path,required=True)
 ap.add_argument("--profile",choices=["physical_like","structural_edges","both"],default="both")
 ap.add_argument("--width",type=int,default=1024)
 ap.add_argument("--height",type=int,default=1024)
 ap.add_argument("--zoom",type=float,default=0.92)
 ap.add_argument("--limit",type=int)
 args=ap.parse_args()
 if args.limit is not None and args.limit<=0:ap.error("Limit must be positive")
 if args.width<=0 or args.height<=0 or not math.isfinite(args.zoom) or args.zoom<=0:
  ap.error("Width, height and zoom must be positive")
 root=args.ldraw_root.resolve(); exe=args.ldview.resolve(); out=args.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
 if not exe.is_file():ap.error("LDView executable not found")
 settings=out/"brickmen-render-settings.ini"
 settings.write_text("[General]\n",encoding="utf-8",newline="\n")
 configuration={"settings_sha256":sha256(settings),"primitive_substitution":False,"autocrop":False,"width":args.width,"height":args.height,"zoom":args.zoom,
                "renderer_sha256":sha256(exe),"library_revision":args.library_revision}
 profiles=[]
 if args.profile in ("physical_like","both"):profiles.append(("physical_like",False))
 if args.profile in ("structural_edges","both"):profiles.append(("structural_edges",True))
 records=[];failures=0;source_count=0;errors=[]
 for rec in load(args.manifest.resolve()):
  if args.limit is not None and source_count>=args.limit:break
  source=(root/rec["source_path"]).resolve()
  if not source.is_relative_to(root) or not source.is_file():
   failures+=1;errors.append({"source_path":rec["source_path"],"stage":"source_integrity","reason":"Source missing or outside library"});continue
  if sha256(source)!=rec.get("sha256"):
   failures+=1;errors.append({"source_path":rec["source_path"],"stage":"source_integrity","reason":"Source hash mismatch"});continue
  try:
   dependencies,dependencies_sha256=dependency_snapshot(root,rec)
  except (ValueError,OSError,RecursionError) as exc:
   failures+=1;errors.append({"source_path":rec["source_path"],"stage":"dependency_inventory","reason":str(exc)});continue
  record_configuration={**configuration,"dependencies_sha256":dependencies_sha256}
  source_count+=1
  source_records=[]
  stem=Path(rec.get("ldraw_name") or source.name).stem.replace(" ","_")
  for profile,edges in profiles:
   for view,lat,lon in VIEWS:
    render_id=render_identity(rec,profile,view,record_configuration)
    target=out/profile/stem/f"{view}-{render_id}.png";target.parent.mkdir(parents=True,exist_ok=True)
    pending=target.with_name(f".{render_id}-{uuid.uuid4().hex}.pending.png")
    rc,detail=render(exe,source,pending,lat,lon,args.width,args.height,edges,args.zoom,root,settings)
    if rc!=0 or not pending.is_file():
     failures+=1;errors.append({"source_path":rec["source_path"],"stage":"render","view":view,"reason":detail});continue
    try:
     with Image.open(pending) as snapshot:
      if snapshot.format!="PNG" or snapshot.size!=(args.width,args.height):
       raise ValueError("Renderer output is not a PNG on the requested pixel grid")
      snapshot.verify()
    except (ValueError,OSError) as exc:
     failures+=1;errors.append({"source_path":rec["source_path"],"stage":"render_integrity","view":view,"reason":str(exc)});continue
    pending.replace(target)
    source_records.append({
      "derived_asset_id":render_id,
      "sample_id":rec.get("sample_id") or rec["reference_asset_id"],
      "source_reference_asset_id":rec["reference_asset_id"],
      "source_path":rec["source_path"],
      "source_sha256":rec.get("sha256"),
      "source_author":rec.get("author"),
      "source_license":rec.get("license"),
      "authority":"community_structured",
      "component_type":rec.get("component_type"),
      "render_profile":profile,
      "render_configuration":record_configuration,
      "geometry_revision":dependencies_sha256,
      "geometry_dependencies":dependencies,
      "dependency_binding":"verified_expected" if rec.get("dependencies_sha256") else "captured_current_bytes",
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
  if sha256(exe)!=configuration["renderer_sha256"] or sha256(settings)!=configuration["settings_sha256"] or any(not (root/d["path"]).is_file() or sha256(root/d["path"])!=d["sha256"] for d in dependencies):
   failures+=1;errors.append({"source_path":rec["source_path"],"stage":"dependency_integrity","reason":"Source dependencies changed during rendering"})
  else:
   records.extend(source_records)
 manifest=out/"render_manifest.jsonl"
 with manifest.open("w",encoding="utf-8") as f:
  for r in records:f.write(json.dumps(r,ensure_ascii=False)+"\n")
 report={"schema":"ldraw-pattern-multiview-render-report/v1","version":VERSION,"sources_attempted":source_count,"sources_rendered":len({r["source_reference_asset_id"] for r in records}),"renders":len(records),"failures":failures,"errors":errors,"profiles":[p[0] for p in profiles],"views":[v[0] for v in VIEWS],"manifest":str(manifest)}
 (out/"import_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print(json.dumps(report,indent=2))
 return 2 if failures else 0
if __name__=="__main__":raise SystemExit(main())
