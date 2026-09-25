#!/usr/bin/env python3
"""Create visual embeddings for local minifigure DerivedAssets.

Supports:
- facebook DINOv3 models through Transformers image-feature extraction
- Google SigLIP2 vision embeddings through Transformers

Embeddings are stored in a NumPy matrix plus JSONL metadata. Pin an exact model revision
for reproducible corpus snapshots.
"""
from __future__ import annotations

import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor,AutoModel,AutoProcessor

VERSION="minifigure-embedding-index/v1"

def now_iso():return datetime.now(timezone.utc).isoformat()
def sha256(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()

def load_records(path):
 with path.open("r",encoding="utf-8") as f:
  for line in f:
   if line.strip():yield json.loads(line)

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--input",type=Path,required=True)
 ap.add_argument("--output-dir",type=Path,required=True)
 ap.add_argument("--model",required=True,help="e.g. facebook/dinov3-convnext-tiny-pretrain-lvd1689m or google/siglip2-base-patch16-224")
 ap.add_argument("--revision",default=None)
 ap.add_argument("--batch-size",type=int,default=16)
 ap.add_argument("--device",default="cuda" if torch.cuda.is_available() else "cpu")
 args=ap.parse_args()
 args.output_dir.mkdir(parents=True,exist_ok=True)

 model=AutoModel.from_pretrained(args.model,revision=args.revision).to(args.device).eval()
 try: processor=AutoProcessor.from_pretrained(args.model,revision=args.revision)
 except Exception: processor=AutoImageProcessor.from_pretrained(args.model,revision=args.revision)

 records=list(load_records(args.input))
 vectors=[]; meta=[]
 for start in range(0,len(records),args.batch_size):
  batch=records[start:start+args.batch_size]
  images=[Image.open(r["local_path"]).convert("RGB") for r in batch]
  inputs=processor(images=images,return_tensors="pt")
  inputs={k:v.to(args.device) if hasattr(v,"to") else v for k,v in inputs.items()}
  with torch.no_grad():
   out=model(**inputs)
  if hasattr(out,"image_embeds") and out.image_embeds is not None:
   emb=out.image_embeds
  elif hasattr(out,"pooler_output") and out.pooler_output is not None:
   emb=out.pooler_output
  elif hasattr(out,"last_hidden_state"):
   emb=out.last_hidden_state.mean(dim=1)
  else:
   raise RuntimeError("Could not find image embedding in model output")
  emb=torch.nn.functional.normalize(emb.float(),dim=-1).cpu().numpy()
  for r,v in zip(batch,emb):
   idx=len(vectors); vectors.append(v.astype(np.float32))
   source_hash=sha256(Path(r["local_path"]))
   meta.append({
    "embedding_record_id":"emb-"+hashlib.sha256((r["derived_asset_id"]+"|"+args.model+"|"+str(args.revision)+"|"+source_hash).encode()).hexdigest()[:24],
    "derived_asset_id":r["derived_asset_id"],
    "source_reference_asset_id":r.get("source_reference_asset_id"),
    "source_sha256":source_hash,
    "model_name":args.model,
    "model_revision":args.revision,
    "model_family":"siglip2" if "siglip" in args.model.lower() else "dinov3" if "dinov3" in args.model.lower() else "other",
    "vector_index":idx,
    "dimension":int(v.shape[0]),
    "normalized":True,
    "created_at":now_iso()
   })
 matrix=np.stack(vectors) if vectors else np.zeros((0,0),dtype=np.float32)
 np.save(args.output_dir/"embeddings.npy",matrix)
 with (args.output_dir/"embedding_records.jsonl").open("w",encoding="utf-8") as f:
  for r in meta:f.write(json.dumps(r,ensure_ascii=False)+"\n")
 report={"schema":"minifigure-embedding-index-report/v1","version":VERSION,"created_at":now_iso(),"model":args.model,"revision":args.revision,"device":args.device,"records":len(meta),"dimension":int(matrix.shape[1]) if matrix.ndim==2 and matrix.shape[0] else None,"embeddings":str(args.output_dir/"embeddings.npy"),"metadata":str(args.output_dir/"embedding_records.jsonl")}
 (args.output_dir/"import_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print(json.dumps(report,indent=2))

if __name__=="__main__":main()
