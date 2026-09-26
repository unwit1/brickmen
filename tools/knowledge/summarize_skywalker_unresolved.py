#!/usr/bin/env python3
"""Summarize unresolved/version-review Skywalker counterpart records into tractable cohorts."""
from __future__ import annotations
import argparse,json,re
from collections import Counter,defaultdict
from pathlib import Path

VERSION="skywalker-unresolved-diagnostic/v1"

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
    for r in rows:
        toks=r.get("variant_suffix_tokens") or []
        fam=suffix_family(toks)
        families[fam]+=1
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
        for r in top:f.write(json.dumps(r,ensure_ascii=False)+"\n")

    summary={
      "schema":"skywalker-unresolved-diagnostic-summary/v1",
      "processor_version":VERSION,
      "records":len(rows),
      "counterpart_status_counts":dict(counterpart),
      "exact_version_status_counts":dict(exact),
      "suffix_family_counts":dict(families),
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
          "top_physical":(r.get("top_physical_candidate") or {}).get("name")
      } for r in top[:100]],
      "status":"unresolved_diagnostic_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:summary[k] for k in ("records","counterpart_status_counts","exact_version_status_counts","suffix_family_counts","score_bands","status")},indent=2))
if __name__=="__main__":main()
