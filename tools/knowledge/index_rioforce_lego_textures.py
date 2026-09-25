#!/usr/bin/env python3
"""Index a local clone of rioforce/LEGO-Textures.

The repository states its SVG/PNG texture work is CC BY 3.0 and scanned from real LEGO
bricks. This tool does not download the repository; it inventories a local reviewed clone,
hashes files, pairs SVG/PNG siblings, and records attribution requirements.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

VERSION="rioforce-lego-textures-index/v1"
ALLOWED={".svg",".png"}

def now_iso():return datetime.now(timezone.utc).isoformat()
def sha256(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);args=ap.parse_args()
 root=args.root.resolve();groups=defaultdict(dict)
 for p in root.rglob("*"):
  if p.is_file() and p.suffix.lower() in ALLOWED:
   rel=p.relative_to(root); key=str(rel.with_suffix(""))
   groups[key][p.suffix.lower()]=p
 args.output.parent.mkdir(parents=True,exist_ok=True)
 with args.output.open("w",encoding="utf-8") as f:
  for key,forms in sorted(groups.items()):
   record={
    "asset_group_id":"rioforce-"+hashlib.sha256(key.encode()).hexdigest()[:24],
    "relative_stem":key,
    "category":Path(key).parts[0] if Path(key).parts else "",
    "files":{ext:{"path":str(p),"sha256":sha256(p)} for ext,p in forms.items()},
    "authority":"community_scan_reconstruction",
    "license":"CC BY 3.0",
    "attribution":"LEGO Textures by rioforce",
    "training_rights_status":"allowed_with_attribution",
    "underlying_design_rights_note":"Repository license covers rioforce texture work; underlying LEGO/licensed decoration rights remain separate.",
    "processor_version":VERSION
   }
   f.write(json.dumps(record,ensure_ascii=False)+"\n")
 print(json.dumps({"groups":len(groups),"output":str(args.output),"version":VERSION},indent=2))
if __name__=="__main__":main()
