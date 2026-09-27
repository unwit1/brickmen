# Reference Fitting Pipeline

Created: 2026-09-27

## Purpose

Turn catalog images, canonical renders and physical measurements into **auditable parameter fits** for Brickmen body skeletons.

The fitter is not a reverse-engineering shortcut for connector geometry.

It answers:

> Which allowed Brickmen body proportions best explain this reference?

It does **not** answer:

> What diameter should the shoulder pin be?

## Implemented tools

### Skeleton fitter

`tools/geometry/fit_body_skeleton.py`

Inputs:
- BodySkeleton JSON;
- BodyReferenceLandmarkObservation JSON.

Optimizes only bounded skeleton parameters.

Outputs:
- fitted parameters;
- normalized RMSE;
- per-landmark residuals;
- bound hits;
- diagnostic flags;
- target visual height where a catalog range is known.

### Batch fitter

`tools/geometry/fit_body_skeleton_batch.py`

Runs every pair in:
`data/reference-landmarks/manifest.json`.

## Current seed references

- Alpha Toys AF325 Venom -> Broad
- Alpha Toys AF345 Hulk -> XL
- LEGO SH0371 Hulk -> Giant
- KDL K2302 Thing -> XL
- LEGO Axl -> Broad stress test

These are manually estimated seed landmarks and require later reannotation.

## Critical distinction: skeleton vs visual envelope

A reference image contains at least two different kinds of width information.

### Mechanical/skeletal landmarks

Examples:
- neck center;
- shoulder pivot;
- wrist center;
- hip center.

These should influence BodySkeleton fitting.

### Visual-envelope landmarks

Examples:
- outside of shoulder armor;
- deltoid silhouette;
- widest chest point;
- abdomen edge;
- forearm outer edge;
- hand envelope.

These should influence BodyStyleProfile / shell envelopes.

**Do not use a visual shoulder edge as the shoulder joint center.**

This distinction is especially important for:
- Axl armor;
- Alpha Venom;
- Bane armor/tubes;
- Thanos shoulder armor;
- Thing rock mass;
- Blob/Kingpin abdomen.

## Seed fitting results

The initial manual reference set produces:

| Reference | Skeleton | RMSE | Result |
| --- | --- | ---: | --- |
| LEGO Giant Hulk | Giant | 0.035 | usable |
| Alpha AF345 Hulk | XL | 0.047 | usable |
| KDL K2302 Thing | XL | 0.055 | weak/review |
| Alpha AF325 Venom | Broad | 0.067 | weak/review |
| Axl | Broad | 0.084 | mismatch/review |

These values only evaluate the current **manual seed landmarks and v0 parameterization**.

They are not quality scores for the products or architectures.

## What the boundary hits tell us

### Giant

Only arm length saturates in the current seed fit.

Interpretation:
the base Giant skeleton is close enough to continue into envelope and joint work.

### XL / Alpha 7 cm

Arm length and lower-body compression reach bounds.

Research:
- create independent thigh/leg-length parameters;
- verify whether current image crop exaggerates apparent upper-body length;
- add head-size fitting.

### Broad / Venom

Several parameters reach bounds.

Do **not** immediately widen the shoulder joint.

First:
1. reannotate actual pivot;
2. annotate shoulder **outer silhouette** separately;
3. fit shell envelope;
4. then decide whether joint spacing requires expansion.

### Broad / Axl

Current fit is outside the v0 design space.

Axl's armor heavily obscures joint centers.

Treat it as:
- a valuable shell-envelope reference;
- a low-confidence skeleton-pivot reference.

## Next fitting data model

Reference observation should evolve into:

```
BodyReferenceObservation
  skeletal_landmarks
  silhouette_landmarks
  region_widths
  component_boundaries
  known_scale
  confidence
  view/camera
```

Then:

```
skeletal landmarks -> BodySkeleton fitter
silhouette/region measurements -> envelope fitter
surface features -> BodyStyleCompiler
physical metrology -> EngineeringSkeleton / JointCartridge
```

## Architecture fit should remain comparative

For an unresolved body such as KDL:

run the same reference against:
- Broad;
- Mid;
- XL;
- Giant;

then compare:
- residual;
- number of bound hits;
- topology mismatch;
- known scale;
- visual style.

This creates an evidence-backed architecture candidate ranking without pretending the nearest visual skeleton proves mechanical identity.

## Planned automatic annotation

Future front-image pipeline:

```
image
 -> figure segmentation
 -> body bbox
 -> landmark detector
 -> component masks
 -> silhouette extrema
 -> confidence
 -> reference JSON
 -> skeleton + envelope fit
```

Until a validated landmark model exists, manually reviewed annotations remain preferable to confident automated noise.

## Production boundary

No catalog-image fit can promote:
- socket diameter;
- pin diameter;
- bar diameter;
- insertion depth;
- friction torque;
- material clearance.

Those come only from engineering/physical evidence.
