# Conservative Continuous Rotation Collision Validation

Brickmen now has a continuous-motion collision proof stage for the declared single-axis joint rotations:

- `data/body-generation-continuous-collision-validation.schema.json`
- `tools/geometry/validate_body_generation_continuous_collisions.py`

## Proof idea

A rotating point around a fixed axis has each coordinate:

`C + A cos(theta) + B sin(theta)`

For an angle interval, the validator evaluates:
- both endpoints;
- every derivative root within the interval.

That yields exact coordinate minima/maxima for the rotating vertex over that interval.

For a triangle, unioning the three vertex bounds gives a conservative swept AABB. If that box does not intersect a static triangle AABB, collision is impossible anywhere in the interval.

If the boxes overlap, the interval is recursively subdivided.

## Validated-contact proof

If the **entire possible overlap AABB** is contained inside an explicitly validated joint-local contact AABB, the interval is also safe with respect to disallowed collision: any possible intersection must be inside the validated contact region.

Pending/candidate contact regions are ignored.

## Conservative failure modes

The validator does not force a yes/no answer.

If a near-contact interval remains ambiguous below the configured angular resolution/depth, it reports:

`unresolved_near_contact_interval`

and the gate does not pass.

That is preferable to claiming continuous clearance from sparse pose samples.

## Scope

A pass applies to:
- supplied meshes;
- supplied provider→Brickmen transforms;
- declared single-axis joint rotation;
- the validated contact regions supplied with the run.

It does not automatically cover:
- simultaneous multi-joint motion;
- flexible/deforming parts;
- tolerance stack-up;
- material compression;
- manufacturing variability;
- fit/torque/wear.

Those remain separate engineering concerns.
