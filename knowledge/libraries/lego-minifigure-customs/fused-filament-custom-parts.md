# FDM/FFF Custom Minifigure Parts and Production Engineering

Research status: deep research pass, 2026-09-27.

## Executive conclusion

FDM/FFF is **not the primary process for tiny high-detail minifigure accessories**, but it is important enough to deserve a first-class Brickmen production profile rather than being treated as a fallback.

Use FDM primarily for:

- larger or intentionally chunky accessories;
- shields, backpacks and simple equipment where layer texture is acceptable;
- stands, trays, nests, fixtures, inspection jigs and go/no-go holders;
- buildings, terrain, vehicles and large props;
- wash/cure fixtures and automation-cell hardware made from chemically compatible materials;
- mold boxes and casting fixtures;
- dimensional prototypes where photopolymer chemistry is unnecessary.

Use resin first for:

- ornate helmets/hair;
- fine weapons;
- tiny engraved/raised features;
- organic creature features;
- detailed minifigure-scale cosmetic shells.

A tuned 0.20-0.25 mm nozzle can produce surprisingly good miniature geometry, but nozzle diameter, bead geometry and layer staircase remain much larger physical constraints than modern MSLA pixel pitch.

## Evidence for small-nozzle feasibility

Prusa documents 0.25 mm nozzle use with PLA, PETG, ASA/ABS, PC and nylon, while noting that high precision takes substantially longer and that composite/fiber-filled materials can clog small nozzles.

Prusa has also published a miniature-printing workflow using a 0.25 mm nozzle and approximately 0.07-0.10 mm layers.

Bambu Lab sells a 0.20 mm A1-series hotend specifically positioning it for miniature models, intricate logos/text and other high-resolution applications.

These sources establish that sub-standard-nozzle miniature FDM is a valid process. They do not establish resin-equivalent cosmetic quality.

## Nozzle strategy

### 0.20 mm

Best for:
- cosmetic prototypes;
- tiny text/raised motifs;
- small fixtures requiring fine edges.

Costs:
- slow;
- more sensitive to material cleanliness/moisture;
- greater clogging risk;
- profile tuning becomes critical.

### 0.25 mm

Good compromise:
- small accessories;
- jigs with detailed locating geometry;
- easier profile support on some ecosystems.

### 0.40 mm+

Default for:
- fixtures;
- trays;
- stands;
- buildings;
- automation-cell components;
- mold boxes.

Do not force a 0.20 mm nozzle onto a part whose smallest meaningful feature does not benefit from it.

## Material matrix

### PLA

Advantages:
- easiest path to crisp small features;
- low warp;
- inexpensive;
- good for visual prototypes and gauges that do not flex or see heat.

Limitations:
- lower heat resistance;
- can be brittle at thin clip features;
- not the default for repeated snap fits.

Role:
**detail baseline and nonfunctional fixture material.**

### PETG

Prusa describes PETG as tough/tenacious with low warping and very good layer adhesion, but also notes stringing and that it is not ideal for very small/detailed parts.

Advantages:
- better toughness than ordinary PLA;
- easy large fixture production;
- chemical resistance useful for some shop hardware.

Limitations:
- stringing can be severe at minifigure scale;
- tiny cosmetic detail is weaker than PLA/resin;
- supports can be difficult.

Role:
**general jigs, trays, stands, larger durable accessories.**

### ASA / ABS

Prusa describes ASA as suitable for technical parts with impact/wear resistance and better UV/temperature behavior than PLA, while warning about warping and styrene-containing fumes and recommending enclosure/ventilation.

Advantages:
- thermoplastic behavior closer to the material family associated with molded toy parts;
- acetone smoothing is possible;
- durable functional fixtures.

Limitations:
- enclosure/process control;
- emissions/ventilation;
- shrinkage/warp;
- acetone smoothing can erase small detail.

Role:
**functional experiments, durable fixtures, larger custom pieces.**

Do not infer that an FDM ABS/ASA print has LEGO-equivalent mechanics merely because the polymer family is similar. Layer interfaces, voids, orientation and process history are fundamentally different from injection molding.

### Nylon

Advantages:
- toughness;
- wear/fatigue potential;
- useful for clips and flexible mechanical experiments.

Limitations:
- moisture sensitivity;
- drying requirements;
- stringing;
- dimensional control;
- process complexity;
- cosmetic finish.

Role:
**advanced connector/fixture R&D, not first cosmetic choice.**

### Polycarbonate

Advantages:
- strength and temperature resistance.

Limitations:
- high-temperature printing;
- enclosure/drying;
- difficult small-part process;
- unnecessary for most accessories.

Role:
**specialized tooling/mechanical fixtures only.**

### Fiber-filled filaments

Deprioritize for minifigure accessory production:
- abrasive;
- small nozzle clog risk;
- surface texture;
- fibers do not solve visual-detail requirements.

## Orientation is a mechanical variable

A resin accessory and an FDM accessory can share nominal CAD but should not share an unexamined functional profile.

For each FDM connector test:
- print the bar/pin axis in multiple orientations;
- measure diameter in multiple axes;
- record seam location;
- test force and failure direction;
- inspect layer splitting.

A bar printed vertically may have better roundness but unfavorable layer-direction fracture behavior. A horizontal bar may show stronger continuous extrusion along its axis but poorer circularity/stair-stepping. Determine the production choice empirically.

## FDM connector compensation

Maintain independent calibration for:
- outside diameter;
- inside hole;
- rectangular tab/slot;
- clip throat;
- thin-wall thickness;
- first-layer contact geometry.

Do not apply one global XY scale factor.

For small holes, extrusion geometry and slicer compensation can cause a meaningful mismatch between CAD and printed bore. Use a measured compensation curve by feature type.

## Surface-finish policy

For cosmetic minifigure parts:
1. optimize orientation so stair-stepping falls on hidden surfaces;
2. use the smallest justified layer height;
3. control seam placement;
4. avoid support contact on display faces;
5. prefer resin if sanding/vapor smoothing labor becomes significant.

For ASA/ABS vapor smoothing:
- treat as a dimensional process;
- remeasure every critical interface;
- never smooth a production connector based on cosmetic settings alone.

## FDM as the automation-cell fabricator

This is one of FDM's strongest roles.

Automatically generate:
- wash baskets;
- cure trays;
- resin-drip fixtures;
- build-platform racks;
- labeled sample carriers;
- camera nests;
- force-test fixtures;
- go/no-go holders;
- part sorting trays;
- UV print jigs;
- shipping/packing nests;
- mold boxes.

Every fixture should carry:
- fixture_id;
- revision;
- machine/material;
- generated-from profile;
- mating-part IDs;
- dimensional acceptance check;
- chemical/heat compatibility notes.

## Headless automation stack

Preferred abstractions:

```
fdm.generate_fixture(spec)
fdm.slice(model, printer_profile, material_profile)
fdm.validate(gcode)
fdm.enqueue(job)
fdm.telemetry()
fdm.camera()
fdm.abort(reason)
```

### OrcaSlicer

Current documentation states that OrcaSlicer can run headless from the CLI for automation, batch processing and CI. This makes it attractive for automated FDM build generation.

### PrusaSlicer

PrusaSlicer also supports command-line operation and loads profiles from AMF/3MF during CLI slicing.

### OctoPrint

REST API provides a broad adapter surface for:
- file management;
- job control;
- printer state;
- temperatures;
- system commands.

### Klipper + Moonraker

Moonraker exposes HTTP/WebSocket/JSON-RPC interfaces around Klipper, including status, files, queue/history, webcams and extensible device/sensor integration.

### PrusaLink / Prusa Connect SDK

Prusa maintains an OpenAPI specification for PrusaLink Web and a Python printer SDK for Prusa Connect.

## 3MF over loose STL where possible

Brickmen should prefer 3MF as the manufacturing exchange container when the downstream application supports it.

Reasons:
- explicit units;
- model/build metadata;
- materials/colors/extensions;
- stronger interoperability than a naked STL;
- one container can carry production context.

The 3MF Consortium publishes the specification and lib3mf, an open-source implementation with language bindings and validation/conversion capabilities. ISO/IEC 25422:2025 defines the 3MF specification suite as an international standard.

Keep the canonical CAD source separately. A slicer-generated 3MF project is a build artifact, not the canonical parametric model.

## Parametric CAD recommendation

For automation-generated connectors, coupons and fixtures, CadQuery is a strong candidate because:
- it is Python-native;
- explicitly parametric;
- based on OpenCascade;
- exports STEP, STL and 3MF;
- plain-text source can be versioned and tested.

Recommended division:
- CadQuery: precision connectors, coupons, fixtures, simple hard-surface accessories;
- Blender: organic sculpting, mesh editing, visual shells;
- final part assembly: replace all functional interfaces with validated parametric connector solids before export.

## Automated fixture generation example

Input:
```yaml
fixture_type: force_test_hand_grip
connector_profile: hand_bar_v4
sample_count: 12
spacing_mm: 8
label: resin_X_profile_07
camera_fiducials: true
```

Pipeline:
```
schema validate
 -> CadQuery generator
 -> STEP master + 3MF build artifact
 -> Orca/PrusaSlicer CLI
 -> gcode preflight
 -> print
 -> inspect critical dimensions
 -> register fixture revision
```

## FDM qualification experiments

Before approving a new printer/material/nozzle combination:
1. extrusion/flow calibration;
2. dimensional artifact;
3. hole/pin ladder;
4. 3.18-family bar ladder;
5. thin wall ladder;
6. seam/orientation study;
7. support-interface study;
8. repeated clip/flex study if applicable;
9. thermal exposure relevant to shop conditions;
10. chemical compatibility for wash/resin fixtures.

## Current conclusion

For Brickmen, FDM should be treated as the **factory-building and macro-part process**, while resin is the **micro-part/detail process**. That combination is more automated and economical than attempting to force either technology to manufacture everything.

## Sources

- Prusa 0.25 mm nozzle guidance: https://help.prusa3d.com/article/e3d-v6-nozzles_920168
- Prusa miniature workflow: https://blog.prusa3d.com/printing-great-looking-miniatures-with-a-0-25mm-nozzle-on-the-original-prusa-mini_33457/
- Prusa PETG: https://help.prusa3d.com/article/petg_2059
- Prusa ASA: https://help.prusa3d.com/article/asa_1809
- Bambu A1 hotends: https://us.store.bambulab.com/products/bambu-hotend-a1-series
- OrcaSlicer CLI: https://www.orcaslicer.com/wiki/cli/cli_mode
- PrusaSlicer CLI: https://github.com/prusa3d/PrusaSlicer/wiki/Command-Line-Interface
- OctoPrint API: https://docs.octoprint.org/en/main/api/index.html
- Moonraker API: https://moonraker.readthedocs.io/en/latest/external_api/introduction/
- CadQuery: https://cadquery.readthedocs.io/en/latest/intro.html
- 3MF specifications: https://3mf.io/spec/
- lib3mf: https://github.com/3MFConsortium/lib3mf
- ISO/IEC 25422:2025: https://www.iso.org/standard/90283.html
