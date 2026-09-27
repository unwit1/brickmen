#!/usr/bin/env python3
"""Create/validate Brickmen provider-output component mappings.

A provider process can exit successfully while still producing the wrong part
count or decomposition. This gate requires every required Brickmen component
slot to resolve exactly once before the output is considered structurally
complete.

The gate does not validate mesh quality, physical interfaces, or manufacturing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_assignments(values: Sequence[str]) -> list[dict[str, str]]:
    result=[]
    for raw in values:
        if "=" not in raw:
            raise ValueError(f"Assignment must be slot_id=path: {raw}")
        slot,path=raw.split("=",1)
        slot=slot.strip()
        path=path.strip()
        if not slot or not path:
            raise ValueError(f"Assignment must be slot_id=path: {raw}")
        result.append({"slot_id":slot,"path":path})
    return result


def parse_transforms(values: Sequence[str]) -> dict[str, list[float]]:
    result: dict[str, list[float]] = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError(
                f"Transform must be slot_id=m00,m01,...,m33: {raw}"
            )
        slot, payload = raw.split("=", 1)
        numbers = [float(x.strip()) for x in payload.split(",") if x.strip()]
        if len(numbers) != 16:
            raise ValueError(
                f"Transform for {slot.strip()} must contain exactly 16 numbers"
            )
        result[slot.strip()] = numbers
    return result


def validate_output_mapping(
    job: Mapping[str, Any],
    run: Mapping[str, Any],
    assignments: Sequence[Mapping[str, str]],
    *,
    transforms: Mapping[str, Sequence[float]] | None = None,
) -> dict[str, Any]:
    if job["provider_id"] != run["provider_id"]:
        raise ValueError("Provider job and run provider_id differ")
    if job["provider_job_id"] != run["provider_job_id"]:
        raise ValueError("Provider job and run provider_job_id differ")

    transforms = transforms or {}
    required=[        str(item["slot_id"])
        for item in job.get("component_slots",{}).get("required",[])
    ]
    optional=[
        str(item["slot_id"])
        for item in job.get("component_slots",{}).get("optional",[])
    ]
    known=set(required)|set(optional)
    discovered=[str(x) for x in run.get("discovered_outputs",[])]

    by_slot: dict[str,list[str]]={}
    unknown=[]
    missing_files=[]
    not_discovered=[]
    for item in assignments:
        slot=str(item["slot_id"])
        path=str(Path(item["path"]))
        by_slot.setdefault(slot,[]).append(path)
        if slot not in known:
            unknown.append(slot)
        if not Path(path).is_file():
            missing_files.append(path)
        if discovered and path not in discovered:
            # Compare resolved paths too, because callers may use equivalent
            # relative/absolute spellings.
            resolved=str(Path(path).resolve())
            discovered_resolved={str(Path(x).resolve()) for x in discovered}
            if resolved not in discovered_resolved:
                not_discovered.append(path)

    duplicates=sorted(slot for slot,paths in by_slot.items() if len(paths)!=1)
    mapped=set(by_slot)
    missing_required=sorted(set(required)-mapped)

    components=[]
    assigned_paths=set()
    for slot in sorted(mapped & known):
        paths=by_slot[slot]
        if len(paths)!=1:
            continue
        path=paths[0]
        assigned_paths.add(str(Path(path).resolve()))
        transform = transforms.get(slot)
        if transform is not None and len(transform) != 16:
            raise ValueError(
                f"Transform for {slot} must contain exactly 16 numbers"
            )
        components.append({
            "slot_id":slot,
            "path":path,
            "provider_part_id":None,
            "mapping_authority":"explicit_operator_or_adapter_assignment",
            "transform_status":(
                "brickmen_mm_transform_supplied"
                if transform is not None
                else "unreconciled_provider_frame"
            ),
            "transform_matrix_to_brickmen_mm":(
                [float(v) for v in transform]
                if transform is not None
                else None
            ),
            "transform_source":(
                "explicit_cli_assignment" if transform is not None else None
            ),
            "geometry_authority":"generated_visual_geometry_nonproduction",
        })

    unassigned=[]
    for path in discovered:
        if str(Path(path).resolve()) not in assigned_paths:
            unassigned.append(path)

    run_failed=(
        run.get("mode")=="executed"
        and (
            run.get("return_code") not in (0,None)
            or run.get("execution_succeeded") is False
        )
    )
    errors=[]
    if run_failed:
        errors.append("provider_execution_failed")
    if unknown:
        errors.append("unknown_component_slots")
    if duplicates:
        errors.append("duplicate_component_slot_assignments")
    if missing_required:
        errors.append("missing_required_component_slots")
    if missing_files:
        errors.append("assigned_output_files_missing")
    if not_discovered:
        errors.append("assigned_files_not_in_provider_run_outputs")

    structurally_complete=not any(
        code in errors for code in (
            "provider_execution_failed",
            "unknown_component_slots",
            "duplicate_component_slot_assignments",
            "missing_required_component_slots",
            "assigned_output_files_missing",
            "assigned_files_not_in_provider_run_outputs",
        )
    )

    if structurally_complete:
        status="component_graph_complete_requires_geometry_validation"
    elif assignments:
        status="component_mapping_incomplete_or_invalid"
    else:
        status="manual_component_mapping_required"

    return {
        "schema_version":"0.1",
        "provider_id":job["provider_id"],
        "provider_job_id":job["provider_job_id"],
        "run_mode":run.get("mode"),
        "components":components,
        "unassigned_outputs":unassigned,
        "acceptance":{
            "status":status,
            "structurally_complete":structurally_complete,
            "required_slots":required,
            "optional_slots":optional,
            "mapped_slots":sorted(mapped & known),
            "missing_required_slots":missing_required,
            "unknown_slots":sorted(set(unknown)),
            "duplicate_slots":duplicates,
            "missing_files":sorted(set(missing_files)),
            "assigned_files_not_in_discovered_outputs":sorted(set(not_discovered)),
            "errors":errors,
            "next_required_checks":[
                "component-to-skeleton transform reconciliation",
                "visual-envelope conformance",
                "mechanical keep-out intersection test",
                "articulation sweep/collision test",
                "mesh repair/manifold/printability checks",
                "deterministic validated interface insertion",
                "physical validation where mechanics matter",
            ],
        },
        "production_geometry_authority":False,
        "warning":(
            "Structural component mapping is only the first output gate. Generated "
            "meshes remain visual/nonproduction geometry."
        ),
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("job")
    parser.add_argument("run")
    parser.add_argument("--assign",action="append",default=[])
    parser.add_argument(
        "--transform",
        action="append",
        default=[],
        help="slot_id=m00,m01,...,m33 row-major provider->Brickmen-mm transform",
    )
    parser.add_argument("-o","--output",required=True)
    args=parser.parse_args()
    result=validate_output_mapping(
        load_json(args.job),
        load_json(args.run),
        parse_assignments(args.assign),
        transforms=parse_transforms(args.transform),
    )
    Path(args.output).write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    return 0 if result["acceptance"]["structurally_complete"] else 2


if __name__=="__main__":
    raise SystemExit(main())
