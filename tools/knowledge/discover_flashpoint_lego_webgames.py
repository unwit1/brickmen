#!/usr/bin/env python3
"""Discover LEGO-related preserved web games in a local Flashpoint installation.

Read-only metadata/indexing tool. It does not download entries, launch games, or modify
Flashpoint. The output is a candidate list; archive presence alone is not proof that LEGO
officially published or commissioned a title.
"""
from __future__ import annotations
import argparse, json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROCESSOR_VERSION="flashpoint-lego-webgame-discovery/v1"

def now_iso(): return datetime.now(timezone.utc).isoformat()
def columns(conn,table): return {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}
def tables(conn): return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
def pick_game_table(conn):
    ts=tables(conn)
    if "game" in ts: return "game"
    candidates=[]
    for table in ts:
        cols=columns(conn,table)
        if {"id","title"}.issubset(cols):
            score=len(cols & {"developer","publisher","source","alternateTitles","series","platform","primaryPlatform"})
            candidates.append((score,table))
    if not candidates: raise RuntimeError("Could not locate a Flashpoint game metadata table.")
    return sorted(candidates,reverse=True)[0][1]
def get(row,name,default=""):
    try: value=row[name]
    except (IndexError,KeyError): return default
    return default if value is None else value

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--flashpoint-root",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--term",action="append",default=["lego"],help="Repeat to add discovery terms")
    args=ap.parse_args()
    root=args.flashpoint_root.resolve()
    db=root/"Data"/"flashpoint.sqlite"
    if not db.is_file(): raise SystemExit(f"Flashpoint database not found: {db}")
    conn=sqlite3.connect(f"file:{db}?mode=ro",uri=True); conn.row_factory=sqlite3.Row
    game_table=pick_game_table(conn); game_cols=columns(conn,game_table)
    wanted=["id","title","alternateTitles","series","developer","publisher","source","platform","primaryPlatform","releaseDate","version","originalDescription","notes","library","activeDataId"]
    selected=[c for c in wanted if c in game_cols]
    sql=f'SELECT {",".join(chr(34)+c+chr(34) for c in selected)} FROM "{game_table}"'
    terms=tuple(dict.fromkeys(t.lower() for t in args.term if t.strip()))
    data_table=next((c for c in ("game_data","gameData","game_data_v2") if c in tables(conn)),None)
    data_by_game={}
    if data_table:
        dcols=columns(conn,data_table)
        game_id_col="gameId" if "gameId" in dcols else "game_id" if "game_id" in dcols else None
        if game_id_col:
            fields=[c for c in ("id",game_id_col,"title","sha256","presentOnDisk","path","size","applicationPath","launchCommand") if c in dcols]
            q=f'SELECT {",".join(chr(34)+c+chr(34) for c in fields)} FROM "{data_table}"'
            for drow in conn.execute(q):
                gid=str(drow[game_id_col]); data_by_game.setdefault(gid,[]).append({c:drow[c] for c in fields})
    candidates=[]
    for row in conn.execute(sql):
        searchable=[str(get(row,c,"")) for c in ("title","alternateTitles","series","developer","publisher","source","originalDescription","notes") if c in selected]
        haystack="\n".join(searchable).lower(); hits=sorted(t for t in terms if t in haystack)
        if not hits: continue
        gid=str(get(row,"id","")); packs=data_by_game.get(gid,[]); local_paths=[]
        for pack in packs:
            if pack.get("path") and pack.get("presentOnDisk"): local_paths.append(str(root/str(pack["path"])))
        default_zip=root/"Data"/"Games"/f"{gid}.zip"
        if default_zip.exists() and str(default_zip) not in local_paths: local_paths.append(str(default_zip))
        record={c:get(row,c,None) for c in selected}
        record.update({"flashpoint_game_id":gid,"discovery_hits":hits,"game_data":packs,"resolved_local_paths":local_paths,"official_lego_verification":"pending","corpus_status":"candidate_only","source_authority":"preservation_archive","processor_version":PROCESSOR_VERSION})
        candidates.append(record)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in sorted(candidates,key=lambda x:(str(x.get("title") or "").lower(),str(x.get("flashpoint_game_id")))): f.write(json.dumps(r,ensure_ascii=False)+"\n")
    report={"schema":"flashpoint-lego-webgame-discovery-report/v1","created_at":now_iso(),"processor_version":PROCESSOR_VERSION,"flashpoint_root":str(root),"database":str(db),"game_table":game_table,"game_data_table":data_table,"terms":terms,"candidate_count":len(candidates),"candidates_with_local_data":sum(bool(r["resolved_local_paths"]) for r in candidates),"output":str(args.output),"warning":"Candidates require independent LEGO/developer provenance verification before official-corpus promotion."}
    args.output.with_suffix(".report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    conn.close(); print(json.dumps(report,indent=2))
if __name__=="__main__": main()
