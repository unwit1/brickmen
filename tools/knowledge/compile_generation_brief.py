#!/usr/bin/env python3
"""Compile the existing generation packet into a reproducible prompt and checklist.

This is a metadata preflight, not image generation or a physical accuracy score.
The existing control-generation packet and output contracts remain authoritative.
No network calls, model loading or source-image redistribution are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

VERSION = "brickmen-generation-brief/v1"
DATA = Path(__file__).resolve().parents[2] / "knowledge/libraries/lego-minifigure-customs/data"
UNKNOWN = {"unknown", "pending", "tbd", "todo", "unavailable", ""}


def known(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in UNKNOWN and "|" not in value
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def content_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _compile_brief(brief, data_dir=DATA, base_dir=None):
    contracts = read_json(data_dir / "ai-output-contracts.json")
    protocol = read_json(data_dir / "chatgpt-control-generation-schema.json")
    packet_template = protocol["control_generation_packet"]
    errors, warnings = [], []

    def need(value, label, collection=False):
        valid_type = (isinstance(value, list) if collection else isinstance(value, str)) or (label == "canonical_parts.color_id" and type(value) is int)
        if not valid_type or not known(value):
            errors.append(f"Missing or unresolved {label}")

    if not isinstance(brief, dict):
        raise ValueError("Brief must be an object")
    if brief.get("schema_version") != VERSION:
        errors.append(f"schema_version must be {VERSION}")
    need(brief.get("brief_id"), "brief_id")
    kind = brief.get("target_kind")
    if kind not in {"minifigure", "part"}:
        errors.append("target_kind must be minifigure or part")
    output = brief.get("output_contract")
    if output not in contracts["outputs"]:
        errors.append("Unknown output_contract")
    if kind == "part" and output == "concept_render":
        errors.append("Standalone parts use part_render, not the assembly concept_render contract")
    if kind == "minifigure" and output == "part_render":
        errors.append("Complete minifigures use concept_render, not part_render")
    packet = brief.get("generation_packet") or {}
    if not isinstance(packet, dict):
        raise ValueError("generation_packet must be an object")
    for key in ("target_identity", "structural_locks", "official_style", "mask_translation", "transformation", "rendering", "output", "evaluation"):
        if key in packet and not isinstance(packet[key], dict):
            raise ValueError(f"{key} must be an object")
    for key in ("references", "critical_features", "allowed_changes", "forbidden_changes"):
        if key in packet and not isinstance(packet[key], list):
            raise ValueError(f"{key} must be a list")
    for key in ("required_views", "required_part_slots", "unknowns", "unresolved_conflicts"):
        if key in brief and not isinstance(brief[key], list):
            raise ValueError(f"{key} must be a list")
    for key in ("required_views", "required_part_slots", "unknowns"):
        if any(not isinstance(item, str) or not known(item) for item in brief.get(key, [])):
            raise ValueError(f"{key} entries must be resolved strings")
    for key in ("allowed_changes", "forbidden_changes"):
        if any(not isinstance(item, str) for item in packet.get(key, [])):
            raise ValueError(f"{key} entries must be strings")
    for key in ("references", "critical_features"):
        if any(not isinstance(item, dict) for item in packet.get(key, [])):
            raise ValueError(f"{key} entries must be objects")
    identity = packet.get("target_identity") or {}
    for key in ("subject", "source_appearance"):
        need(identity.get(key), f"target_identity.{key}")
    if kind == "minifigure":
        for key in ("incarnation_version", "outfit", "expression", "mask_headgear_state"):
            need(identity.get(key), f"target_identity.{key}")

    refs = packet.get("references") or []
    need(refs, "references", collection=True)
    ref_ids, roles, attachments = set(), set(), []
    appearance_views, geometry_views, production_views = set(), set(), set()
    appearance_roles = {"identity_primary", "identity_secondary", "costume_front", "costume_back", "side_reference", "face_closeup", "mask_headgear"}
    allowed_roles = set(packet_template["references"][0]["semantic_role"].split("|"))
    for reference in refs:
        ref_id = reference.get("reference_id")
        if ref_id is not None and not isinstance(ref_id, str):
            raise ValueError("reference_id must be a string")
        need(ref_id, "reference_id")
        if ref_id in ref_ids:
            errors.append(f"Duplicate reference_id: {ref_id}")
        ref_ids.add(ref_id)
        role = reference.get("semantic_role")
        if role is not None and not isinstance(role, str):
            raise ValueError("semantic_role must be a string")
        if role not in allowed_roles:
            errors.append(f"Unknown semantic_role: {role}")
        roles.add(role)
        need(reference.get("provenance_id"), f"reference {ref_id} provenance_id")
        view = reference.get("view")
        if view is not None and not isinstance(view, str):
            raise ValueError("Reference view must be a string")
        if known(view):
            if role in appearance_roles:
                appearance_views.add(view)
            elif role == "geometry_template":
                geometry_views.add(view)
            elif role == "production_template":
                production_views.add(view)
        local = reference.get("local_path")
        if local is not None and not isinstance(local, str):
            raise ValueError("Reference local_path must be a string")
        if local:
            path = Path(local)
            if not path.is_absolute():
                path = (base_dir or Path.cwd()) / path
            if not path.is_file():
                errors.append(f"Reference file missing: {ref_id}")
            else:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                expected = reference.get("sha256")
                if expected != digest:
                    errors.append(f"Reference hash missing or mismatched: {ref_id}")
                attachments.append({"reference_id": ref_id, "sha256": digest})
        else:
            warnings.append(f"Reference {ref_id} has metadata only; attach and visually verify its asset before generation")
    if "geometry_template" not in roles:
        errors.append("A geometry_template reference is required")
    if kind == "minifigure" and "identity_primary" not in roles:
        errors.append("An identity_primary reference is required")
    required_views = brief.get("required_views") or []
    need(required_views, "required_views", collection=True)
    requires_appearance = kind == "minifigure" or output == "print_art"
    covered_views = appearance_views if requires_appearance else geometry_views | appearance_views
    for view in required_views:
        if view not in covered_views:
            errors.append(f"Missing reference view: {view}")

    features = packet.get("critical_features") or []
    need(features, "critical_features", collection=True)
    feature_names = set()
    for feature in features:
        name = feature.get("feature")
        if name is not None and not isinstance(name, str):
            raise ValueError("Feature descriptions must be strings")
        need(name, "critical feature description")
        if name in feature_names:
            errors.append(f"Duplicate critical feature: {name}")
        feature_names.add(name)
        if feature.get("priority") not in {"P0", "P1", "P2"}:
            errors.append(f"Invalid feature priority: {name}")
        evidence = feature.get("source_reference_ids") or []
        if not isinstance(evidence, list) or any(not isinstance(item, str) for item in evidence):
            raise ValueError("source_reference_ids must be a list of strings")
        need(evidence, f"feature {name} evidence", collection=True)
        for ref_id in evidence:
            if ref_id not in ref_ids:
                errors.append(f"Feature {name} cites missing reference {ref_id}")

    locks = packet.get("structural_locks") or {}
    for key in ("geometry_profile", "geometry_revision", "pose", "camera_view"):
        need(locks.get(key), f"structural_locks.{key}")
    parts = locks.get("canonical_parts") or []
    if not isinstance(parts, list):
        raise ValueError("canonical_parts must be a list")
    need(parts, "canonical_parts", collection=True)
    part_slots = set()
    for part in parts:
        if not isinstance(part, dict):
            errors.append("canonical_parts entries must identify slot, namespace, part_id, color_id and geometry_revision")
            continue
        for key in ("slot", "namespace", "part_id", "color_id", "geometry_revision"):
            need(part.get(key), f"canonical_parts.{key}")
        if part.get("slot") in part_slots:
            errors.append(f"Duplicate part slot: {part.get('slot')}")
        part_slots.add(part.get("slot"))
    required_slots = brief.get("required_part_slots") or []
    need(required_slots, "required_part_slots", collection=True)
    for slot in required_slots:
        if slot not in part_slots:
            errors.append(f"Missing canonical part slot: {slot}")
    if kind == "minifigure":
        need((packet.get("official_style") or {}).get("profile"), "official_style.profile")
        translation = packet.get("mask_translation") or {}
        allowed_routes = set(packet_template["mask_translation"]["route"].split("|"))
        if translation.get("route") not in allowed_routes:
            errors.append("Select an explicit mask/headgear translation route")
    transformation = packet.get("transformation") or {}
    need(transformation.get("target"), "transformation.target")
    if transformation.get("preserve_by_default") is not True:
        errors.append("preserve_by_default must be true; enumerate allowed edits")
    allowed = packet.get("allowed_changes") or []
    forbidden = packet.get("forbidden_changes") or []
    if set(allowed) & set(forbidden):
        errors.append("The same change cannot be both allowed and forbidden")
    rendering = packet.get("rendering") or {}
    for key in ("view", "projection", "lighting", "background", "framing"):
        need(rendering.get(key), f"rendering.{key}")
    if rendering.get("view") != locks.get("camera_view"):
        errors.append("rendering.view must match structural_locks.camera_view")
    output_spec = packet.get("output") or {}
    contract = contracts["outputs"].get(output, {})
    target_type = output_spec.get("target_type")
    if target_type not in contract.get("target_types", []):
        errors.append("output.target_type must match the selected output contract")
    for field in contract.get("preflight_required", []):
        value = brief
        for key in field.split("."):
            value = value.get(key) if isinstance(value, dict) else None
        need(value, field, collection=field.endswith(".template_boundaries"))
    for role in contract.get("reference_roles", []):
        if role not in roles:
            errors.append(f"Output contract requires a {role} reference")
    if brief.get("unresolved_conflicts"):
        errors.append("Resolve evidence conflicts before compilation")
    for unknown in brief.get("unknowns") or []:
        warnings.append(f"Unresolved design detail: {unknown}; do not invent it")

    manifest = {
        "schema_version": VERSION, "brief_id": brief.get("brief_id"), "target_kind": kind,
        "output_contract": output, "brief_sha256": content_hash(brief),
        "contracts_sha256": content_hash(contracts), "protocol_sha256": content_hash(protocol),
        "status": "blocked" if errors else "ready_for_metadata_review",
        "errors": errors, "warnings": warnings, "verified_local_attachments": attachments,
        "view_coverage": {"required": required_views, "appearance": sorted(appearance_views),
                          "geometry": sorted(geometry_views), "production": sorted(production_views),
                          "required_axis": "appearance" if requires_appearance else "geometry_or_appearance"},
        "required_output_fields": contracts["outputs"].get(output, {}).get("required", []),
        "required_deliverables": contracts["outputs"].get(output, {}).get("deliverables", []),
        "automatic_reject_conditions": contracts["automatic_reject_conditions"],
        "human_review": contracts["human_review"],
        "feature_checklist": [{"feature": f.get("feature"), "priority": f.get("priority"),
                               "source_reference_ids": f.get("source_reference_ids"), "result": "unreviewed"}
                              for f in features],
    }
    prompt = None
    if not errors:
        sections = [f"Brickmen brief {brief['brief_id']} ({kind}; {output}).",
                    "Use the attached references in their stated roles. Preserve exact source appearance, part IDs, colors, geometry and views.",
                    "Keep unknown details unresolved. Do not mirror asymmetric features or substitute moulds. A concept is not a calibrated production master."]
        # One structured packet serves ChatGPT and local workflows; avoid a second prompt schema.
        for key in ("target_identity", "references", "critical_features", "transformation", "structural_locks",
                    "official_style", "mask_translation", "allowed_changes", "forbidden_changes", "rendering", "output", "evaluation"):
            if key in packet:
                sections.append(f"{key}:\n" + json.dumps(packet[key], indent=2, ensure_ascii=False))
        sections.append("Unknowns:\n" + json.dumps(brief.get("unknowns", []), ensure_ascii=False))
        sections.append("Required output metadata:\n" + json.dumps(manifest["required_output_fields"]))
        prompt = "\n\n".join(sections) + "\n"
    return manifest, prompt


def compile_brief(brief, data_dir=DATA, base_dir=None):
    """Return a blocked preflight for malformed inputs, consistently with the CLI."""
    try:
        return _compile_brief(brief, data_dir, base_dir)
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
        return {"schema_version": VERSION, "status": "blocked", "errors": [f"Invalid brief: {exc}"], "warnings": []}, None


def new_brief(kind, data_dir=DATA):
    packet = read_json(data_dir / "chatgpt-control-generation-schema.json")["control_generation_packet"]
    # Provider-specific run metadata belongs to the actual generation, not preflight.
    for key in ("experiment_id", "run_id", "provider", "provider_surface", "generated_at", "compiler_version", "prompt_schema_version"):
        packet.pop(key, None)
    slots = ["head", "torso", "hips_legs", "arm_left", "arm_right", "hand_left", "hand_right"] if kind == "minifigure" else ["primary"]
    packet["structural_locks"]["geometry_revision"] = ""
    packet["output"]["target_type"] = "concept_render" if kind == "minifigure" else "part_render"
    packet["structural_locks"]["canonical_parts"] = [
        {"slot": slot, "namespace": "", "part_id": "", "color_id": "", "geometry_revision": ""}
        for slot in slots
    ]
    packet["references"][0].update({"semantic_role": "identity_primary" if kind == "minifigure" else "geometry_template", "view": "front", "local_path": "", "sha256": ""})
    if kind == "part":
        packet["target_identity"] = {"subject": "", "source_appearance": "", "accessories": []}
        packet.pop("official_style", None)
        packet.pop("mask_translation", None)
    return {"schema_version": VERSION, "brief_id": "", "target_kind": kind,
            "output_contract": "concept_render" if kind == "minifigure" else "part_render",
            "required_views": ["front", "rear", "left", "right"], "required_part_slots": slots,
            "unknowns": [], "unresolved_conflicts": [], "generation_packet": packet}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--input", type=Path)
    mode.add_argument("--init", choices=["minifigure", "part"])
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.init:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        target = args.output_dir / "brief.json"
        if target.exists():
            parser.error("brief.json already exists; use another directory")
        target.write_text(json.dumps(new_brief(args.init), indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"template": str(target), "status": "requires_completion"}))
        return 0
    if args.output_dir.resolve() == args.input.resolve().parent:
        parser.error("Use a separate output directory")
    try:
        brief = read_json(args.input)
        manifest, prompt = compile_brief(brief, base_dir=args.input.resolve().parent)
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
        manifest = {"schema_version": VERSION, "status": "blocked", "errors": [f"Invalid brief: {exc}"], "warnings": []}
        prompt = None
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "preflight.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    prompt_path = args.output_dir / "prompt.txt"
    if prompt is not None:
        prompt_path.write_text(prompt, encoding="utf-8")
    elif prompt_path.exists():
        prompt_path.unlink()  # A failed rerun must not leave a stale usable prompt.
    print(json.dumps({"status": manifest["status"], "errors": manifest["errors"], "warnings": manifest["warnings"]}, indent=2))
    return 2 if manifest["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
