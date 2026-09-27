#!/usr/bin/env python3
"""Build a standalone local semantic-part mask editor for PAct/Brickmen.

The generated HTML contains component-slot labels but never embeds a source
image. The operator loads a local image in-browser, paints integer semantic
labels, and exports:
- a lossless grayscale PNG where pixel value = semantic label;
- a JSON legend mapping labels to Brickmen component slots.

The output is input-conditioning evidence only, not semantic truth or
manufacturing authority.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any, Mapping


def load_json(path: str | Path) -> dict[str,Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _slots(conditioning: Mapping[str,Any]) -> list[dict[str,Any]]:
    slots=[
        dict(item)
        for item in conditioning.get("component_plan",{}).get(
            "generated_component_slots",[]
        )
        if item.get("required",True)
    ]
    if not slots:
        seen=set()
        for env in conditioning.get("visual_envelopes",[]):
            slot=env.get("component_slot_id")
            if slot and slot not in seen:
                seen.add(slot)
                slots.append({"slot_id":slot,"required":True})
    return slots


def build_pact_mask_editor_html(
    conditioning: Mapping[str,Any],
) -> str:
    slots=_slots(conditioning)
    if not slots:
        raise ValueError("Conditioning has no generated component slots")
    if len(slots)>254:
        raise ValueError("Semantic PNG editor supports at most 254 positive labels")
    labels=[
        {
            "label":i+1,
            "slot_id":str(item["slot_id"]),
            "role":item.get("role"),
            "side":item.get("side"),
        }
        for i,item in enumerate(slots)
    ]
    payload={
        "schema_version":"0.1",
        "architecture_id":conditioning.get("architecture_id"),
        "target_height_mm":conditioning.get("target_height_mm"),
        "labels":labels,
        "background_label":0,
        "production_geometry_authority":False,
    }
    embedded=(
        json.dumps(payload,separators=(",",":"),ensure_ascii=False)
        .replace("</","<\\/")
        .replace("<!--","<\\!--")
    )
    title=html.escape(str(conditioning.get("architecture_id","Brickmen")))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Brickmen PAct Semantic Mask Editor — {title}</title>
<style>
:root{{font-family:system-ui,-apple-system,sans-serif;color-scheme:dark;background:#111;color:#eee}}
*{{box-sizing:border-box}}
body{{margin:0;display:grid;grid-template-columns:minmax(0,1fr) 340px;min-height:100vh}}
main{{padding:12px;display:flex;flex-direction:column;gap:10px;min-width:0}}
aside{{padding:14px;border-left:1px solid #333;background:#171717;overflow:auto}}
.stage{{position:relative;min-height:440px;background:#090909;border:1px solid #333;border-radius:8px;overflow:auto;display:grid;place-items:center}}
canvas{{max-width:100%;height:auto;image-rendering:auto;touch-action:none;cursor:crosshair}}
label{{display:block;font-size:12px;color:#bbb;margin:10px 0 4px}}
input,select,button{{width:100%;padding:7px;background:#222;color:#eee;border:1px solid #555;border-radius:5px}}
button{{cursor:pointer;margin-top:7px}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:7px}}
.primary{{background:#2541b2}}
.small{{font-size:11px;color:#aaa;line-height:1.45}}
.legend{{font:12px/1.45 ui-monospace,monospace;white-space:pre-wrap;background:#101010;padding:8px;border-radius:6px;border:1px solid #333}}
#status{{font-size:12px;min-height:2em;margin-top:8px}}
</style>
</head>
<body>
<main>
  <div class="row">
    <div>
      <label for="image-file">Local source image</label>
      <input id="image-file" type="file" accept="image/*">
    </div>
    <div>
      <label for="overlay-opacity">Overlay opacity</label>
      <input id="overlay-opacity" type="range" min="0" max="1" step="0.05" value="0.55">
    </div>
  </div>
  <div class="stage"><canvas id="canvas"></canvas></div>
  <p class="small">The source image is loaded only into this browser tab. Exported PNG pixels contain semantic label values, not the display colors.</p>
</main>
<aside>
  <h2 style="margin-top:0">Semantic mask</h2>
  <label for="label-select">Paint label</label>
  <select id="label-select"></select>
  <label for="brush-size">Brush radius (image pixels)</label>
  <input id="brush-size" type="range" min="1" max="100" value="18">
  <label for="tool">Tool</label>
  <select id="tool">
    <option value="brush">Brush</option>
    <option value="fill">Flood fill label region</option>
    <option value="eraser">Erase to background</option>
  </select>
  <div class="row">
    <button id="undo">Undo</button>
    <button id="redo">Redo</button>
  </div>
  <button id="clear">Clear all labels</button>
  <button class="primary" id="export-png">Export semantic PNG</button>
  <button id="export-legend">Export label legend JSON</button>
  <h3>Label map</h3>
  <div id="legend" class="legend"></div>
  <div id="status"></div>
</aside>
<script id="brickmen-mask-config" type="application/json">{embedded}</script>
<script>
"use strict";
const cfg=JSON.parse(document.getElementById("brickmen-mask-config").textContent);
const canvas=document.getElementById("canvas");
const ctx=canvas.getContext("2d");
const source=document.createElement("canvas"), sctx=source.getContext("2d");
let labels=null, width=0, height=0, drawing=false;
let history=[], future=[];
const palette=[
  [0,0,0],[244,67,54],[33,150,243],[76,175,80],[255,193,7],
  [156,39,176],[255,87,34],[0,188,212],[139,195,74],[255,152,0],
  [63,81,181],[233,30,99],[121,85,72],[0,150,136],[205,220,57]
];
const select=document.getElementById("label-select");
const options=[{{label:0,slot_id:"background"}},...cfg.labels];
for(const item of options){{
  const o=document.createElement("option");
  o.value=String(item.label);
  o.textContent=String(item.label)+" — "+item.slot_id;
  select.append(o);
}}
document.getElementById("legend").textContent=options.map(
  x=>String(x.label).padStart(3," ")+"  "+x.slot_id
).join("\n");

function colorFor(label){{
  if(label===0) return [0,0,0,0];
  const p=palette[label%palette.length];
  return [p[0],p[1],p[2],255];
}}
function snapshot(){{
  if(!labels) return;
  history.push(labels.slice());
  if(history.length>25) history.shift();
  future=[];
}}
function restore(next){{
  if(!labels||!next) return;
  labels=next.slice(); render();
}}
function setStatus(text){{document.getElementById("status").textContent=text;}}
function render(){{
  if(!labels||!width||!height) return;
  ctx.clearRect(0,0,width,height);
  ctx.drawImage(source,0,0);
  const image=ctx.getImageData(0,0,width,height);
  const alpha=Number(document.getElementById("overlay-opacity").value);
  for(let i=0;i<labels.length;i++){{
    const label=labels[i];
    if(!label) continue;
    const c=colorFor(label), j=i*4;
    image.data[j]=Math.round(image.data[j]*(1-alpha)+c[0]*alpha);
    image.data[j+1]=Math.round(image.data[j+1]*(1-alpha)+c[1]*alpha);
    image.data[j+2]=Math.round(image.data[j+2]*(1-alpha)+c[2]*alpha);
  }}
  ctx.putImageData(image,0,0);
}}
function eventPoint(evt){{
  const rect=canvas.getBoundingClientRect();
  return [
    Math.max(0,Math.min(width-1,Math.floor((evt.clientX-rect.left)*width/rect.width))),
    Math.max(0,Math.min(height-1,Math.floor((evt.clientY-rect.top)*height/rect.height)))
  ];
}}
function paint(x,y,label){{
  const radius=Number(document.getElementById("brush-size").value);
  const r2=radius*radius;
  const xmin=Math.max(0,x-radius), xmax=Math.min(width-1,x+radius);
  const ymin=Math.max(0,y-radius), ymax=Math.min(height-1,y+radius);
  for(let yy=ymin;yy<=ymax;yy++) for(let xx=xmin;xx<=xmax;xx++){{
    const dx=xx-x,dy=yy-y;
    if(dx*dx+dy*dy<=r2) labels[yy*width+xx]=label;
  }}
}}
function flood(x,y,newLabel){{
  const start=y*width+x, old=labels[start];
  if(old===newLabel) return;
  const stack=[start]; labels[start]=newLabel;
  while(stack.length){{
    const idx=stack.pop(), px=idx%width, py=Math.floor(idx/width);
    const n=[];
    if(px>0)n.push(idx-1); if(px+1<width)n.push(idx+1);
    if(py>0)n.push(idx-width); if(py+1<height)n.push(idx+width);
    for(const ni of n) if(labels[ni]===old){{labels[ni]=newLabel;stack.push(ni);}}
  }}
}}
canvas.onpointerdown=evt=>{{
  if(!labels)return;
  canvas.setPointerCapture(evt.pointerId);
  snapshot();
  const [x,y]=eventPoint(evt), tool=document.getElementById("tool").value;
  const label=tool==="eraser"?0:Number(select.value);
  if(tool==="fill") flood(x,y,label); else {{drawing=true;paint(x,y,label);}}
  render();
}};
canvas.onpointermove=evt=>{{
  if(!drawing||!labels)return;
  const [x,y]=eventPoint(evt);
  const tool=document.getElementById("tool").value;
  paint(x,y,tool==="eraser"?0:Number(select.value)); render();
}};
canvas.onpointerup=()=>{{drawing=false;}};
canvas.onpointercancel=()=>{{drawing=false;}};

document.getElementById("image-file").onchange=evt=>{{
  const file=evt.target.files?.[0]; if(!file)return;
  const url=URL.createObjectURL(file), img=new Image();
  img.onload=()=>{{
    width=img.naturalWidth;height=img.naturalHeight;
    canvas.width=source.width=width;canvas.height=source.height=height;
    sctx.clearRect(0,0,width,height);sctx.drawImage(img,0,0);
    labels=new Uint8Array(width*height);history=[];future=[];render();
    URL.revokeObjectURL(url);
    setStatus("Image loaded locally. Paint labels, then export PNG.");
  }};
  img.src=url;
}};
document.getElementById("overlay-opacity").oninput=render;
document.getElementById("undo").onclick=()=>{{
  if(!labels||!history.length)return;
  future.push(labels.slice()); restore(history.pop());
}};
document.getElementById("redo").onclick=()=>{{
  if(!labels||!future.length)return;
  history.push(labels.slice()); restore(future.pop());
}};
document.getElementById("clear").onclick=()=>{{
  if(!labels)return;snapshot();labels.fill(0);render();
}};
document.getElementById("export-png").onclick=()=>{{
  if(!labels){{setStatus("Load an image first.");return;}}
  const out=document.createElement("canvas");out.width=width;out.height=height;
  const ox=out.getContext("2d"), image=ox.createImageData(width,height);
  for(let i=0;i<labels.length;i++){{
    const v=labels[i],j=i*4;
    image.data[j]=v;image.data[j+1]=v;image.data[j+2]=v;image.data[j+3]=255;
  }}
  ox.putImageData(image,0,0);
  out.toBlob(blob=>{{
    const a=document.createElement("a");a.href=URL.createObjectURL(blob);
    a.download=(cfg.architecture_id||"brickmen")+"-pact-semantic-mask.png";
    a.click();URL.revokeObjectURL(a.href);
    setStatus("Semantic PNG exported. Pixel value equals label ID.");
  }},"image/png");
}};
document.getElementById("export-legend").onclick=()=>{{
  const payload={{
    ...cfg,
    source_image_embedded:false,
    semantic_mask_encoding:"lossless_grayscale_png_pixel_value_is_label_id",
    review_status:"operator_authored_not_semantically_validated"
  }};
  const blob=new Blob([JSON.stringify(payload,null,2)+"\n"],{{type:"application/json"}});
  const a=document.createElement("a");a.href=URL.createObjectURL(blob);
  a.download=(cfg.architecture_id||"brickmen")+"-pact-mask-legend.json";
  a.click();URL.revokeObjectURL(a.href);
}};
</script>
</body>
</html>"""


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    payload=load_json(args.conditioning)
    Path(args.output).write_text(
        build_pact_mask_editor_html(payload),encoding="utf-8"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
