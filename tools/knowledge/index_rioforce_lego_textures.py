#!/usr/bin/env python3
"""Index a local clone of rioforce/LEGO-Textures.

The repository states its SVG/PNG texture work is CC BY 3.0 and scanned from real LEGO
bricks. This tool does not download the repository; it inventories a local reviewed clone,
hashes files, pairs SVG/PNG siblings, and records attribution requirements.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

VERSION="rioforce-lego-textures-index/v2"
ALLOWED={".svg",".png"}

def now_iso():return datetime.now(timezone.utc).isoformat()
def classify_asset(key: str):
 low=key.casefold(); parts=Path(key).parts; leaf=parts[-1].casefold() if parts else low
 category=parts[0] if parts else ""
 role=None
 patterns=(
  (r"\b(?:face|head)\b","head"),
  (r"\btorso\b","torso"),
  (r"\bhips?\b","hips"),
  (r"\blegs?\b","leg"),
  (r"\barms?\b","arm"),
  (r"\b(?:helmet|cowl|hair|hood|mask|hat|cap|headgear)\b","headgear"),
  (r"\bshield\b","weapon_or_tool"),
 )
 for pattern,value in patterns:
  if re.search(pattern,low):
   role=value;break
 # Standalone logos and symbols are reusable design primitives, not exact part maps.
 if re.search(r"\blogo\b",low) or category=="Bricks" and "star of life" in low:
  return "motif_primitive",role
 # Animal/body/brick decorations are useful, but not minifigure surface maps.
 if category in {"Animals","Bricks"}:
  return "non_minifigure_component_art",role
 # A named surface can be crosswalked to decorated minifigure components.
 if role:
  return "minifigure_surface_map",role
 # Remaining generic apparel/pattern art is useful as design supervision, but must
 # not be promoted to one exact component solely by a fuzzy figure-name match.
 return "unscoped_design_or_pattern",None

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
   asset_class,surface_role=classify_asset(key)
   record={
    "asset_group_id":"rioforce-"+hashlib.sha256(key.encode()).hexdigest()[:24],
    "relative_stem":key,
    "category":Path(key).parts[0] if Path(key).parts else "",
    "asset_class":asset_class,
    "surface_role_hint":surface_role,
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
