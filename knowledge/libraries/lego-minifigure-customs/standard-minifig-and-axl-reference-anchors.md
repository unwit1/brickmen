# Standard Minifigure and Axl Reference Anchors

Research continuation: 2026-09-27

This pass closes a major ambiguity in the body-reference fitter: a wide visual silhouette does not necessarily imply a uniformly enlarged skeleton.

## Standard minifigure assembly frame

Official LDraw references provide a stable donor frame for ordinary minifigure components.

The official `973c01.dat` torso shortcut places:

- the base torso `973.dat` at the identity transform;
- right arm `3818.dat` at x = -15.552, y = 9, z = 0 LDU;
- left arm `3819.dat` at x = +15.552, y = 9, z = 0 LDU;
- the hands with explicit posed transforms.

The arm part files independently publish the same placement coordinates in their `!HELP` metadata. This makes the arm frames useful donor-component alignment anchors.

The official standing lower-body shortcut `73200b-f1.dat` places the hips at the origin and both standing leg parts at y = 12 LDU.

These values are **assembly-frame ground truth inside LDraw**, not physical tolerance or friction measurements.

## Axl is a hybrid architecture

BrickLink's Axl `nex069` inventory contains:

- a normal 970-family minifigure hips/legs assembly;
- dedicated armored arms `24101pb01` and `24104pb01`;
- modified oversized torso assembly `23763c01pb03`.

The current LDraw Parts Tracker model for `23763.dat` is especially informative even though it remains unofficial: it composes `973.dat` and `24128.dat` at the same identity transform.

That means the best current digital-twin hypothesis is:

```
standard lower body
  -> standard 973 torso core
     -> oversized 24128 upper shell
     -> dedicated Axl arms
```

This is more useful than classifying Axl merely as "midfig" or fitting the outer shoulder width as if it were a shoulder-joint span.

## Authority split

### Safe to use as reference-frame evidence

- official `973c01`, `3818`, `3819`, and `73200b-f1` LDraw assembly transforms;
- BrickLink's component inventory for Axl;
- the fact that the current 23763 LDraw draft explicitly combines 973 + 24128.

### Provisional only

The 23763/24128 LDraw work is still unofficial. The development thread includes source-mesh/draft coordinates for the Axl arm pinhole, but contributors also flag uncertainty and explicitly prefer real measurements.

Therefore:

- preserve those coordinates as hypotheses;
- do not turn them into a production ConnectorProfile;
- acquire/measure a physical Axl body before locking mechanical geometry.

## Consequence for Brickmen Broad

Axl should be a **hybrid-shell control**, not a generic scale target.

The Broad body pipeline should be able to hold these variables independently:

1. lower-body compatibility frame;
2. torso-core frame;
3. outer shoulder/chest envelope;
4. special-arm attachment frame;
5. head/helmet envelope;
6. surface/style profile.

This allows a character to become much broader without accidentally scaling standard-compatible lower-body or donor interfaces.

## Consequence for fitting and generation

Reference fitting should now prefer:

1. component-frame evidence for known donor parts;
2. physical measurements when available;
3. visual landmarks for unknown pivots;
4. silhouette observations for mass/shape only.

The next fitter revision should support fixed/reference anchors so a standard donor frame can remain locked while only shell/envelope parameters are optimized.

## Sources

- Official LDraw torso assembly: https://library.ldraw.org/parts/14193
- Official LDraw right arm: https://library.ldraw.org/parts/7182
- Official LDraw left arm: https://library.ldraw.org/parts/7186
- Official LDraw standing lower body: https://library.ldraw.org/parts/26214
- BrickLink Axl nex069 inventory: https://www.bricklink.com/catalogItemInv.asp?M=nex069
- Current unofficial LDraw 23763: https://library.ldraw.org/parts/51698
- LDraw 23763 development thread: https://forums.ldraw.org/thread-28851.html
