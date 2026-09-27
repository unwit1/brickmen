# Pose-Sampled Generated-Body Collision Validation

Brickmen now has a real triangle-level articulated collision sampler:

- `data/body-generation-pose-collision-validation.schema.json`
- `tools/geometry/validate_body_generation_pose_collisions.py`

## Motion model

For every skeleton joint with associated visual-envelope component slots, the validator:

1. loads mapped provider meshes;
2. applies the explicit provider→Brickmen-mm transform;
3. identifies all component slots moved by that joint;
4. rotates those slots around the Brickmen pivot/axis;
5. samples the declared joint range;
6. checks moving triangles against all static component meshes.

For the Giant shoulders, the downstream hand is included with the arm during shoulder motion.

## Contact suppression is evidence-gated

A triangle collision is suppressible only when:
- the joint record explicitly declares that component pair;
- a contact region exists;
- the region is `validated_prototype` or `production_approved`;
- the collision witness lies inside that region.

These do **not** suppress collisions:
- pending contact records;
- candidate regions;
- generic LDraw part bounds;
- same-joint membership by itself.

This prevents a shoulder or wrist from being declared collision-free merely because the collision happens near the joint.

## Discrete sampling limitation

This is pose-sampled collision, not continuous collision detection.

Passing means:

`sampled_pose_collision_gate_passed`

It does not prove that the continuous path between sampled angles is collision-free.

A later continuous stage should use:
- conservative continuous collision detection; or
- adaptive interval subdivision with a mathematically conservative bound.

## Current Giant implication

The Giant contact record intentionally has no validated shoulder/wrist contact volumes yet.

Therefore real generated Giant meshes can be tested immediately, but any triangle intersection at those joints remains a disallowed collision until physical interface validation supplies an allowed-contact region.
