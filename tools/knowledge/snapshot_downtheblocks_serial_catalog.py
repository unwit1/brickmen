#!/usr/bin/env python3
"""Snapshot a serial-numbered DownTheBlocks minifigure catalog.

Designed for historical compatible-brand catalog pages such as KDL/Koruit, Kopf/Chengyi,
POGO, and World Minifigures. Serial observations, blank slots, duplicates and conflicts
are retained independently from current HeroBloks data.
"""
from __future__ import annotations
import argparse,hashlib,json,re,urllib.request
from collections import Counter
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path

VERSION="downtheblocks-serial-catalog/v1"
UA="BrickmenResearch/1.0"

def now_iso(): return datetime.now(timezone.utc).isoformat()

class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]
    def handle_data(self,data):
        if data and data.strip(): self.parts.append(" ".join(data.split()))

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=90) as r:return r.read()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-url",required=True)
    ap.add_argument("--catalog-id",required=True)
    ap.add_argument("--brand-label",required=True)
    ap.add_argument("--prefix-regex",required=True,help=r"Regex prefix alternatives, e.g. K|XP or KF")
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    raw=fetch(args.source_url)
    parser=TextCollector(); parser.feed(raw.decode("utf-8","replace"))
    text="\n".join(parser.parts)
    updated=None
    m=re.search(r"Updated\s+(?:as\s+of\s+)?([^\n.]+(?:\d{4})?)",text,re.I)
    if m: updated=m.group(1).strip()

    serial_pat=re.compile(rf"\b((?:{args.prefix_regex})\s*[-_]?\s*\d{{1,6}}[A-Za-z]?)\b",re.I)
    matches=list(serial_pat.finditer(text))
    observations={}
    for idx,m in enumerate(matches):
        code=re.sub(r"[^A-Z0-9]+","",m.group(1).upper())
        end=matches[idx+1].start() if idx+1<len(matches) else len(text)
        segment=text[m.end():end]
        first_line=(segment.splitlines()[0] if segment.splitlines() else "").strip()
        first_line=re.sub(r"^[\s:–—-]+","",first_line).strip()
        # Skip obvious page navigation/date labels if captured after a blank slot.
        name=first_line or None
        if name and len(name)>250:name=name[:250]
        observations.setdefault(code,[]).append(name)

    digest=hashlib.sha256(raw).hexdigest()
    rows=[]
    for code,obs in observations.items():
        names=[]
        for name in obs:
            if name and name not in names:names.append(name)
        status="blank_catalog_slot" if not names else "named" if len(names)==1 else "conflicting_names"
        rows.append({
          "serial":code,
          "catalog_id":args.catalog_id,
          "brand_label":args.brand_label,
          "historical_name":names[0] if names else None,
          "historical_names":names,
          "name_status":status,
          "occurrence_count":len(obs),
          "source_url":args.source_url,
          "source_updated_label":updated,
          "source_sha256":digest,
          "processor_version":VERSION,
          "policy":"Historical catalog observation only. Blank slots, duplicate serials and name conflicts are retained. Catalog evidence does not independently prove factory ownership or corporate relationships."
        })
    rows.sort(key=lambda r:(re.sub(r"\d","",r["serial"]),int(re.sub(r"\D","",r["serial"]) or 0),r["serial"]))
    normalized=hashlib.sha256("\n".join(
      f"{r['serial']}|{r['name_status']}|{';'.join(r['historical_names'])}|{r['occurrence_count']}" for r in rows
    ).encode()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"downtheblocks-serial-catalog-summary/v1",
      "created_at":now_iso(),"processor_version":VERSION,
      "catalog_id":args.catalog_id,"brand_label":args.brand_label,
      "source_url":args.source_url,"source_updated_label":updated,
      "source_sha256":digest,"normalized_catalog_sha256":normalized,
      "source_bytes":len(raw),"catalog_records":len(rows),
      "named_records":sum(r["name_status"]=="named" for r in rows),
      "blank_catalog_slots":sum(r["name_status"]=="blank_catalog_slot" for r in rows),
      "conflicting_name_records":sum(r["name_status"]=="conflicting_names" for r in rows),
      "duplicate_serial_records":sum(r["occurrence_count"]>1 for r in rows),
      "prefix_counts":dict(Counter(re.match(r"^[A-Z]+",r["serial"]).group(0) for r in rows)),
      "status":"historical_catalog_snapshot_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
