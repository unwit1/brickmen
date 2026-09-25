#!/usr/bin/env python3
"""Index the iechevarria/lego-face-VAE training image corpus and head metadata."""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageStat

VERSION="lego-face-vae-dataset-index/v1"
VOCAB=[
 "grin","smile","eyebrow","eyebrows","eyelash","eyelashes","moustache","mustache",
 "beard","stubble","freckles","glasses","sunglasses","scar","wrinkle","wrinkles",
 "lipstick","lips","headset","eyepatch","goatee","pupils","teeth","tongue","frown",
 "angry","scared","sad","surprised","squint","hair","bandana","robot","alien","skull"
]
def now_iso():return datetime.now(timezone.utc).isoformat()
def sha256(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()
def tokens(name):
 low=(name or "").lower()
 return sorted({v for v in VOCAB if re.search(r"\b"+re.escape(v)+r"\b",low)})
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--root",type=Path,required=True)
 ap.add_argument("--heads-csv",type=Path,required=True)
 ap.add_argument("--output",type=Path,required=True)
 ap.add_argument("--summary",type=Path,required=True)
 args=ap.parse_args()
 heads={}
 with args.heads_csv.open("r",encoding="utf-8-sig",newline="") as f:
  for r in csv.DictReader(f):
   pid=str(r.get("Number") or "").strip()
   if pid:heads[pid]=r
 files=[p for p in args.root.rglob("*") if p.is_file() and p.suffix.lower() in {".jpg",".jpeg",".png"}]
 rows=[];dims=Counter();matched=0;descriptors=Counter()
 for p in sorted(files):
  stem=p.stem
  # Dataset filenames are expected to preserve BrickLink part IDs; tolerate common suffixes.
  candidates=[stem,re.sub(r"[-_](front|back|reverse|[0-9]+)$","",stem,flags=re.I)]
  pid=next((c for c in candidates if c in heads),None)
  meta=heads.get(pid,{}) if pid else {}
  with Image.open(p) as im:
   im.load(); w,h=im.size; mode=im.mode
   thumb=im.convert("RGB").resize((32,32),Image.Resampling.LANCZOS)
   mean=[round(x,2) for x in ImageStat.Stat(thumb).mean[:3]]
  ds=tokens(meta.get("Name") or "")
  for d in ds:descriptors[d]+=1
  if pid:matched+=1
  rows.append({
   "asset_id":"facevae-"+sha256(p)[:24],
   "relative_path":p.relative_to(args.root).as_posix(),
   "sha256":sha256(p),"bytes":p.stat().st_size,
   "width":w,"height":h,"mode":mode,"mean_rgb_32":mean,
   "bricklink_head_part_id":pid,
   "bricklink_head_name":meta.get("Name") or None,
   "bricklink_category_id":meta.get("Category ID") or None,
   "dimensions_text":meta.get("Dimensions") or None,
   "semantic_descriptor_tokens":ds,
   "authority":"community_training_dataset_derived_from_bricklink",
   "source_system":"iechevarria/lego-face-VAE",
   "training_permission_basis":"project_specific_permission",
   "processor_version":VERSION
  })
  dims[f"{w}x{h}"]+=1
 args.output.parent.mkdir(parents=True,exist_ok=True)
 with args.output.open("w",encoding="utf-8") as f:
  for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
 summary={
  "schema":"lego-face-vae-dataset-index-summary/v1","created_at":now_iso(),
  "processor_version":VERSION,"image_records":len(rows),"head_table_records":len(heads),
  "images_matched_to_head_table":matched,"unmatched_images":len(rows)-matched,
  "unique_matched_head_parts":len({r["bricklink_head_part_id"] for r in rows if r["bricklink_head_part_id"]}),
  "dimension_counts":dict(dims),
  "semantic_descriptor_counts":dict(descriptors.most_common()),
  "status":"training_face_corpus_indexed"
 }
 args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
