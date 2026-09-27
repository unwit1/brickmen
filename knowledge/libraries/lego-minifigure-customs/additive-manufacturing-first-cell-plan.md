# First Automation-First Minifigure Manufacturing Cell

Research status: recommended first implementation, 2026-09-27.

## Objective

Build the smallest physical system that can answer the real engineering questions before Brickmen spends money automating the wrong process.

The first cell is not intended to be a lights-out factory. It is intended to make **every print a structured experiment** while automating all digital preparation, traceability, analysis and repeatable machine operations that can safely be automated immediately.

## Recommended first-cell architecture

### Fine-detail resin station

Required capabilities:
- modern fine-pixel MSLA printer;
- repeatable network job transfer where practical;
- camera/status monitoring where available;
- resin-level/failure sensing where available;
- replaceable build surface/film;
- dedicated enclosed, ventilated work area.

A current Mars 5 Ultra-class machine is a useful low-cost reference because it combines 18 micrometer XY sampling with Wi-Fi, camera functions, automatic leveling and resin/residue monitoring. The exact purchased model should be selected from current availability at procurement time.

Do **not** make the manufacturing software depend on one vendor's undocumented network protocol.

### Resin post-processing

Start with:
- dedicated wash station;
- dedicated cure station;
- two-stage wash workflow if testing proves it useful;
- lidded containers;
- drip tray;
- standardized part baskets;
- barcode/QR-labeled sample carriers.

Do not automate robot transfer initially. Instrument and standardize the manual operation first so automation has a stable process to reproduce.

### FDM station

Required:
- reliable network-connected printer;
- standard nozzle plus 0.20-0.25 mm option;
- open/documented or adapter-friendly job interface;
- enclosure if using materials requiring it.

Uses:
- force-test fixtures;
- inspection nests;
- sample carriers;
- resin handling fixtures;
- jigs;
- mold boxes;
- large accessories/scenery;
- automation-cell hardware.

### Measurement station

Initial:
- quality digital micrometer;
- digital caliper;
- metric pin/plug gauges around the connector ranges being studied;
- controlled microscope/camera;
- precision scale;
- simple force gauge.

Upgrade quickly to:
- motorized low-force test stand;
- instrumented load cell;
- displacement capture;
- automatic repeated cycling.

### Compute/control station

Local service manages:
- part/job database;
- parametric CAD;
- slicers;
- UVtools;
- printer adapters;
- QR/barcode;
- cameras;
- force-test data;
- metrology input;
- analysis;
- profile promotion;
- cost model.

Prefer local/offline-capable control; cloud services should be optional adapters.

## Software stack

### Canonical data

Git:
- schemas;
- connector definitions;
- approved process profiles;
- generator source;
- experiment definitions;
- validated conclusions.

Local database/object store:
- raw camera images;
- force curves;
- large slice files;
- printer telemetry;
- high-frequency measurements;
- temporary build artifacts.

Git records hashes/provenance for large local artifacts.

### Geometry

- CadQuery for connectors/coupons/fixtures;
- Blender for organic visual shells;
- STEP as neutral exact geometry when possible;
- 3MF for rich manufacturing exchange;
- STL only as compatibility export.

### Build preparation

Resin:
- slicer adapter;
- UVtools CLI post-slice validation;
- job manifest/hash.

FDM:
- OrcaSlicer or PrusaSlicer CLI;
- G-code/3MF manifest;
- printer adapter via Moonraker, OctoPrint, PrusaLink/other supported API.

### Identification

Every build:
- job ID;
- plate ID;
- material lot;
- machine/profile;
- QR/barcode.

Every physical sample carrier:
- plate/sample ID readable by human and camera.

Tiny individual accessories do not need labels printed onto them during early R&D; keep them in indexed nests/trays tied to sample IDs.

## Material shortlist for initial qualification

Test mechanically distinct materials rather than eight similar ABS-like resins.

### Candidate A — miniature-focused tough resin
AmeraLabs TGM-7.

Reason:
- designed for tabletop miniatures;
- high manufacturer-listed elongation;
- useful detail/durability target.

Specific test:
- dimensional/retention aging because its published 24-hour water absorption is high enough to warrant attention.

### Candidate B — stiffer engineering-tough resin
Siraya Tech Blu Tough or Blu Nylon Black.

Reason:
- stronger/stiffer target;
- useful contrast to TGM-7.

Blu Nylon Black is especially interesting for a less-brittle rigid connector candidate.

### Candidate C — inexpensive baseline
One readily available ABS-like hobby resin such as Anycubic ABS-Like Pro 2 or ELEGOO ABS-Like V3.

Reason:
- establish whether specialty resin produces enough real benefit to justify cost/process complexity.

### Candidate D — controlled toughening blend
One chosen base resin + Siraya Tenacious.

Run a small blend ladder **by mass** after the base materials have already been characterized.

Do not begin with a blend. Otherwise the system has no baseline.

### Professional reference later
If Form 4-class hardware becomes available, compare Tough 1500 V2/Tough 2000 V2 against the winning hobby process.

## First geometry to make

Do not start with a complete minifigure.

Implement these parametric families:

1. hand-held bar ladder;
2. headwear socket ladder;
3. neck/armor opening ladder;
4. thin blade/shaft ladder;
5. clip test;
6. generic geometry benchmark;
7. orientation/warp study;
8. inspection nest;
9. force-test fixture.

Then make:
1. simple sword;
2. simple helmet;
3. ornate sword;
4. ornate helmet/hair;
5. shoulder/neck armor.

This sequence isolates connector physics before complex visual shells.

## Digital workflow for every experiment

```
experiment spec
 -> schema validation
 -> generator
 -> exact geometry hash
 -> process-profile selection
 -> slice
 -> UVtools/G-code preflight
 -> build manifest
 -> printer dispatch
 -> telemetry + status
 -> postprocess checklist
 -> inspection queue
 -> measurement ingestion
 -> analysis
 -> candidate profile update
```

If the experiment definition changes, create a new revision rather than altering the completed record.

## First physical experiments

### E001 — resin exposure baseline
Purpose:
- stable cure/detail window for each material.

Do not decide connector dimensions yet.

### E002 — generic dimensional benchmark
Purpose:
- characterize outer/inner features across build plate.

### E003 — post-cure dimensional change
Measure same samples:
- after wash/dry;
- after production cure;
- later time point.

### E004 — 3.18-family hand-bar ladder
Sweep dimensions around the expected fit.

Use sacrificial/reference fixtures first.

### E005 — force-vs-diameter
Measure insertion/removal force for E004.

This converts "tightness" into data.

### E006 — repeated-cycle hand-bar study
Cycle selected values until:
- defined count;
- damage;
- retention loss.

### E007 — orientation study
Same geometry in multiple orientations.

Measure:
- X/Y diameter;
- straightness;
- fracture;
- support scars;
- force.

### E008 — headwear socket ladder
Measure insertion/removal/rotational retention.

### E009 — neck armor/articulation
Check neck fit plus head/arm movement.

### E010 — thin weapon study
Blade/shaft thickness vs:
- straightness;
- bend;
- drop;
- fracture.

### E011 — support strategy
Compare contact size/location/raft strategy.

Optimize:
- automatic release;
- scar size;
- support removal time.

### E012 — build-position study
Repeat the same coupons across corners/center.

### E013 — same-build repeatability
Many identical coupons on one plate.

### E014 — between-build repeatability
Same plate on multiple days.

### E015 — material comparison
Use one frozen geometry/profile methodology across candidates.

### E016 — blend study
Only after baseline candidate selection.

### E017 — creep/retention
Leave assembled samples under defined time/temperature conditions.

### E018 — color-through resin study
Only mechanically acceptable resin/color systems.

Measure:
- color;
- dimensions;
- force;
- aging.

### E019 — finished accessory pilot
One sword, one helmet, one armor item.

### E020 — small batch pilot
Produce enough units to obtain:
- real accepted yield;
- labor seconds;
- resin consumption;
- support waste;
- QC time;
- per-part economics.

Only after E020 should Brickmen make a serious equipment/tooling ROI decision.

## Automation milestones

### Milestone 1 — digital reproducibility
No manual slicer clicking required for standard experiments.

### Milestone 2 — automatic queue/traceability
Selecting an experiment generates:
- geometry;
- builds;
- manifests;
- labels;
- print queue;
- inspection queue.

### Milestone 3 — automatic analysis
Measurements produce:
- compensation regression;
- plots;
- candidate fit window;
- drift alarms.

### Milestone 4 — automatic profile proposal
The system proposes a new connector/process profile with exact evidence.

Human approval still required for promotion.

### Milestone 5 — instrumented physical test
Motorized insertion/removal and cycles produce raw force curves automatically.

### Milestone 6 — vision QC
Fixed-camera station classifies obvious defects and straightness/geometry.

### Milestone 7 — standardized wet process
Wash/cure uses logged recipes, labeled baskets and interlocks.

### Milestone 8 — automated handling
Only after data proves unload/transfer/support removal is a meaningful bottleneck.

## Primary recommendation

The fastest route to a genuinely automated Brickmen manufacturing system is **not** buying the most automated printer first.

It is:

1. make connector/coupon geometry parametric;
2. make all experiments machine-readable;
3. collect force/dimension/yield/labor data;
4. select the best material/process from evidence;
5. automate repetitive physical handling only after the stable workflow is known.

This keeps early capital low while making every prototype useful training data for the eventual factory.

## Related Brickmen documents

- `parametric-cad-and-connector-automation.md`
- `automated-additive-manufacturing-cell.md`
- `additive-manufacturing-validation-program.md`
- `additive-manufacturing-equipment-and-automation-options.md`
- `additive-manufacturing-economics-and-process-crossover.md`
- `data/additive-material-candidates.json`
- `data/additive-manufacturing-automation-contracts.json`
- `data/additive-manufacturing-validation-plan.json`
- `data/additive-process-selection-rules.json`
