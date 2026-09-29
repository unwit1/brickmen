#!/usr/bin/env python3
"""Build a standalone reviewer for Fortnite -> LEGO semantic translation batches.

The generated HTML embeds only batch metadata and image URLs. It does not copy source
images. Review progress stays in the browser's localStorage until the reviewer exports
JSONL. Exported records are intended for validate_fortnite_semantic_reviews.py.

Measurement signals are shown as review-priority hints only and are never prefilled as
semantic labels.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any, Mapping

BATCH_SCHEMA = "fortnite-semantic-review-work-batch/v1"
VERSION = "fortnite-semantic-review-ui/v1"


def _script_json(value: Any) -> str:
    return (
        json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        .replace("</", "<\\/")
        .replace("<!--", "<\\!--")
    )


def validate_batch(batch: Mapping[str, Any]) -> None:
    if batch.get("schema") != BATCH_SCHEMA:
        raise ValueError(f"batch schema must be {BATCH_SCHEMA!r}")
    items = batch.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("review batch must contain at least one item")
    if batch.get("selected_records") != len(items):
        raise ValueError("selected_records must match items length")
    for index, item in enumerate(items):
        pair_id = item.get("translation_pair_id")
        if not isinstance(pair_id, str) or not pair_id:
            raise ValueError(f"items[{index}] requires translation_pair_id")
        for key in ("source_image_url", "lego_image_url"):
            value = item.get(key)
            if not isinstance(value, str) or not value.startswith("https://"):
                raise ValueError(f"items[{index}].{key} must be an https URL")
        template = item.get("review_template")
        if not isinstance(template, dict):
            raise ValueError(f"items[{index}] requires review_template")
        if template.get("translation_pair_id") != pair_id:
            raise ValueError(
                f"items[{index}] review_template translation_pair_id mismatch"
            )
        evidence = template.get("evidence") or {}
        if evidence.get("claims_unobserved_surfaces") is not False:
            raise ValueError(
                f"items[{index}] must forbid claims_unobserved_surfaces"
            )


def build_review_html(batch: Mapping[str, Any]) -> str:
    validate_batch(batch)
    embedded = _script_json(batch)
    title = html.escape(str(batch.get("batch_id") or "Fortnite semantic review"))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Brickmen Semantic Review — {title}</title>
<style>
:root{{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color-scheme:dark;background:#101114;color:#f2f2f2}}
*{{box-sizing:border-box}}
body{{margin:0;min-height:100vh;display:grid;grid-template-rows:auto 1fr;background:#101114}}
header{{display:flex;gap:12px;align-items:center;padding:10px 14px;border-bottom:1px solid #30333a;background:#16181d;position:sticky;top:0;z-index:5}}
header strong{{font-size:14px}} header .spacer{{flex:1}}
button,input,select,textarea{{font:inherit;color:#eee;background:#20232a;border:1px solid #4b505a;border-radius:6px;padding:7px}}
button{{cursor:pointer}} button.primary{{background:#2746b9}} button.good{{background:#1f6b43}}
main{{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(360px,.75fr);min-height:0}}
.visual{{padding:12px;overflow:auto;border-right:1px solid #30333a}}
.images{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.figure{{background:#17191f;border:1px solid #30333a;border-radius:8px;overflow:hidden}}
.figure h2{{font-size:12px;margin:0;padding:8px 10px;border-bottom:1px solid #30333a}}
.figure img{{display:block;width:100%;height:min(56vh,620px);object-fit:contain;background:#0c0d10}}
.caption{{padding:7px 10px;font-size:11px;color:#aeb4bf;word-break:break-all}}
.signals{{margin-top:10px;padding:10px;background:#17191f;border:1px solid #30333a;border-radius:8px}}
.signals h2,.panel h2{{font-size:13px;margin:0 0 8px}}
.signal{{display:inline-block;margin:2px;padding:4px 7px;border:1px solid #4a4f5a;border-radius:999px;font-size:10px;color:#c9ced8}}
.panel{{padding:12px;overflow:auto;background:#13151a}}
.meta{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
label{{display:block;font-size:11px;color:#b9bec8;margin:7px 0 4px}}
textarea{{width:100%;min-height:66px;resize:vertical}} input,select{{width:100%}}
.region{{margin:12px 0;padding:10px;border:1px solid #373b44;border-radius:8px;background:#181a20}}
.region h3{{font-size:12px;margin:0 0 7px;text-transform:capitalize}}
.annotation{{display:grid;grid-template-columns:1.3fr 1fr .65fr 1fr auto;gap:6px;align-items:end;margin:6px 0}}
.annotation button{{width:auto;padding:7px 9px}}
.small{{font-size:11px;color:#9ea5b1;line-height:1.4}}
.warning{{color:#ffd27a}}
.goodtext{{color:#8ee7b1}}
.status{{font-size:11px;min-width:180px;text-align:right;color:#9ea5b1}}
hr{{border:0;border-top:1px solid #30333a;margin:14px 0}}
@media(max-width:980px){{main{{grid-template-columns:1fr}}.visual{{border-right:0;border-bottom:1px solid #30333a}}.annotation{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<header>
  <button id="prev">← Previous</button>
  <button id="next">Next →</button>
  <strong id="counter"></strong>
  <span id="pair-id" class="small"></span>
  <span class="spacer"></span>
  <button id="save">Save draft</button>
  <button id="submit" class="good">Mark submitted</button>
  <button id="export" class="primary">Export JSONL</button>
  <span id="status" class="status"></span>
</header>
<main>
<section class="visual">
  <div class="images">
    <div class="figure">
      <h2>Source appearance</h2>
      <img id="source-image" alt="Source appearance">
      <div id="source-url" class="caption"></div>
    </div>
    <div class="figure">
      <h2>LEGO translation</h2>
      <img id="lego-image" alt="LEGO translation">
      <div id="lego-url" class="caption"></div>
    </div>
  </div>
  <div class="signals">
    <h2>Measurement signals — prioritization only</h2>
    <div id="signals"></div>
    <p class="small warning">These signals may tell you where to look. They are not semantic labels and must not be copied into preserve/simplify/omit decisions without direct visual evidence.</p>
  </div>
</section>
<section class="panel">
  <h2>Review metadata</h2>
  <div class="meta">
    <div><label>Reviewer ID</label><input id="reviewer-id"></div>
    <div><label>Reviewer type</label><select id="reviewer-type"><option>human</option><option>model</option><option>hybrid</option></select></div>
    <div><label>Model ID (model/hybrid)</label><input id="model-id"></div>
    <div><label>Model revision</label><input id="model-revision"></div>
    <div><label>Evidence scope</label><select id="evidence-scope"><option>front_pair</option><option>wide_pair</option><option>front_and_wide</option><option>multi_view</option><option>mixed</option><option>unknown</option></select></div>
    <div><label>Review role</label><input id="review-role" readonly></div>
  </div>
  <p class="small">Unobserved/rear surfaces are never claimable from this front/wide pair. Add a limitation instead of guessing.</p>

  <div id="regions"></div>

  <label>Identity-critical features (one per line)</label>
  <textarea id="identity-features"></textarea>
  <label>Mask/headgear route</label>
  <input id="mask-route" placeholder="optional; use only if visible/evidenced">
  <label>Expression translation</label>
  <input id="expression" placeholder="optional; front-visible evidence only">
  <label>Limitations (one per line)</label>
  <textarea id="limitations" placeholder="e.g. front/wide evidence only; rear treatment unknown"></textarea>
  <label>Adjudicates review IDs (one per line; adjudicator mode only)</label>
  <textarea id="adjudicates"></textarea>
  <hr>
  <p class="small">Saving keeps a draft in localStorage. “Mark submitted” timestamps this record but does not make it canonical. Canonical training supervision still requires the repository adjudication/promotion gates.</p>
</section>
</main>
<script id="batch-data" type="application/json">{embedded}</script>
<script>
"use strict";
const batch = JSON.parse(document.getElementById("batch-data").textContent);
const decisions = ["preserved","simplified","omitted","exaggerated","moved_to_mould","moved_to_accessory","moved_to_cloth","color_block_changed","not_applicable","uncertain"];
const bases = ["observed_in_both","source_only","lego_only","multi_view","metadata_only","uncertain"];
const regionNames = ["head","torso","lower_body","accessory_or_silhouette"];
const storageKey = "brickmen-semantic-review:" + batch.batch_id;
let index = 0;
let saved = JSON.parse(localStorage.getItem(storageKey) || "{{}}");

function lines(value){{return value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean)}}
function status(msg,bad=false){{const el=document.getElementById("status");el.textContent=msg;el.style.color=bad?"#ff9b9b":"#8ee7b1"}}
function currentItem(){{return batch.items[index]}}
function defaultRecord(){{
  const t=structuredClone(currentItem().review_template);
  t.review_id=null;
  return t;
}}
function currentRecord(){{
  const id=currentItem().translation_pair_id;
  return saved[id] ? structuredClone(saved[id]) : defaultRecord();
}}
function selectHtml(values,selected){{
  return values.map(v=>'<option value="'+v+'"'+(v===selected?' selected':'')+'>'+v+'</option>').join("");
}}
function annotationRow(region,item={{}}){{
  const row=document.createElement("div"); row.className="annotation"; row.dataset.region=region;
  row.innerHTML =
    '<div><label>Feature</label><input class="feature"></div>'+
    '<div><label>Decision</label><select class="decision">'+selectHtml(decisions,item.decision||"uncertain")+'</select></div>'+
    '<div><label>Confidence</label><input class="confidence" type="number" min="0" max="1" step=".05"></div>'+
    '<div><label>Evidence</label><select class="basis">'+selectHtml(bases,item.evidence_basis||"uncertain")+'</select></div>'+
    '<button type="button" class="remove">×</button>';
  row.querySelector(".feature").value=item.feature||"";
  row.querySelector(".confidence").value=item.confidence ?? .5;
  row.querySelector(".remove").onclick=()=>row.remove();
  return row;
}}
function renderRegions(record){{
  const host=document.getElementById("regions"); host.replaceChildren();
  for(const region of regionNames){{
    const box=document.createElement("div");box.className="region";box.dataset.region=region;
    const title=document.createElement("h3");title.textContent=region.replaceAll("_"," ");
    const add=document.createElement("button");add.type="button";add.textContent="+ add observed feature";
    const rows=document.createElement("div");rows.className="rows";
    for(const item of ((record.annotations?.regions||{{}})[region]||[])) rows.append(annotationRow(region,item));
    add.onclick=()=>rows.append(annotationRow(region));
    box.append(title,rows,add);host.append(box);
  }}
}}
function render(){{
  const item=currentItem(), record=currentRecord();
  document.getElementById("counter").textContent=(index+1)+" / "+batch.items.length;
  document.getElementById("pair-id").textContent=item.translation_pair_id+" · priority "+item.review_priority_score;
  document.getElementById("source-image").src=item.source_image_url;
  document.getElementById("lego-image").src=item.lego_image_url;
  document.getElementById("source-url").textContent=item.source_image_url;
  document.getElementById("lego-url").textContent=item.lego_image_url;
  const sig=document.getElementById("signals");sig.replaceChildren();
  for(const s of item.measurement_signals||[]){{
    const span=document.createElement("span");span.className="signal";
    span.textContent=(s.region||"global")+": "+s.signal+" = "+String(s.value);
    sig.append(span);
  }}
  document.getElementById("reviewer-id").value=record.reviewer?.reviewer_id||batch.reviewer_id||"";
  document.getElementById("reviewer-type").value=record.reviewer?.reviewer_type||batch.reviewer_type||"human";
  document.getElementById("model-id").value=record.reviewer?.model_id||"";
  document.getElementById("model-revision").value=record.reviewer?.model_revision||"";
  document.getElementById("evidence-scope").value=record.evidence?.evidence_scope||"front_pair";
  document.getElementById("review-role").value=record.reviewer?.review_role||"reviewer";
  document.getElementById("identity-features").value=(record.annotations?.identity_critical_features||[]).join("\n");
  document.getElementById("mask-route").value=record.annotations?.mask_headgear_route||"";
  document.getElementById("expression").value=record.annotations?.expression_translation||"";
  document.getElementById("limitations").value=(record.limitations||[]).join("\n");
  document.getElementById("adjudicates").value=(record.adjudicates_review_ids||[]).join("\n");
  renderRegions(record);
  status(saved[item.translation_pair_id] ? "saved "+(saved[item.translation_pair_id].review_status||"draft") : "unsaved draft");
}}
function collect(){{
  const item=currentItem(), record=currentRecord();
  record.reviewer = {{
    reviewer_type:document.getElementById("reviewer-type").value,
    reviewer_id:document.getElementById("reviewer-id").value.trim(),
    model_id:document.getElementById("model-id").value.trim()||null,
    model_revision:document.getElementById("model-revision").value.trim()||null,
    review_role:document.getElementById("review-role").value
  }};
  record.evidence.evidence_scope=document.getElementById("evidence-scope").value;
  record.evidence.claims_unobserved_surfaces=false;
  record.annotations.regions={{}};
  document.querySelectorAll(".region").forEach(box=>{{
    const region=box.dataset.region;record.annotations.regions[region]=[];
    box.querySelectorAll(".annotation").forEach(row=>{{
      const feature=row.querySelector(".feature").value.trim();
      if(!feature)return;
      record.annotations.regions[region].push({{
        feature,
        decision:row.querySelector(".decision").value,
        confidence:Number(row.querySelector(".confidence").value),
        evidence_basis:row.querySelector(".basis").value,
        notes:null
      }});
    }});
  }});
  record.annotations.identity_critical_features=lines(document.getElementById("identity-features").value);
  record.annotations.mask_headgear_route=document.getElementById("mask-route").value.trim()||null;
  record.annotations.expression_translation=document.getElementById("expression").value.trim()||null;
  record.limitations=lines(document.getElementById("limitations").value);
  record.adjudicates_review_ids=lines(document.getElementById("adjudicates").value);
  return record;
}}
function save(submit=false){{
  const item=currentItem(), record=collect();
  if(!record.reviewer.reviewer_id){{status("reviewer ID required",true);return false}}
  if((record.reviewer.reviewer_type==="model"||record.reviewer.reviewer_type==="hybrid") && (!record.reviewer.model_id||!record.reviewer.model_revision)){{
    status("model/hybrid review requires model ID and revision",true);return false;
  }}
  const count=Object.values(record.annotations.regions).reduce((n,x)=>n+x.length,0);
  if(submit && count===0){{status("submitted review requires at least one annotation",true);return false}}
  if(submit){{
    record.review_status=record.reviewer.review_role==="adjudicator"?"adjudicated":"submitted";
    record.created_at=new Date().toISOString();
  }} else if(!record.created_at) record.review_status="draft";
  saved[item.translation_pair_id]=record;
  localStorage.setItem(storageKey,JSON.stringify(saved));
  status("saved "+record.review_status);
  return true;
}}
function exportJsonl(){{
  save(false);
  const rows=batch.items.map(x=>saved[x.translation_pair_id]).filter(Boolean);
  const text=rows.map(x=>JSON.stringify(x)).join("\n")+"\n";
  const blob=new Blob([text],{{type:"application/x-ndjson"}});
  const url=URL.createObjectURL(blob),a=document.createElement("a");
  a.href=url;a.download=batch.batch_id+"-reviews.jsonl";a.click();URL.revokeObjectURL(url);
  status("exported "+rows.length+" review records");
}}
document.getElementById("prev").onclick=()=>{{save(false);index=(index-1+batch.items.length)%batch.items.length;render()}};
document.getElementById("next").onclick=()=>{{save(false);index=(index+1)%batch.items.length;render()}};
document.getElementById("save").onclick=()=>save(false);
document.getElementById("submit").onclick=()=>save(true);
document.getElementById("export").onclick=exportJsonl;
render();
</script>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    batch = json.loads(args.batch.read_text(encoding="utf-8"))
    output = build_review_html(batch)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(
        json.dumps(
            {
                "processor_version": VERSION,
                "batch_id": batch.get("batch_id"),
                "items": len(batch.get("items") or []),
                "output": str(args.output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
