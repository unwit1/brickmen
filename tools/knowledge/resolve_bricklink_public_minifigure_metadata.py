#!/usr/bin/env python3
"""Resolve BrickLink minifigure IDs from public catalog metadata pages.

Metadata only: item ID, catalog name, release years, page URL/hash and retrieval status.
No images, price guide data, wanted-list data or authenticated/API endpoints are accessed.
"""
from __future__ import annotations
import argparse,hashlib,json,re,time,urllib.error,urllib.request
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path

VERSION="bricklink-public-minifigure-metadata/v1"
UA="BrickmenResearch/1.0 metadata-only"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def catalog_id_from_record(rec):
    direct=str(rec.get("catalog_id") or rec.get("bricklink_minifigure_id") or "").strip()
    if direct:return direct.casefold()
    url=str(rec.get("catalog_url") or rec.get("bricklink_catalog_url") or "")
    m=re.search(r"[?&]M=([^&#]+)",url,re.I)
    return m.group(1).strip().casefold() if m else None

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.og_title=None;self.description=None;self.title_parts=[];self.in_title=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag.lower()=="meta":
            prop=(a.get("property") or a.get("name") or "").lower()
            content=a.get("content")
            if prop=="og:title" and content:self.og_title=content
            if prop=="description" and content:self.description=content
        if tag.lower()=="title":self.in_title=True
    def handle_endtag(self,tag):
        if tag.lower()=="title":self.in_title=False
    def handle_data(self,data):
        if self.in_title:self.title_parts.append(data)
    @property
    def title(self):return " ".join(" ".join(self.title_parts).split()) or None

def fetch(url,timeout=30,retries=3):
    last=None
    for attempt in range(retries+1):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return r.read(),r.status
        except Exception as exc:
            last=exc
            if attempt<retries:time.sleep(1.0*(2**attempt))
    raise last

def clean_og_name(value,item_id):
    s=" ".join(str(value or "").split())
    patterns=[
      rf"\s*:\s*Minifigure\s+{re.escape(item_id)}\s*\|\s*BrickLink\s*$",
      rf"\s*:\s*Minifigure\s+{re.escape(item_id)}\s*$",
      r"\s*\|\s*BrickLink\s*$",
    ]
    for p in patterns:s=re.sub(p,"",s,flags=re.I)
    return s.strip(" -:") or None

def parse_years(text):
    if not text:return None,None
    m=re.search(r"Years\s+Released\s*:\s*(\d{4})(?:\s*-\s*(\d{4}))?",text,re.I)
    if not m:return None,None
    return int(m.group(1)),int(m.group(2) or m.group(1))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--queue",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    ap.add_argument("--delay-seconds",type=float,default=0.4)
    args=ap.parse_args()

    rows=[];resolved=0;failed=0;name_support=0;name_conflict=0
    for q in load_jsonl(args.queue):
        item_id=catalog_id_from_record(q)
        if not item_id:
            continue
        url=f"https://www.bricklink.com/v2/catalog/catalogitem.page?M={item_id}"
        rec={
          **q,
          "catalog_namespace":q.get("catalog_namespace") or "bricklink_minifigure_id",
          "catalog_id":item_id,
          "name_or_note":q.get("name_or_note") or q.get("name"),
          "bricklink_public_catalog_url":url,
          "processor_version":VERSION
        }
        try:
            raw,status=fetch(url)
            text=raw.decode("utf-8","replace")
            p=MetaParser();p.feed(text)
            catalog_name=clean_og_name(p.og_title,item_id)
            # Some BrickLink pages omit OG metadata. Fall back to a prominent v2 text pattern.
            if not catalog_name:
                m=re.search(r'<h1[^>]*>(.*?)</h1>',text,re.I|re.S)
                if m:
                    catalog_name=re.sub(r"<[^>]+>"," ",m.group(1))
                    catalog_name=" ".join(catalog_name.split()) or None
            y0,y1=parse_years(re.sub(r"<[^>]+>"," ",text))
            rec.update({
              "bricklink_catalog_name":catalog_name,
              "years_released_start":y0,
              "years_released_end":y1,
              "http_status":status,
              "page_sha256":hashlib.sha256(raw).hexdigest(),
              "retrieved_at":now_iso(),
              "resolution_status":"bricklink_public_metadata_resolved" if catalog_name else "bricklink_page_retrieved_name_unparsed"
            })
            if catalog_name:resolved+=1
            else:failed+=1
            user_name=str(q.get("name_or_note") or "").strip()
            if user_name and catalog_name:
                a=set(re.findall(r"[a-z0-9]+",user_name.casefold()))
                b=set(re.findall(r"[a-z0-9]+",catalog_name.casefold()))
                overlap=len(a&b)/len(a|b) if a and b else 0
                rec["user_name_catalog_token_overlap"]=round(overlap,4)
                if overlap>=0.35:name_support+=1
                elif overlap<0.15:name_conflict+=1
        except Exception as exc:
            failed+=1
            rec.update({
              "resolution_status":"bricklink_public_metadata_failed",
              "error":str(exc)[:500],
              "retrieved_at":now_iso()
            })
        rows.append(rec)
        if args.delay_seconds:time.sleep(args.delay_seconds)

    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
      "schema":"bricklink-public-minifigure-metadata-summary/v1",
      "processor_version":VERSION,
      "records":len(rows),
      "catalog_names_resolved":resolved,
      "failed_or_unparsed":failed,
      "named_source_records_with_supportive_catalog_overlap":name_support,
      "named_source_records_with_strong_conflict_signal":name_conflict,
      "policy":"Public catalog metadata only; no authenticated API, prices, images or personal account data.",
      "status":"bricklink_public_metadata_resolution_complete"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
