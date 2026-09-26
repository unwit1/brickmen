#!/usr/bin/env python3
"""Snapshot the DownTheBlocks XINH/G historical minifigure database.

The source is a dated historical catalog/discovery source. Blank catalog entries are preserved
as known serial slots with unknown names rather than silently omitted.
"""
from __future__ import annotations
import argparse,hashlib,json,re,urllib.request
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path

VERSION="downtheblocks-xinh-gh-catalog/v1"
DEFAULT_URL="https://downtheblocks.com/xinh-minifigure-set-list-database/"
UA="BrickmenResearch/1.0"

def now_iso(): return datetime.now(timezone.utc).isoformat()

class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]
    def handle_data(self,data):
        if data and data.strip(): self.parts.append(" ".join(data.split()))

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=90) as r:
        return r.read()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-url",default=DEFAULT_URL)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    raw=fetch(args.source_url)
    parser=TextCollector(); parser.feed(raw.decode("utf-8","replace"))
    text="\n".join(parser.parts)

    updated=None
    m=re.search(r"Updated\s+as\s+of\s+([^\n]+)",text,re.I)
    if m: updated=m.group(1).strip()

    # Match XH/GH serials and any same-line descriptive text. Preserve blanks.
    pat=re.compile(r"\b((?:XH|GH)\s*[-_]?\s*\d{1,5})\s*[–—-]\s*([^\n]*)",re.I)
    by_code={}
    for m in pat.finditer(text):
        raw_code=m.group(1)
        code=re.sub(r"[^A-Z0-9]+","",raw_code.upper())
        name=m.group(2).strip(" \t-–—") or None
        # Avoid swallowing obvious page chrome that may follow a blank slot.
        if name and len(name)>250: name=name[:250]
        by_code[code]={
          "serial":code,
          "brand_family":"XINH/GH historical catalog",
          "historical_name":name,
          "name_status":"named" if name else "blank_catalog_slot",
          "source_url":args.source_url,
          "source_updated_label":updated,
          "source_sha256":hashlib.sha256(raw).hexdigest(),
          "processor_version":VERSION,
          "policy":"Historical catalog observation only. Does not prove factory ownership, chronology beyond source context, or equivalence to current brand relationships."
        }

    rows=[by_code[k] for k in sorted(by_code,key=lambda x:(re.sub(r"\d","",x),int(re.sub(r"\D","",x) or 0)))]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
      "schema":"downtheblocks-xinh-gh-catalog-summary/v1",
      "created_at":now_iso(),
      "processor_version":VERSION,
      "source_url":args.source_url,
      "source_updated_label":updated,
      "source_sha256":hashlib.sha256(raw).hexdigest(),
      "source_bytes":len(raw),
      "catalog_records":len(rows),
      "named_records":sum(r["historical_name"] is not None for r in rows),
      "blank_catalog_slots":sum(r["historical_name"] is None for r in rows),
      "xh_records":sum(r["serial"].startswith("XH") for r in rows),
      "gh_records":sum(r["serial"].startswith("GH") for r in rows),
      "status":"historical_catalog_snapshot_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
