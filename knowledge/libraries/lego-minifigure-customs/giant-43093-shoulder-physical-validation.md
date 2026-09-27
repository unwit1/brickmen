# Giant 43093 Shoulder Physical Validation Plan

Machine-readable plan:
- `data/validation-plans/giant-43093-shoulder-physical-validation-v0.json`

Joint-contact status:
- `data/joint-contact-regions/brickmen-giant-v0.json`

## Why this exists

The pinned LDraw work establishes:
- reference shape;
- pivot placement;
- hardware identity;
- a useful fixed-mm keep-out.

It does **not** establish:
- real contact geometry;
- fit/interference;
- friction;
- force;
- torque;
- wear;
- intentional collision/contact zone.

Exact pose-wise collision also needs to know where connected parts are intentionally allowed to touch. Brickmen will not guess that region from the LDraw hardware bounding box.

## Protocol strategy

The validation plan separates:
1. hardware metrology;
2. official torso/arm mating metrology;
3. official functional force/torque/play baseline;
4. cycle/wear characterization;
5. printed candidate process/material/orientation matrix;
6. pre-registered qualification criteria.

Initial sample-count/checkpoint suggestions are for evidence collection, not automatic acceptance thresholds.

The actual production thresholds remain intentionally undefined until the baseline distribution and use requirements exist.

## Contact-region consequence

Once physical mating geometry is validated, the resulting intentional contact zone can be promoted into the joint-contact record.

Only then should exact pose-wise triangle collision suppress intersections inside that zone.

Intersections elsewhere remain collisions.
