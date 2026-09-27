#!/usr/bin/env python3
"""Promote one reviewed anonymous-part mapping proposal into an output mapping.

Promotion is explicit: the caller selects the candidate index. The selected
global transform is copied to every assigned provider component and the normal
provider-output structural validator is run before the mapping is written.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from tools.geometry.validate_body_generation_provider_output import (
    validate_output_mapping,
)


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def promote_mapping_candidate(
    proposal: Mapping[str,Any],
    provider_job: Mapping[str,Any],
    provider_run: Mapping[str,Any],
    candidate_index: int,
    *,
    reviewer: str | None=None,
    review_note: str | None=None,
) -> dict[str,Any]:
    candidates=proposal.get("global_alignment_candidates",[])
    if candidate_index<0 or candidate_index>=len(candidates):
        raise ValueError(
            f"candidate_index {candidate_index} outside proposal range 0..{len(candidates)-1}"
        )
    if provider_job.get("requires_component_slot_mapping") is False:
        raise ValueError("Provider job is not a primary component-mapping job")
    if provider_job.get("provider_id")!=proposal.get("provider_id"):
        raise ValueError("Proposal/provider-job provider IDs differ")
    if provider_run.get("provider_id")!=proposal.get("provider_id"):
        raise ValueError("Proposal/provider-run provider IDs differ")

    candidate=candidates[candidate_index]
    if not candidate.get("complete_visual_slot_assignment"):
        raise ValueError(
            "Selected proposal candidate does not resolve every required visual slot"
        )
    matrix=candidate["global_transform_matrix_to_brickmen_mm"]
    assignments=[
        {
            "slot_id":item["slot_id"],
            "path":item["provider_part_path"],
        }
        for item in candidate.get("assignments",[])
    ]
    transforms={
        item["slot_id"]:matrix
        for item in candidate.get("assignments",[])
    }
    provenance_by_path={
        str(item["provider_part_path"]):{
            "provider_part_id":item.get("provider_part_id"),
            "provider_part_index":item.get("provider_part_index"),
            "provider_manifest":item.get("provider_manifest"),
        }
        for item in candidate.get("assignments",[])
    }
    result=validate_output_mapping(
        provider_job,
        provider_run,
        assignments,
        transforms=transforms,
    )
    if not result["acceptance"]["structurally_complete"]:
        raise ValueError(
            "Selected proposal failed the provider-output structural validator: "
            + ",".join(result["acceptance"].get("errors",[]))
        )

    for component in result.get("components",[]):
        component["mapping_authority"]="reviewed_geometry_proposal_promotion"
        component["transform_source"]="reviewed_global_mapping_proposal"
        provenance=provenance_by_path.get(str(component.get("path")),{})
        component["provider_part_id"]=provenance.get("provider_part_id")
        component["provider_part_index"]=provenance.get("provider_part_index")
        component["provider_manifest"]=provenance.get("provider_manifest")

    result["mapping_promotion"]={
        "proposal_schema_version":proposal.get("schema_version"),
        "selected_candidate_index":candidate_index,
        "selected_candidate_total_score":candidate.get("total_score"),
        "selected_candidate_union_shape_log_rmse":candidate.get(
            "union_shape_log_rmse"
        ),
        "selected_candidate_average_assignment_cost":candidate.get(
            "average_assignment_cost"
        ),
        "proposal_automatic_promotion_allowed":proposal.get(
            "automatic_promotion_allowed",False
        ),
        "proposal_ambiguity":proposal.get("ambiguity"),
        "reviewer":reviewer,
        "review_note":review_note,
        "promotion_is_explicit":True,
    }
    result["production_geometry_authority"]=False
    return result


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("proposal")
    parser.add_argument("provider_job")
    parser.add_argument("provider_run")
    parser.add_argument("candidate_index",type=int)
    parser.add_argument("--reviewer",default=None)
    parser.add_argument("--review-note",default=None)
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    result=promote_mapping_candidate(
        load_json(args.proposal),
        load_json(args.provider_job),
        load_json(args.provider_run),
        args.candidate_index,
        reviewer=args.reviewer,
        review_note=args.review_note,
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
