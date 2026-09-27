from pathlib import Path

from tools.geometry.compile_body_articulation_sweeps import compile_articulation_sweeps
from tools.geometry.render_body_generation_guides import (
    build_guide_pack,
    load_json,
    render_guide_svg,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"knowledge"/"libraries"/"lego-minifigure-customs"/"data"


def giant():
    return load_json(BASE/"generation-conditioning"/"brickmen-giant-official-cad-v0.json")


def test_front_guide_contains_slots_and_mechanical_keepouts():
    c=giant()
    sweeps=compile_articulation_sweeps(c)
    svg=render_guide_svg(c,view="front",sweeps=sweeps)
    assert "<svg" in svg
    assert 'data-slot="arm_l_shell"' in svg
    assert "lego_giant_43093_shoulder_reference_v0" in svg
    assert 'data-joint="shoulder_l"' in svg
    assert "source-image" not in svg.lower()


def test_side_guide_contains_depth_sweep():
    c=giant()
    sweeps=compile_articulation_sweeps(c)
    svg=render_guide_svg(c,view="side",sweeps=sweeps)
    assert "view=side" in svg
    assert 'data-joint="shoulder_l"' in svg


def test_guide_pack_manifest_is_nonproduction(tmp_path: Path):
    c=giant()
    sweeps=compile_articulation_sweeps(c)
    manifest=build_guide_pack(c,tmp_path,sweeps=sweeps)
    assert manifest["production_geometry_authority"] is False
    assert manifest["source_image_embedded"] is False
    assert len([x for x in manifest["component_slots"] if x["required"]])==7
    assert (tmp_path/"front.svg").exists()
    assert (tmp_path/"side.svg").exists()
