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
import argparse,hashlib,io,json,math,os,re,shlex,subprocess,sys,uuid
from PIL import Image
from datetime import datetime,timezone
from pathlib import Path, PureWindowsPath

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.geometry.ingest_ldraw_geometry import flatten_ldraw, reference_candidates

VERSION="ldraw-pattern-multiview-render/v8"

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

def texture_references(text, label):
 """Validate external-PNG TEXMAP declarations and list their appearance assets."""
 references=[]; active=False; fallback=False; next_pending=False
 for number,raw in enumerate(text.splitlines(),1):
  line=raw.strip()
  if not line:continue
  if next_pending:
   if line.split()[0] not in {"1","2","3","4","5"}:
    raise ValueError(f"{label}:{number}: TEXMAP NEXT must precede a geometry line")
   next_pending=False
  words=line.split()
  if words[:2] in (["0","FILE"],["0","!DATA"]):
   raise ValueError(f"{label}:{number}: embedded MPD/DATA assets are not inventoried")
  if words==["0","STEP"]:
   active=False;fallback=False
  if words[:2]!=["0","!TEXMAP"]:continue
  try:tokens=shlex.split(line,posix=True)
  except ValueError as exc:raise ValueError(f"{label}:{number}: malformed TEXMAP quoting") from exc
  if len(tokens)<3:raise ValueError(f"{label}:{number}: malformed TEXMAP command")
  command=tokens[2]
  if command in {"END","FALLBACK"}:
   if len(tokens)!=3:raise ValueError(f"{label}:{number}: malformed TEXMAP {command}")
   if command=="FALLBACK":
    if not active or fallback:raise ValueError(f"{label}:{number}: TEXMAP FALLBACK without START or repeated")
    fallback=True
   if command=="END":active=False;fallback=False
   continue
  if command not in {"START","NEXT"} or len(tokens)<4:
   raise ValueError(f"{label}:{number}: unsupported TEXMAP command")
  if active:raise ValueError(f"{label}:{number}: nested TEXMAP requires verified renderer support")
  count={"PLANAR":9,"CYLINDRICAL":10,"SPHERICAL":11}.get(tokens[3])
  if count is None:raise ValueError(f"{label}:{number}: unsupported TEXMAP projection")
  if len(tokens) not in {5+count,7+count}:
   raise ValueError(f"{label}:{number}: malformed TEXMAP parameters or filename")
  try:parameters=[float(v) for v in tokens[4:4+count]]
  except ValueError as exc:raise ValueError(f"{label}:{number}: invalid TEXMAP coordinates") from exc
  if any(not math.isfinite(v) for v in parameters) or any(v<=0 for v in parameters[9:]):
   raise ValueError(f"{label}:{number}: nonfinite coordinates or nonpositive TEXMAP angles")
  u=[parameters[i+3]-parameters[i] for i in range(3)]
  v=[parameters[i+6]-parameters[i] for i in range(3)]
  cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
  if not any(cross) or any(not math.isfinite(c) for c in cross):
   raise ValueError(f"{label}:{number}: degenerate TEXMAP projection")
  assets=[("texture",tokens[4+count])]
  if len(tokens)==7+count:
   if tokens[5+count]!="GLOSSMAP":raise ValueError(f"{label}:{number}: malformed TEXMAP GLOSSMAP")
   assets.append(("glossmap",tokens[6+count]))
  for kind,name in assets:
   normalized=name.replace("\\","/")
   if not name or PureWindowsPath(name).drive or normalized.startswith("/") or ".." in Path(normalized).parts:
    raise ValueError(f"{label}:{number}: texture path outside library")
   if Path(normalized).suffix.casefold()!=".png":
    raise ValueError(f"{label}:{number}: TEXMAP assets must be external PNG files")
   references.append({"kind":kind,"reference":normalized,"parent":label,"line":number,"projection":tokens[3]})
  active=command=="START";fallback=False;next_pending=command=="NEXT"
 if next_pending:raise ValueError(f"{label}: TEXMAP NEXT has no following geometry")
 return references

def resolve_texture(root,current,name):
 """Use the shared resolver, preferring textures/ as required by TEXMAP."""
 for reference in ("textures/"+name,name):
  # Reject shadow copies: different loader search orders must not select an
  # unrecorded appearance asset. The local library is the only search boundary.
  matches=set(reference_candidates(root,current,reference,
              extra_bases=(root/"unofficial/parts",root/"unofficial/p")))
  if matches:
   if len(matches)!=1:raise ValueError(f"Ambiguous texture lookup: {name}")
   path=matches.pop()
   if not path.is_relative_to(root.resolve()):raise ValueError("Texture dependency outside library")
   return path
 raise FileNotFoundError(f"Missing texture dependency: {name}")

def dependency_snapshot(root,rec):
 """Reuse hierarchy ingestion to bind every resolved source file, not just the root."""
 root=root.resolve()
 result=flatten_ldraw(root,rec["source_path"],strict_missing=True,confine_to_library=True,inventory_texmap_geometry=True)
 dependencies=[{"path":d["path"],"sha256":d["sha256"],"license":d["metadata"].get("license"),"kind":"geometry"}
               for d in result["dependencies"]]
 payload={"schema":"ldraw-dependency-snapshot/v2"}
 root_path=(root/rec["source_path"]).resolve()
 if sha256(root_path)!=rec.get("sha256"):
  raise ValueError("Root bytes changed during dependency inventory")
 textures={}
 for dependency in dependencies:
  source=root/dependency["path"]
  raw=source.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=dependency["sha256"]:
   raise ValueError("Geometry bytes changed during dependency inventory")
  for ref in texture_references(raw.decode("utf-8",errors="replace"),dependency["path"]):
   path=resolve_texture(root,source,ref["reference"])
   label=path.relative_to(root).as_posix(); raw_texture=path.read_bytes()
   try:
    with Image.open(io.BytesIO(raw_texture)) as png:
     if png.format!="PNG":raise ValueError(f"Texture is not PNG: {label}")
     png.verify()
   except (OSError,SyntaxError) as exc:
    raise ValueError(f"Invalid PNG texture: {label}") from exc
   digest=hashlib.sha256(raw_texture).hexdigest()
   item=textures.setdefault(label,{"path":label,"sha256":digest,"license":None,"kind":"texture","roles":[],"references":[]})
   if digest!=item["sha256"]:raise ValueError("Texture bytes changed during dependency inventory")
   if ref["kind"] not in item["roles"]:item["roles"].append(ref["kind"])
   item["references"].append(ref)
 dependencies.extend(textures.values())
 color_config=root/"LDConfig.ldr"
 if color_config.is_file():
  if not color_config.resolve().is_relative_to(root.resolve()):
   raise ValueError("Color configuration outside library")
  dependencies.append({"path":"LDConfig.ldr","sha256":sha256(color_config),"license":None,"kind":"color_configuration"})
 declarations=rec.get("dependency_licenses") or {}
 if not isinstance(declarations,dict):raise ValueError("dependency_licenses must be an object")
 for dependency in dependencies:
  declaration=declarations.get(dependency["path"])
  if declaration is not None:
   if (not isinstance(declaration,dict) or declaration.get("sha256")!=dependency["sha256"]
       or not isinstance(declaration.get("license"),str) or not declaration["license"].strip()
       or not isinstance(declaration.get("provenance_id"),str) or not declaration["provenance_id"].strip()):
    raise ValueError(f"Invalid byte-bound license declaration: {dependency['path']}")
   if dependency["license"] and declaration["license"]!=dependency["license"]:
    raise ValueError(f"License declaration conflicts with source header: {dependency['path']}")
   dependency["license"]=declaration["license"];dependency["license_provenance_id"]=declaration["provenance_id"]
 dependencies.sort(key=lambda d:d["path"])
 payload["files"]=[{"path":d["path"],"sha256":d["sha256"]} for d in dependencies]
 digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 if rec.get("dependencies_sha256") and rec["dependencies_sha256"]!=digest:
  raise ValueError("Dependency snapshot does not match the pinned dependencies_sha256")
 return dependencies,digest

def training_rights(dependencies):
 """A permissive root cannot erase unknown/restricted dependency licenses."""
 licenses=[d.get("license") for d in dependencies if d["kind"]!="color_configuration"]
 statuses=[]
 for license in licenses:
  if isinstance(license,str) and re.fullmatch(r"(?:Licensed under |Redistributable under )?CC0(?: 1\.0)?(?: : see .+)?",license.strip(),re.I):statuses.append("allowed_open")
  elif isinstance(license,str) and re.fullmatch(r"(?:Licensed under |Redistributable under )?CC BY 4\.0(?: : see .+)?",license.strip(),re.I):statuses.append("allowed_with_attribution")
  else:statuses.append("requires_permission")
 if not statuses or "requires_permission" in statuses:return "requires_permission"
 return "allowed_with_attribution" if "allowed_with_attribution" in statuses else "allowed_open"

def render(exe,source,out,lat,lon,width,height,edges,zoom,root,settings,lighting="lit"):
 cmd=[
  str(exe),str(source),
  f"-LDrawDir={root}",
  "-LDrawZip=",
  f"-IniFile={settings}",
  "-AllowPrimitiveSubstitution=0",
  "-Texmaps=1",
  "-TextureStuds=0",
  "-TextureFilterType=9987",
  "-AnisoLevel=1",
  "-AutoCrop=0",
  f"-Lighting={1 if lighting=='lit' else 0}",
  "-UseQualityLighting=0",
  f"-UseSpecular={1 if lighting=='lit' else 0}",
  "-PerformSmoothing=1",
  "-UseFlatShading=0",
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
 options={"timeout":120}
 if os.name=="nt":
  startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
  options["startupinfo"]=startup
 try:p=subprocess.run(cmd,capture_output=True,text=True,check=False,**options)
 except (OSError,subprocess.TimeoutExpired) as exc:return 2,f"LDView execution failed: {exc}"
 return p.returncode,(p.stderr or p.stdout)[-2000:]

def main(argv=None, *, quiet=False):
 ap=argparse.ArgumentParser()
 ap.add_argument("--manifest",type=Path,required=True)
 ap.add_argument("--ldraw-root",type=Path,required=True)
 ap.add_argument("--ldview",type=Path,required=True)
 ap.add_argument("--library-revision",required=True,help="Pinned library archive hash or commit, including dependencies")
 ap.add_argument("--output-dir",type=Path,required=True)
 ap.add_argument("--profile",choices=["physical_like","structural_edges","both"],default="both")
 ap.add_argument("--lighting",choices=["lit","unlit"],default="lit",help="Unlit removes simulated shading for decoration/color inspection; neither mode is physical evidence")
 ap.add_argument("--width",type=int,default=1024)
 ap.add_argument("--height",type=int,default=1024)
 ap.add_argument("--zoom",type=float,default=0.92)
 ap.add_argument("--limit",type=int)
 ap.add_argument("--view",action="append",choices=[v[0] for v in VIEWS],help="Select repeatable canonical views; default is all views")
 args=ap.parse_args(argv)
 if args.view and len(args.view)!=len(set(args.view)):ap.error("Duplicate requested view")
 if not args.library_revision.strip():ap.error("Library revision must not be empty")
 views=[v for v in VIEWS if args.view is None or v[0] in args.view]
 if args.limit is not None and args.limit<=0:ap.error("Limit must be positive")
 if args.width<=0 or args.height<=0 or not math.isfinite(args.zoom) or args.zoom<=0:
  ap.error("Width, height and zoom must be positive")
 root=args.ldraw_root.resolve(); exe=args.ldview.resolve(); out=args.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
 if not exe.is_file():ap.error("LDView executable not found")
 settings=out/"brickmen-render-settings.ini"
 settings.write_text("[General]\n",encoding="utf-8",newline="\n")
 configuration={"settings_sha256":sha256(settings),"primitive_substitution":False,"autocrop":False,"texture_mapping":True,"texture_studs":False,"texture_filter":9987,"anisotropy":1,"width":args.width,"height":args.height,"zoom":args.zoom,
                "lighting":args.lighting,"quality_lighting":False,"specular":args.lighting=="lit","smooth_curves":True,"flat_shading":False,
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
   if any("glossmap" in d.get("roles",[]) for d in dependencies):
    raise ValueError("GLOSSMAP rendering requires verified renderer support; assets are inventoried but rendering is blocked")
  except (ValueError,OSError,RecursionError) as exc:
   failures+=1;errors.append({"source_path":rec["source_path"],"stage":"dependency_inventory","reason":str(exc)});continue
  record_configuration={**configuration,"dependencies_sha256":dependencies_sha256}
  source_count+=1
  source_records=[]
  stem=re.sub(r"[^A-Za-z0-9_-]","_",source.stem) or "part"
  for profile,edges in profiles:
   for view,lat,lon in views:
    render_id=render_identity(rec,profile,view,record_configuration)
    target=out/profile/stem/f"{view}-{render_id}.png";target.parent.mkdir(parents=True,exist_ok=True)
    pending=target.with_name(f".{render_id}-{uuid.uuid4().hex}.pending.png")
    rc,detail=render(exe,source,pending,lat,lon,args.width,args.height,edges,args.zoom,root,settings,args.lighting)
    if rc!=0 or not pending.is_file():
     failures+=1;errors.append({"source_path":rec["source_path"],"stage":"render","view":view,"reason":detail});continue
    try:
     with Image.open(pending) as snapshot:
      if snapshot.format!="PNG" or snapshot.size!=(args.width,args.height):
       raise ValueError("Renderer output is not a PNG on the requested pixel grid")
      snapshot.verify()
    except (ValueError,OSError,SyntaxError) as exc:
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
      "medium":"structured_pattern_reconstruction" if "pattern" in str(rec.get("medium","")).lower() else "structured_geometry_reconstruction",
      "source_medium":rec.get("medium"),
      "part_namespace":rec.get("part_namespace","ldraw"),
      "part_id":rec.get("part_id",source.stem),
      "part_type":rec.get("part_type"),
      "category":rec.get("category"),
      "component_type":rec.get("component_type"),
      "render_profile":profile,
      "render_configuration":record_configuration,
      "geometry_revision":dependencies_sha256,
      "geometry_dependencies":[d for d in dependencies if d["kind"]=="geometry"],
      "appearance_dependencies":[d for d in dependencies if d["kind"]!="geometry"],
      "render_dependencies":dependencies,
      "dependency_binding":"verified_expected" if rec.get("dependencies_sha256") else "captured_current_bytes",
      "view":view,
      "latitude":lat,
      "longitude":lon,
      "width":args.width,
      "height":args.height,
      "edge_lines":edges,
      "local_path":str(target),
      "sha256":sha256(target),
      "training_rights_status":training_rights(dependencies),
      "processor_version":VERSION,
      "created_at":now_iso()
    })
  try:
   changed=dependency_snapshot(root,rec)[1]!=dependencies_sha256
  except (ValueError,OSError,RecursionError):changed=True
  if changed or sha256(exe)!=configuration["renderer_sha256"] or sha256(settings)!=configuration["settings_sha256"]:
   failures+=1;errors.append({"source_path":rec["source_path"],"stage":"dependency_integrity","reason":"Source dependencies changed during rendering"})
  else:
   records.extend(source_records)
 manifest=out/"render_manifest.jsonl"
 with manifest.open("w",encoding="utf-8") as f:
  for r in records:f.write(json.dumps(r,ensure_ascii=False)+"\n")
 report={"schema":"ldraw-pattern-multiview-render-report/v1","version":VERSION,"sources_attempted":source_count,"sources_rendered":len({r["source_reference_asset_id"] for r in records}),"renders":len(records),"failures":failures,"errors":errors,"profiles":[p[0] for p in profiles],"views":[v[0] for v in views],"manifest":str(manifest)}
 (out/"import_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 if not quiet:print(json.dumps(report,indent=2))
 return 2 if failures else 0
if __name__=="__main__":raise SystemExit(main())
