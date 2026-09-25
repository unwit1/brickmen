#!/usr/bin/env python3
"""Snapshot Hugging Face dataset metadata/file inventory through the public Hub API."""
from __future__ import annotations
import argparse,json,urllib.request,hashlib
from datetime import datetime,timezone
from pathlib import Path

VERSION="hf-dataset-metadata-snapshot/v1"
def now_iso():return datetime.now(timezone.utc).isoformat()
def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"PersonalAgentOS-LEGOResearch/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode())
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--dataset",required=True);ap.add_argument("--output",type=Path,required=True);args=ap.parse_args()
    data=get("https://huggingface.co/api/datasets/"+args.dataset)
    siblings=data.get("siblings") or []
    rec={
      "schema":"hf-dataset-metadata-snapshot/v1","processor_version":VERSION,"created_at":now_iso(),
      "dataset":args.dataset,"id":data.get("id"),"sha":data.get("sha"),"lastModified":data.get("lastModified"),
      "downloads":data.get("downloads"),"likes":data.get("likes"),"private":data.get("private"),
      "disabled":data.get("disabled"),"gated":data.get("gated"),"tags":data.get("tags") or [],
      "cardData":data.get("cardData"),"files":[{"rfilename":x.get("rfilename"),"size":x.get("size"),"blobId":x.get("blobId")} for x in siblings],
      "file_count":len(siblings)
    }
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(rec,indent=2),encoding="utf-8")
    print(json.dumps({"dataset":args.dataset,"sha":rec["sha"],"file_count":rec["file_count"]},indent=2))
if __name__=="__main__":main()
