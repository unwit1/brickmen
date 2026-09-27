from pathlib import Path

import pytest

from tools.geometry.measure_reference_mesh_profile import (
    load_obj_triangles,
    measure_profile,
    triangle_plane_intersections,
)


def cube_obj() -> str:
    return """# 2 x 4 x 6 box
v -1 -4 -3
v 1 -4 -3
v 1 0 -3
v -1 0 -3
v -1 -4 3
v 1 -4 3
v 1 0 3
v -1 0 3
f 1 2 3 4
f 5 8 7 6
f 1 5 6 2
f 2 6 7 3
f 3 7 8 4
f 5 1 4 8
"""


def test_plane_intersection_crosses_triangle_edges():
    tri = ((0, -2, 0), (2, 0, 0), (0, 0, 2))
    points = triangle_plane_intersections(tri, axis=1, coordinate=-1)
    assert any(p[0] == pytest.approx(1.0) for p in points)
    assert any(p[2] == pytest.approx(1.0) for p in points)


def test_cube_profile_uses_negative_y_as_up(tmp_path: Path):
    path = tmp_path / "cube.obj"
    path.write_text(cube_obj(), encoding="utf-8")
    triangles = load_obj_triangles(path)
    result = measure_profile(triangles, samples=5)

    assert result["body_height"] == pytest.approx(4.0)
    assert result["overall"]["front_span"] == pytest.approx(2.0)
    assert result["overall"]["side_span"] == pytest.approx(6.0)
    middle = next(x for x in result["slices"] if x["height_norm"] == 0.5)
    assert middle["plane_coordinate"] == pytest.approx(-2.0)
    assert middle["front"]["span"] == pytest.approx(2.0)
    assert middle["front"]["span_over_body_height"] == pytest.approx(0.5)
    assert middle["side"]["span"] == pytest.approx(6.0)
    assert middle["side"]["span_over_body_height"] == pytest.approx(1.5)


def test_extra_height_is_included(tmp_path: Path):
    path = tmp_path / "cube.obj"
    path.write_text(cube_obj(), encoding="utf-8")
    result = measure_profile(
        load_obj_triangles(path),
        samples=3,
        extra_heights=[0.70880344668549],
    )
    assert any(
        x["height_norm"] == pytest.approx(0.70880344668549)
        for x in result["slices"]
    )
