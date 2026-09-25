#!/usr/bin/env python3
"""Ingest structured rows from the BricksFinder Hugging Face minifigure-caption dataset.

Uses the public HF datasets-server row API so caption/ID/part supervision can be
materialized without downloading the embedded ~558 MB image payload.
"""
from __future__ import annotations
import argparse,json,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path

VERSION="bricksfinder-caption-ingest/v1"
API="https://datasets-server.huggingface.co/rows"
UA="BrickmenResearch/1.0"

def now_iso():return datetime.now(timezone.utc).isoformat()
def load_jsonl(path):
 with Path(path).open("r",encoding="utf-8") as f:
  for line in f:
   line=line.strip()
   if line:yield json.loads(line)
def fetch_json(url,timeout=60):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode("utf-8"))
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--dataset",default="Armaggheddon/lego_minifigure_captions")
 ap.add_argument("--config",default="default")
 ap.add_argument("--split",default="train")
 ap.add_argument("--current-samples",type=Path,required=True)
 ap.add_argument("--output-dir",type=Path,required=True)
 ap.add_argument("--page-size",type=int,default=100)
 ap.add_argument("--shard-size",type=int,default=1000)
 ap.add_argument("--delay",type=float,default=0.05)
 args=ap.parse_args()
 current={r.get("fig_num"):r for r in load_jsonl(args.current_samples) if r.get("fig_num")}
 out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
 rows=[];offset=0;reported=None;pages=0
 while True:
  qs=urllib.parse.urlencode({"dataset":args.dataset,"config":args.config,"split":args.split,"offset":offset,"length":args.page_size})
  data=fetch_json(API+"?"+qs);pages+=1
  if reported is None:reported=data.get("num_rows_total")
  batch=data.get("rows") or []
  if not batch:break
  for item in batch:
   row=item.get("row") or {}
   fig=row.get("fig_num")
   cur=current.get(fig)
   image=row.get("image")
   image_ref=None
   if isinstance(image,dict):
    image_ref=image.get("src") or image.get("path")
   rec={
    "dataset_row_index":item.get("row_idx"),
    "fig_num":fig,
    "short_caption":row.get("short_caption"),
    "caption":row.get("caption"),
    "num_parts_dataset":row.get("num_parts"),
    "minifig_inventory_ids":row.get("minifig_inventory_id"),
    "part_inventory_id":row.get("part_inventory_id"),
    "part_nums":row.get("part_num"),
    "image_reference":image_ref,
    "current_rebrickable_match":bool(cur),
    "current_rebrickable_name":cur.get("name") if cur else None,
    "current_component_count":cur.get("component_count_resolved") if cur else None,
    "current_catalog_image_url":cur.get("catalog_image_url") if cur else None,
    "short_caption_matches_current_name":bool(cur and row.get("short_caption")==cur.get("name")),
    "source_dataset":args.dataset,
    "training_permission_basis":"project_specific_permission",
    "processor_version":VERSION
   }
   rows.append(rec)
  offset+=len(batch)
  if reported is not None and offset>=reported:break
  if len(batch)<args.page_size:break
  time.sleep(args.delay)
 shard_names=[]
 for start in range(0,len(rows),args.shard_size):
  idx=start//args.shard_size+1
  name=f"records-part-{idx:02d}.jsonl";shard_names.append(name)
  with (out/name).open("w",encoding="utf-8") as f:
   for r in rows[start:start+args.shard_size]:f.write(json.dumps(r,ensure_ascii=False)+"\n")
 manifest={
  "schema":"bricksfinder-caption-ingest-manifest/v1","created_at":now_iso(),
  "processor_version":VERSION,"dataset":args.dataset,"config":args.config,"split":args.split,
  "reported_rows":reported,"records":len(rows),"pages":pages,
  "current_rebrickable_matches":sum(r["current_rebrickable_match"] for r in rows),
  "current_rebrickable_missing":sum(not r["current_rebrickable_match"] for r in rows),
  "short_caption_matches_current_name":sum(r["short_caption_matches_current_name"] for r in rows),
  "short_caption_name_drift":sum(r["current_rebrickable_match"] and not r["short_caption_matches_current_name"] for r in rows),
  "records_with_caption":sum(bool(r.get("caption")) for r in rows),
  "records_with_part_nums":sum(bool(r.get("part_nums")) for r in rows),
  "shard_size":args.shard_size,"shard_count":len(shard_names),"shards":shard_names,
  "status":"structured_caption_supervision_ingested"
 }
 (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(manifest,indent=2))
if __name__=="__main__":main()
