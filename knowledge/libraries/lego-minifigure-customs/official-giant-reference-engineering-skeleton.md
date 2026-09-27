# Official Giant Reference Engineering Skeleton

Research snapshot: 2026-09-27

Brickmen now keeps an explicit **official-reference engineering skeleton** separate from the original `brickmen_giant_v0` design skeleton.

Machine-readable record:
- `data/engineering-skeletons/lego-giant-modular-2303.json`
- schema: `data/reference-engineering-skeleton.schema.json`

## Why a second skeleton is necessary

The official Giant arm is not well represented by a straight front-view shoulder→wrist line.

The pinned LDraw assembly establishes the left arm's intrinsic shoulder→hand-socket vector, in the Brickmen semantic frame, as approximately:

```
[ +12 mm lateral,
  -16 mm depth,
  -16 mm vertical ]
```

Normalized by the official reference height:

```
[ +0.1687, -0.2250, -0.2250 ]
length ≈ 0.3601 body heights
```

The right arm mirrors X.

This means the physical/visual component is a **fixed bent 3D arm** whose hand attachment sits forward/back as well as downward from the shoulder.

The current Brickmen Giant generation skeleton is intentionally simpler and keeps its own design freedom. The official reference therefore remains comparison/supervision evidence rather than silently rewriting the Brickmen architecture.

## Component envelope evidence

Pinned official component profiles also give intrinsic visual mass.

### Arm 10154 / 10124

Central cross-section mean, normalized by full official body height:
- front width ≈ 0.1818;
- side depth ≈ 0.2798.

Overall component bounding spans:
- front ≈ 0.2510;
- side ≈ 0.3570.

The overall box includes extrema and should not be confused with a typical cross-section.

### Hand 10127 / 10126

Central cross-section mean:
- front width ≈ 0.1743 body heights;
- side depth ≈ 0.2481.

Overall bounding spans:
- front ≈ 0.1916;
- side ≈ 0.3272.

The hand's local profile is separate from its default assembly rotation.

## Generation consequence

Future body conditioning should support:
- bone/component-aligned arm envelopes;
- independent arm cross-section bulk;
- independent hand envelopes;
- explicit component-local frames;
- architecture-specific fixed-bend or segmented limb topology.

This is better than enlarging a generic torso box or treating arm width as shoulder spacing.

## Engineering consequence

Keep three questions independent:

1. **Where are the reference component frames?**
   Answerable from official CAD.

2. **What visual mass does the arm/hand occupy?**
   Answerable from reference mesh profiles.

3. **What socket/pin dimensions and force/torque behavior are production-correct?**
   Requires physical validation.

Only the third question can authorize manufacturing-critical joint geometry.
