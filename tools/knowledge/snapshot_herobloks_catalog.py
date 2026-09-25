#!/usr/bin/env python3
"""Snapshot HeroBloks' public complete figure list into a compact catalog census.

The /list page is intentionally used as an index. This tool records catalog identifiers,
URLs, URL-derived brand/serial/name slugs, and aggregate code-family observations. It does
not assume brand ownership/factory relationships from shared prefixes or collaborations.
"""
from __future__ import annotations
import argparse, hashlib, json, re, urllib.request
from collections import Counter,defaultdict
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin,urlparse,unquote

VERSION="herobloks-catalog-census/v1"
BASE="https://www.herobloks.com"
LIST_URL=BASE+"/list"
UA="BrickmenResearch/1.0"

def now_iso():return datetime.now(timezone.utc).isoformat()

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.href=None; self.buf=[]; self.rows=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a":
            self.href=dict(attrs).get("href"); self.buf=[]
    def handle_data(self,data):
        if self.href is not None:self.buf.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=="a" and self.href is not None:
            self.rows.append((self.href," ".join("".join(self.buf).split())))
            self.href=None; self.buf=[]

def fetch(url,timeout=60):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()

def parse_figure_href(href,text):
    u=urlparse(urljoin(BASE,href))
    parts=[unquote(x) for x in u.path.split("/") if x]
    if len(parts)<2 or parts[0]!="figures" or not parts[1].isdigit():return None
    catalog_id=int(parts[1])
    brand_slug=parts[2] if len(parts)>2 else None
    serial_slug=parts[3] if len(parts)>3 else None
    name_slug=parts[4] if len(parts)>4 else None
    # Some older URLs omit brand/serial; preserve null rather than guessing.
    return {
      "herobloks_id":catalog_id,
      "url":f"{u.scheme or 'https'}://{u.netloc or 'www.herobloks.com'}{u.path}",
      "brand_slug":brand_slug,
      "serial_slug":serial_slug,
      "name_slug":name_slug,
      "anchor_text":text or None
    }

def code_family(serial):
    if not serial:return None
    cleaned=serial.replace("-","").replace("_","")
    m=re.match(r"([a-zA-Z]+)",cleaned)
    return m.group(1).upper() if m else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    ap.add_argument("--brand-output",type=Path)
    ap.add_argument("--source-url",default=LIST_URL)
    args=ap.parse_args()
    raw=fetch(args.source_url)
    parser=Links(); parser.feed(raw.decode("utf-8","replace"))
    by_id={}
    for href,text in parser.rows:
        rec=parse_figure_href(href,text)
        if rec:by_id[rec["herobloks_id"]]=rec
    rows=[by_id[k] for k in sorted(by_id)]
    brand=Counter();prefix=Counter();brand_prefix=defaultdict(Counter)
    for r in rows:
        b=r.get("brand_slug") or "unknown"; brand[b]+=1
        p=code_family(r.get("serial_slug"))
        if p:
            prefix[p]+=1;brand_prefix[b][p]+=1
            r["serial_prefix_candidate"]=p
        else:r["serial_prefix_candidate"]=None
        r["processor_version"]=VERSION
        r["relationship_policy"]="URL brand/serial fields are catalog observations only; do not infer manufacturer ownership/factory identity."
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    brand_rows=[]
    for b,count in sorted(brand.items(),key=lambda kv:(-kv[1],kv[0])):
        pref=brand_prefix.get(b,Counter())
        top=pref.most_common()
        top_count=top[0][1] if top else 0
        dominance=round(top_count/count,4) if count else 0
        brand_rows.append({
          "brand_slug":b,
          "figure_count":count,
          "serial_prefix_candidates":[{"prefix":k,"count":v,"fraction":round(v/count,4)} for k,v in top[:50]],
          "dominant_prefix":top[0][0] if top else None,
          "dominant_prefix_count":top_count,
          "dominant_prefix_fraction":dominance,
          "stable_prefix_candidate":bool(top and top_count>=10 and dominance>=0.80),
          "policy":"Catalog-derived brand/prefix observation only; never infer ownership or factory identity from this record."
        })
    if args.brand_output:
        args.brand_output.parent.mkdir(parents=True,exist_ok=True)
        args.brand_output.write_text(json.dumps({
          "schema":"herobloks-brand-census/v1",
          "created_at":now_iso(),
          "source_url":args.source_url,
          "source_sha256":hashlib.sha256(raw).hexdigest(),
          "brand_records":brand_rows
        },indent=2)+"\n",encoding="utf-8")

    summary={
      "schema":"herobloks-catalog-census-summary/v1",
      "created_at":now_iso(),"processor_version":VERSION,
      "source_url":args.source_url,"source_sha256":hashlib.sha256(raw).hexdigest(),
      "source_bytes":len(raw),"figure_records":len(rows),
      "brand_slug_count":len(brand),"serial_prefix_candidate_count":len(prefix),
      "top_brand_slugs":[{"brand_slug":k,"count":v} for k,v in brand.most_common(100)],
      "top_serial_prefix_candidates":[{"prefix":k,"count":v} for k,v in prefix.most_common(100)],
      "brand_prefix_candidates":{
        b:[{"prefix":k,"count":v} for k,v in c.most_common(20)]
        for b,c in sorted(brand_prefix.items(),key=lambda kv:(-sum(kv[1].values()),kv[0]))[:100]
      },
      "status":"catalog_index_snapshot_complete"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:summary[k] for k in ("figure_records","brand_slug_count","serial_prefix_candidate_count","status")},indent=2))

if __name__=="__main__":main()
