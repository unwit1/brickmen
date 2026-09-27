# Official Giant Reference Anchors

Research snapshot: 2026-09-27

The Giant reference fitting can now use explicit LDraw anchor metadata in addition to catalog-image landmarks.

## Body shoulder sockets

Official LDraw Bigfig Hulk body `10128.dat` contains:

```
!HELP Arm sockets at x = +/-40, y = -126
```

This establishes a reference shoulder-center separation of:

```
80 LDU
≈ 32 mm at the normal 0.4 mm/LDU conversion
```

This is substantially stronger evidence than estimating shoulder pivots from the outside of a rendered deltoid.

It remains **reference CAD geometry**, not a tolerance measurement.

## Arm hand sockets

Official left BigFig arm `10154.dat` publishes:

```
Hand socket at x = 30, y = 40, z = -40
```

Official right arm `10124.dat` mirrors that X coordinate:

```
Hand socket at x = -30, y = 40, z = -40
```

This provides canonical local wrist/hand attachment frames for digital-twin reconstruction.

## Fitting policy

For official Giant:

### Prefer
1. explicit LDraw component anchors;
2. component assembly transforms;
3. physical measurements;
4. catalog image landmarks.

### Image landmarks remain useful for
- head/body visual proportions;
- silhouette;
- pose;
- decoration/surface regions.

They should no longer be the primary source for known shoulder/wrist centers when better geometry evidence exists.

## Brickmen Giant consequence

Do not immediately rewrite `brickmen_giant_v0` around 10128 dimensions.

Brickmen Giant is an original architecture target.

Instead maintain two related artifacts:

- `lego_giant_modular EngineeringSkeleton` — reconciles actual official reference geometry;
- `brickmen_giant_v0` — original body skeleton that may optionally choose Giant-compatible hardware/interfaces.

If Brickmen Giant opts into direct official Giant arm compatibility, the relevant engineering frames can be mapped intentionally.

## Sources

- LDraw 10128 body: https://sources.debian.org/src/ldraw-parts/1802%2Bds-1/parts/10128.dat
- LDraw 10154 left arm: https://sources.debian.org/src/ldraw-parts/2206%2Bds-1/parts/10154.dat
- LDraw 10124 right arm: https://library.ldraw.org/parts/213
- LDraw 43093 pin: https://library.ldraw.org/parts/8530
