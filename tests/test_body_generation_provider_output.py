from pathlib import Path

from tools.geometry.validate_body_generation_provider_output import (
    validate_output_mapping,
)


def job():
    return {
        "provider_id":"fake",
        "provider_job_id":"job-1",
        "component_slots":{
            "required":[
                {"slot_id":"torso_shell"},
                {"slot_id":"head_shell"},
            ],
            "optional":[{"slot_id":"lower_body_shell"}],
        },
    }


def run(paths, *, succeeded=True):
    return {
        "provider_id":"fake",
        "provider_job_id":"job-1",
        "mode":"executed",
        "return_code":0 if succeeded else 1,
        "execution_succeeded":succeeded,
        "discovered_outputs":[str(p) for p in paths],
    }


def test_complete_required_mapping_passes(tmp_path: Path):
    torso=tmp_path/"torso.glb"; torso.write_bytes(b"x")
    head=tmp_path/"head.glb"; head.write_bytes(b"x")
    result=validate_output_mapping(
        job(),run([torso,head]),
        [
            {"slot_id":"torso_shell","path":str(torso)},
            {"slot_id":"head_shell","path":str(head)},
        ],
    )
    assert result["acceptance"]["structurally_complete"] is True
    assert result["acceptance"]["missing_required_slots"]==[]
    assert result["production_geometry_authority"] is False


def test_no_assignments_requires_manual_mapping(tmp_path: Path):
    mesh=tmp_path/"part.glb"; mesh.write_bytes(b"x")
    result=validate_output_mapping(job(),run([mesh]),[])
    assert result["acceptance"]["status"]=="manual_component_mapping_required"
    assert set(result["acceptance"]["missing_required_slots"])=={
        "torso_shell","head_shell"
    }
    assert result["unassigned_outputs"]==[str(mesh)]


def test_duplicate_and_unknown_slots_fail(tmp_path: Path):
    a=tmp_path/"a.glb"; a.write_bytes(b"x")
    b=tmp_path/"b.glb"; b.write_bytes(b"x")
    result=validate_output_mapping(
        job(),run([a,b]),
        [
            {"slot_id":"torso_shell","path":str(a)},
            {"slot_id":"torso_shell","path":str(b)},
            {"slot_id":"mystery","path":str(a)},
        ],
    )
    assert result["acceptance"]["structurally_complete"] is False
    assert "torso_shell" in result["acceptance"]["duplicate_slots"]
    assert "mystery" in result["acceptance"]["unknown_slots"]


def test_failed_provider_run_cannot_pass(tmp_path: Path):
    torso=tmp_path/"torso.glb"; torso.write_bytes(b"x")
    head=tmp_path/"head.glb"; head.write_bytes(b"x")
    result=validate_output_mapping(
        job(),run([torso,head],succeeded=False),
        [
            {"slot_id":"torso_shell","path":str(torso)},
            {"slot_id":"head_shell","path":str(head)},
        ],
    )
    assert result["acceptance"]["structurally_complete"] is False
    assert "provider_execution_failed" in result["acceptance"]["errors"]
