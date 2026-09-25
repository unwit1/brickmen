#!/usr/bin/env python3
"""Build candidate Fortnite normal-style -> LEGO Style TranslationPairs.

Inputs are Fortnite-API compatible BR and LEGO cosmetics JSON snapshots. The script is
schema-defensive: it extracts list payloads, flattens scalar identifiers, and joins by
strong identifiers first, then unique normalized names.

This produces *candidate* TranslationPairs. Visual/exact outfit review still determines
whether a pair is accepted for training.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

VERSION="fortnite-lego-translation-pairs/v1"
def now_iso():return datetime.now(timezone.utc).isoformat()
def load(path):
    obj=json.loads(path.read_text(encoding="utf-8"))
    if isinstance(obj,list):return obj
    if isinstance(obj,dict):
        for k in ("data","items","cosmetics","results"):
            if isinstance(obj.get(k),list):return obj[k]
    raise ValueError(f"could not find list payload in {path}")
def norm(s):return re.sub(r"[^a-z0-9]+"," ",str(s or "").casefold()).strip()
def scalars(obj,prefix=""):
    out=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            key=f"{prefix}.{k}" if prefix else k
            if isinstance(v,(str,int,float,bool)) or v is None:out.append((key,v))
            elif isinstance(v,(dict,list)):out.extend(scalars(v,key))
    elif isinstance(obj,list):
        for i,v in enumerate(obj):out.extend(scalars(v,f"{prefix}[{i}]"))
    return out
def first(obj,*keys):
    for k in keys:
        if isinstance(obj,dict) and obj.get(k) not in (None,""):return obj[k]
    return None
def image_urls(obj):
    vals=[]
    for k,v in scalars(obj):
        if isinstance(v,str) and v.startswith(("http://","https://")) and any(x in k.casefold() for x in ("image","icon","small","large","wide")):
            vals.append(v)
    return sorted(set(vals))
def stable(*parts):
    return hashlib.sha256("|".join(str(x) for x in parts).encode()).hexdigest()[:24]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--br",type=Path,required=True)
    ap.add_argument("--lego",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    br=load(args.br);lego=load(args.lego);out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)

    br_by_id={str(first(x,"id","backendValue","path")):x for x in br if first(x,"id","backendValue","path")}
    br_name=defaultdict(list)
    for x in br:
        n=norm(first(x,"name","displayName"))
        if n:br_name[n].append(x)

    pairs=[];methods=Counter();unmatched=[]
    for l in lego:
        lid=str(first(l,"id","backendValue","path") or "")
        lname=str(first(l,"name","displayName") or "")
        candidate=None;method=None;confidence=0.0;evidence=[]

        # 1. Exact same primary identifier.
        if lid and lid in br_by_id:
            candidate=br_by_id[lid];method="exact_primary_id";confidence=1.0;evidence=[lid]

        # 2. Any scalar value in LEGO object exactly equals a BR primary ID.
        if candidate is None:
            hits=[]
            for k,v in scalars(l):
                if isinstance(v,str) and v in br_by_id:hits.append((k,v))
            unique={v for _,v in hits}
            if len(unique)==1:
                bid=next(iter(unique));candidate=br_by_id[bid];method="embedded_br_id";confidence=.98;evidence=hits

        # 3. Unique exact normalized display name.
        if candidate is None:
            n=norm(lname)
            if n and len(br_name[n])==1:
                candidate=br_name[n][0];method="unique_exact_name";confidence=.85;evidence=[lname]

        if candidate is None:
            unmatched.append({"lego_id":lid or None,"lego_name":lname or None,"field_names":sorted(l.keys()) if isinstance(l,dict) else []})
            continue

        bid=str(first(candidate,"id","backendValue","path") or "")
        bname=str(first(candidate,"name","displayName") or "")
        rec={
            "translation_pair_id":"fortnitepair-"+stable(lid,bid,method),
            "pair_family":"fortnite_outfit_to_lego_style",
            "source_appearance":{"provider":"Fortnite","br_id":bid or None,"name":bname or None,"images":image_urls(candidate)},
            "lego_target":{"provider":"Fortnite LEGO Style","lego_id":lid or None,"name":lname or None,"images":image_urls(l)},
            "join_method":method,
            "join_evidence":evidence,
            "identity_match_confidence":confidence,
            "exactness":"candidate_same_cosmetic_identity",
            "review_status":"automatic_candidate",
            "processor_version":VERSION
        }
        pairs.append(rec);methods[method]+=1

    with (out/"fortnite_lego_translation_pairs.jsonl").open("w",encoding="utf-8") as f:
        for r in sorted(pairs,key=lambda x:(x["source_appearance"]["name"] or "",x["translation_pair_id"])):f.write(json.dumps(r,ensure_ascii=False)+"\n")
    with (out/"fortnite_lego_unmatched.jsonl").open("w",encoding="utf-8") as f:
        for r in unmatched:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
        "schema":"fortnite-lego-translation-pair-summary/v1","created_at":now_iso(),
        "processor_version":VERSION,"br_records":len(br),"lego_records":len(lego),
        "candidate_pairs":len(pairs),"unmatched_lego":len(unmatched),
        "pair_methods":dict(methods),
        "lego_top_level_fields":sorted(set(k for x in lego if isinstance(x,dict) for k in x.keys())),
        "br_top_level_fields":sorted(set(k for x in br if isinstance(x,dict) for k in x.keys()))
    }
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
