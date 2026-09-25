#!/usr/bin/env python3
"""Profile explicit training-source webpages without recursive crawling.

Records page status, final URL, content hash, image/link counts, media URLs and outbound
hosts. This is source-discovery metadata, not a web mirroring tool.
"""
from __future__ import annotations
import argparse,hashlib,json,urllib.request,urllib.parse
from collections import Counter
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path

VERSION="training-source-web-profile/v1"
class P(HTMLParser):
    def __init__(self,base):
        super().__init__();self.base=base;self.images=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag in {"img","source"}:
            u=d.get("src") or d.get("srcset")
            if u:self.images.append(urllib.parse.urljoin(self.base,u.split(",")[0].split(" ")[0]))
        if tag=="a" and d.get("href"):self.links.append(urllib.parse.urljoin(self.base,d["href"]))
def now_iso():return datetime.now(timezone.utc).isoformat()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source-id",required=True);ap.add_argument("--url",required=True);ap.add_argument("--output",type=Path,required=True);args=ap.parse_args()
    rec={"schema":"training-source-web-profile/v1","processor_version":VERSION,"source_id":args.source_id,"requested_url":args.url,"created_at":now_iso()}
    try:
        req=urllib.request.Request(args.url,headers={"User-Agent":"PersonalAgentOS-LEGOResearch/1.0","Accept":"text/html,*/*"})
        with urllib.request.urlopen(req,timeout=60) as r:
            body=r.read();final=r.geturl();ctype=r.headers.get("Content-Type","")
        rec.update({"status":"ok","final_url":final,"content_type":ctype,"content_bytes":len(body),"content_sha256":hashlib.sha256(body).hexdigest()})
        if "html" in ctype.lower() or body.lstrip().startswith(b"<"):
            text=body.decode("utf-8",errors="replace");p=P(final);p.feed(text)
            rec["image_count"]=len(p.images);rec["link_count"]=len(p.links)
            rec["image_urls"]=sorted(set(p.images))[:5000]
            rec["outbound_hosts"]=dict(Counter(urllib.parse.urlparse(x).hostname or "" for x in p.links).most_common())
            rec["media_candidate_count"]=len(set(p.images))
    except Exception as exc:
        rec.update({"status":"error","error":str(exc)[:2000]})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(rec,indent=2),encoding="utf-8")
    print(json.dumps({k:rec.get(k) for k in ("source_id","status","image_count","link_count","error")},indent=2))
if __name__=="__main__":main()
