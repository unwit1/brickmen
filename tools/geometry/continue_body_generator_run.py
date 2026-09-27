#!/usr/bin/env python3
"""Orchestrate an executed generator run through Brickmen mapping/validation.

The workflow deliberately stops at a review boundary unless a mapping-selection
record is supplied.

Stages:
1. verify executed primary/baseline generator run;
2. propose anonymous part -> Brickmen slot mapping;
3. write standalone mapping review HTML;
4. stop for explicit candidate selection, OR
5. promote selected mapping through structural validation;
6. run the complete generated-body validation bundle.

This command does not invoke the external GPU provider.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.geometry.build_body_provider_mapping_review_ui import (
    build_mapping_review_html,
)
from tools.geometry.promote_body_provider_output_mapping import (
    promote_mapping_candidate,
)
from tools.geometry.propose_body_provider_output_mapping import (
    propose_output_mapping,
)
from tools.geometry.run_body_generation_validation_bundle import (
    run_validation_bundle,
)


def load_json(path: str | Path | None) -> dict[str,Any] | None:
    if path is None:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: Path,payload: dict[str,Any]) -> None:
    path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")


def automatic_mapping_selection(
    proposal: dict[str,Any],
    *,
    enabled: bool,
) -> dict[str,Any] | None:
    """Return a synthetic explicit selection only for a strict unambiguous proposal."""
    if not enabled or not proposal.get("automatic_promotion_allowed",False):
        return None
    candidates=proposal.get("global_alignment_candidates") or []
    if not candidates:
        return None
    ambiguity=proposal.get("ambiguity") or {}
    if ambiguity.get("near_best_candidate_count") != 1:
        return None
    if ambiguity.get("distinct_near_best_mapping_count") != 1:
        return None
    best=candidates[0]
    if not best.get("complete_visual_slot_assignment"):
        return None
    return {
        "schema_version":"0.1",
        "provider_id":proposal.get("provider_id"),
        "provider_job_id":proposal.get("provider_job_id"),
        "architecture_id":proposal.get("architecture_id"),
        "selected_candidate_index":0,
        "selected_candidate_total_score":best.get("total_score"),
        "reviewer":"brickmen:auto-unambiguous-v0",
        "review_note":(
            "Automatically selected because the proposal explicitly satisfied "
            "Brickmen's strict unambiguous auto-promotion criteria."
        ),
        "proposal_automatic_promotion_allowed":True,
        "proposal_ambiguity":ambiguity,
        "explicit_review_selection":True,
        "automatic_selection":True,
        "production_geometry_authority":False,
    }


def continue_generator_run(
    conditioning: dict[str,Any],
    provider_job: dict[str,Any],
    provider_run: dict[str,Any],
    workspace: str | Path,
    *,
    mapping_selection: dict[str,Any] | None=None,
    auto_promote_unambiguous: bool=False,
    sweeps: dict[str,Any] | None=None,
    guide_manifest: dict[str,Any] | None=None,
    contact_regions: dict[str,Any] | None=None,
    conditioning_path: str | None=None,
    provider_job_path: str | None=None,
    provider_run_path: str | None=None,
    sweeps_path: str | None=None,
    guide_manifest_path: str | None=None,
    contact_regions_path: str | None=None,
) -> dict[str,Any]:
    out=Path(workspace)
    out.mkdir(parents=True,exist_ok=True)

    if provider_job.get("pipeline_stage")=="post_generation_critic":
        raise ValueError(
            "Post-generation critic runs use the critic workflow, not generator continuation"
        )
    if provider_job.get("requires_component_slot_mapping") is False:
        raise ValueError("Provider job does not produce primary component mappings")
    if provider_job.get("provider_id")!=provider_run.get("provider_id"):
        raise ValueError("Provider job/run provider IDs differ")
    if provider_job.get("provider_job_id")!=provider_run.get("provider_job_id"):
        raise ValueError("Provider job/run IDs differ")
    if provider_run.get("mode")!="executed":
        raise ValueError("Generator continuation requires an executed provider run")
    if provider_run.get("return_code") not in (0,None) or provider_run.get(
        "execution_succeeded"
    ) is False:
        raise ValueError("Provider run did not complete successfully")

    proposal=propose_output_mapping(
        conditioning,provider_run,provider_job=provider_job
    )
    proposal_path=out/"mapping-proposal.json"
    _write(proposal_path,proposal)
    review_path=out/"mapping-review.html"
    review_path.write_text(
        build_mapping_review_html(proposal),encoding="utf-8"
    )

    if mapping_selection is None:
        mapping_selection=automatic_mapping_selection(
            proposal,enabled=auto_promote_unambiguous
        )

    base_manifest={
        "schema_version":"0.1",
        "architecture_id":conditioning.get("architecture_id"),
        "provider_id":provider_job.get("provider_id"),
        "provider_job_id":provider_job.get("provider_job_id"),
        "pipeline_stage":provider_job.get("pipeline_stage"),
        "artifacts":{
            "mapping_proposal":str(proposal_path),
            "mapping_review_html":str(review_path),
        },
        "mapping_review_required":mapping_selection is None,
        "automatic_promotion_requested":bool(auto_promote_unambiguous),
        "automatic_promotion_used":bool(
            mapping_selection and mapping_selection.get("automatic_selection")
        ),
        "production_geometry_authority":False,
    }

    if mapping_selection is None:
        manifest={
            **base_manifest,
            "status":"mapping_review_required",
            "next_action":(
                "Open mapping-review.html, select/review a ranked candidate, "
                "then rerun with --mapping-selection."
            ),
            "automatic_promotion_allowed":proposal.get(
                "automatic_promotion_allowed",False
            ),
            "proposal_ambiguity":proposal.get("ambiguity"),
        }
        _write(out/"generator-continuation-manifest.json",manifest)
        return manifest

    if not mapping_selection.get("explicit_review_selection"):
        raise ValueError("Mapping selection must record explicit_review_selection=true")
    for key in ("provider_id","provider_job_id","architecture_id"):
        expected={
            "provider_id":provider_job.get("provider_id"),
            "provider_job_id":provider_job.get("provider_job_id"),
            "architecture_id":conditioning.get("architecture_id"),
        }[key]
        if mapping_selection.get(key)!=expected:
            raise ValueError(f"Mapping selection {key} does not match current run")

    index=int(mapping_selection["selected_candidate_index"])
    mapping=promote_mapping_candidate(
        proposal,provider_job,provider_run,index,
        reviewer=mapping_selection.get("reviewer"),
        review_note=mapping_selection.get("review_note"),
    )
    mapping_path=out/"output-mapping.json"
    _write(mapping_path,mapping)

    validation_dir=out/"validation"
    validation_manifest=run_validation_bundle(
        conditioning,mapping,validation_dir,
        conditioning_path=conditioning_path,
        output_mapping_path=str(mapping_path),
        sweeps=sweeps,
        sweeps_path=sweeps_path,
        guide_manifest=guide_manifest,
        guide_manifest_path=guide_manifest_path,
        provider_job=provider_job,
        provider_job_path=provider_job_path,
        provider_run=provider_run,
        provider_run_path=provider_run_path,
        contact_regions=contact_regions,
        contact_regions_path=contact_regions_path,
    )
    manifest={
        **base_manifest,
        "status":(
            "generated_geometry_validation_passed"
            if validation_manifest["generated_geometry_validation_passed"]
            else "generated_geometry_validation_review_required"
        ),
        "mapping_review_required":False,
        "selected_candidate_index":index,
        "artifacts":{
            **base_manifest["artifacts"],
            "output_mapping":str(mapping_path),
            "validation_directory":str(validation_dir),
            "validation_bundle_manifest":validation_manifest["artifacts"].get(
                "pipeline_state"
            ) and str(validation_dir/"bundle-manifest.json"),
        },
        "generated_geometry_validation_passed":validation_manifest[
            "generated_geometry_validation_passed"
        ],
        "pipeline_production_ready":validation_manifest[
            "pipeline_production_ready"
        ],
        "production_blocking_gates":validation_manifest[
            "production_blocking_gates"
        ],
        "next_action":(
            "Review validation/pipeline-state.json and resolve remaining gates."
        ),
    }
    _write(out/"generator-continuation-manifest.json",manifest)
    return manifest


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("provider_job")
    parser.add_argument("provider_run")
    parser.add_argument("workspace")
    parser.add_argument("--mapping-selection",default=None)
    parser.add_argument("--auto-promote-unambiguous",action="store_true")
    parser.add_argument("--sweeps",default=None)
    parser.add_argument("--guide-manifest",default=None)
    parser.add_argument("--contact-regions",default=None)
    args=parser.parse_args()
    manifest=continue_generator_run(
        load_json(args.conditioning),
        load_json(args.provider_job),
        load_json(args.provider_run),
        args.workspace,
        mapping_selection=load_json(args.mapping_selection),
        auto_promote_unambiguous=args.auto_promote_unambiguous,
        sweeps=load_json(args.sweeps),
        guide_manifest=load_json(args.guide_manifest),
        contact_regions=load_json(args.contact_regions),
        conditioning_path=args.conditioning,
        provider_job_path=args.provider_job,
        provider_run_path=args.provider_run,
        sweeps_path=args.sweeps,
        guide_manifest_path=args.guide_manifest,
        contact_regions_path=args.contact_regions,
    )
    if manifest["status"]=="mapping_review_required":
        return 3
    return 0 if manifest.get("generated_geometry_validation_passed") else 2


if __name__=="__main__":
    raise SystemExit(main())
