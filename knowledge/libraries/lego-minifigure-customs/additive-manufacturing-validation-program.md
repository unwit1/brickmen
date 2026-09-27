# Additive Manufacturing Validation Program

Research status: deep research pass, 2026-09-27.

## Purpose

Define how Brickmen converts a promising print into a **validated production process**.

The system intentionally borrows principles from ISO/ASTM additive-manufacturing quality practice without claiming certification.

Relevant standards:
- ISO/ASTM 52902:2023: geometric capability assessment using benchmarking artefacts;
- ISO/ASTM 52920:2023: qualification principles for AM processes and production sites;
- ISO/ASTM 52901:2017, confirmed 2023: exchanged requirements, feedstock, final characteristics, inspection and acceptance for purchased AM parts.

Brickmen should implement the useful engineering concepts in a lightweight, machine-readable manner.

## Validation hierarchy

### Level 0 — digital-only

Allowed:
- concept review;
- collision/articulation simulation;
- slicer feasibility;
- cost estimate.

Not allowed:
- production fit claims;
- durability claims;
- donor-safety claims.

### Level 1 — first article

Required:
- successful print;
- dimensional measurements;
- fit category;
- macro/micro photographs;
- failure notes.

Status:
**prototype only.**

### Level 2 — controlled repeatability

Required:
- repeated specimens from same plate;
- repeated plates;
- critical dimensions;
- insertion/removal force;
- process logs;
- variance calculation.

Status:
**candidate profile.**

### Level 3 — functional qualification

Required as relevant:
- cycle test;
- drop/impact;
- bending;
- creep/retention;
- UV/light aging;
- temperature conditioning;
- decoration abrasion/adhesion;
- cleaning chemical compatibility.

Status:
**validated for defined use envelope.**

### Level 4 — production qualification

Required:
- frozen machine/material/postprocess profiles;
- golden sample;
- acceptance limits;
- sampling plan;
- traceability;
- drift triggers;
- rollback profile;
- known failure modes.

Status:
**production approved.**

## Geometric capability artifact

Maintain a generic Brickmen geometric benchmark inspired by ISO/ASTM 52902 concepts plus minifigure-specific features.

Include:
- outer cylinders;
- internal holes;
- thin walls;
- slots;
- pins;
- stepped heights;
- negative/positive embossed features;
- flatness plate;
- angled surfaces;
- unsupported features within safe test limits;
- multiple XY positions across build area.

Purpose:
- machine capability;
- local build-area distortion;
- post-cure distortion;
- cross-machine comparison.

Do not confuse this with connector-fit coupons. The generic artifact diagnoses the machine; connector coupons validate the application.

## Minifigure interface coupon suite

### Held accessory bar

Sweep CAD diameters around the current expected production dimension.

Record:
- diameter X;
- diameter Y;
- roundness proxy;
- insertion force;
- removal force;
- cycles;
- donor/fixture ID;
- stress whitening/cracks.

The nominal 3.18 mm LEGO connection family is a starting reference only.

### Headwear socket

Sweep:
- bore diameter;
- socket depth;
- entry chamfer;
- axial clearance.

Measure:
- insertion/removal force;
- rotational retention;
- scratching;
- stress;
- post-cycle retention.

### Neck armor opening

Sweep:
- bore/slot geometry;
- axial thickness;
- shoulder/arm clearance.

Test full articulation envelope.

### Clip interface

Sweep:
- throat;
- root thickness;
- inside radius;
- opening;
- material/orientation.

Measure:
- insertion force;
- retention;
- cycle fatigue;
- crack initiation.

### Stud/tube interfaces

Only build when a project actually needs them. Brick clutch is a separate, demanding system and should not be assumed solved by minifigure bar/head tests.

## Measurement system

### Critical outside dimensions

A micrometer is preferred where the geometry permits.

Example industrial reference:
Mitutoyo's 293-340-30 has 0.001 mm display resolution and manufacturer-listed +/-0.00005 in accuracy. This illustrates the type of capability available; Brickmen does not require this exact model.

Record:
- device ID;
- resolution;
- stated accuracy;
- calibration/check date;
- measuring force/mechanism;
- operator/automation;
- temperature if high precision matters.

### Internal bores

Use calibrated pin/plug gauges when possible.

Vermont Gage Class ZZ pins are available with approximately 0.005 mm tolerance in the cited range and are intended for hole/Go-NoGo work.

For a known connector family, a custom small Go/NoGo set is faster in production than manually recording every bore.

### Force

Use an instrumented tension/compression test stand.

A suitable architecture provides:
- low-force sensor sized to expected load;
- controlled speed;
- displacement/travel;
- repeat cycling;
- USB/serial/ASCII control;
- force-vs-time and preferably force-vs-displacement.

Mark-10's equipment demonstrates that commercial stands can provide PC/ASCII control, programmable travel/cycling and force data. This validates the automation architecture; a custom lower-cost load-cell stage may ultimately be more economical.

## Measurement-system rule

Never use display resolution as accuracy.

For each measurement, record uncertainty/capability appropriate to the tolerance.

If the process variation is the same scale as measurement uncertainty, improve the gauge before making compensation decisions.

## Automated force test

Desired state machine:

```
load sample fixture
 -> identify fixture/sample
 -> zero force/displacement
 -> approach at controlled speed
 -> detect contact/preload
 -> insert to target displacement
 -> record peak/curve
 -> dwell if specified
 -> extract
 -> record peak/curve
 -> photograph
 -> repeat cycle count
 -> classify
 -> store raw data + summary
```

Hard stops:
- force exceeds donor-safe limit;
- crack/acoustic/vision event;
- displacement outside envelope;
- fixture ID mismatch.

Do not infer donor-safe force limits from intuition. Establish them experimentally using sacrificial parts/fixtures and conservative limits.

## Resin exposure/material qualification

### Exposure finder

Use manufacturer/community calibration artifacts to find a stable starting exposure window.

Phrozen publishes exposure-finder guidance; AmeraLabs provides calibration/troubleshooting artifacts and explains the common dimensional effect that overexposure tends to enlarge outside features while closing holes.

Then switch to Brickmen application coupons.

Variables:
- normal exposure;
- bottom exposure/layers;
- lift/retract;
- resin temperature;
- layer height;
- orientation;
- antialias/image blur if relevant.

## Resin material candidate tests

Supplier datasheets prove that photopolymers span a wide mechanical range; they do not replace Brickmen physical testing.

Useful examples:

### Siraya Tech Blu Tough

Manufacturer currently reports approximately:
- tensile stress at break: 50 MPa;
- elongation at break: 32%;
- Young's modulus: 1800 MPa;
- notched Izod: 45 J/m.

Use as a tough engineering candidate.

### Siraya Tech Tenacious

Manufacturer currently reports for Clear/Obsidian:
- tensile stress at break: 28 MPa;
- elongation: 70%;
- modulus: 800 MPa;
- notched Izod: 57 J/m.

Manufacturer explicitly says it can be mixed into other 405 nm resins to increase impact resistance.

Treat every blend ratio as a **new material profile** requiring exposure, dimension and cure validation. Community reports commonly use roughly 10-20% Tenacious blends for miniatures, but these are anecdotal starting experiments, not Brickmen production recipes.

### Siraya Tenacious Flex Black

Manufacturer reports 140% elongation and 70A Shore hardness. This is likely too elastomeric for most rigid accessories but is relevant to flexible components/blend studies.

### Formlabs Tough family

Tough 1500 V2 and Tough 2000 V2 illustrate professional tough photopolymers with much higher elongation than generic brittle resins. Use manufacturer-specific cure/property data only within their defined process.

## Material experiment matrix

For each candidate:
- pure resin;
- approved blend ratios if blending is supported;
- 2+ orientations;
- 2+ relevant section thicknesses;
- validated cure schedules.

Measure:
- dimension;
- detail;
- bend-to-break;
- drop outcome;
- force/cycle performance;
- creep;
- color/UV stability where relevant;
- sanding/primer behavior;
- UV print/paint adhesion where relevant.

## Creep and retention

A part can pass insertion testing and still fail by slowly relaxing.

For clips/helmets/retained pieces:
- measure initial retention;
- leave assembled for controlled durations;
- condition at room temperature and a modest elevated temperature appropriate to expected storage/shipping;
- remeasure retention;
- inspect permanent deformation.

Record actual temperatures/times. Do not invent "accelerated aging equivalence" without a validated model.

## Drop/impact

Create a defined test:
- known drop height;
- known surface;
- defined orientations or randomized controlled sequence;
- minimum sample count;
- pre/post photos;
- fracture code.

The goal is comparative material/design ranking, not a claim of compliance with a toy standard unless an applicable standard test is actually performed by the required lab.

## Thin-feature test

Weapons need a dedicated specimen.

Include:
- blade/shaft thickness ladder;
- multiple lengths;
- fillet/root variants;
- printing orientations.

Measure:
- straightness;
- hand feel;
- bending force;
- fracture energy proxy;
- drop failure.

Use results to build DFM limits:
```
minimum_free_spear_shaft(resin, profile)
minimum_blade_root(resin, profile)
minimum_horn_diameter(resin, profile)
```

## Warp/straightness

For swords/spears/staffs:
- photograph against calibrated backlight/grid;
- automatically fit centerline;
- compute maximum deviation from straight;
- store pre-cure and post-cure measurements.

This can become a low-cost vision metric.

## Visual inspection station

Standardize:
- camera;
- lens;
- magnification;
- diffuse lighting;
- background;
- part nest;
- fiducials;
- exposure/white balance.

Automatable defects:
- missing feature;
- gross deformation;
- support remnant;
- surface void/pit;
- bent shaft;
- severe layer/peel artifact;
- decoration registration.

Use OpenCV/fiducials for pose normalization. Maintain human review for ambiguous cosmetic judgments until the classifier is proven.

## Statistical process control

Do not overcomplicate early R&D, but preserve data so SPC becomes possible.

For production-critical dimensions:
- retain every first-article measurement;
- sample every plate/batch initially;
- compute mean/stddev/range;
- plot drift by machine/material lot;
- detect step changes after film/screen/nozzle/cure changes.

Do not automatically "correct" a drifting process from one sample. Trigger a calibration build.

## Profile promotion

```
observed
 -> experimental
 -> candidate
 -> validation_pending
 -> validated
 -> production_approved
 -> superseded
```

Promotion requires links to:
- sample IDs;
- raw measurements;
- photos;
- equipment calibration state;
- exact input/build hashes;
- reviewer/automation decision.

## Automatic rejection examples

Reject/quarantine when:
- wrong material lot/profile;
- unrecognized slice hash;
- unresolved UVtools structural warning;
- critical dimension outside acceptance;
- insertion force above safe limit;
- part is visibly cracked;
- cure cycle incomplete;
- ventilation/interlock event occurred;
- traceability is broken.

## Standards-inspired acceptance packet

For every released custom printed component preserve:

1. part definition/revision;
2. manufacturing method;
3. machine;
4. feedstock lot;
5. build orientation/location;
6. slice/build artifact hash;
7. postprocess;
8. critical dimensions;
9. functional acceptance tests;
10. cosmetic acceptance;
11. quantity/rejects;
12. golden sample/photos;
13. release decision.

This mirrors the useful information-exchange and process-control principles of ISO/ASTM 52901/52920 without claiming formal certification.

## Sources

- ISO/ASTM 52902:2023: https://www.iso.org/standard/79683.html
- ISO/ASTM 52920:2023: https://www.iso.org/standard/76911.html
- ISO/ASTM 52901:2017: https://www.iso.org/standard/67288.html
- Vermont Gage Class ZZ: https://vermontgage.com/gaging-products/standard-pin-gages-and-sets/steel-class-zz-gage-pins-and-sets
- Mitutoyo digital micrometer reference: https://dev.pim.mitutoyo.com/products/small-tool-instruments-and-data-management/micrometers/digimatic-micrometers/coolant-proof-micrometer/
- Mark-10 force gauges: https://mark-10.com/products/force-gauges/series-7/
- Mark-10 motorized stand: https://mark-10.com/products/legacy-products/esm303/
- Siraya Tech Blu: https://siraya.tech/pages/blu-user-guide
- Siraya Tech Blu TDS: https://siraya.tech/pages/blu-tough-resin-tds-for-regular-blu
- Siraya Tech Tenacious: https://siraya.tech/pages/tenacious-user-guide
- AmeraLabs resin troubleshooting: https://ameralabs.com/blog/resin-3d-printing-troubleshooting/
- Phrozen exposure finder: https://helpcenter.phrozen3d.com/hc/en-us/articles/6324863205145-Which-Exposure-Finder-Should-I-Use
- OpenCV: https://docs.opencv.org/
