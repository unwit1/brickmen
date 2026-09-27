# Provider Frame Alignment Candidates

Provider meshes do not arrive in a guaranteed Brickmen coordinate frame or unit scale.

Brickmen now has a candidate estimator:

- `data/body-provider-alignment-candidates.schema.json`
- `tools/geometry/propose_body_provider_alignment.py`

## What it can infer from bounds

Given:
- a mapped component slot;
- its Brickmen visual-envelope target;
- a provider mesh bounding box;

the estimator searches:
- axis permutations;
- orientation-preserving axis sign combinations;
- one uniform scale;
- translation to the target component center.

It ranks candidates by dimension-shape error.

## What bounds cannot infer safely

Bounding boxes usually cannot determine:
- left vs right;
- front vs back;
- whether a visually symmetric mesh is rotated 180°;
- semantic feature alignment.

Therefore sign-equivalent candidates remain explicit.

The current estimator normally sets:

`automatic_promotion_allowed: false`

until richer evidence removes the ambiguity.

## Intended next evidence

Promote a transform only after one or more:
- structural-guide render comparison;
- semantic landmark matching;
- component-local feature detection;
- user-reviewed orientation;
- ICP/point-cloud registration against a stronger target mesh.

The selected matrix can then be supplied to the provider-output mapping and used by the geometry gate.

This separates useful automation from silent coordinate assumptions.
