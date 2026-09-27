# Additive Manufacturing Feasibility for Minifigure-Scale Custom Parts

Research status: deep research pass, 2026-09-27.

## Executive conclusion

Custom minifigure accessories are a strong additive-manufacturing use case, but the correct production method depends on the part.

- **MSLA/SLA resin is the primary process for tiny visual geometry**: helmets, hair, armor, weapons, creature features, heads, ornate props, masters for molding, and short-run specialty components.
- **FDM/FFF is a secondary process at minifigure scale**: useful for larger/chunkier accessories, fixtures, trays, jigs, stands, buildings, vehicles, packaging aids, and some mechanically forgiving components. A 0.20-0.25 mm nozzle can make convincing miniatures, but it does not match fine resin surface detail.
- **Existing molded donor parts + printed overlays/accessories is the preferred first production architecture.** It preserves proven articulation/clutch geometry while custom printing the geometry that actually needs to be novel.
- **Full printed articulated minifigures are feasible as an R&D program, not the first production target.** The visual shapes are straightforward; repeated-fit joints and durable friction interfaces are the difficult part.
- **Low-volume injection molding with printed tooling is a credible bridge process** when true thermoplastic behavior is required but steel tooling is not yet justified.
- **Steel/aluminum production molds become increasingly attractive for stable, high-volume designs.** There is no single fixed break-even quantity; geometry, cavities, labor, finishing, reject rate, tooling quote, and selling price determine the crossover.

The core engineering rule is: **pixel size is not dimensional accuracy, and nominal LEGO-compatible dimensions are not production tolerances.** Every critical connector must be calibrated physically for the exact printer/material/cure/orientation workflow.

## Why resin is technically viable

Modern hobby MSLA machines have XY pixel pitches far smaller than most minifigure accessory features. For example, ELEGOO specifies the Mars 5 Ultra at 18 micrometers XY pixel size, 0.01-0.2 mm layers, and Wi-Fi/cluster printing. This is a useful indication of image sampling/detail capability, not a guarantee that every feature will be dimensionally accurate to 18 micrometers.

Professional resin systems trade headline pixel pitch for characterized dimensional behavior, process control, validated materials, software automation, and repeatability. Formlabs specifies Form 4 at 50 micrometer pixel size with typical XY dimensional tolerances of +/-0.15% for many features; its design guide gives a lower-limit example of +/-0.02 mm for 1-30 mm features under the stated test conditions.

Therefore two distinct printer-selection objectives exist:

1. **Maximum visual detail per dollar**: fine-pixel hobby MSLA.
2. **Maximum characterized process control/repeatability/integration**: professional SLA/LFD ecosystems.

Do not rank printers solely by "K" marketing resolution.

## Functional connector reality

The widely documented minifigure/bar connection family is based around a nominal 3.18 mm bar. The 3.18 mm figure is useful as a geometry-family reference, not a universal CAD value that should be printed unchanged.

The production dimension that matters is whatever CAD dimension, exposure, orientation, material, wash and cure sequence produces the target physical fit on the intended mating part.

For every connector, preserve:

- nominal reference geometry,
- measured mating-part distribution,
- printer/material compensation,
- intended fit class,
- insertion force,
- removal force,
- visible stress,
- cycle count,
- failure mode.

Default safety bias for removable accessories: prefer a controlled slightly-loose fit over an overly tight fit that can stress or crack a donor hand/head/torso.

## Part-by-part feasibility

| Part family | Resin | FDM | Engineering issue |
|---|---|---|---|
| swords, knives, guns, tools | excellent | fair-good | thin sections, grip fit, drop resistance |
| helmets, hats, hair | excellent | fair-good | head socket fit, support scars, thin rims |
| armor, pauldrons, backpacks | excellent | good | neck clearance, arm articulation, warpage |
| shields | excellent | good | clips/bars, flatness, decoration |
| rigid skirts/robes | excellent | fair-good | leg clearance/articulation |
| creature appendages | excellent | fair | thin features/fatigue |
| custom heads | excellent visually | fair | neck interface + decoration |
| hands | difficult functional target | poor target | flex fatigue and stress concentration |
| arms | feasible R&D target | difficult | friction pivots, hand bore, wear |
| torsos | feasible R&D target | fair | arm pivots, hip interface, decoration |
| hips/legs | feasible R&D target | fair | pin joints, clutch, wear |
| complete articulated figure | feasible R&D | low priority | multi-interface tolerance stack |
| display stands / jigs | good | excellent | dimensional repeatability |
| buildings / terrain / large props | good | excellent | cost/throughput |

## Material strategy

### Resin

Do not use generic brittle standard resin as the default functional material.

Candidate classes:

- ABS-like/toughened hobby resin for general accessories.
- High-elongation tough resin for snap-like or repeatedly handled parts.
- Tough + flexible blends only after controlled testing; blending changes exposure, dimensions, cure response and long-term behavior.
- Rigid/high-temperature resin for tooling, not for hand-held parts that benefit from compliance.
- Castable formulations only where a casting workflow specifically needs them.

Mechanical-property examples demonstrate why "resin is brittle" is too broad:

- Formlabs Tough 1500 V2: manufacturer reports 155% elongation at break after its specified cure and positions it for compliant mechanisms/snap fits.
- Formlabs Tough 2000 V2: manufacturer reports 79% elongation at break and a tensile modulus around 1800 MPa, positioning it closer to ABS stiffness.
- Anycubic ABS-Like Resin Pro 2 reports 35-40% elongation at break under its stated test data.
- ELEGOO ABS-Like V3.0 is marketed for functional/mechanical parts with improved toughness and lower shrinkage versus earlier formulations.

These values are not directly interchangeable because test method, specimen, cure, orientation and printer differ. Build an internal functional test library instead of selecting materials from one property number.

### FDM/FFF

For minifigure-scale functional parts:

- **PLA**: best easy-detail baseline but less attractive for heat/impact/fatigue use.
- **PETG**: tough, low warping, excellent layer adhesion; Prusa explicitly notes it is not ideal for very detailed tiny parts and can string.
- **ASA/ABS**: attractive for mechanical behavior and postprocessing; 0.25 mm nozzles can print ASA/ABS, but warping, enclosure requirements and styrene-containing emissions make process controls important.
- **Nylon/PC**: advanced functional experiments where wear/compliance matter, with drying and process complexity.
- **fiber-filled filaments**: deprioritize for 0.20-0.25 mm nozzles because fillers can clog small nozzles; also surface finish is usually not the desired minifigure aesthetic.

Prusa documents 0.25 mm nozzle support for PLA, PETG, ASA/ABS, PC and nylon, while warning that precision takes much longer. Bambu sells a 0.2 mm A1-series nozzle specifically for miniature models, intricate logos, text and molds.

## Dimensional calibration

A calibration profile is keyed by at least:

- printer model + serial,
- firmware,
- screen/light-engine hours where available,
- resin/filament manufacturer + SKU + lot,
- resin pigment/blend recipe if used,
- layer height,
- exposure or extrusion profile,
- ambient/material temperature,
- model orientation,
- support strategy,
- wash recipe,
- post-cure recipe,
- dimensional compensation,
- date and operator/automation version.

### Resin calibration ladder

Print independent coupon families:

1. outside pin/bar diameter,
2. inside circular hole,
3. headgear socket,
4. neck/armor opening,
5. rectangular tab/slot,
6. C-clip,
7. wall-thickness ladder,
8. thin blade/shaft ladder,
9. engraved/recessed feature ladder,
10. raised-detail ladder,
11. flat plate warp coupon,
12. support-contact scar study.

Use stepped values around the expected production geometry. Never infer hole compensation from outside-pin compensation; light bleed/overexposure can make outer dimensions grow while holes close.

Phrozen and AmeraLabs both document exposure calibration artifacts. AmeraLabs explicitly notes the practical pattern: overexposure tends to make outer parts larger and holes smaller; underexposure can move the opposite direction. Use generic exposure artifacts to establish a stable exposure window, then use Brickmen-specific connector coupons for final fit.

### FDM calibration ladder

Measure:

- extrusion/flow calibration,
- first-layer accuracy,
- pressure advance,
- temperature,
- retraction/stringing,
- XY hole and peg compensation,
- bar roundness by orientation,
- layer seam location,
- thin-wall repeatability,
- bridge/overhang quality,
- support-interface damage.

For FDM functional bars, print specimens in multiple orientations because layer direction changes strength and roundness.

## Orientation and support policy

Separate the model into:

- visual surfaces,
- connector surfaces,
- articulation clearance,
- high-stress surfaces,
- sacrificial/support surfaces.

Preferred policy:

- keep support contacts away from connector bores and polished/display faces;
- avoid support scars on a 3.18-family grip;
- orient long thin weapons to balance peel force, straightness and layer-direction strength;
- do not create sealed resin cavities;
- treat hollowing as an engineered operation with explicit drain/vent validation;
- reject unsupported suction cups/resin traps in slice preflight.

Formlabs' current Form 4 guide recommends at least 0.75 mm drain holes under its own process assumptions. Hobby machines/materials require separate validation.

## Surface finish and color

### Surface finish

Possible resin workflow:

wash -> dry -> controlled post-cure -> support removal -> micro-sand/spot-fill -> primer if needed -> color/decorate -> protective finish -> QC.

Support removal timing should be experimentally optimized. Removing supports before full cure may reduce scar severity on some materials, but geometry can be more vulnerable; the rule must be material-specific.

### Color-through-material

A colored resin/filament part is preferable when wear would expose a contrasting substrate.

For custom resin colors:

- use a known base resin,
- dose pigments by mass, not drops,
- record pigment lot and scale calibration,
- remix using a defined protocol,
- recalibrate exposure after pigment changes,
- measure cured swatches under controlled lighting,
- store spectrophotometer/colorimeter values when available.

Do not assume a visual screen RGB or a vendor's color name equals a physical LEGO color.

### Decoration

Geometry and decoration are separate manufacturing stages.

Candidate processes:

- UV direct print,
- pad print,
- waterslide,
- paint/airbrush,
- screen print for appropriate flat/cloth work,
- molded-in material color.

UV printing is attractive for low-volume variable artwork; pad printing is attractive for repeatable production and curved-surface transfer. A resin part needs its own substrate/adhesion profile rather than inheriting settings from ABS donor parts.

## Hybrid manufacturing

The strongest near-term architecture is:

1. use genuine or high-quality compatible molded donor bodies for articulation;
2. resin-print novel visual geometry;
3. UV/pad/decal/paint decoration as a separate stage;
4. use FDM for fixtures, trays, storage, jigs and larger environment parts.

This minimizes the number of precision wear interfaces the project must solve.

### Printed master -> silicone mold -> casting

Useful for short repeat runs when a cast material has better target properties or when print labor dominates.

Risks:

- mold seam/flash,
- air entrapment,
- material cure/shrinkage,
- manual mixing/degassing,
- master surface texture replication,
- mold life variation.

### 3D-printed injection mold -> thermoplastic part

This is unusually relevant to minifigure accessories because the finished part can be a real thermoplastic instead of photopolymer.

Formlabs documents low-volume injection molding with printed tooling and reports examples ranging from dozens to hundreds/thousands of shots depending on geometry, mold material and process. It also documents thermoplastics including PP, PE, TPE/TPU, POM, ABS and PA in customer workflows.

This creates a potential production ladder:

- 1-50: direct resin print.
- tens to low hundreds: direct print or cast depending on finishing/labor.
- low-volume thermoplastic requirement: printed injection tooling.
- stable high-volume SKU: quoted aluminum/steel tooling.

Those ranges are planning bands only, not financial break-even rules. Build a cost model from actual quotes and cycle data.

## Quality standard

A printable part is not automatically a production-quality part.

Each release needs a golden sample plus:

- dimensional critical-to-quality features,
- visual defect limits,
- fit class,
- insertion/removal force range,
- repeated-cycle requirement,
- drop/impact requirement when relevant,
- straightness/warp requirement,
- decoration registration and abrasion requirement,
- color target,
- batch traceability.

### Functional tests

For accessories held in a minifigure hand:

1. measure bar diameter in at least two axes;
2. record hand/fixture identity;
3. measure insertion force;
4. measure removal force;
5. inspect hand and accessory for whitening/cracking;
6. cycle repeatedly;
7. remeasure retention;
8. inspect with magnification.

Create sacrificial standardized compatibility fixtures before testing valuable donor parts.

## Process-selection engine

The agent should calculate a production recommendation from:

- bounding box and minimum feature size,
- thin-wall/blade features,
- connector family,
- expected mechanical cycles,
- desired color,
- decoration requirement,
- quantity,
- deadline,
- acceptable support scars,
- desired surface finish,
- true delivered cost,
- labor minutes,
- reject/rework rate,
- rights/provenance status.

Example rules:

- tiny ornate helmet -> resin.
- rigid 3.18-bar weapon -> tough resin prototype, then consider molded thermoplastic for scale.
- storage jig -> FDM.
- building wall -> FDM.
- one-off highly decorated torso -> donor molded torso + UV/decal.
- articulated full body -> R&D queue unless there is a specific reason to replace donor parts.

## Safety is an automation requirement

NIOSH's 2025 guidance for desktop vat photopolymerization notes that uncured resin can contain acrylates associated with asthma/dermatitis hazards, that printing and curing can release particles/gases, and that IPA cleaning adds solvent exposure. NIOSH specifically identifies automated resin dispensing and automated part handling as ways to lower exposure.

Therefore the automation architecture must include:

- local exhaust/ventilation,
- enclosed chemical handling,
- spill detection/containment,
- resin-level monitoring,
- door/cover interlocks,
- cure/wash state tracking,
- solvent state tracking,
- PPE/manual-service procedures,
- controlled waste handling,
- emergency stop,
- no autonomous robot motion while a person is inside the cell.

FDM also needs ventilation strategy; NIOSH reports particle/VOC emissions varying by filament/material and recommends engineering controls.

## Research conclusions to retain

1. Consumer-resin pixel size is a detail metric, not a fit guarantee.
2. Connector calibration is more important than nominal dimensional copying.
3. Tough/ductile photopolymers make functional accessories far more plausible than standard brittle resin.
4. FDM is useful but should not be the primary fine-accessory process.
5. Donor-body + custom-accessory production eliminates the hardest articulation problems.
6. Printed injection tooling may be the most interesting bridge from resin prototypes to thermoplastic short runs.
7. An automated workflow needs empirical measurement feedback, not one-way CAD -> slicer -> printer automation.
8. A safe resin cell should automate chemical handling specifically because that also reduces operator exposure.

## Primary/technical sources

- ELEGOO Mars 5 Ultra specs: https://www.elegoo.com/products/mars-5-ultra-9k-7inch-monochrome-lcd-resin-3d-printer
- Formlabs Form 4 design guide: https://formlabs.com/white-papers/form-4-design-guide/
- Formlabs Tough 1500 V2: https://formlabs.com/global/products/tough-1500-resin/
- Formlabs Tough family comparison: https://formlabs.com/support/Using-Tough-Resin/
- Anycubic ABS-Like Resin Pro 2: https://store.anycubic.com/products/abs-like-resin-pro-2
- ELEGOO ABS-Like Resin V3.0: https://www.elegoo.com/products/elegoo-abs-like-resin-v-3-0
- Prusa 0.25 mm nozzle guidance: https://help.prusa3d.com/article/e3d-v6-nozzles_920168
- Prusa miniature-printing example: https://blog.prusa3d.com/printing-great-looking-miniatures-with-a-0-25mm-nozzle-on-the-original-prusa-mini_33457/
- Prusa PETG: https://help.prusa3d.com/article/petg_2059
- Prusa ASA: https://help.prusa3d.com/article/asa_1809
- Bambu A1 hotend/nozzle guide: https://us.store.bambulab.com/products/bambu-hotend-a1-series
- New Elementary 3.18 mm connection research: https://www.newelementary.com/2016/12/bravo-three-one-eight.html
- Brothers Brick mirror/guest post: https://www.brothers-brick.com/2017/02/25/lego-3-18-mm-connection-analysis-new-elementary-guest-post/
- AmeraLabs calibration/troubleshooting: https://ameralabs.com/blog/resin-3d-printing-troubleshooting/
- Phrozen exposure calibration: https://helpcenter.phrozen3d.com/hc/en-us/articles/6324863205145-Which-Exposure-Finder-Should-I-Use
- Formlabs printed injection molds: https://formlabs.com/white-papers/low-volume-rapid-injection-molding-with-3d-printed-molds/
- Formlabs injection-molding FAQ: https://formlabs.com/blog/3d-printed-injection-molds-faq/
- Formlabs silicone mold-making: https://formlabs.com/support/Silicone-mold-making-and-silicone-part-production/
- BrickWarriors production description: https://www.brickwarriors.com/about-us/
- NIOSH safe vat-photopolymerization guidance: https://www.cdc.gov/niosh/media/pdfs/2025/01/Safe-3D-Printing.pdf
- NIOSH safe 3D printing guide: https://www.cdc.gov/niosh/docs/2024-103/default.html
