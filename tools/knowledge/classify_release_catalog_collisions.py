#!/usr/bin/env python3
"""Classify exact-serial catalog collisions into package/shared-code vs true ambiguity."""
from __future__ import annotations
import argparse,json,re,unicodedata
from collections import Counter
from pathlib import Path
VERSION="release-collision-classifier/v1"

def load(path):
  with Path(path).open(encoding="utf-8") as f:
    for line in f:
      line=line.strip()
      if line: yield json.loads(line)

def norm(v):
  s=unicodedata.normalize("NFKD",str(v or ""))
  s="".join(c for c in s if not unicodedata.combining(c)).casefold()
  return " ".join(re.findall(r"[a-z0-9]+",s))

def toks(v): return set(norm(v).split())

def main():
  ap=argparse.ArgumentParser()
  ap.add_argument("--input",type=Path,required=True)
  ap.add_argument("--output",type=Path,required=True)
  ap.add_argument("--summary",type=Path,required=True)
  a=ap.parse_args()
  out=[];counts=Counter()
  for r in load(a.input):
    names=r.get("observed_names") or []
    matches=r.get("herobloks_matches") or []
    mt=[toks(m.get("anchor_text") or m.get("name_slug")) for m in matches]
    ot=set().union(*(toks(n) for n in names)) if names else set()
    all_match_tokens=set().union(*mt) if mt else set()
    micro=any("microfigure" in x for x in all_match_tokens)
    # Multiple catalog entries sharing a serial can represent package contents when the user
    # label itself joins multiple named subjects or when every match contributes a subject token.
    joined_label=any(re.search(r"\b(and|with|&|\+)\b",str(n),re.I) for n in names)
    supportive=sum(bool(ot & x) for x in mt)
    if micro and supportive>=1:
      cls="shared_code_scale_or_component_variant"
    elif joined_label and supportive>=2:
      cls="shared_package_code_multiple_figures"
    elif supportive==1:
      cls="one_catalog_entry_matches_user_identity_other_collision_needs_review"
    elif supportive>=2:
      cls="multiple_catalog_entries_support_user_label"
    else:
      cls="true_or_unresolved_catalog_collision"
    counts[cls]+=1
    out.append({
      "maker_product_code":r.get("maker_product_code"),
      "observed_names":names,
      "classification":cls,
      "supportive_catalog_entries":supportive,
      "catalog_entry_count":len(matches),
      "catalog_matches":matches,
      "resolution_status":"structurally_classified_needs_canonical_release_review",
      "policy":"Structural classification only. Shared serials are not collapsed into one figure identity; package/component relationships require explicit release modeling.",
      "processor_version":VERSION
    })
  out.sort(key=lambda x:(x["classification"],x["maker_product_code"] or ""))
  a.output.parent.mkdir(parents=True,exist_ok=True)
  with a.output.open("w",encoding="utf-8") as f:
    for x in out:f.write(json.dumps(x,ensure_ascii=False)+"\n")
  summary={"schema":"release-collision-classification-summary/v1","processor_version":VERSION,
           "records":len(out),"classification_counts":dict(counts),
           "status":"release_collision_structure_classified"}
  a.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
  print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
