#!/usr/bin/env python3
"""Classify Skywalker records at three distinct levels:
1) official digital identity label present,
2) physical character-family support,
3) unique physical release/version support.

This avoids treating an ambiguous Leia/Luke outfit as an unknown character merely because
several physical releases have similarly good names.
"""
from __future__ import annotations
import argparse,json,re,unicodedata
from collections import Counter,defaultdict
from pathlib import Path

VERSION="skywalker-identity-family/v1"
GENERIC={"goon","friend","alien","human","officer","trooper","droid","guard","clone"}

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:yield json.loads(line)

def split_camel(v):
    s=re.sub(r"([a-z0-9])([A-Z])",r"\1 \2",str(v or ""))
    s=re.sub(r"([A-Za-z])([0-9])",r"\1 \2",s)
    s=re.sub(r"([0-9])([A-Za-z])",r"\1 \2",s)
    return s

def norm(v):
    s=unicodedata.normalize("NFKD",split_camel(v))
    s="".join(c for c in s if not unicodedata.combining(c)).casefold()
    s=re.sub(r"[^a-z0-9]+"," ",s)
    return " ".join(s.split())

ALIASES={
    "leia":"princess leia",
    "luke":"luke skywalker",
    "han solo":"han solo",
    "obi wan":"obi wan kenobi",
    "rose":"rose tico",
    "padme":"padme amidala",
    "anakin":"anakin skywalker",
    "lando":"lando calrissian",
    "rey":"rey",
    "finn":"finn",
    "poe dameron":"poe dameron",
    "palpatine":"palpatine",
    "darth vader":"darth vader",
    "darth maul":"darth maul",
    "boba fett":"boba fett",
    "jango fett":"jango fett",
    "r2d2":"r2 d2",
    "c3po":"c 3po",
    "chewbacca":"chewbacca",
}

def base_key(key):
    return str(key or "").split("_",1)[0]

def alias_label(base):
    n=norm(base)
    return ALIASES.get(n,n)

def physical_support(base,candidates):
    label=alias_label(base)
    lt=[t for t in label.split() if t]
    if not lt:return []
    supported=[]
    for c in candidates or []:
        name=norm(c.get("name"))
        nt=set(name.split())
        if all(t in nt for t in lt):
            supported.append(c)
        elif len(lt)==1 and lt[0] in nt:
            supported.append(c)
    return supported

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    rows=[];levels=Counter();base_counts=Counter()
    for r in load_jsonl(args.candidates):
        key=r.get("character_variant_key")
        base=base_key(key)
        suffix=str(key or "").split("_")[1:]
        top=r.get("top_candidates") or []
        supported=physical_support(base,top)
        label=alias_label(base)
        generic=label in GENERIC or any(t in GENERIC for t in label.split())

        if supported and not generic:
            character_status="physical_character_family_supported"
        elif supported and generic:
            character_status="generic_role_family_supported"
        else:
            character_status="digital_identity_only_no_physical_name_support"

        if len(supported)==1 and float(r.get("top_margin") or 0)>=0.10:
            release_status="unique_physical_release_candidate"
        elif len(supported)>=1:
            release_status="physical_release_ambiguous_within_character_family"
        else:
            release_status="no_supported_physical_release_candidate"

        if suffix:
            version_status="digital_variant_label_present_requires_version_mapping"
        elif release_status=="unique_physical_release_candidate":
            version_status="unsuffixed_identity_unique_release_candidate_version_still_unverified"
        elif supported:
            version_status="unsuffixed_identity_multiple_physical_versions"
        else:
            version_status="digital_version_unresolved"

        levels[character_status]+=1
        levels[release_status]+=1
        levels[version_status]+=1
        base_counts[base]+=1
        rows.append({
          "asset_id":r.get("asset_id"),
          "character_variant_key":key,
          "base_character_key":base,
          "digital_identity_label":label,
          "variant_suffix_tokens":suffix,
          "digital_identity_source":"official_Skywalker_Saga_profile_filename",
          "character_family_status":character_status,
          "physical_release_status":release_status,
          "version_status":version_status,
          "physical_family_support_count":len(supported),
          "supported_physical_candidates":supported,
          "all_top_candidates":top,
          "top_score":r.get("top_score"),
          "top_margin":r.get("top_margin"),
          "policy":"An official filename-derived identity label is valid digital identity evidence. Character-family support does not establish exact outfit/version equivalence. Generic role labels remain role families rather than canonical named characters.",
          "processor_version":VERSION,
        })

    rows.sort(key=lambda x:(
      0 if x["character_family_status"]=="physical_character_family_supported" else
      1 if x["character_family_status"]=="generic_role_family_supported" else 2,
      0 if x["physical_release_status"]=="unique_physical_release_candidate" else 1,
      -(float(x.get("top_score") or 0)),
      x.get("character_variant_key") or ""
    ))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")

    summary={
      "schema":"skywalker-identity-family-summary/v1",
      "processor_version":VERSION,
      "records":len(rows),
      "character_family_status_counts":dict(Counter(r["character_family_status"] for r in rows)),
      "physical_release_status_counts":dict(Counter(r["physical_release_status"] for r in rows)),
      "version_status_counts":dict(Counter(r["version_status"] for r in rows)),
      "digital_variant_suffix_records":sum(bool(r["variant_suffix_tokens"]) for r in rows),
      "base_identity_count":len(base_counts),
      "top_base_identities":[{"base":k,"records":v} for k,v in base_counts.most_common(100)],
      "status":"digital_identity_and_physical_family_layer_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
