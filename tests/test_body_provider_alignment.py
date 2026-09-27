from pathlib import Path

import pytest

from tools.geometry.propose_body_provider_alignment import (
    propose_alignment_candidates,
)


def conditioning():
    return {
        "skeleton_control":{
            "nodes":{
                "chest":{"position_mm_at_target_height":[10,20,30]}
            }
        },
        "visual_envelopes":[
            {
                "envelope_id":"torso",
                "component_slot_id":"torso_shell",
                "shape":"box",
                "center_node":"chest",
                "size_mm_at_target_height":[20,10,30],
            }
        ],
    }


def write_box(path: Path, size):
    sx,sy,sz=size
    pts=[
        (x,y,z)
        for x in (0,sx)
        for y in (0,sy)
        for z in (0,sz)
    ]
    path.write_text(
        "\n".join(f"v {x} {y} {z}" for x,y,z in pts)+"\n",
        encoding="utf-8",
    )


def test_alignment_recovers_scale_and_axis_permutation_but_reports_sign_ambiguity(tmp_path: Path):
    # Provider dimensions [3,2,1], target [20,10,30] -> target axes draw
    # provider [Y,Z,X] with uniform scale 10.
    mesh=tmp_path/"provider.obj"
    write_box(mesh,[3,2,1])
    result=propose_alignment_candidates(
        conditioning(),mesh,"torso_shell",candidate_limit=24
    )
    best=result["candidates"][0]
    assert best["shape_log_rmse"]==pytest.approx(0,abs=1e-12)
    assert best["uniform_scale_provider_units_to_mm"]==pytest.approx(10)
    assert best["axis_permutation_target_from_provider"]==[1,2,0]
    assert result["ambiguity"]["sign_or_front_back_ambiguous"] is True
    assert result["automatic_promotion_allowed"] is False


def test_missing_slot_visual_target_rejected(tmp_path: Path):
    mesh=tmp_path/"provider.obj"; write_box(mesh,[1,1,1])
    with pytest.raises(ValueError,match="No visual target"):
        propose_alignment_candidates(conditioning(),mesh,"arm_l_shell")
