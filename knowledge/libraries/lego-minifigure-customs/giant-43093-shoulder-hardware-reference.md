# Giant 43093 Shoulder Hardware Reference

Research snapshot: 2026-09-27

Brickmen now has a first machine-readable commodity-hardware shoulder profile:

- `data/joint-profiles/lego-giant-43093-shoulder-reference-v0.json`

## What is established

The official Giant assembly uses one `43093` Technic axle pin at each shoulder.

In the normalized Brickmen frame, the hardware's long axis is lateral (X). The pinned LDraw reference mesh has a nominal reference bounding extent of approximately:

- 16.0 mm along X;
- 6.4 mm along Y;
- 6.4 mm along Z.

Those are **mesh extents**, not a statement that every functional cylindrical/axle feature is 6.4 mm diameter.

## Shoulder spacing is not the cartridge

The official Hulk body places the shoulder centers 32 mm apart.

That spacing is useful as official body-shape/reference evidence, but the two `43093` pieces are independent local shoulder interfaces. Therefore a Brickmen-original Giant torso does **not** need to inherit 32 mm center spacing merely to use the same hardware/arm-interface concept.

Keep separate:

```
body proportion / shoulder-center spacing
!=
local shoulder hardware profile
!=
physical socket tolerance
```

A Brickmen torso can move the shoulder centers for its own silhouette while keeping each local cartridge frame and hardware keep-out deterministic.

## What remains unknown

LDraw does not establish:

- real pin/socket interference;
- insertion or removal force;
- shoulder running/breakaway torque;
- play;
- wear;
- creep;
- printable socket compensation.

Those must be measured physically.

## Brickmen use

For `brickmen_giant_v0`:

1. reserve a local shoulder hardware keep-out;
2. preserve the commodity pin at fixed physical dimensions;
3. allow the visual torso shell and shoulder spacing to vary independently;
4. insert a validated printed/molded mating interface around the hardware;
5. reject generated shell geometry that invades the keep-out or articulation sweep.

This is the first concrete JointProfile candidate connecting the reference digital twin to the printable-body engineering layer.
