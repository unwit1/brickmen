#!/usr/bin/env python3
"""Compile a BodyGenerationConditioning payload into a provider-neutral job.

The output is orchestration metadata only. It does not execute external models
and never upgrades generated geometry to manufacturing authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def provider_map(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {item["provider_id"]: item for item in registry["providers"]}


def _digest(conditioning: Mapping[str, Any]) -> str:
    payload = json.dumps(
        conditioning, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _slots(conditioning: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in conditioning.get("component_plan", {}).get(
            "generated_component_slots", []
        )
    ]


def compile_provider_job(
    conditioning: Mapping[str, Any],
    provider: Mapping[str, Any],
    *,
    source_image: str | None = None,
    guide_manifest: Mapping[str, Any] | None = None,
    sweep_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    slots = _slots(conditioning)
    required = [slot for slot in slots if slot.get("required", True)]
    optional = [slot for slot in slots if not slot.get("required", True)]
    part_count = conditioning.get("component_plan", {}).get(
        "expected_generated_part_count"
    )

    native_args: dict[str, Any] = {}
    if provider["provider_id"] == "partcrafter" and part_count:
        native_args["num_parts"] = int(part_count["min"])
        native_args["part_count_policy"] = (
            "Use required component count by default; rerun with optional "
            "components only when the selected Brickmen architecture requests them."
        )

    if source_image is not None:
        native_args["source_image"] = source_image

    mechanical = conditioning.get("mechanical_constraints", [])
    has_unapproved = any(
        not bool(item.get("manufacturing_authority", False)) for item in mechanical
    )

    post = list(
        provider.get("brickmen_integration", {}).get("post_generation", [])
    )
    post.extend(
        [
            "validate returned component count and slot mapping",
            "transform every generated component into the Brickmen conditioning frame",
            "validate shell against visual envelopes and articulation/keep-out volumes",
            "preserve fixed-mm commodity hardware dimensions",
            "insert only separately validated deterministic interfaces after visual generation",
        ]
    )

    return {
        "schema_version": "0.1",
        "provider_job_id": (
            f"{conditioning['architecture_id']}::{provider['provider_id']}::"
            f"{_digest(conditioning)[:12]}"
        ),
        "provider_id": provider["provider_id"],
        "provider_role": provider["role"],
        "provider_availability": provider["availability"],
        "conditioning_digest_sha256": _digest(conditioning),
        "architecture_id": conditioning["architecture_id"],
        "target_height_mm": conditioning["target_height_mm"],
        "source_image": source_image,
        "guide_pack": dict(guide_manifest) if guide_manifest else None,
        "articulation_sweep_summary": (
            {
                "architecture_id": sweep_report.get("architecture_id"),
                "joint_ids": [
                    item.get("joint_id")
                    for item in sweep_report.get("joint_sweeps", [])
                ],
                "production_geometry_authority": sweep_report.get(
                    "production_geometry_authority", False
                ),
            }
            if sweep_report
            else None
        ),
        "component_slots": {
            "required": required,
            "optional": optional,
            "expected_part_count": part_count,
        },
        "native_arguments": native_args,
        "pre_generation_steps": provider.get("brickmen_integration", {}).get(
            "pre_generation", []
        ),
        "post_generation_steps": post,
        "conditioning_channels": conditioning.get("conditioning_channels", {}),
        "mechanical_constraints": mechanical,
        "mechanical_review_required": bool(mechanical),
        "contains_nonproduction_mechanical_constraints": has_unapproved,
        "output_acceptance_rules": [
            "All expected required component slots must be resolved or the run is incomplete.",
            "Generated meshes may satisfy visual envelopes but cannot redefine selected skeleton joint frames automatically.",
            "Generated geometry intersecting locked mechanical keep-outs must be repaired or rejected.",
            "Provider-inferred articulation may be recorded as evidence but cannot overwrite validated Brickmen joint records automatically.",
            "No provider output is manufacturing-authoritative until deterministic interface insertion and downstream engineering validation pass.",
        ],
        "production_geometry_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("conditioning")
    parser.add_argument("registry")
    parser.add_argument("provider_id")
    parser.add_argument("--source-image", default=None)
    parser.add_argument("--guide-manifest", default=None)
    parser.add_argument("--sweeps", default=None)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()

    conditioning = load_json(args.conditioning)
    registry = load_json(args.registry)
    providers = provider_map(registry)
    if args.provider_id not in providers:
        raise SystemExit(f"Unknown provider_id: {args.provider_id}")
    job = compile_provider_job(
        conditioning,
        providers[args.provider_id],
        source_image=args.source_image,
        guide_manifest=(
            load_json(args.guide_manifest) if args.guide_manifest else None
        ),
        sweep_report=(load_json(args.sweeps) if args.sweeps else None),
    )
    Path(args.output).write_text(
        json.dumps(job, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
