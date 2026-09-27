# Provider Geometry Validation Gate

After component-slot mapping, Brickmen now has a **transform-aware coarse geometry gate**:

- `data/body-generation-geometry-validation.schema.json`
- `tools/geometry/validate_body_generation_provider_geometry.py`
- mesh bounds: `tools/geometry/inspect_mesh_bounds.py`

## Required transform

Provider meshes have unknown:
- units;
- scale;
- origin;
- orientation.

Therefore Brickmen refuses visual-envelope conformance checks until a 4×4 row-major provider→Brickmen-mm transform is explicitly supplied for the component.

There is no silent “assume meters,” “assume centimeters,” or “center automatically” rule in the validation gate.

## Current supported bounds formats

Dependency-free:
- OBJ;
- STL;
- ASCII PLY;
- glTF/GLB when POSITION accessors expose min/max metadata.

## Coarse visual check

For each component slot:
1. combine its Brickmen visual envelopes into an expected AABB;
2. inspect the provider mesh AABB;
3. transform it into Brickmen mm;
4. compare center/size to the expected visual region with explicit tolerance.

This detects:
- wildly wrong scale;
- wrong axis/orientation;
- extreme translation;
- tiny or oversized parts;
- slot-mapping mistakes.

## Mechanical and articulation review flags

The gate also reports AABB intersection with:
- fixed mechanical keep-outs scoped to that component;
- articulation sweeps belonging to other moving components.

These are **potential** conflicts only.

A shell AABB can contain a valid internal cavity, so bounding-box overlap cannot prove actual material intersection.

The next exact stage should use:
- triangle-vs-keepout intersection;
- boolean subtraction validation;
- pose-wise triangle collision;
- clearance margins from validated engineering data.

## Authority boundary

Passing status:

`bbox_geometry_plausible_requires_exact_collision_validation`

It never means:
- printable;
- mechanically compatible;
- collision-free;
- production approved.
