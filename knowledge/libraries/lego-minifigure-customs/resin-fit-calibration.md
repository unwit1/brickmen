# Resin Fit Calibration and Connector Engineering

## Rule
Never publish one universal clearance number for all resin printers. Build empirical compensation profiles.

## Coupon families
Create stepped test coupons for:
- circular hole/pin,
- rectangular slot/tab,
- cylindrical headgear socket,
- neck/armor opening,
- hand-held rod diameter,
- clips,
- studs/tubes where appropriate,
- hinge/axle-like interfaces when a custom project needs them.

Each coupon should sweep nominal offset around the measured mating part.

## Measurements
For each coupon record CAD nominal, printed dimension before cure, printed dimension after cure, mating-part measurement, insertion force category, retention category, visible stress, cycles to failure and notes.

## Fit labels
- free clearance
- close clearance
- removable friction
- firm friction
- excessive/interference
- damaging
- failed

The desired fit depends on the part. A helmet should be removable without scratching; a display-only decorative insert may tolerate different retention.

## Resin/material effects
Profiles are keyed by printer, resin, layer height, orientation, exposure, support strategy, wash and cure. A new resin or changed cure schedule invalidates assumptions until sampled.

## Small-feature design
Manufacturer guidance is a starting envelope only. Formlabs' Form 4 guide, for example, lists a 0.5 mm minimum hole and reports dimensional tolerances under a specified printer/resin/layer/cure test. These values should never be silently generalized to another machine.

## Orientation
Avoid placing precision connector faces directly on heavy support contacts. Record orientation because anisotropy, support deformation and overcure can change fit.

## Parametric connector library
Store each validated connector as a reusable CAD feature with:
- connector_id
- revision
- mating family
- nominal source dimensions
- compensation profile
- keep-out envelope
- insertion axis
- approved resin profiles
- physical validation samples.

AI-generated meshes should have their invented connector removed and replaced with one of these validated connector features.

## Sources
https://formlabs.com/white-papers/form-4-design-guide/
https://formlabs.com/global/blog/3D-printing-tolerances-for-engineering-fit/
