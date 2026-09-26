#!/usr/bin/env python3
"""Classify Skywalker digital->physical candidates into character-level vs exact-version evidence.

This layer is intentionally conservative:
- character-level counterpart means the digital asset and physical record appear to depict the same named character;
- exact-version equivalence requires stronger version/outfit evidence and is never inferred from name alone;
- filename suffix variants remain distinct unless independently resolved.
"""
from __future__ import annotations
import argparse,json,re,unicodedata
from collections import Counter
from pathlib import Path

VERSION="skywalker-counterpart-classification/v1"

STOP={"lego","star","wars","minifig","minifigure","figure","character","profile","icon","icons"}

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def split_camel(v):
    s=re.sub(r"([a-z0-9])([A-Z])",r"\1 \2",str(v or ""))
    s=re.sub(r"([A-Za-z])([0-9])",r"\1 \2",s)
    s=re.sub(r"([0-9])([A-Za-z])",r"\1 \2",s)
    return s

def norm(v):
    s=unicodedata.normalize("NFKD",split_camel(v))
    s="".join(c for c in s if not unicodedata.combining(c)).casefold()
    s=re.sub(r"[^a-z0-9]+"," ",s)
    return " ".join(t for t in s.split() if t and t not in STOP)

def key_parts(key):
    raw=str(key or "")
    parts=raw.split("_")
    base=parts[0]
    suffix=parts[1:] if len(parts)>1 else []
    return base,suffix

def same_character(base_key, physical_name):
    base_tokens=norm(base_key).split()
    p=norm(physical_name)
    pt=set(p.split())
    if not base_tokens:return False
    # Require every base-character token to occur in the physical catalog name.
    return all(t in pt for t in base_tokens)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    rows=[];counts=Counter()
    for r in load_jsonl(args.candidates):
        key=r.get("character_variant_key")
        base,suffix=key_parts(key)
        top=(r.get("top_candidates") or [])
        first=top[0] if top else None
        same=bool(first and same_character(base,first.get("name")))
        top_score=float(r.get("top_score") or 0)
        margin=float(r.get("top_margin") or 0)

        has_variant_suffix=bool(suffix)
        if same and top_score>=0.86 and margin>=0.10:
            counterpart="strong_character_counterpart"
        elif same and top_score>=0.76 and margin>=0.05:
            counterpart="review_character_counterpart"
        else:
            counterpart="unresolved_character_counterpart"

        # Exact outfit/version equivalence is intentionally stricter.
        if counterpart=="strong_character_counterpart" and not has_variant_suffix:
            exact="character_match_only_version_unresolved"
        elif counterpart in {"strong_character_counterpart","review_character_counterpart"} and has_variant_suffix:
            exact="variant_suffix_requires_version_resolution"
        else:
            exact="unresolved"

        counts[counterpart]+=1
        counts[exact]+=1
        rows.append({
          "asset_id":r.get("asset_id"),
          "character_variant_key":key,
          "base_character_key":base,
          "variant_suffix_tokens":suffix,
          "class":r.get("class"),
          "filename":r.get("filename"),
          "top_physical_candidate":first,
          "top_score":top_score,
          "top_margin":margin,
          "character_counterpart_status":counterpart,
          "exact_version_status":exact,
          "all_top_candidates":top,
          "policy":"Character-level counterpart evidence may support identity alignment. Exact physical outfit/version equivalence is never inferred from name similarity alone; variant suffixes remain separate until independently resolved.",
          "processor_version":VERSION
        })

    rows.sort(key=lambda x:(
      0 if x["character_counterpart_status"]=="strong_character_counterpart" else
      1 if x["character_counterpart_status"]=="review_character_counterpart" else 2,
      0 if not x["variant_suffix_tokens"] else 1,
      -(x["top_score"] or 0),
      x.get("character_variant_key") or ""
    ))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"skywalker-counterpart-classification-summary/v1",
      "processor_version":VERSION,
      "records":len(rows),
      "strong_character_counterparts":sum(x["character_counterpart_status"]=="strong_character_counterpart" for x in rows),
      "review_character_counterparts":sum(x["character_counterpart_status"]=="review_character_counterpart" for x in rows),
      "unresolved_character_counterparts":sum(x["character_counterpart_status"]=="unresolved_character_counterpart" for x in rows),
      "variant_suffix_records":sum(bool(x["variant_suffix_tokens"]) for x in rows),
      "character_match_only_version_unresolved":sum(x["exact_version_status"]=="character_match_only_version_unresolved" for x in rows),
      "variant_suffix_requires_version_resolution":sum(x["exact_version_status"]=="variant_suffix_requires_version_resolution" for x in rows),
      "status":"character_counterpart_layer_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
