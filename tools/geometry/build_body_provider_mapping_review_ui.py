#!/usr/bin/env python3
"""Build a standalone HTML reviewer for provider part mapping proposals.

The HTML embeds proposal metadata/AABBs only. It never embeds source images
or generated mesh bytes.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any, Mapping

from tools.geometry.inspect_mesh_triangles import load_mesh_triangles


def _script_json(value: Any) -> str:
    return (
        json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        .replace("</", "<\\/")
        .replace("<!--", "<\\!--")
    )


def _edge_key(a, b, *, digits: int=6):
    aa=tuple(round(float(v),digits) for v in a)
    bb=tuple(round(float(v),digits) for v in b)
    return tuple(sorted((aa,bb)))


def _sample_review_wireframes(
    proposal: Mapping[str,Any],
    *,
    max_edges_per_part: int=500,
) -> dict[str,Any]:
    """Extract a bounded metadata-only wireframe sample for reviewer visualization."""
    paths=[]
    for candidate in proposal.get("global_alignment_candidates",[]):
        for assignment in candidate.get("assignments",[]):
            path=str(assignment.get("provider_part_path",""))
            if path and path not in paths:
                paths.append(path)

    result={}
    for path in paths:
        try:
            triangles=load_mesh_triangles(path)
        except Exception as exc:
            result[path]={
                "segments":[],
                "source_triangle_count":0,
                "wireframe_segment_count":0,
                "status":"unavailable",
                "reason":str(exc),
            }
            continue
        unique={}
        for tri in triangles:
            for a,b in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
                key=_edge_key(a,b)
                unique.setdefault(
                    key,
                    [
                        [float(v) for v in a],
                        [float(v) for v in b],
                    ],
                )
        keys=sorted(unique)
        if len(keys)>max_edges_per_part:
            step=max(1,(len(keys)+max_edges_per_part-1)//max_edges_per_part)
            keys=keys[::step][:max_edges_per_part]
        result[path]={
            "segments":[unique[key] for key in keys],
            "source_triangle_count":len(triangles),
            "wireframe_segment_count":len(keys),
            "status":"available",
        }
    return result


def build_mapping_review_html(proposal: Mapping[str, Any]) -> str:
    candidates = proposal.get("global_alignment_candidates", [])
    if not candidates:
        raise ValueError("Mapping proposal contains no global alignment candidates")
    review_payload=dict(proposal)
    review_payload["review_wireframes"]=_sample_review_wireframes(proposal)
    embedded = _script_json(review_payload)
    title = html.escape(
        str(proposal.get("provider_id", "provider"))
        + " -> "
        + str(proposal.get("architecture_id", "architecture"))
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Brickmen Mapping Review — {title}</title>
<style>
:root{{font-family:system-ui,-apple-system,sans-serif;color-scheme:dark;background:#111;color:#eee}}
body{{margin:0;display:grid;grid-template-columns:minmax(0,1fr) 390px;min-height:100vh}}
main{{padding:16px;overflow:auto}}
aside{{padding:16px;border-left:1px solid #333;background:#151515;overflow:auto}}
h1{{font-size:19px;margin:0 0 8px}} h2{{font-size:15px;margin:18px 0 8px}}
.views{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.view{{background:#181818;border:1px solid #333;border-radius:8px;padding:8px}}
svg{{width:100%;aspect-ratio:1;display:block;background:#101010}}
.target{{fill:#4cc9f0;fill-opacity:.12;stroke:#4cc9f0;stroke-width:2}}
.actual{{fill:#f8961e;fill-opacity:.13;stroke:#f8961e;stroke-width:2;stroke-dasharray:6 4}}
.label{{font-family:monospace;font-size:11px;fill:#fff;paint-order:stroke;stroke:#000;stroke-width:3}}
.axis{{stroke:#444;stroke-dasharray:4 4}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th,td{{padding:6px;border-bottom:1px solid #333;text-align:left;vertical-align:top}}
code{{font-size:11px;word-break:break-all}}
input,textarea,select,button{{box-sizing:border-box;width:100%;padding:7px;background:#222;color:#eee;border:1px solid #555;border-radius:5px}}
textarea{{min-height:70px;resize:vertical}}
button{{cursor:pointer;margin-top:8px}}
.primary{{background:#2541b2}}
.badge{{display:inline-block;padding:2px 7px;border:1px solid #555;border-radius:999px;font-size:10px;margin:2px}}
.good{{color:#9ee6a8}} .warn{{color:#ffd166}} .bad{{color:#ff9a9a}}
.small{{font-size:11px;color:#aaa;line-height:1.4}}
#status{{margin-top:8px;font-size:12px;min-height:1.4em}}
</style>
</head>
<body>
<main>
  <h1>Brickmen Provider Part Mapping Review</h1>
  <div id="badges"></div>
  <p class="small">Blue = Brickmen target slot AABB. Orange dashed = provider part AABB after the proposed shared global transform. White = bounded wireframe sample extracted from provider triangles when readable. Metadata only: no generated mesh or source-image bytes are embedded.</p>
  <div class="views">
    <section class="view"><strong>Front (X/Z)</strong><svg id="front" viewBox="0 0 700 700"></svg></section>
    <section class="view"><strong>Side (Y/Z)</strong><svg id="side" viewBox="0 0 700 700"></svg></section>
  </div>
  <h2>Assignments</h2>
  <table>
    <thead><tr><th>Provider part</th><th>Brickmen slot</th><th>Cost</th><th>IoU</th></tr></thead>
    <tbody id="assignments"></tbody>
  </table>
  <h2>Candidate details</h2>
  <pre id="details" class="small"></pre>
</main>
<aside>
  <h2>Ranked candidate</h2>
  <label for="candidate">Candidate index</label>
  <select id="candidate"></select>
  <div id="score"></div>
  <h2>Ambiguity</h2>
  <div id="ambiguity" class="small"></div>
  <h2>Review</h2>
  <label for="reviewer">Reviewer / agent ID</label>
  <input id="reviewer" placeholder="optional">
  <label for="note">Review note</label>
  <textarea id="note" placeholder="Why this candidate is being selected; what was checked?"></textarea>
  <button class="primary" id="download">Download promotion selection JSON</button>
  <button id="copy-cli">Copy promotion CLI</button>
  <p class="small">The selection record is not an output mapping. The Brickmen promotion tool reruns structural validation before producing one.</p>
  <div id="status"></div>
</aside>
<script id="proposal-data" type="application/json">{embedded}</script>
<script>
"use strict";
const proposal=JSON.parse(document.getElementById("proposal-data").textContent);
const candidates=proposal.global_alignment_candidates||[];
const select=document.getElementById("candidate");
for(let i=0;i<candidates.length;i++){{
  const option=document.createElement("option");
  option.value=String(i);
  option.textContent="#" + i + " — score " + Number(candidates[i].total_score).toFixed(4);
  select.append(option);
}}
function badge(text,cls){{
  return '<span class="badge ' + (cls||"") + '">' + text + '</span>';
}}
document.getElementById("badges").innerHTML=[
  badge(proposal.provider_id||"provider"),
  badge(proposal.architecture_id||"architecture"),
  badge("near-best: "+String(proposal.ambiguity?.near_best_candidate_count ?? "?"),
        (proposal.ambiguity?.near_best_candidate_count||0)>1?"warn":"good"),
  badge(proposal.automatic_promotion_allowed?"auto-promotion eligible":"explicit review required",
        proposal.automatic_promotion_allowed?"good":"warn")
].join("");

function boxUnion(boxes){{
  return {{
    min:[0,1,2].map(i=>Math.min(...boxes.map(b=>Number(b.min[i])))),
    max:[0,1,2].map(i=>Math.max(...boxes.map(b=>Number(b.max[i]))))
  }};
}}
function svgEl(tag,attrs){{
  const el=document.createElementNS("http://www.w3.org/2000/svg",tag);
  for(const [k,v] of Object.entries(attrs||{{}})) el.setAttribute(k,String(v));
  return el;
}}
function transformPoint(p,m){{
  if(!Array.isArray(m)||m.length!==16) return p.map(Number);
  const x=Number(p[0]),y=Number(p[1]),z=Number(p[2]);
  const out=[
    Number(m[0])*x+Number(m[1])*y+Number(m[2])*z+Number(m[3]),
    Number(m[4])*x+Number(m[5])*y+Number(m[6])*z+Number(m[7]),
    Number(m[8])*x+Number(m[9])*y+Number(m[10])*z+Number(m[11])
  ];
  const w=Number(m[12])*x+Number(m[13])*y+Number(m[14])*z+Number(m[15]);
  return (Math.abs(w)>1e-12&&Math.abs(w-1)>1e-12)?out.map(v=>v/w):out;
}}
function draw(svg,axisH,axisV,candidate){{
  svg.replaceChildren();
  const boxes=[];
  for(const a of candidate.assignments||[]) boxes.push(a.target_aabb_mm,a.transformed_aabb_mm);
  if(!boxes.length) return;
  const u=boxUnion(boxes);
  let hmin=u.min[axisH],hmax=u.max[axisH],vmin=u.min[axisV],vmax=u.max[axisV];
  const span=Math.max(hmax-hmin,vmax-vmin,1), pad=span*.12;
  hmin-=pad;hmax+=pad;vmin-=pad;vmax+=pad;
  const tx=v=>55+(Number(v)-hmin)/(hmax-hmin)*590;
  const ty=v=>645-(Number(v)-vmin)/(vmax-vmin)*590;
  if(hmin<=0&&hmax>=0) svg.append(svgEl("line",{{x1:tx(0),x2:tx(0),y1:55,y2:645,class:"axis"}}));
  if(vmin<=0&&vmax>=0) svg.append(svgEl("line",{{x1:55,x2:645,y1:ty(0),y2:ty(0),class:"axis"}}));
  for(const a of candidate.assignments||[]){{
    const wire=proposal.review_wireframes?.[a.provider_part_path];
    const matrix=candidate.global_transform_matrix_to_brickmen_mm;
    if(wire?.segments?.length && Array.isArray(matrix)){{
      for(const segment of wire.segments){{
        const p0=transformPoint(segment[0],matrix), p1=transformPoint(segment[1],matrix);
        svg.append(svgEl("line",{{
          x1:tx(p0[axisH]),y1:ty(p0[axisV]),
          x2:tx(p1[axisH]),y2:ty(p1[axisV]),
          class:"wire"
        }}));
      }}
    }}
    const pairs=[[a.target_aabb_mm,"target","T"],[a.transformed_aabb_mm,"actual","P"]];
    for(const entry of pairs){{
      const box=entry[0], cls=entry[1], prefix=entry[2];
      const x=tx(box.min[axisH]), x2=tx(box.max[axisH]);
      const y=ty(box.max[axisV]), y2=ty(box.min[axisV]);
      svg.append(svgEl("rect",{{x:x,y:y,width:x2-x,height:y2-y,class:cls}}));
      const text=svgEl("text",{{x:x+4,y:y+13,class:"label"}});
      text.textContent=prefix+":"+a.slot_id;
      svg.append(text);
    }}
  }}
}}
function esc(s){{
  return String(s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
}}
function render(){{
  const i=Number(select.value||0), c=candidates[i];
  draw(document.getElementById("front"),0,2,c);
  draw(document.getElementById("side"),1,2,c);
  document.getElementById("assignments").innerHTML=(c.assignments||[]).map(a=>
    "<tr><td><code>"+esc(a.provider_part_path)+"</code></td>"+
    "<td><code>"+esc(a.slot_id)+"</code></td>"+
    "<td>"+Number(a.pair_cost?.total||0).toFixed(4)+"</td>"+
    "<td>"+Number(a.pair_cost?.aabb_iou||0).toFixed(3)+"</td></tr>"
  ).join("");
  const complete=c.complete_visual_slot_assignment;
  document.getElementById("score").innerHTML=
    '<p class="'+(complete?"good":"bad")+'"><strong>'+
    (complete?"Complete visual-slot assignment":"Incomplete assignment")+
    "</strong></p><p class=\"small\">score="+Number(c.total_score).toFixed(6)+
    "<br>union shape error="+Number(c.union_shape_log_rmse).toFixed(6)+
    "<br>average assignment cost="+Number(c.average_assignment_cost).toFixed(6)+"</p>";
  document.getElementById("ambiguity").innerHTML=
    "near-best candidates: <strong>"+String(proposal.ambiguity?.near_best_candidate_count ?? "?")+"</strong><br>"+
    "distinct mappings: <strong>"+String(proposal.ambiguity?.distinct_near_best_mapping_count ?? "?")+"</strong><br>"+
    "best→second margin: <strong>"+String(proposal.ambiguity?.best_to_second_score_margin ?? "n/a")+"</strong><br>"+
    esc(proposal.ambiguity?.explanation||"");
  document.getElementById("details").textContent=JSON.stringify({{
    candidate_index:i,
    axis_permutation:c.axis_permutation_target_from_provider,
    axis_signs:c.axis_signs,
    uniform_scale:c.uniform_scale_provider_units_to_mm,
    missing_visual_target_slots:c.missing_visual_target_slots,
    missing_geometrically_mappable_slots:c.missing_geometrically_mappable_slots,
    unassigned_provider_parts:c.unassigned_provider_parts
  }},null,2);
}}
select.onchange=render;
document.getElementById("download").onclick=()=>{{
  const i=Number(select.value||0);
  const payload={{
    schema_version:"0.1",
    provider_id:proposal.provider_id,
    provider_job_id:proposal.provider_job_id,
    architecture_id:proposal.architecture_id,
    selected_candidate_index:i,
    selected_candidate_total_score:candidates[i].total_score,
    reviewer:document.getElementById("reviewer").value.trim()||null,
    review_note:document.getElementById("note").value.trim()||null,
    proposal_automatic_promotion_allowed:proposal.automatic_promotion_allowed,
    proposal_ambiguity:proposal.ambiguity,
    explicit_review_selection:true,
    production_geometry_authority:false
  }};
  const blob=new Blob([JSON.stringify(payload,null,2)+"\n"],{{type:"application/json"}});
  const a=document.createElement("a");
  a.href=URL.createObjectURL(blob);
  a.download=(proposal.provider_id||"provider")+"-mapping-selection.json";
  a.click();
  URL.revokeObjectURL(a.href);
  document.getElementById("status").textContent="Selection record downloaded.";
}};
document.getElementById("copy-cli").onclick=async()=>{{
  const i=Number(select.value||0);
  const command="python -m tools.geometry.promote_body_provider_output_mapping mapping-proposal.json provider-job.json provider-run.json "+i+" -o output-mapping.json";
  await navigator.clipboard.writeText(command);
  document.getElementById("status").textContent="Promotion CLI copied.";
}};
render();
</script>
</body>
</html>"""


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("proposal")
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    proposal=json.loads(Path(args.proposal).read_text(encoding="utf-8"))
    Path(args.output).write_text(
        build_mapping_review_html(proposal), encoding="utf-8"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
