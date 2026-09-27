import math
from pathlib import Path

import pytest

from tools.geometry.compile_body_articulation_sweeps import (
    compile_articulation_sweeps,
    load_json,
    rotate_about_axis,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"knowledge"/"libraries"/"lego-minifigure-customs"/"data"


def giant():
    return load_json(
        BASE/"generation-conditioning"/"brickmen-giant-official-cad-v0.json"
    )


def test_rodrigues_rotation_about_x():
    out=rotate_about_axis([0,1,0],[0,0,0],[1,0,0],90)
    assert out[0]==pytest.approx(0)
    assert out[1]==pytest.approx(0,abs=1e-9)
    assert out[2]==pytest.approx(1)


def test_giant_shoulder_sweep_expands_into_depth():
    report=compile_articulation_sweeps(giant(),samples_per_joint=37)
    left=next(x for x in report["joint_sweeps"] if x["joint_id"]=="shoulder_l")
    box=left["combined_swept_aabb_normalized_body_height"]
    pivot=left["pivot_normalized_body_height"]
    assert box["min"][1] < pivot[1]
    assert box["max"][1] > pivot[1]
    assert left["mechanical_placements_at_pivot"]
    assert left["mechanical_placements_at_pivot"][0]["manufacturing_authority"] is False
    assert left["authority_class"]=="visual_articulation_sweep_nonproduction"


def test_visual_sweep_scales_with_body_but_fixed_hardware_does_not():
    payload=giant()
    report=compile_articulation_sweeps(payload)
    shoulder=next(x for x in report["joint_sweeps"] if x["joint_id"]=="shoulder_l")
    mech=shoulder["mechanical_placements_at_pivot"][0]["placement"]
    assert mech["reference_keepout_local_max_mm"]==pytest.approx([8,3.2,3.2])
    assert report["production_geometry_authority"] is False


def test_zero_range_lower_body_has_single_angle_sample():
    report=compile_articulation_sweeps(giant(),samples_per_joint=99)
    lower=next(x for x in report["joint_sweeps"] if x["joint_id"]=="lower_body")
    assert lower["visual_envelopes"][0]["samples"]==1
