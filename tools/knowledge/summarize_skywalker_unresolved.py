#!/usr/bin/env python3
"""Summarize unresolved/version-review Skywalker counterpart records into tractable cohorts."""
from __future__ import annotations
import argparse,json,re
from collections import Counter,defaultdict
from pathlib import Path

VERSION="skywalker-unresolved-diagnostic/v2"

def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def suffix_family(tokens):
    if not tokens:return "no_suffix"
    joined="_".join(tokens).casefold()
    if all(re.fullmatch(r"\d+(?:\.\d+)?",str(t)) for t in tokens):
        return "numeric_suffix"
    if re.search(r"episode|ep\d|chapter|mission",joined):return "episode_or_mission_suffix"
    if re.search(r"old|young|classic|hood|helmet|cape|disguise|outfit|robes|armor|armour|jacket|coat|shirt|dress|uniform|casual",joined):
        return "descriptive_variant_suffix"
    if re.search(r"holiday|christmas|halloween|summer|winter",joined):return "seasonal_variant_suffix"
    return "other_suffix"

SEMANTIC_PATTERNS={
    "episode_or_timeline":r"(?:^|_)(?:ep\d+|episode\d+|flashback|old|young|boy|padawan|jediknight|jedimaster|phase\d+)(?:_|$)",
    "location_or_scene":r"(?:tatooine|hoth|endor|crait|kijimi|ahchto|cloudcity|bespin|geonosis|kashyyyk|jabbaspalace|theed|coruscant|utapau|swamp|starkiller|cantina|skiff)",
    "outfit_or_accessory":r"(?:hood|helmet|cape|nocape|nohelmet|coat|jacket|vest|robe|shirt|dress|uniform|casual|hat|whiteshirt|hoodedcape|reforgedhelmet|silverleg|redarm|redeyes|yelloweyes|darkturquoise|white|black|grey|silver|orange)",
    "rank_or_role":r"(?:commander|cmd|captain|cpt|sergeant|sgt|lieutenant|lt|general|princess|pilot|firstorder|fso|security|heavy|scout|stormtrooper|handmaiden|royalguard|clone)",
    "physical_state":r"(?:burnt|bandaged|rusted|topless|noshell|bacta|pregnant|scar)",
    "story_or_prop_state":r"(?:carbonite|ceremony|training|waiter|bin|yodaonback|friend)",
    "identity_selector":r"(?:fn2187|cardo|kuruk|ushar|vicrul|trudgen|aplek|skywalker)",
}

def semantic_routes(tokens):
    if not tokens:return ["no_suffix"]
    joined="_".join(str(t) for t in tokens).casefold()
    if all(re.fullmatch(r"\d+(?:\.\d+)?",str(t)) for t in tokens):
        return ["opaque_source_code"]
    if all(len(str(t))==1 and str(t).isalnum() for t in tokens):
        return ["opaque_source_code"]
    labels=[name for name,pat in SEMANTIC_PATTERNS.items() if re.search(pat,joined)]
    if not labels:
        if any(str(t).casefold() in {"a","b","c","1","2","5"} for t in tokens):
            labels.append("opaque_source_code")
        else:
            labels.append("other_unclassified")
    return labels

def primary_review_route(tokens):
    labels=semantic_routes(tokens)
    if len(labels)==1:return labels[0]
    return "mixed_semantics"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--records",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    ap.add_argument("--top-output",type=Path,required=True)
    args=ap.parse_args()

    rows=list(load_jsonl(args.records))
    families=Counter()
    suffix_tokens=Counter()
    counterpart=Counter()
    exact=Counter()
    base=Counter()
    score_bands=Counter()
    semantic_counts=Counter()
    review_routes=Counter()
    for r in rows:
        toks=r.get("variant_suffix_tokens") or []
        fam=suffix_family(toks)
        semantics=semantic_routes(toks)
        route=primary_review_route(toks)
        families[fam]+=1
        for label in semantics: semantic_counts[label]+=1
        review_routes[route]+=1
        for t in toks:suffix_tokens[str(t)]+=1
        counterpart[r.get("character_counterpart_status") or "unknown"]+=1
        exact[r.get("exact_version_status") or "unknown"]+=1
        base[r.get("base_character_key") or "unknown"]+=1
        s=float(r.get("top_score") or 0)
        score_bands[
            "0.90+" if s>=.9 else "0.80-0.899" if s>=.8 else "0.70-0.799" if s>=.7 else "0.50-0.699" if s>=.5 else "<0.50"
        ]+=1

    top=sorted(rows,key=lambda r:(-(float(r.get("top_score") or 0)),-(float(r.get("top_margin") or 0)),r.get("character_variant_key") or ""))[:200]
    with args.top_output.open("w",encoding="utf-8") as f:
        for r in top:
            enriched=dict(r)
            toks=r.get("variant_suffix_tokens") or []
            enriched["suffix_semantic_labels"]=semantic_routes(toks)
            enriched["review_route"]=primary_review_route(toks)
            f.write(json.dumps(enriched,ensure_ascii=False)+"\n")

    summary={
      "schema":"skywalker-unresolved-diagnostic-summary/v1",
      "processor_version":VERSION,
      "records":len(rows),
      "counterpart_status_counts":dict(counterpart),
      "exact_version_status_counts":dict(exact),
      "suffix_family_counts":dict(families),
      "suffix_semantic_label_counts":dict(semantic_counts),
      "review_route_counts":dict(review_routes),
      "top_suffix_tokens":[{"token":k,"count":v} for k,v in suffix_tokens.most_common(100)],
      "top_base_character_groups":[{"base_character_key":k,"count":v} for k,v in base.most_common(100)],
      "score_bands":dict(score_bands),
      "top_high_score_records":[{
          "key":r.get("character_variant_key"),
          "base":r.get("base_character_key"),
          "suffix":r.get("variant_suffix_tokens"),
          "score":r.get("top_score"),
          "margin":r.get("top_margin"),
          "counterpart":r.get("character_counterpart_status"),
          "version":r.get("exact_version_status"),
          "top_physical":(r.get("top_physical_candidate") or {}).get("name"),
          "suffix_semantic_labels":semantic_routes(r.get("variant_suffix_tokens") or []),
          "review_route":primary_review_route(r.get("variant_suffix_tokens") or [])
      } for r in top[:100]],
      "status":"unresolved_diagnostic_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:summary[k] for k in ("records","counterpart_status_counts","exact_version_status_counts","suffix_family_counts","suffix_semantic_label_counts","review_route_counts","score_bands","status")},indent=2))
if __name__=="__main__":main()
