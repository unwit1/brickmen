# Exact Mechanical Keep-out Validation

Brickmen now has an exact-geometry gate for fixed reference keep-outs:

- `data/body-generation-exact-keepout-validation.schema.json`
- `tools/geometry/validate_body_generation_exact_keepouts.py`
- triangle extraction: `tools/geometry/inspect_mesh_triangles.py`

## What it checks

For each mapped component affected by a mechanical keep-out:

1. load real mesh triangles;
2. apply the explicit provider→Brickmen-mm transform;
3. run triangle-vs-AABB separating-axis tests;
4. detect surface crossings;
5. when the mesh is a closed two-manifold candidate, ray-test the keep-out center and corners to detect a keep-out completely buried inside solid material.

Possible outcomes include:
- `keepout_geometrically_empty`;
- `keepout_surface_intersection`;
- `keepout_inside_solid_material`;
- `inconclusive_open_or_nonmanifold_mesh`.

## Why inside-solid testing matters

A shoulder hardware box can sit entirely inside a solid torso mesh without touching any triangle.

Surface intersection alone would miss that.

For a closed shell/solid boundary, point-in-mesh sampling catches the buried-volume case.

## Limits

This exact gate validates only the reference keep-out volume.

It still does not establish:
- socket dimensions;
- press/friction fit;
- clearance margin;
- torque;
- wear;
- material behavior;
- exact articulation across all poses.

Passing means the tested generated mesh leaves the current reference keep-out geometrically empty under the supplied transform.

The 43093 profile remains reference-only until physical validation promotes a real deterministic shoulder interface.
