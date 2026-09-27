# Body Articulation Sweep Conditioning

Brickmen now derives conservative visual articulation volumes from the same generation-conditioning payload used for 3D shell generation.

Core:
- `data/body-articulation-sweep.schema.json`
- `tools/geometry/compile_body_articulation_sweeps.py`

## Purpose

A part-aware generator should not make a torso visually correct in the neutral pose but fill the space an arm or hand needs when it rotates.

The sweep compiler uses:
- selected Brickmen joint pivot;
- selected joint axis/range;
- visual envelope associated with that joint;
- target body scale;
- fixed-mm mechanical placements at the same pivot.

It samples the moving envelope across the joint range and produces a conservative AABB.

## Authority

These are **visual/collision conditioning volumes**.

They may be used to:
- reserve shell clearance during generation;
- reject obvious interpenetration;
- prioritize post-generation mesh trimming;
- compare alternative visual shell candidates.

They may not establish:
- real physical clearance;
- pin/socket tolerance;
- torque;
- wear;
- exact collision geometry;
- final articulation range.

Those require exact component meshes and physical validation.

## Conservative approximation

Current v0:
- rotates the moving envelope center/endpoint about the selected joint axis;
- expands the arc by a conservative envelope radius;
- includes the joint pivot for between-node arm/lower-body envelopes;
- reports normalized and target-mm swept boxes.

Later versions should add:
- oriented capsule/box sweeps instead of isotropic expansion;
- exact triangle-mesh collision sweeps;
- self-collision against torso/head/lower-body meshes;
- validated physical clearance margins;
- pose-specific provider guide renders.

## Giant value

For Giant shoulder generation this closes an important gap:

```
shoulder pivot
+ arm visual envelope
+ ±105° joint range
+ fixed-mm 43093 keep-out placement
 -> conservative shoulder/arm generation exclusion volume
```

The body can still use original Brickmen proportions and shell shapes while keeping motion space explicit.
