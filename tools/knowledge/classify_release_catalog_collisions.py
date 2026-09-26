#!/usr/bin/env python3
"""Classify exact-serial catalog collisions into package/shared-code vs true ambiguity."""
from __future__ import annotations
import argparse,json,re,unicodedata
from collections import Counter
from pathlib import Path
VERSION="release-collision-classifier/v2"

def load(path):
  with Path(path).open(encoding="utf-8") as f:
    for line in f:
      line=line.strip()
      if line: yield json.loads(line)

def load_evidence(path):
  if not path:
    return {}
  payload=json.loads(Path(path).read_text(encoding="utf-8"))
  rows=payload.get("records",payload if isinstance(payload,list) else [])
  return {str(r.get("maker_product_code") or "").upper():r for r in rows if r.get("maker_product_code")}

def norm(v):
  s=unicodedata.normalize("NFKD",str(v or ""))
  s="".join(c for c in s if not unicodedata.combining(c)).casefold()
  return " ".join(re.findall(r"[a-z0-9]+",s))

def toks(v): return set(norm(v).split())

def main():
  ap=argparse.ArgumentParser()
  ap.add_argument("--input",type=Path,required=True)
  ap.add_argument("--evidence",type=Path)
  ap.add_argument("--output",type=Path,required=True)
  ap.add_argument("--summary",type=Path,required=True)
  a=ap.parse_args()
  evidence=load_evidence(a.evidence)
  out=[];counts=Counter();source_backed=0
  for r in load(a.input):
    names=r.get("observed_names") or []
    matches=r.get("herobloks_matches") or []
    mt=[toks(m.get("anchor_text") or m.get("name_slug")) for m in matches]
    ot=set().union(*(toks(n) for n in names)) if names else set()
    all_match_tokens=set().union(*mt) if mt else set()
    micro=any("microfigure" in x for x in all_match_tokens)
    joined_label=any(re.search(r"\b(and|with|&|\+)\b",str(n),re.I) for n in names)
    supportive=sum(bool(ot & x) for x in mt)
    if micro and supportive>=1:
      structural_cls="shared_code_scale_or_component_variant"
    elif joined_label and supportive>=2:
      structural_cls="shared_package_code_multiple_figures"
    elif supportive==1:
      structural_cls="one_catalog_entry_matches_user_identity_other_collision_needs_review"
    elif supportive>=2:
      structural_cls="multiple_catalog_entries_support_user_label"
    else:
      structural_cls="true_or_unresolved_catalog_collision"

    code=str(r.get("maker_product_code") or "").upper()
    ev=evidence.get(code)
    if ev:
      cls=ev.get("resolution_classification") or structural_cls
      resolution_status=ev.get("resolution_status") or "source_backed_collision_resolved"
      source_backed+=1
    else:
      cls=structural_cls
      resolution_status="structurally_classified_needs_canonical_release_review"

    counts[cls]+=1
    row={
      "maker_product_code":r.get("maker_product_code"),
      "observed_names":names,
      "classification":cls,
      "structural_classification":structural_cls,
      "supportive_catalog_entries":supportive,
      "catalog_entry_count":len(matches),
      "catalog_matches":matches,
      "resolution_status":resolution_status,
      "policy":"Shared serials are never collapsed solely from catalog coincidence. Source-backed overrides may resolve the user-facing release identity while retaining package/component/catalog-collision structure.",
      "processor_version":VERSION
    }
    if ev:
      row["source_backed_evidence"]=ev
    out.append(row)

  out.sort(key=lambda x:(x["classification"],x["maker_product_code"] or ""))
  a.output.parent.mkdir(parents=True,exist_ok=True)
  with a.output.open("w",encoding="utf-8") as f:
    for x in out:f.write(json.dumps(x,ensure_ascii=False)+"\n")
  unresolved=sum(1 for x in out if x["classification"]=="true_or_unresolved_catalog_collision")
  summary={
    "schema":"release-collision-classification-summary/v2",
    "processor_version":VERSION,
    "records":len(out),
    "classification_counts":dict(counts),
    "source_backed_resolutions":source_backed,
    "true_or_unresolved_catalog_collisions":unresolved,
    "status":"release_collision_structure_and_source_evidence_classified"
  }
  a.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
  print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
