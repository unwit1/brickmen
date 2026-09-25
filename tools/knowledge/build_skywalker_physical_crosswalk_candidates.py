#!/usr/bin/env python3
"""Generate conservative Skywalker Saga digital-profile -> Rebrickable physical candidates.

Filename-derived game keys and catalog names are compared as identity candidates only.
No candidate is promoted to physical equivalence automatically; digital-only variants
must remain possible.
"""
from __future__ import annotations
import argparse, json, re, unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

VERSION="skywalker-physical-crosswalk-candidates/v1"
STOP={
    "lego","star","wars","minifig","minifigure","figure","with","and","the","a","an",
    "episode","ep","old","new","version","variant","character","profile","icons","icon",
}

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def camel(value):
    value=re.sub(r"([a-z0-9])([A-Z])",r"\1 \2",str(value or ""))
    value=re.sub(r"([A-Za-z])([0-9])",r"\1 \2",value)
    value=re.sub(r"([0-9])([A-Za-z])",r"\1 \2",value)
    return value

def norm(value):
    value=camel(unicodedata.normalize("NFKD",str(value or "")))
    value="".join(ch if ch.isalnum() else " " for ch in value.casefold())
    toks=[t for t in value.split() if t and t not in STOP]
    return " ".join(toks),toks

def is_star_wars(sample):
    for occ in sample.get("set_occurrences") or []:
        for node in occ.get("theme_path") or []:
            if "star wars" in str(node.get("name") or "").casefold():
                return True
    return False

def score(key,name):
    ka,kt=norm(key);na,nt=norm(name)
    ks=set(kt);ns=set(nt)
    if not ks or not ns:return 0.0,{}
    inter=ks&ns
    union=ks|ns
    jac=len(inter)/len(union)
    containment=len(inter)/len(ks)
    seq=SequenceMatcher(None,ka,na).ratio()
    # First two normalized key tokens are often the character identity.
    core=kt[:2]
    core_hit=sum(1 for t in core if t in ns)/max(1,len(core))
    value=0.35*containment+0.25*jac+0.20*seq+0.20*core_hit
    return round(value,4),{
        "key_normalized":ka,
        "catalog_normalized":na,
        "overlap_tokens":sorted(inter),
        "key_token_coverage":round(containment,4),
        "jaccard":round(jac,4),
        "sequence_ratio":round(seq,4),
        "core_token_hit":round(core_hit,4),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--skywalker-census",type=Path,required=True)
    ap.add_argument("--physical-samples",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    ap.add_argument("--top-k",type=int,default=5)
    args=ap.parse_args()

    census=json.loads(args.skywalker_census.read_text(encoding="utf-8"))
    digital=census.get("records") or []
    physical=[x for x in load_jsonl(args.physical_samples) if is_star_wars(x)]
    rows=[];bands=Counter()
    for d in digital:
        key=d.get("character_variant_key") or d.get("filename")
        candidates=[]
        for p in physical:
            sc,why=score(key,p.get("name"))
            if sc<=0:continue
            candidates.append({
                "fig_num":p.get("fig_num"),
                "name":p.get("name"),
                "score":sc,
                "catalog_image_url":p.get("catalog_image_url"),
                "set_occurrences":p.get("set_occurrences"),
                "evidence":why,
            })
        candidates.sort(key=lambda x:(-x["score"],x["fig_num"] or ""))
        top=candidates[:max(1,args.top_k)]
        top_score=top[0]["score"] if top else 0
        second=top[1]["score"] if len(top)>1 else 0
        margin=round(top_score-second,4)
        if top_score>=0.86 and margin>=0.10:band="strong_candidate"
        elif top_score>=0.76 and margin>=0.05:band="review_candidate"
        else:band="unresolved"
        bands[band]+=1
        rows.append({
            "asset_id":d.get("asset_id"),
            "character_variant_key":key,
            "class":d.get("class"),
            "filename":d.get("filename"),
            "source_path":d.get("source_path"),
            "top_candidates":top,
            "top_score":top_score,
            "top_margin":margin,
            "confidence_band":band,
            "resolution_status":"candidate_only",
            "policy":"Do not collapse a digital profile to a physical release without independent identity/version confirmation; unmatched records may be digital-only.",
            "processor_version":VERSION,
        })

    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
        "schema":"skywalker-physical-crosswalk-candidate-summary/v1",
        "processor_version":VERSION,
        "digital_profile_assets":len(digital),
        "star_wars_physical_candidates_indexed":len(physical),
        "records_written":len(rows),
        "confidence_bands":dict(bands),
        "top_k":args.top_k,
        "status":"candidate_crosswalk_requires_independent_confirmation"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
