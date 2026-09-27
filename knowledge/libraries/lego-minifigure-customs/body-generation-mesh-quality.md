# Generated Body Mesh Quality Preflight

Brickmen now audits mapped provider meshes independently of visual fit and mechanical keep-outs:

- `data/body-generation-mesh-quality.schema.json`
- `tools/geometry/validate_body_generation_mesh_quality.py`

Checks include:
- boundary edges / open meshes;
- non-manifold edges;
- inconsistent adjacent winding;
- duplicate triangles;
- degenerate triangles;
- disconnected face components;
- Euler characteristic;
- signed/absolute enclosed volume;
- closed two-manifold candidacy.

When a provider→Brickmen-mm transform is present, volume is reported in mm³. Otherwise topology can still be audited in provider units.

## Why this is separate

A mesh can:
- match the target silhouette;
- map to the right component slot;
- leave a hardware keep-out empty;

and still be unprintable because it is open or non-manifold.

Likewise, a watertight mesh can still have the wrong proportions.

Brickmen keeps these gates independent so repairs do not blur their causes.

## Still not DFM

Topology preflight does **not** yet validate:
- self-intersections;
- minimum wall thickness;
- trapped/internal shells;
- overhang/support needs;
- feature-size limits;
- resin drain holes;
- process compensation;
- strength;
- connector force/torque behavior.

Those remain later DFM/process-specific stages.
