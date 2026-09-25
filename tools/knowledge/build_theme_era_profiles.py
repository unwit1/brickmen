#!/usr/bin/env python3
"""Build quantitative era/theme baselines from the Rebrickable physical census.

These aggregates describe catalog/component distributions, not aesthetic quality.
They are intended to ground theme-profile retrieval with measured evidence.
"""
from __future__ import annotations
import argparse,json,statistics
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

VERSION="minifigure-theme-era-profile/v1"

def now_iso(): return datetime.now(timezone.utc).isoformat()
def load_jsonl(path):
    with Path(path).open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

def era(year):
    if not year: return "unknown"
    y=int(year)
    if y<=1988:return "1978-1988"
    if y<=1998:return "1989-1998"
    if y<=2009:return "1999-2009"
    if y<=2019:return "2010-2019"
    return "2020-present"

def top_theme(occ):
    path=occ.get("theme_path") or []
    if not path: return "unknown"
    # theme_path is leaf -> ancestors; take highest named ancestor.
    return (path[-1].get("name") or "unknown").strip() or "unknown"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--samples",type=Path,required=True)
    ap.add_argument("--components",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()

    samples=list(load_jsonl(args.samples))
    comps_by_fig=defaultdict(list)
    for c in load_jsonl(args.components):
        comps_by_fig[c.get("fig_num")].append(c)

    groups=defaultdict(list)
    era_groups=defaultdict(list)
    for s in samples:
        occs=s.get("set_occurrences") or []
        themes=sorted({top_theme(o) for o in occs}) or ["unknown"]
        years=[o.get("year") for o in occs if o.get("year")]
        first=min(years) if years else None
        for t in themes: groups[t].append((s,first))
        era_groups[era(first)].append((s,first))

    def profile(name,kind,items):
        figs={s.get("fig_num"):s for s,_ in items}
        year_by_fig={}
        for sample,yr in items:
            if yr:
                key=sample.get("fig_num")
                prev=year_by_fig.get(key)
                year_by_fig[key]=min(prev, int(yr)) if prev else int(yr)
        role=Counter(); printed=Counter(); colors=Counter(); printed_colors=Counter()
        part_counts=[]; printed_per=[]; headgear_figs=bodywear_figs=weapon_figs=0
        years=[]
        for fig_num,s in figs.items():
            if s.get("num_parts") is not None: part_counts.append(int(s.get("num_parts") or 0))
            seen_roles=set(); pcount=0
            for c in comps_by_fig.get(fig_num,[]):
                r=c.get("component_role") or "unknown"
                role[r]+=1; seen_roles.add(r)
                color=c.get("color_name")
                if color: colors[color]+=1
                if c.get("print_of"):
                    printed[r]+=1; pcount+=1
                    if color: printed_colors[color]+=1
            printed_per.append(pcount)
            headgear_figs += int("headgear" in seen_roles)
            bodywear_figs += int("bodywear" in seen_roles)
            weapon_figs += int("weapon_or_tool" in seen_roles)
            yr=year_by_fig.get(fig_num)
            if yr: years.append(yr)
        n=max(1,len(figs))
        return {
            "profile_id":f"{kind}:{name}",
            "profile_kind":kind,
            "name":name,
            "figure_count":len(figs),
            "observed_year_min":min(years) if years else None,
            "observed_year_max":max(years) if years else None,
            "mean_declared_parts":round(statistics.mean(part_counts),3) if part_counts else None,
            "median_declared_parts":statistics.median(part_counts) if part_counts else None,
            "mean_printed_components":round(statistics.mean(printed_per),3) if printed_per else 0,
            "headgear_figure_fraction":round(headgear_figs/n,4),
            "bodywear_figure_fraction":round(bodywear_figs/n,4),
            "weapon_or_tool_figure_fraction":round(weapon_figs/n,4),
            "component_role_counts":dict(role.most_common()),
            "printed_component_role_counts":dict(printed.most_common()),
            "top_component_colors":[{"color":k,"count":v} for k,v in colors.most_common(20)],
            "top_printed_component_colors":[{"color":k,"count":v} for k,v in printed_colors.most_common(20)],
            "processor_version":VERSION,
            "interpretation_policy":"Catalog/component distribution baseline only; do not infer subjective style quality from frequency alone."
        }

    rows=[]
    for name,items in sorted(groups.items(),key=lambda kv:(-len({s.get("fig_num") for s,_ in kv[1]}),kv[0])):
        rows.append(profile(name,"top_level_theme",items))
    for name,items in sorted(era_groups.items()):
        rows.append(profile(name,"era",items))

    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary={
        "schema":"minifigure-theme-era-profile-summary/v1",
        "created_at":now_iso(),
        "processor_version":VERSION,
        "physical_samples":len(samples),
        "top_level_theme_profiles":len(groups),
        "era_profiles":len(era_groups),
        "profile_records":len(rows),
        "largest_theme_profiles":[{"name":r["name"],"figure_count":r["figure_count"]} for r in rows if r["profile_kind"]=="top_level_theme"][:20],
        "status":"aggregate_profiles_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
