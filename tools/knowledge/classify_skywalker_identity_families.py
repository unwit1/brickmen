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
from skywalker_identity_keys import parse_identity_key, specialized_role_match

VERSION="skywalker-identity-family/v6"
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
    "savage oppress":"savage opress",
}

def base_key(key):
    return str(key or "").split("_",1)[0]

def alias_label(base):
    n=norm(base)
    return ALIASES.get(n,n)

def compact(v):
    return re.sub(r"[^a-z0-9]+","",norm(v))

def looks_like_compact_identifier(v):
    s=compact(v)
    return bool(re.search(r"[a-z]",s) and re.search(r"[0-9]",s) and len(s)<=10)

def semantic_variant_tokens(value):
    raw=norm(value).split()
    out=[];i=0
    while i<len(raw):
        t=raw[i]
        nxt=raw[i+1] if i+1<len(raw) else None
        if t=="phase" and nxt in {"i","1","ii","2"}:
            out.append("phase1" if nxt in {"i","1"} else "phase2")
            i+=2;continue
        if t=="first" and nxt=="order":
            out.append("firstorder");i+=2;continue
        if t in {"cmd","cpt","sgt","lt"}:
            out.append({"cmd":"commander","cpt":"captain","sgt":"sergeant","lt":"lieutenant"}[t])
            i+=1;continue
        if t=="fso":
            out.append("firstorder");i+=1;continue
        if t=="geonosian":
            out.append("geonosis");i+=1;continue
        out.append(t);i+=1
    return out

def meaningful_suffix_tokens(key):
    parsed=parse_identity_key(key)
    suffix=parsed["variant_suffix_tokens"]
    if not suffix or all(str(x).isdigit() for x in suffix):
        return []
    return semantic_variant_tokens(" ".join(suffix))

def physical_support(base,candidates):
    label=alias_label(base)
    lt=[t for t in label.split() if t]
    if not lt:return []
    supported=[]
    code_like=looks_like_compact_identifier(base)
    compact_label=compact(label)
    for c in candidates or []:
        raw_name=str(c.get("name") or "")
        name=norm(raw_name)
        ordered=name.split()
        nt=set(ordered)
        if code_like:
            # Avoid droid/code collisions such as 8D8 -> R5-D8. The complete
            # compact identifier must occur in the physical catalog name.
            if compact_label and compact_label in compact(raw_name):
                supported.append(c)
            continue
        if len(lt)==1:
            # One-word identities may have harmless titles/species wrappers
            # (Snoke -> Supreme Leader Snoke, Teebo -> Teebo Ewok), but a token
            # buried inside another entity label (Rancor Battalion) is unsafe.
            if ordered and lt[0] in {ordered[0],ordered[-1]}:
                supported.append(c)
            continue
        if all(t in nt for t in lt):
            supported.append(c)
    return supported

NEGATIVE_SUFFIX_FEATURES={
    "nohelmet":"helmet",
    "nocape":"cape",
    "nohat":"hat",
    "noshell":"shell",
}

def negative_suffix_features(key):
    parsed=parse_identity_key(key)
    compact_suffix="".join(str(x) for x in parsed.get("variant_suffix_tokens") or []).casefold()
    return [feature for marker,feature in NEGATIVE_SUFFIX_FEATURES.items() if marker in compact_suffix]

def constrain_by_suffix(key,supported):
    tokens=meaningful_suffix_tokens(key)
    negative=negative_suffix_features(key)
    if not tokens and not negative:
        return supported,"no_semantic_suffix"
    if negative:
        filtered=[]
        for candidate in supported:
            nt=set(semantic_variant_tokens(candidate.get("name")))
            if not any(feature in nt for feature in negative):
                filtered.append(candidate)
        remaining=[t for t in tokens if t not in {"no",*negative}]
        if remaining:
            positive=[
                candidate for candidate in filtered
                if all(t in set(semantic_variant_tokens(candidate.get("name"))) for t in remaining)
            ]
            if positive:
                return positive,"negative_feature_filtered_plus_catalog_text_match"
        if len(filtered)<len(supported):
            return filtered,"negative_feature_explicit_contradictions_filtered"
        return supported,"negative_feature_unresolved_no_explicit_contradiction"
    constrained=[]
    for candidate in supported:
        nt=set(semantic_variant_tokens(candidate.get("name")))
        if all(t in nt for t in tokens):
            constrained.append(candidate)
    if constrained:
        return constrained,"suffix_catalog_text_match"
    return supported,"suffix_not_resolved_in_supported_candidates"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    rows=[];levels=Counter();base_counts=Counter()
    for r in load_jsonl(args.candidates):
        key=r.get("character_variant_key")
        parsed_key=parse_identity_key(key)
        base=parsed_key["base_character_key"]
        suffix=parsed_key["variant_suffix_tokens"]
        top=r.get("top_candidates") or []
        base_supported=physical_support(base,top)
        supported=base_supported
        specialized=specialized_role_match(key)
        specialized_supported=[]
        if specialized:
            required=set(specialized.get("required_catalog_semantic_tokens") or [])
            for candidate in top:
                catalog_tokens=set(semantic_variant_tokens(candidate.get("name")))
                if required and required.issubset(catalog_tokens):
                    specialized_supported.append(candidate)
        if specialized_supported:
            supported=list(specialized_supported)
            variant_supported=list(specialized_supported)
            suffix_constraint_status="specialized_role_catalog_match"
        else:
            variant_supported,suffix_constraint_status=constrain_by_suffix(key,supported)
        label=norm(parsed_key.get("canonical_identity_label") or alias_label(base))
        generic=label in GENERIC or any(t in GENERIC for t in label.split())

        if supported and not generic:
            character_status="physical_character_family_supported"
        elif supported and generic:
            character_status="generic_role_family_supported"
        else:
            character_status="digital_identity_only_no_physical_name_support"

        semantic_suffix=bool(meaningful_suffix_tokens(key))
        suffix_resolved=suffix_constraint_status in {"suffix_catalog_text_match","specialized_role_catalog_match","negative_feature_filtered_plus_catalog_text_match"}
        release_pool=variant_supported if (semantic_suffix and suffix_resolved) else supported
        negative_state=suffix_constraint_status.startswith("negative_feature_")
        if semantic_suffix and (suffix_constraint_status=="suffix_not_resolved_in_supported_candidates" or negative_state):
            release_status="variant_constrained_physical_release_unresolved"
        elif len(release_pool)==1 and float(r.get("top_margin") or 0)>=0.10:
            release_status="unique_physical_release_candidate"
        elif len(release_pool)>=1:
            release_status="physical_release_ambiguous_within_character_family"
        else:
            release_status="no_supported_physical_release_candidate"

        if suffix and suffix_constraint_status=="specialized_role_catalog_match":
            version_status="digital_specialized_role_matches_catalog_requires_visual_confirmation"
        elif suffix and suffix_constraint_status=="negative_feature_filtered_plus_catalog_text_match":
            version_status="digital_negative_feature_plus_catalog_text_requires_visual_confirmation"
        elif suffix and suffix_constraint_status.startswith("negative_feature_"):
            version_status="digital_negative_feature_requires_visual_mapping"
        elif suffix and suffix_constraint_status=="suffix_catalog_text_match":
            version_status="digital_variant_suffix_matches_catalog_text_requires_visual_confirmation"
        elif suffix:
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
          "identity_key_parse_mode":parsed_key["parse_mode"],
          "identity_key_parse_reason":parsed_key.get("reason"),
          "variant_suffix_tokens":suffix,
          "meaningful_variant_suffix_tokens":meaningful_suffix_tokens(key),
          "negative_variant_features":negative_suffix_features(key),
          "suffix_constraint_status":suffix_constraint_status,
          "digital_identity_source":"official_Skywalker_Saga_profile_filename",
          "character_family_status":character_status,
          "physical_release_status":release_status,
          "version_status":version_status,
          "physical_family_support_count":len(supported),
          "supported_physical_candidates":release_pool,
          "base_character_physical_candidates":base_supported,
          "specialized_role_match":specialized,
          "all_top_candidates":top,
          "top_score":r.get("top_score"),
          "top_margin":r.get("top_margin"),
          "policy":"An official filename-derived identity label is valid digital identity evidence. Full-name identity tokens are resolved before variant parsing. Character-family support does not establish exact outfit/version equivalence. Compact identifiers require full-code agreement; variant matching normalizes audited semantic equivalents such as Phase II/Phase2, First Order, common rank abbreviations, and Geonosis/Geonosian; meaningful digital suffixes constrain physical variants; audited specialized-role mappings may replace a generic base noun; generic role labels remain role families rather than canonical named characters.",
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
      "suffix_constraint_status_counts":dict(Counter(r["suffix_constraint_status"] for r in rows)),
      "base_identity_count":len(base_counts),
      "top_base_identities":[{"base":k,"records":v} for k,v in base_counts.most_common(100)],
      "status":"digital_identity_and_physical_family_layer_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
