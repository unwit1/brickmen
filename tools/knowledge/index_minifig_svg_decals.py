#!/usr/bin/env python3
"""Index a local clone of jpgerdeman/minifig-svg-decals.

Repository license is CC BY-NC-SA 3.0. Therefore records default to research_only for
the user's business pipeline while remaining useful for noncommercial thesis experiments,
custom-style extension analysis, and template grammar.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
VERSION="minifig-svg-decals-index/v1"

def sha256(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);args=ap.parse_args()
 root=args.root.resolve();records=[]
 for p in sorted(root.rglob("*.svg")):
  rel=p.relative_to(root)
  top=rel.parts[0].lower() if rel.parts else ""
  role="completed_custom_design" if top=="figures" else "reusable_component" if top=="library" else "template_or_resource" if top=="resources" else "other_svg"
  records.append({
   "asset_id":"minifigsvg-"+hashlib.sha256(str(rel).encode()).hexdigest()[:24],
   "relative_path":rel.as_posix(),
   "local_path":str(p),
   "sha256":sha256(p),
   "role":role,
   "authority":"community_custom_vector",
   "license":"CC BY-NC-SA 3.0",
   "training_rights_status":"research_only",
   "style_admission_class":"unscored_custom_reference",
   "processor_version":VERSION
  })
 args.output.parent.mkdir(parents=True,exist_ok=True)
 with args.output.open("w",encoding="utf-8") as f:
  for r in records:f.write(json.dumps(r,ensure_ascii=False)+"\n")
 print(json.dumps({"svg_records":len(records),"output":str(args.output),"version":VERSION},indent=2))
if __name__=="__main__":main()
