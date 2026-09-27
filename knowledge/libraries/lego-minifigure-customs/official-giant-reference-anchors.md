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


## Complete default-pose assembly shortcut

A stronger official reference is available in `10128p01c01.dat`, the LDraw shortcut for the complete dark-purple-trouser Hulk bigfig. The shortcut explicitly assembles the body, both `43093` shoulder pins, both arms, and both hands.

Default root-space transforms:

| component | translation (LDU) | nominal mm at 0.4 mm/LDU | rotation |
| --- | --- | --- | --- |
| body `10128p01` | `[0, 0, 0]` | `[0, 0, 0]` | identity |
| left shoulder pin `43093` | `[40, -126, 0]` | `[16, -50.4, 0]` | identity |
| left arm `10154` | `[40, -126, 0]` | `[16, -50.4, 0]` | identity |
| left hand `10127` | `[70, -86, -40]` | `[28, -34.4, -16]` | approximately -22.5 degrees around Z |
| right shoulder pin `43093` | `[-40, -126, 0]` | `[-16, -50.4, 0]` | mirrored pin transform |
| right arm `10124` | `[-40, -126, 0]` | `[-16, -50.4, 0]` | identity |
| right hand `10126` | `[-70, -86, -40]` | `[-28, -34.4, -16]` | approximately +22.5 degrees around Z |

This resolves the earlier missing shoulder Z coordinate: the complete shortcut places both shoulder centers at `z = 0` in the body frame.

It also cross-checks the local arm hand-socket metadata exactly:

- left hand root translation minus left arm root translation = `[30, 40, -40]` LDU;
- right hand root translation minus right arm root translation = `[-30, 40, -40]` LDU.

Those are exactly the published hand-socket centers in `10154` and `10124`.

The hand files add another useful style/interaction anchor: both publish the power-grip center at local `y = -9.745, z = -20` LDU. The published HELP lines do not specify X, so the digital twin intentionally keeps that coordinate unknown rather than inventing it.

Machine-readable component-frame twin:
- `data/digital-twins/lego-giant-hulk-10128p01c01.json`

### What this does and does not establish

This is now strong ground truth for the **default LDraw assembly frames**. It is appropriate for digital-twin registration, component alignment, articulation visualization, and checking generated proportions.

It still does not establish:
- mould tolerances;
- interference/clearance values;
- insertion or retention force;
- friction;
- wear;
- resin/FDM compensation;
- exact physical articulation limits.

Those remain measurement/test tasks.

### Sources

- Complete Hulk shortcut: https://sources.debian.org/src/ldraw-parts/1802%2Bds-1/parts/10128p01c01.dat
- Official Bigfig body: https://library.ldraw.org/parts/216
- Official Bigfig left arm: https://library.ldraw.org/parts/226
- Official Bigfig right arm: https://library.ldraw.org/parts/213
- Official Bigfig left hand: https://library.ldraw.org/parts/215
- Official Bigfig right hand: https://library.ldraw.org/parts/214
- Official Technic axle pin: https://library.ldraw.org/parts/8530


## Coordinate-frame normalization

LDraw's source coordinate system is right-handed with **-Y as up**. Brickmen generation skeletons use a different semantic frame:

- Brickmen X = left/right;
- Brickmen Y = back/front depth;
- Brickmen Z = feet/head up.

The canonical right-handed conversion is therefore:

```
brickmen_x = ldraw_x
brickmen_y = ldraw_z
brickmen_z = -ldraw_y
```

All raw source transforms remain preserved for provenance, but downstream Brickmen fitting/generation must use the normalized semantic frame.

Examples from the complete Giant assembly:

| anchor | raw LDraw LDU | Brickmen LDU | Brickmen nominal mm |
| --- | --- | --- | --- |
| left shoulder | `[40, -126, 0]` | `[40, 0, 126]` | `[16, 0, 50.4]` |
| right shoulder | `[-40, -126, 0]` | `[-40, 0, 126]` | `[-16, 0, 50.4]` |
| left hand root | `[70, -86, -40]` | `[70, -40, 86]` | `[28, -16, 34.4]` |
| right hand root | `[-70, -86, -40]` | `[-70, -40, 86]` | `[-28, -16, 34.4]` |

The local left-arm hand socket `[30, 40, -40]` becomes `[30, -40, -40]` in Brickmen LDU, and the mirrored right socket becomes `[-30, -40, -40]`.

The machine-readable Giant twin stores both frames and converts the component rotation matrices by basis change rather than relabeling their axes.

### Why this matters

Without the conversion, raw LDraw Y could be mistaken for body depth and raw LDraw Z for body height. That would make side-view envelope measurements, articulation vectors, and learned 3D conditioning systematically wrong even when the source mesh itself was correct.

The recursive geometry ingester now emits:

- raw `bbox_ldu` and `bbox_nominal_mm`;
- `bbox_brickmen_ldu` and `bbox_brickmen_nominal_mm`;
- the explicit frame mapping;
- optional OBJ output directly in the Brickmen semantic frame.

LDraw's nominal unit conversion remains reference CAD scaling rather than production metrology.
