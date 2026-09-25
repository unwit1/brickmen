#!/usr/bin/env python3
"""Snapshot the current LEGO Pick a Brick catalog through LEGO's GraphQL endpoint.

This adapter uses the public Pick a Brick web application's GraphQL request pattern.
As of 2026-06-24 the request requires Origin, x-locale and Referer headers, and the
quantityInSet query must pass sku:null rather than declaring an unused $sku variable.

The tool fetches the full catalog, not only minifigure parts. Downstream reconciliation
with Rebrickable/BrickLink/LEGO identifiers classifies minifigure components reliably.

Outputs:
  pick_a_brick_elements.jsonl
  summary.json

No authentication credentials are required by the current web endpoint. Network errors
are recorded rather than silently returning an empty catalog.
"""
from __future__ import annotations
import argparse, hashlib, json, time, urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

VERSION="lego-pick-a-brick-snapshot/v1"

QUERY=r"""
query PickABrickQuery($input: ElementQueryInput!) {
  searchElements(input: $input) {
    results {
      ...ElementLeaf
      __typename
    }
    total
    count
    __typename
  }
}
fragment ElementLeaf on SearchResultElement {
  id
  designId
  collapseDesignId
  name
  imageUrl
  maxOrderQuantity
  deliveryChannel
  colorHex
  contrastColorHex
  price {
    centAmount
    formattedAmount
    currencyCode
    formattedValue
    __typename
  }
  quantityInSet(sku: null)
  siblings {
    id
    colorHex
    contrastColorHex
    availability
    price {
      formattedAmount
      formattedValue
      __typename
    }
    __typename
  }
  availability
  __typename
}
"""

def now_iso(): return datetime.now(timezone.utc).isoformat()

def post(url,body,headers,timeout):
    req=urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={**headers,"Content-Type":"application/json","Accept":"application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--locale",default="en-US")
    ap.add_argument("--page-size",type=int,default=400)
    ap.add_argument("--delay",type=float,default=0.15)
    ap.add_argument("--timeout",type=float,default=60)
    ap.add_argument("--query",default="")
    ap.add_argument("--include-out-of-stock",action="store_true",default=True)
    args=ap.parse_args()
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    locale=args.locale.replace("_","-")
    route=locale.lower()
    url="https://www.lego.com/api/graphql/PickABrickQuery"
    headers={
      "Origin":"https://www.lego.com",
      "x-locale":locale,
      "Referer":f"https://www.lego.com/{route}/pick-and-build/pick-a-brick",
      "User-Agent":"Mozilla/5.0 PersonalAgentOS-LEGOResearch/1.0"
    }
    all_primary=[]; total_reported=None; page=1; page_counts=[]
    while True:
        inp={
          "page":page,
          "perPage":args.page_size,
          "sort":{"key":"RELEVANCE","direction":"DESC"},
          "query":args.query,
          "fetchSiblings":True,
          "availability":["AVAILABLE","OUT_OF_STOCK"] if args.include_out_of_stock else ["AVAILABLE"]
        }
        payload={"operationName":"PickABrickQuery","variables":{"input":inp},"query":QUERY}
        data=post(url,payload,headers,args.timeout)
        if data.get("errors"):
            raise RuntimeError(json.dumps(data["errors"])[:4000])
        search=data["data"]["searchElements"]
        results=search.get("results") or []
        if total_reported is None: total_reported=search.get("total")
        page_counts.append(len(results))
        all_primary.extend(results)
        if not results or len(results)<args.page_size:break
        page+=1;time.sleep(args.delay)

    # Preserve primary result and sibling variants while deduplicating by LEGO element ID.
    dedup={}
    for item in all_primary:
        element_id=str(item.get("id") or "")
        if element_id: dedup[element_id]={**item,"record_role":"primary_result"}
        for sib in item.get("siblings") or []:
            sid=str(sib.get("id") or "")
            if not sid:continue
            merged={**item,**sib}
            merged["designId"]=item.get("designId")
            merged["collapseDesignId"]=item.get("collapseDesignId")
            merged["name"]=item.get("name")
            merged["deliveryChannel"]=item.get("deliveryChannel")
            merged["imageUrl"]=item.get("imageUrl")
            merged["maxOrderQuantity"]=item.get("maxOrderQuantity")
            merged["record_role"]="sibling_color_variant"
            merged.pop("siblings",None)
            dedup.setdefault(sid,merged)

    records=[]
    for element_id,item in sorted(dedup.items()):
        rec={
          "element_id":element_id,
          "design_id":item.get("designId"),
          "collapse_design_id":item.get("collapseDesignId"),
          "name":item.get("name"),
          "image_url":item.get("imageUrl"),
          "max_order_quantity":item.get("maxOrderQuantity"),
          "delivery_channel":item.get("deliveryChannel"),
          "availability":item.get("availability"),
          "color_hex":item.get("colorHex"),
          "contrast_color_hex":item.get("contrastColorHex"),
          "price":item.get("price"),
          "record_role":item.get("record_role"),
          "locale":locale,
          "retrieved_at":now_iso()
        }
        records.append(rec)
    with (out/"pick_a_brick_elements.jsonl").open("w",encoding="utf-8") as f:
        for r in records:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"lego-pick-a-brick-snapshot/v1","processor_version":VERSION,
      "created_at":now_iso(),"locale":locale,"query":args.query,
      "endpoint":url,"total_reported":total_reported,
      "primary_results":len(all_primary),"unique_element_variants":len(records),
      "pages":len(page_counts),"page_counts":page_counts,
      "availability_counts":dict(Counter(str(r.get("availability")) for r in records)),
      "delivery_channel_counts":dict(Counter(str(r.get("delivery_channel")) for r in records)),
      "currency_counts":dict(Counter(str((r.get("price") or {}).get("currencyCode")) for r in records)),
      "next_stage":"crosswalk element_id/design_id against official/Rebrickable/BrickLink component records and classify minifigure surfaces"
    }
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
