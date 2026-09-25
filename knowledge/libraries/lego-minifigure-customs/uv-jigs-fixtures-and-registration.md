# UV Jigs, Fixtures and Registration

## Purpose
At minifigure scale, repeatable registration is as important as nominal printer resolution. Treat the jig as part of the print profile.

## Fixture coordinate system
Every fixture needs:
- machine coordinate origin,
- fixture datum,
- cavity/index number,
- part-local origin,
- orientation quaternion/Euler transform,
- Z datum,
- artwork transform,
- validated printable polygon/mask.

A print file should be regenerable from these transforms.

## Fixture design
Prefer hard deterministic locating features over visual placement. Avoid locating against cosmetic surfaces when a mechanical datum is available. Use replaceable inserts for frequently changed part families.

Track:
- CAD revision,
- fixture material,
- manufacturing method,
- measured cavity dimensions,
- thermal/warp behavior,
- cleaning compatibility,
- maximum part height,
- collision clearance.

## Registration calibration
Print fiducials on sacrificial fixtures or test pieces and measure X/Y/rotation error. Maintain per-cavity correction if the bed or fixture introduces systematic offsets.

For white + CMYK + varnish jobs, measure inter-layer registration independently from fixture registration.

## Compound surfaces
A minifigure head is cylindrical and arms/legs include curved/tapered surfaces. A flatbed head may require indexed rotations. Store each indexed orientation as a known transform and constrain artwork to the surface visible/reliably printable in that orientation.

## Artwork transforms
Never manually nudge production art without recording the correction. Corrections belong in a machine/jig profile so the same design can be regenerated.

## Z control
Before printing:
1. verify fixture revision,
2. verify installed part family,
3. measure/confirm tallest point,
4. apply validated head-clearance policy,
5. run low-risk setup procedure required by the printer.

## QC metrics
Track X error, Y error, angular error, white-to-CMYK error, varnish-to-CMYK error, cavity repeatability and removal/reload repeatability.

## AI use
A generation agent should know the exact fixture transform and printable mask. It can then render a proof showing where generated artwork lands on the real part and reject artwork outside validated zones.
