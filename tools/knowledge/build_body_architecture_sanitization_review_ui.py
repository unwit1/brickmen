#!/usr/bin/env python3
"""Build a local-only visual reviewer for sanitized architecture benchmark candidates.

The generated HTML embeds metadata and source URLs only. Sanitized derivative bytes are
never embedded or copied. The reviewer selects locally generated PNGs; the browser
computes SHA-256 and refuses approval unless the file exactly matches the candidate hash.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any, Mapping

VERSION = "body-architecture-sanitization-review-ui/v1"
CANDIDATE_SCHEMA_VERSION = "0.1"

CHECKS = [
    ("identity_preserved", "Identity preserved"),
    ("primary_figure_complete", "Primary figure complete"),
    ("forbidden_text_absent", "Forbidden text / branding absent"),
    ("task_confounders_absent", "Task-confounding panels / extra figures absent"),
    ("architecture_evidence_preserved", "Architecture evidence preserved"),
    ("no_material_transform_artifacts", "No material transform artifacts"),
]


def _script_json(value: Any) -> str:
    return (
        json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        .replace("</", "<\\/")
        .replace("<!--", "<\\!--")
    )


def build_payload(
    candidates: Mapping[str, Any],
    queue: Mapping[str, Any],
) -> dict[str, Any]:
    queue_by_id = {
        row["source_record_id"]: row
        for row in queue.get("queue", [])
    }
    items = []
    for candidate in candidates.get("records", []):
        record_id = candidate["source_record_id"]
        queue_row = queue_by_id.get(record_id)
        if not queue_row:
            raise ValueError(f"candidate missing queue record: {record_id}")
        if queue_row.get("status") != "sanitization_required":
            raise ValueError(
                f"candidate queue status must be sanitization_required: {record_id}"
            )
        source = queue_row.get("source") or {}
        if source.get("source_file_sha256") != candidate.get("source_file_sha256"):
            raise ValueError(f"candidate source hash mismatch: {record_id}")
        expected_filename = (
            f"{record_id}--"
            f"{str(candidate['sanitized_pixel_sha256'])[:16]}.png"
        )
        items.append(
            {
                "source_record_id": record_id,
                "case_id": candidate.get("case_id"),
                "split": candidate.get("split"),
                "source_id": candidate.get("source_id"),
                "source_url": source.get("exact_image_url"),
                "source_file_sha256": candidate.get("source_file_sha256"),
                "source_dimensions": candidate.get("source_dimensions"),
                "output_dimensions": candidate.get("output_dimensions"),
                "sanitized_pixel_sha256": candidate.get(
                    "sanitized_pixel_sha256"
                ),
                "sanitized_png_sha256": candidate.get("sanitized_png_sha256"),
                "expected_derivative_filename": expected_filename,
                "operations": candidate.get("operations") or [],
                "review_context": {
                    "visible_text_leakage": (
                        queue_row.get("review") or {}
                    ).get("visible_text_leakage") or [],
                    "visual_confounders": (
                        queue_row.get("review") or {}
                    ).get("visual_confounders") or [],
                    "sanitization_action": (
                        queue_row.get("review") or {}
                    ).get("sanitization_action"),
                    "notes": (queue_row.get("review") or {}).get("notes") or [],
                },
            }
        )

    items.sort(key=lambda row: str(row["source_record_id"]))
    return {
        "schema": "body-architecture-sanitization-review-ui-payload/v1",
        "processor_version": VERSION,
        "candidate_count": len(items),
        "items": items,
        "policy": [
            "Derivative bytes stay local and are never embedded in this HTML.",
            "Approval is disabled until the selected local PNG SHA-256 exactly matches the generated candidate.",
            "All visual checks must be true for an approved review.",
            "Rejected/revise reviews remain useful failure evidence but never authorize model input.",
        ],
    }


def validate_payload(payload: Mapping[str, Any]) -> None:
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("payload must contain candidate items")
    if payload.get("candidate_count") != len(items):
        raise ValueError("candidate_count mismatch")
    seen = set()
    for index, item in enumerate(items):
        record_id = item.get("source_record_id")
        if not isinstance(record_id, str) or not record_id:
            raise ValueError(f"items[{index}] missing source_record_id")
        if record_id in seen:
            raise ValueError(f"duplicate candidate: {record_id}")
        seen.add(record_id)
        if not str(item.get("source_url") or "").startswith("https://"):
            raise ValueError(f"items[{index}] source_url must be https")
        for key in (
            "source_file_sha256",
            "sanitized_pixel_sha256",
            "sanitized_png_sha256",
        ):
            value = str(item.get(key) or "")
            if len(value) != 64:
                raise ValueError(f"items[{index}].{key} must be SHA-256")
        expected = (
            f"{record_id}--"
            f"{str(item['sanitized_pixel_sha256'])[:16]}.png"
        )
        if item.get("expected_derivative_filename") != expected:
            raise ValueError(f"items[{index}] derivative filename mismatch")


def build_review_html(payload: Mapping[str, Any]) -> str:
    validate_payload(payload)
    embedded = _script_json(payload)
    check_html = "".join(
        f'<label class="check"><input type="checkbox" data-check="{html.escape(key)}"> {html.escape(label)}</label>'
        for key, label in CHECKS
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Brickmen Architecture Sanitization Review</title>
<style>
:root{{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color-scheme:dark;background:#101114;color:#f2f2f2}}
*{{box-sizing:border-box}} body{{margin:0;background:#101114}}
header{{position:sticky;top:0;z-index:4;display:flex;gap:9px;align-items:center;padding:10px 12px;background:#17191f;border-bottom:1px solid #333}}
button,input,select,textarea{{font:inherit;color:#eee;background:#22252c;border:1px solid #4a4f5a;border-radius:6px;padding:7px}}
button{{cursor:pointer}} button.good{{background:#1f6b43}} button.bad{{background:#7a302e}} button.warn{{background:#725b22}}
.spacer{{flex:1}} .small{{font-size:11px;color:#aab0bb}} .status{{min-width:210px;text-align:right;font-size:11px;color:#9dddb7}}
main{{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(370px,.7fr);min-height:calc(100vh - 54px)}}
.visual{{padding:12px;border-right:1px solid #333;overflow:auto}} .panel{{padding:12px;overflow:auto}}
.images{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.figure{{background:#17191f;border:1px solid #333;border-radius:8px;overflow:hidden}}
.figure h2{{font-size:12px;margin:0;padding:8px 10px;border-bottom:1px solid #333}}
.figure img{{display:block;width:100%;height:min(62vh,680px);object-fit:contain;background:#0b0c0f}}
.caption{{font-size:10px;color:#aab0bb;padding:7px;word-break:break-all}}
.box{{margin:10px 0;padding:10px;border:1px solid #383c45;border-radius:8px;background:#17191f}}
.check{{display:block;padding:5px 0;font-size:12px}} label{{font-size:11px;color:#bbc1cb;display:block;margin:7px 0 4px}}
textarea{{width:100%;min-height:80px;resize:vertical}} .hash-ok{{color:#8ee7b1}} .hash-bad{{color:#ff9b9b}}
@media(max-width:980px){{main{{grid-template-columns:1fr}}.visual{{border-right:0;border-bottom:1px solid #333}}}}
</style>
</head>
<body>
<header>
<button id="prev">← Previous</button><button id="next">Next →</button>
<strong id="counter"></strong><span id="record" class="small"></span>
<span class="spacer"></span>
<label style="margin:0">Load derivatives <input id="files" type="file" accept="image/png" multiple style="width:240px"></label>
<button id="save">Save</button><button id="approve" class="good">Approve</button>
<button id="revise" class="warn">Revise</button><button id="reject" class="bad">Reject</button>
<button id="export">Export JSONL</button><span id="status" class="status"></span>
</header>
<main>
<section class="visual">
<div class="images">
<div class="figure"><h2>Verified source reference</h2><img id="source-img"><div id="source-caption" class="caption"></div></div>
<div class="figure"><h2>Local sanitized derivative</h2><img id="derived-img"><div id="derived-caption" class="caption">Load matching local PNG.</div></div>
</div>
<div class="box"><strong>Original review context</strong><div id="context" class="small"></div></div>
<div class="box"><strong>Transform operations</strong><pre id="ops" class="small"></pre></div>
</section>
<section class="panel">
<h2 style="font-size:14px">Hash verification</h2>
<div class="box small">
<div>Expected file: <code id="expected-file"></code></div>
<div>Expected PNG SHA-256: <code id="expected-hash"></code></div>
<div>Observed PNG SHA-256: <code id="observed-hash">not loaded</code></div>
<div id="hash-status">Derivative not verified.</div>
</div>
<h2 style="font-size:14px">Required visual checks</h2>
<div class="box">{check_html}</div>
<label>Reviewer ID</label><input id="reviewer-id" style="width:100%">
<label>Reviewer type</label><select id="reviewer-type" style="width:100%"><option>human</option><option>model</option><option>hybrid</option></select>
<label>Model ID (required for model/hybrid)</label><input id="model-id" style="width:100%">
<label>Model revision (required for model/hybrid)</label><input id="model-revision" style="width:100%">
<label>Review confidence</label><input id="confidence" type="number" min="0" max="1" step=".05" value=".95" style="width:100%">
<label>Notes (one per line; required for reject/revise)</label><textarea id="notes"></textarea>
<p class="small">Approval is metadata only. The exact reviewed source and derivative hashes are preserved; no image bytes are exported.</p>
</section>
</main>
<script id="payload" type="application/json">{embedded}</script>
<script>
"use strict";
const payload=JSON.parse(document.getElementById("payload").textContent);
const storageKey="brickmen-architecture-sanitization-review:"+payload.processor_version;
let index=0;
let saved=JSON.parse(localStorage.getItem(storageKey)||"{{}}");
const loaded={{}};
function current(){{return payload.items[index]}}
function lines(v){{return v.split(/\r?\n/).map(x=>x.trim()).filter(Boolean)}}
function hex(bytes){{return [...new Uint8Array(bytes)].map(b=>b.toString(16).padStart(2,"0")).join("")}}
async function sha256(file){{return hex(await crypto.subtle.digest("SHA-256",await file.arrayBuffer()))}}
function setStatus(msg,bad=false){{const e=document.getElementById("status");e.textContent=msg;e.style.color=bad?"#ff9b9b":"#8ee7b1"}}
function expectedFilename(item){{return item.expected_derivative_filename}}
async function ingestFiles(files){{
 for(const file of files){{
   const match=payload.items.find(x=>expectedFilename(x)===file.name);
   if(!match) continue;
   const digest=await sha256(file);
   loaded[match.source_record_id]={{file,digest,url:URL.createObjectURL(file)}};
 }}
 render();
}}
function recordTemplate(item){{
 return {{
   schema:"body-architecture-sanitized-asset-review/v1",
   source_record_id:item.source_record_id,
   source_file_sha256:item.source_file_sha256,
   sanitized_pixel_sha256:item.sanitized_pixel_sha256,
   sanitized_png_sha256:item.sanitized_png_sha256,
   decision:"revise",
   checks:Object.fromEntries({json.dumps([key for key,_ in CHECKS])}.map(x=>[x,false])),
   reviewer:{{reviewer_id:"",reviewer_type:"human",model_id:null,model_revision:null}},
   review_confidence:.95,notes:[],reviewed_at:null,
   provenance:[{{source:"local_sanitization_review_ui",processor_version:payload.processor_version}}]
 }};
}}
function getRecord(item){{return structuredClone(saved[item.source_record_id]||recordTemplate(item))}}
function render(){{
 const item=current(), rec=getRecord(item), local=loaded[item.source_record_id];
 document.getElementById("counter").textContent=(index+1)+" / "+payload.items.length;
 document.getElementById("record").textContent=item.source_record_id;
 document.getElementById("source-img").src=item.source_url;
 document.getElementById("source-caption").textContent=item.source_url;
 document.getElementById("expected-file").textContent=expectedFilename(item);
 document.getElementById("expected-hash").textContent=item.sanitized_png_sha256;
 document.getElementById("ops").textContent=JSON.stringify(item.operations,null,2);
 document.getElementById("context").textContent=JSON.stringify(item.review_context);
 const d=document.getElementById("derived-img"),cap=document.getElementById("derived-caption");
 const obs=document.getElementById("observed-hash"),hs=document.getElementById("hash-status");
 if(local){{
   d.src=local.url;cap.textContent=local.file.name;obs.textContent=local.digest;
   const ok=local.digest===item.sanitized_png_sha256;
   hs.textContent=ok?"Exact derivative hash verified.":"WRONG FILE OR STALE DERIVATIVE.";
   hs.className=ok?"hash-ok":"hash-bad";
 }}else{{d.removeAttribute("src");cap.textContent="Load "+expectedFilename(item);obs.textContent="not loaded";hs.textContent="Derivative not verified.";hs.className="";}}
 document.querySelectorAll("[data-check]").forEach(e=>e.checked=rec.checks[e.dataset.check]===true);
 document.getElementById("reviewer-id").value=rec.reviewer.reviewer_id||"";
 document.getElementById("reviewer-type").value=rec.reviewer.reviewer_type||"human";
 document.getElementById("model-id").value=rec.reviewer.model_id||"";
 document.getElementById("model-revision").value=rec.reviewer.model_revision||"";
 document.getElementById("confidence").value=rec.review_confidence??.95;
 document.getElementById("notes").value=(rec.notes||[]).join("\n");
 setStatus(saved[item.source_record_id]?"saved "+saved[item.source_record_id].decision:"unsaved");
}}
function collect(decision){{
 const item=current(), rec=getRecord(item);
 rec.decision=decision||rec.decision;
 document.querySelectorAll("[data-check]").forEach(e=>rec.checks[e.dataset.check]=e.checked);
 rec.reviewer={{
  reviewer_id:document.getElementById("reviewer-id").value.trim(),
  reviewer_type:document.getElementById("reviewer-type").value,
  model_id:document.getElementById("model-id").value.trim()||null,
  model_revision:document.getElementById("model-revision").value.trim()||null
 }};
 rec.review_confidence=Number(document.getElementById("confidence").value);
 rec.notes=lines(document.getElementById("notes").value);
 rec.reviewed_at=new Date().toISOString();
 return rec;
}}
function saveDecision(decision){{
 const item=current(), local=loaded[item.source_record_id], rec=collect(decision);
 if(!rec.reviewer.reviewer_id){{setStatus("Reviewer ID required.",true);return false}}
 if((rec.reviewer.reviewer_type==="model"||rec.reviewer.reviewer_type==="hybrid")&&(!rec.reviewer.model_id||!rec.reviewer.model_revision)){{setStatus("Model ID/revision required.",true);return false}}
 if(decision==="approved"){{
   if(!local||local.digest!==item.sanitized_png_sha256){{setStatus("Exact derivative hash must be verified first.",true);return false}}
   if(!Object.values(rec.checks).every(Boolean)){{setStatus("All visual checks must pass for approval.",true);return false}}
 }}else if((decision==="rejected"||decision==="revise")&&rec.notes.length===0){{setStatus("Reject/revise requires notes.",true);return false}}
 saved[item.source_record_id]=rec;localStorage.setItem(storageKey,JSON.stringify(saved));setStatus("saved "+decision);return true;
}}
function exportRows(){{
 const rows=payload.items.map(x=>saved[x.source_record_id]).filter(Boolean);
 const blob=new Blob([rows.map(x=>JSON.stringify(x)).join("\n")+"\n"],{{type:"application/x-ndjson"}});
 const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="body-architecture-sanitization-reviews.jsonl";a.click();URL.revokeObjectURL(url);setStatus("exported "+rows.length+" review records");
}}
document.getElementById("files").onchange=e=>ingestFiles(e.target.files);
document.getElementById("prev").onclick=()=>{{index=(index-1+payload.items.length)%payload.items.length;render()}};
document.getElementById("next").onclick=()=>{{index=(index+1)%payload.items.length;render()}};
document.getElementById("save").onclick=()=>saveDecision(getRecord(current()).decision||"revise");
document.getElementById("approve").onclick=()=>saveDecision("approved");
document.getElementById("revise").onclick=()=>saveDecision("revise");
document.getElementById("reject").onclick=()=>saveDecision("rejected");
document.getElementById("export").onclick=exportRows;
render();
</script>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    payload = build_payload(candidates, queue)
    output = build_review_html(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(
        json.dumps(
            {
                "processor_version": VERSION,
                "candidate_count": payload["candidate_count"],
                "output": str(args.output),
                "policy": "metadata/source URLs only; derivative bytes remain local",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
