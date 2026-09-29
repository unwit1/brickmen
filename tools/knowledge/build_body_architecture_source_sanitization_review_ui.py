#!/usr/bin/env python3
"""Build a local reviewer for byte-verified architecture source images.

The generated HTML embeds queue metadata and HTTPS source URLs, not image bytes. Reviews
are hash-pinned to the queue's verified source SHA-256 and export as the canonical review
set format consumed by validate_body_architecture_source_sanitization_reviews.py.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any, Mapping

VERSION = "body-architecture-source-sanitization-review-ui/v1"

PRIMARY_VIEWS = [
    "front",
    "front_3q",
    "side",
    "rear",
    "multi_view_composite",
    "uncertain",
]
ACTIONS = [
    "none",
    "tight_figure_crop",
    "mask_regions",
    "segment_primary_figure",
    "replace_source",
    "manual_composite_cleanup",
]


def _script_json(value: Any) -> str:
    return (
        json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        .replace("</", "<\\/")
        .replace("<!--", "<\\!--")
    )


def build_payload(queue: Mapping[str, Any]) -> dict[str, Any]:
    items = []
    for index, row in enumerate(queue.get("queue") or []):
        source = row.get("source") or {}
        record_id = row.get("source_record_id")
        source_id = source.get("source_id")
        url = source.get("exact_image_url")
        digest = source.get("source_file_sha256")
        if not isinstance(record_id, str) or not record_id:
            raise ValueError(f"queue[{index}] missing source_record_id")
        if not isinstance(source_id, str) or not source_id:
            raise ValueError(f"queue[{index}] missing source.source_id")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ValueError(f"queue[{index}] source URL must be HTTPS")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"queue[{index}] source SHA-256 is required")
        items.append(
            {
                "source_record_id": record_id,
                "source_id": source_id,
                "exact_image_url": url,
                "source_file_sha256": digest,
                "source_width": source.get("source_width"),
                "source_height": source.get("source_height"),
                "case_id": row.get("case_id"),
                "split": row.get("split"),
                "expected": row.get("expected"),
                "source_risk": row.get("source_risk"),
                "risk_reasons": row.get("risk_reasons") or [],
                "required_checks": row.get("required_checks") or [],
                "recommended_actions": row.get("recommended_actions") or [],
            }
        )
    if not items:
        raise ValueError("sanitization queue contains no reviewable items")
    return {
        "schema": "body-architecture-source-sanitization-review-ui-payload/v1",
        "processor_version": VERSION,
        "queue_status": queue.get("status"),
        "candidate_count": len(items),
        "items": items,
        "policy": [
            "Source image bytes are not embedded or copied into the generated reviewer.",
            "Every review is pinned to the queue's byte-verified source SHA-256.",
            "Approve Raw is valid only when identity and figure completeness are true and no text leakage or visual confounders remain.",
            "A changed source hash invalidates the review through the repository validator.",
            "Sanitization-required reviews do not authorize raw model input.",
        ],
    }


def build_review_html(payload: Mapping[str, Any]) -> str:
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("payload requires items")
    embedded = _script_json(payload)
    view_options = "".join(
        f"<option>{html.escape(value)}</option>" for value in PRIMARY_VIEWS
    )
    action_options = "".join(
        f"<option>{html.escape(value)}</option>" for value in ACTIONS
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Brickmen Source Sanitization Review</title>
<style>
:root{{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color-scheme:dark;background:#101114;color:#f1f1f1}}
*{{box-sizing:border-box}}body{{margin:0;background:#101114}}
header{{position:sticky;top:0;z-index:5;display:flex;gap:8px;align-items:center;padding:10px 12px;background:#17191e;border-bottom:1px solid #353840}}
button,input,select,textarea{{font:inherit;color:#eee;background:#22252b;border:1px solid #4a4f58;border-radius:6px;padding:7px}}
button{{cursor:pointer}}button.good{{background:#1f6b43}}button.warn{{background:#6f5720}}.spacer{{flex:1}}
.small{{font-size:11px;color:#aab0ba}}.status{{min-width:190px;text-align:right;font-size:11px;color:#8ee7b1}}
main{{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(380px,.75fr);min-height:calc(100vh - 52px)}}
.visual{{padding:12px;border-right:1px solid #333;overflow:auto}}.panel{{padding:12px;overflow:auto}}
.figure{{background:#17191f;border:1px solid #333;border-radius:8px;overflow:hidden}}
.figure img{{display:block;width:100%;height:min(70vh,760px);object-fit:contain;background:#0b0c0e}}
.caption{{padding:8px;font-size:10px;color:#aab0ba;word-break:break-all}}
.box{{margin:10px 0;padding:10px;background:#17191f;border:1px solid #373b43;border-radius:8px}}
label{{display:block;font-size:11px;color:#bcc1ca;margin:7px 0 4px}}input,select,textarea{{width:100%}}textarea{{min-height:75px;resize:vertical}}
.inline{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}.check{{display:flex;gap:7px;align-items:center;margin:8px 0;font-size:12px}}.check input{{width:auto}}
.warning{{color:#ffd17b}}
@media(max-width:900px){{main{{grid-template-columns:1fr}}.visual{{border-right:0;border-bottom:1px solid #333}}}}
</style>
</head>
<body>
<header>
<button id="prev">← Previous</button><button id="next">Next →</button>
<strong id="counter"></strong><span id="record" class="small"></span>
<span class="spacer"></span>
<button id="save">Save Draft</button>
<button id="approve" class="good">Approve Raw</button>
<button id="sanitize" class="warn">Needs Sanitization</button>
<button id="export">Export Review Set</button>
<span id="status" class="status"></span>
</header>
<main>
<section class="visual">
<div class="figure"><img id="image" alt="Verified source"><div id="url" class="caption"></div></div>
<div class="box small">
<div>Verified source SHA-256: <code id="sha"></code></div>
<div>Dimensions: <span id="dims"></span></div>
<div>Expected architecture: <span id="expected"></span></div>
<div>Risk: <span id="risk"></span></div>
</div>
<div class="box"><strong>Review guidance</strong><pre id="guidance" class="small"></pre></div>
</section>
<section class="panel">
<h2 style="font-size:14px">Reviewer</h2>
<div class="inline">
<div><label>Reviewer ID</label><input id="reviewer-id"></div>
<div><label>Reviewer type</label><select id="reviewer-type"><option>human</option><option>model</option><option>hybrid</option></select></div>
<div><label>Model family / ID</label><input id="model-family"></div>
<div><label>Model revision</label><input id="model-revision"></div>
</div>
<label>Review method</label><input id="review-method" value="direct_visual_inspection_of_verified_exact_image_url">

<h2 style="font-size:14px;margin-top:18px">Source checks</h2>
<label class="check"><input id="identity" type="checkbox"> Identity matches source record</label>
<label class="check"><input id="complete" type="checkbox"> Primary figure is complete</label>
<label>Primary view</label><select id="view">{view_options}</select>

<label>Visible text leakage (one token/description per line)</label>
<textarea id="leakage" placeholder="release_or_sku_code&#10;character_name_or_alias_text"></textarea>
<label>Visual confounders (one per line)</label>
<textarea id="confounders" placeholder="alternate_expression_inset&#10;secondary_figure"></textarea>
<label>Sanitization action</label><select id="action">{action_options}</select>
<label>Review confidence</label><input id="confidence" type="number" min="0" max="1" step=".05" value=".95">
<label>Notes (one per line)</label><textarea id="notes"></textarea>
<p class="small warning">Approving raw is blocked unless identity and completeness are checked, leakage/confounders are empty, and action is “none”. A sanitization-required decision never authorizes the raw image.</p>
</section>
</main>
<script id="payload" type="application/json">{embedded}</script>
<script>
"use strict";
const payload=JSON.parse(document.getElementById("payload").textContent);
const key="brickmen-source-sanitization-review:"+payload.processor_version+":"+payload.items.map(x=>x.source_file_sha256).join(":");
let index=0;
let saved=JSON.parse(localStorage.getItem(key)||"{{}}");
let reviewer=JSON.parse(localStorage.getItem(key+":reviewer")||"null")||{{reviewer_id:"",reviewer_type:"human",model_family:null,model_revision:null,review_method:"direct_visual_inspection_of_verified_exact_image_url"}};
function item(){{return payload.items[index]}}
function lines(v){{return v.split(/\r?\n/).map(x=>x.trim()).filter(Boolean)}}
function setStatus(msg,bad=false){{const el=document.getElementById("status");el.textContent=msg;el.style.color=bad?"#ff9b9b":"#8ee7b1"}}
function defaultReview(x){{return{{source_record_id:x.source_record_id,source_id:x.source_id,source_file_sha256:x.source_file_sha256,status:"sanitization_required",identity_match:true,primary_view:"front",primary_figure_complete:true,visible_text_leakage:[],visual_confounders:[],sanitization_action:"tight_figure_crop",raw_model_input_allowed:false,review_confidence:.95,notes:[]}}}}
function review(){{const x=item();return structuredClone(saved[x.source_record_id]||defaultReview(x))}}
function render(){{
 const x=item(),r=review();
 document.getElementById("counter").textContent=(index+1)+" / "+payload.items.length;
 document.getElementById("record").textContent=x.source_record_id;
 document.getElementById("image").src=x.exact_image_url;
 document.getElementById("url").textContent=x.exact_image_url;
 document.getElementById("sha").textContent=x.source_file_sha256;
 document.getElementById("dims").textContent=(x.source_width||"?")+" × "+(x.source_height||"?");
 document.getElementById("expected").textContent=x.expected?.architecture_id||"unknown";
 document.getElementById("risk").textContent=x.source_risk||"unknown";
 document.getElementById("guidance").textContent=JSON.stringify({{risk_reasons:x.risk_reasons,required_checks:x.required_checks,recommended_actions:x.recommended_actions}},null,2);
 document.getElementById("reviewer-id").value=reviewer.reviewer_id||"";
 document.getElementById("reviewer-type").value=reviewer.reviewer_type||"human";
 document.getElementById("model-family").value=reviewer.model_family||"";
 document.getElementById("model-revision").value=reviewer.model_revision||"";
 document.getElementById("review-method").value=reviewer.review_method||"direct_visual_inspection_of_verified_exact_image_url";
 document.getElementById("identity").checked=r.identity_match===true;
 document.getElementById("complete").checked=r.primary_figure_complete===true;
 document.getElementById("view").value=r.primary_view||"uncertain";
 document.getElementById("leakage").value=(r.visible_text_leakage||[]).join("\n");
 document.getElementById("confounders").value=(r.visual_confounders||[]).join("\n");
 document.getElementById("action").value=r.sanitization_action||"tight_figure_crop";
 document.getElementById("confidence").value=r.review_confidence??.95;
 document.getElementById("notes").value=(r.notes||[]).join("\n");
 setStatus(saved[x.source_record_id]?"saved "+saved[x.source_record_id].status:"unsaved");
}}
function collect(){{
 const x=item(),r=review();
 reviewer={{
  reviewer_id:document.getElementById("reviewer-id").value.trim(),
  reviewer_type:document.getElementById("reviewer-type").value,
  model_family:document.getElementById("model-family").value.trim()||null,
  model_revision:document.getElementById("model-revision").value.trim()||null,
  review_method:document.getElementById("review-method").value.trim()
 }};
 localStorage.setItem(key+":reviewer",JSON.stringify(reviewer));
 r.source_record_id=x.source_record_id;r.source_id=x.source_id;r.source_file_sha256=x.source_file_sha256;
 r.identity_match=document.getElementById("identity").checked;
 r.primary_figure_complete=document.getElementById("complete").checked;
 r.primary_view=document.getElementById("view").value;
 r.visible_text_leakage=lines(document.getElementById("leakage").value);
 r.visual_confounders=lines(document.getElementById("confounders").value);
 r.sanitization_action=document.getElementById("action").value;
 r.review_confidence=Number(document.getElementById("confidence").value);
 r.notes=lines(document.getElementById("notes").value);
 return r;
}}
function save(status){{
 const r=collect();
 if(!reviewer.reviewer_id){{setStatus("Reviewer ID required.",true);return false}}
 if((reviewer.reviewer_type==="model"||reviewer.reviewer_type==="hybrid")&&!reviewer.model_family){{setStatus("Model/hybrid review requires model family or ID.",true);return false}}
 if(!reviewer.review_method){{setStatus("Review method required.",true);return false}}
 if(status==="approved_raw"){{
  if(!r.identity_match||!r.primary_figure_complete||r.visible_text_leakage.length||r.visual_confounders.length||r.sanitization_action!=="none"){{setStatus("Raw approval checks not satisfied.",true);return false}}
  r.raw_model_input_allowed=true;
 }}else if(status==="sanitization_required"){{
  if(r.sanitization_action==="none"){{setStatus("Choose a sanitization action.",true);return false}}
  r.raw_model_input_allowed=false;
 }}
 r.status=status||r.status;
 saved[r.source_record_id]=r;
 localStorage.setItem(key,JSON.stringify(saved));
 setStatus("saved "+r.status);return true;
}}
function exportSet(){{
 collect();
 if(!reviewer.reviewer_id){{setStatus("Reviewer ID required before export.",true);return}}
 const rows=payload.items.map(x=>saved[x.source_record_id]).filter(Boolean);
 const doc={{schema:"body-architecture-source-sanitization-review-set/v1",created:new Date().toISOString(),review_set_id:"source-sanitization-"+Date.now(),policy:"Reviews are keyed to verified source SHA-256. A changed source hash invalidates approval.",reviewer,reviews:rows}};
 const blob=new Blob([JSON.stringify(doc,null,2)+"\n"],{{type:"application/json"}});
 const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="body-architecture-source-sanitization-reviews.json";a.click();URL.revokeObjectURL(url);setStatus("exported "+rows.length+" reviews");
}}
document.getElementById("prev").onclick=()=>{{index=(index-1+payload.items.length)%payload.items.length;render()}};
document.getElementById("next").onclick=()=>{{index=(index+1)%payload.items.length;render()}};
document.getElementById("save").onclick=()=>save(review().status);
document.getElementById("approve").onclick=()=>save("approved_raw");
document.getElementById("sanitize").onclick=()=>save("sanitization_required");
document.getElementById("export").onclick=exportSet;
render();
</script>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    payload = build_payload(queue)
    output = build_review_html(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(
        json.dumps(
            {
                "processor_version": VERSION,
                "candidate_count": payload["candidate_count"],
                "output": str(args.output),
                "policy": "metadata and verified source URLs only; no source bytes embedded",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
