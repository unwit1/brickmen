from pathlib import Path

import pytest

from tools.geometry.compile_body_generation_provider_job import (
    compile_provider_job,
    load_json,
    provider_map,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "libraries" / "lego-minifigure-customs" / "data"


def registry():
    return load_json(BASE / "body-generation-provider-registry.json")


def conditioning():
    return load_json(
        BASE
        / "generation-conditioning"
        / "brickmen-giant-official-cad-v0.json"
    )


def test_partcrafter_job_uses_required_component_count():
    providers = provider_map(registry())
    job = compile_provider_job(
        conditioning(),
        providers["partcrafter"],
        source_image="input.png",
    )
    assert job["native_arguments"]["num_parts"] == 7
    assert job["source_image"] == "input.png"
    assert len(job["component_slots"]["required"]) == 7
    assert job["production_geometry_authority"] is False
    assert job["contains_nonproduction_mechanical_constraints"] is True


def test_postprocessor_provider_keeps_same_authority_boundary():
    providers = provider_map(registry())
    job = compile_provider_job(conditioning(), providers["particulate"])
    assert job["provider_role"] == "mesh_to_articulation_inference_critic"
    assert job["mechanical_review_required"] is True
    assert job["pipeline_stage"]=="post_generation_critic"
    assert job["requires_component_slot_mapping"] is False
    assert any(
        "cannot overwrite validated Brickmen" in text
        for text in job["output_acceptance_rules"]
    )


def test_provider_registry_has_unique_ids():
    ids = [item["provider_id"] for item in registry()["providers"]]
    assert len(ids) == len(set(ids))
    assert {"partcrafter", "partpacker", "pact", "particulate", "sam_3d_objects"} <= set(ids)


def test_visual_baseline_does_not_require_component_slot_mapping():
    providers = provider_map(registry())
    job = compile_provider_job(conditioning(), providers["sam_3d_objects"])
    assert job["pipeline_stage"]=="baseline_generator"
    assert job["requires_component_slot_mapping"] is False
    assert job["execution_interface"]["adapter_status"]=="runnable_brickmen_python_api_visual_baseline"
    assert job["output_contract"]["kind"]=="masked_gaussian_reconstruction"
