#!/usr/bin/env python3
"""Compare a complete HeroBloks brand census against Brickmen's known maker/brand registries."""
from __future__ import annotations
import argparse,json,re,unicodedata
from pathlib import Path

VERSION="herobloks-brand-gap-analysis/v1"

def slug(value):
    s=unicodedata.normalize("NFKD",str(value or "")).casefold()
    s=s.replace("&"," and ")
    s=re.sub(r"[^a-z0-9]+","-",s).strip("-")
    return s

def collect_known(landscape,crosswalk):
    known={}
    def add(value,source,canonical=None):
        if not value:return
        k=slug(value)
        if k:
            known.setdefault(k,[]).append({"source":source,"canonical":canonical or value})
    groups=landscape.get("groups") or {}
    for gname,items in groups.items():
        if not isinstance(items,list):continue
        for item in items:
            if isinstance(item,str):
                add(item,f"customizer-landscape:{gname}")
            elif isinstance(item,dict):
                name=item.get("name") or item.get("brand")
                add(name,f"customizer-landscape:{gname}",name)
                for a in item.get("aliases") or []:add(a,f"customizer-landscape:{gname}",name)
    for fam in crosswalk.get("families") or []:
        name=fam.get("brand")
        add(name,"compatible-brand-code-crosswalk",name)
        for a in fam.get("aliases") or []:add(a,"compatible-brand-code-crosswalk",name)
    return known

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--brand-census",type=Path,required=True)
    ap.add_argument("--landscape",type=Path,required=True)
    ap.add_argument("--crosswalk",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    census=json.loads(args.brand_census.read_text(encoding="utf-8"))
    landscape=json.loads(args.landscape.read_text(encoding="utf-8"))
    crosswalk=json.loads(args.crosswalk.read_text(encoding="utf-8"))
    known=collect_known(landscape,crosswalk)
    rows=[]
    matched=0
    for b in census.get("brand_records") or []:
        bs=b.get("brand_slug") or ""
        aliases=known.get(slug(bs),[])
        state="known_registry_match" if aliases else "unmodeled_brand_slug"
        matched+=bool(aliases)
        rows.append({
            **b,
            "registry_status":state,
            "registry_matches":aliases,
            "review_priority_score":round(
                (b.get("figure_count") or 0)
                * (1.5 if b.get("stable_prefix_candidate") else 1.0)
                * (0.25 if aliases else 1.0),2
            ),
            "processor_version":VERSION,
        })
    rows.sort(key=lambda x:(x["registry_status"]!="unmodeled_brand_slug",-x["review_priority_score"],x["brand_slug"]))
    unknown=[x for x in rows if x["registry_status"]=="unmodeled_brand_slug"]
    payload={
      "schema":"herobloks-brand-gap-analysis/v1",
      "processor_version":VERSION,
      "hero_bloks_brand_records":len(rows),
      "known_registry_matches":matched,
      "unmodeled_brand_slugs":len(unknown),
      "unmodeled_with_stable_prefix_candidate":sum(bool(x.get("stable_prefix_candidate")) for x in unknown),
      "top_unmodeled":[
        {
          "brand_slug":x["brand_slug"],"figure_count":x["figure_count"],
          "dominant_prefix":x.get("dominant_prefix"),
          "dominant_prefix_fraction":x.get("dominant_prefix_fraction"),
          "stable_prefix_candidate":x.get("stable_prefix_candidate"),
          "review_priority_score":x["review_priority_score"]
        } for x in unknown[:250]
      ],
      "all_brand_analysis":rows,
      "policy":"Unmodeled means absent from current Brickmen registries, not unknown to the world. Brand/prefix observations remain catalog evidence only until identity and relationships are verified.",
      "status":"brand_registry_gap_queue_ready"
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:payload[k] for k in ("hero_bloks_brand_records","known_registry_matches","unmodeled_brand_slugs","unmodeled_with_stable_prefix_candidate","status")},indent=2))
if __name__=="__main__":main()
