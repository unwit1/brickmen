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
from skywalker_identity_keys import parse_identity_key

VERSION="skywalker-physical-crosswalk-candidates/v6"
STOP={
    "lego","star","wars","minifig","minifigure","figure","with","and","the","a","an",
    "episode","ep","new","version","variant","character","profile","icons","icon",
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

def semantic_tokens(value):
    value=camel(unicodedata.normalize("NFKD",str(value or "")))
    value=value.replace("\'","").replace("’","")
    value="".join(ch if ch.isalnum() else " " for ch in value.casefold())
    raw=[t for t in value.split() if t and t not in STOP]
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

def norm(value):
    toks=semantic_tokens(value)
    return " ".join(toks),toks

SCENE_CONTEXT_ALIASES={
    "cantina":[["cantina"],["mos","eisley"]],
    "skiff":[["skiff"]],
    "swamp":[["swamp"],["dagobah"],["yoda","hut"]],
    "tatooine":[["tatooine"],["mos","eisley"],["mos","espa"]],
    "hoth":[["hoth"]],
    "endor":[["endor"]],
    "cloudcity":[["cloud","city"]],
    "bespin":[["bespin"],["cloud","city"]],
    "geonosis":[["geonosis"],["geonosian"]],
    "kashyyyk":[["kashyyyk"]],
    "crait":[["crait"]],
    "kijimi":[["kijimi"]],
    "ahchto":[["ahch","to"],["ahchto"]],
    "jabbaspalace":[["jabba","palace"]],
    "theed":[["theed"]],
    "coruscant":[["coruscant"]],
    "utapau":[["utapau"]],
    "starkiller":[["starkiller"]],
}

def scene_context_terms(key):
    parsed=parse_identity_key(key)
    suffix_compact="".join(semantic_tokens(" ".join(parsed.get("variant_suffix_tokens") or [])))
    found=[]
    for cue,aliases in SCENE_CONTEXT_ALIASES.items():
        if cue in suffix_compact:
            found.append((cue,aliases))
    return found

def set_context_matches(key,occurrences):
    cues=scene_context_terms(key)
    if not cues:return []
    matches=[]
    for occ in occurrences or []:
        set_name=str(occ.get("set_name") or "")
        st=set(semantic_tokens(set_name))
        for cue,aliases in cues:
            for alias in aliases:
                if set(alias).issubset(st):
                    matches.append({
                        "cue":cue,
                        "alias":" ".join(alias),
                        "set_num":occ.get("set_num"),
                        "set_name":set_name,
                        "year":occ.get("year"),
                    })
                    break
    out=[];seen=set()
    for m in matches:
        sig=(m["cue"],m["set_num"],m["alias"])
        if sig not in seen:
            seen.add(sig);out.append(m)
    return out

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

def load_component_summaries(path):
    if not path:return {}
    by_fig={}
    for row in load_jsonl(path):
        fig=str(row.get("fig_num") or "")
        if not fig:continue
        bucket=by_fig.setdefault(fig,{
            "resolved_component_count":0,
            "role_counts":{},
            "accessory_components":[],
        })
        bucket["resolved_component_count"]+=1
        role=str(row.get("component_role") or "other")
        bucket["role_counts"][role]=bucket["role_counts"].get(role,0)+1
        if role in {"headgear","bodywear"}:
            bucket["accessory_components"].append({
                "part_num":row.get("part_num"),
                "part_name":row.get("part_name"),
                "color_name":row.get("color_name"),
                "quantity":row.get("quantity"),
                "is_spare":row.get("is_spare"),
                "component_role":role,
            })
    for bucket in by_fig.values():
        bucket["accessory_components"]=sorted(
            bucket["accessory_components"],
            key=lambda x:(x.get("component_role") or "",x.get("part_name") or "",x.get("part_num") or "")
        )
    return by_fig

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--skywalker-census",type=Path,required=True)
    ap.add_argument("--physical-samples",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    ap.add_argument("--components",type=Path)
    ap.add_argument("--reference-year",type=int,default=2022,
                    help="Reference year for source-plausibility ranking; later releases are retained but receive a bounded penalty.")
    ap.add_argument("--top-k",type=int,default=5)
    args=ap.parse_args()

    census=json.loads(args.skywalker_census.read_text(encoding="utf-8"))
    digital=census.get("records") or []
    physical=[x for x in load_jsonl(args.physical_samples) if is_star_wars(x)]
    component_summaries=load_component_summaries(args.components)
    rows=[];bands=Counter()
    for d in digital:
        key=d.get("character_variant_key") or d.get("filename")
        candidates=[]
        parsed_key=parse_identity_key(key)
        identity_label=parsed_key.get("canonical_identity_label") or parsed_key.get("base_character_key") or key
        for p in physical:
            sc,why=score(key,p.get("name"))
            base_sc,base_why=score(identity_label,p.get("name"))
            context=set_context_matches(key,p.get("set_occurrences"))
            character_gate=(
                float(base_why.get("key_token_coverage") or 0)>=0.80
                and float(base_why.get("core_token_hit") or 0)>=0.50
            )
            context_bonus=0.12 if context and character_gate else 0.0
            years=sorted({
                int(o.get("year")) for o in (p.get("set_occurrences") or [])
                if o.get("year") not in (None,"")
            })
            first_year=years[0] if years else None
            temporal_source_penalty=0.08 if first_year and first_year>args.reference_year else 0.0
            adjusted=round(max(0.0,min(1.0,sc+context_bonus-temporal_source_penalty)),4)
            if adjusted<=0:continue
            why=dict(why)
            why.update({
                "base_identity_label":identity_label,
                "base_identity_score":base_sc,
                "base_identity_token_coverage":base_why.get("key_token_coverage"),
                "scene_context_matches":context,
                "scene_context_character_gate":character_gate,
                "scene_context_bonus":context_bonus,
                "physical_release_years":years,
                "first_physical_release_year":first_year,
                "temporal_source_reference_year":args.reference_year,
                "temporal_source_penalty":temporal_source_penalty,
            })
            candidates.append({
                "fig_num":p.get("fig_num"),
                "name":p.get("name"),
                "score":adjusted,
                "raw_name_score":sc,
                "catalog_image_url":p.get("catalog_image_url"),
                "set_occurrences":p.get("set_occurrences"),
                "component_inventory_summary":component_summaries.get(str(p.get("fig_num") or "")),
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
            "policy":"Do not collapse a digital profile to a physical release without independent identity/version confirmation; unmatched records may be digital-only. Candidate scoring normalizes audited semantic equivalents such as Phase II/Phase2, First Order, common rank abbreviations, and Geonosis/Geonosian. Audited scene/location suffixes may receive a bounded set-occurrence-name bonus only when the physical candidate already passes a character-identity gate. Physical releases whose first known set occurrence is later than the source reference year remain candidates but receive a bounded source-plausibility penalty.",
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
        "component_inventory_summaries_loaded":len(component_summaries),
        "source_plausibility_reference_year":args.reference_year,
        "later_release_candidate_penalty":0.08,
        "status":"candidate_crosswalk_requires_independent_confirmation"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
