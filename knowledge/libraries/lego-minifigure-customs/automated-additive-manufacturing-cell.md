# Automated Additive Manufacturing Cell for Custom Minifigure Parts

Research status: architecture pass, 2026-09-27.

## Goal

Build a provider-independent manufacturing subsystem that can take an approved custom-part design from structured specification through process selection, validated slicing, print dispatch, physical production, post-processing, metrology, fit testing, QC, inventory and learning with the least safe human labor possible.

The target is **closed-loop manufacturing**, not merely "send an STL to a printer."

## Top-level pipeline

```
DesignSpec
  -> geometry resolver
  -> validated connector insertion
  -> DFM/printability analysis
  -> process selector
  -> material/profile selector
  -> build planning/nesting
  -> slicer
  -> slice-file lint/repair
  -> job scheduler
  -> printer dispatch
  -> live telemetry/failure detection
  -> unload
  -> wash/clean
  -> cure/condition
  -> support removal/finish
  -> dimensional inspection
  -> fit/force inspection
  -> visual inspection
  -> decorate/coat
  -> final QC
  -> inventory/package
  -> empirical profile update
```

Every arrow must create provenance. No stage may silently substitute a material, connector revision, resin profile or process.

## Capability tiers

### Tier A: inexpensive R&D cell

Purpose: generate excellent prototypes and calibration data at minimum capital cost.

Candidate stack:

- fine-pixel hobby MSLA printer such as ELEGOO Mars 5 Ultra-class hardware;
- dedicated wash/cure equipment;
- inexpensive FDM printer with 0.20-0.25 mm nozzle for fixtures/jigs;
- digital micrometer/calipers/pin gauges;
- small force gauge + test stand;
- controlled camera/microscope;
- local PC running CAD/Blender/OpenSCAD helpers, slicer, UVtools and Agent OS services.

Automation level:

- digital preparation: high;
- job sending/monitoring: medium-high where supported;
- chemical handling/unloading: mostly manual;
- metrology/QC: semi-automatic;
- profile learning: high.

ELEGOO documents Wi-Fi cluster printing, camera monitoring, resin-level/residue sensing and network control for Mars 5 Ultra. Treat these as useful operator/queue features; there is not currently a documented stable public developer API comparable to OctoPrint/Moonraker/Formlabs API in the sources reviewed. Build the adapter behind an interface so ChituManager/vendor control can later be replaced.

### Tier B: open/control-oriented print farm

Purpose: maximize hackability and headless control.

FDM:

- Prusa + PrusaLink/Prusa Connect;
- or Klipper + Moonraker;
- or conventional printer + OctoPrint.

These ecosystems expose documented machine/job/file APIs.

Resin:

- prefer slicer/file automation via PrusaSlicer SLA output + UVtools where the chosen printer format is supported;
- a Prusa SL1-family adapter can leverage Prusa's software ecosystem if maintained hardware is available;
- hobby MSLA printer dispatch may still require vendor-specific LAN integration.

### Tier C: professional API-driven resin production

Formlabs exposes an API intended to prepare models, slice, upload jobs, automate batch production, and connect printer status to MES/software.

Important generation caveat:

- **Form Auto is documented for Form 3/3+**, where it can automatically remove parts from Build Platform 2 and continue a queue.
- **Form 4 has the stronger current accuracy/speed proposition and Formlabs API support, but do not assume Form Auto compatibility unless Formlabs explicitly adds it.**

So today there is a tradeoff between the best characterized newer print engine and proven automatic part ejection in the older automation ecosystem.

## Digital-control adapters

Define these interfaces independent of vendor:

```
slicer.slice(job)
slicer.validate(slice)
printer.capabilities()
printer.upload(slice)
printer.enqueue(job)
printer.start(job)
printer.pause(job)
printer.abort(job)
printer.status()
printer.telemetry()
printer.camera()
printer.history()
postprocess.wash(job)
postprocess.cure(job)
inspection.capture(job)
inspection.measure(job)
fit_test.run(job)
```

### Resin slice preparation

#### PrusaSlicer

PrusaSlicer has command-line operation and supports SLA export. This makes it useful as a reproducible/headless build-preparation layer where its resin workflow matches the target machine.

#### UVtools

UVtools is strategically important because it supports many resin formats and exposes a CLI plus a .NET library.

Current documented capabilities include:

- detect islands/overhangs/resin traps/suction cups/touching bounds;
- print issue reports;
- set properties;
- run operations/scripts;
- convert known resin formats;
- copy parameters;
- inspect print properties/G-code;
- calibration tools.

Pipeline policy:

```
sliced file
 -> UVtoolsCmd print-issues
 -> policy classifier
 -> automatic safe correction only for approved issue classes
 -> re-analysis
 -> human/re-model gate for unresolved structural issues
```

Do **not** blindly auto-repair everything. UVtools' maintainer explicitly warns that many detected issues do not have a trustworthy automatic fix. The agent should distinguish:
- deterministic repair,
- acceptable known exception,
- reslice/reorient,
- geometry redesign,
- manual review.

### FDM slicing

Preferred headless candidates:

- OrcaSlicer CLI: current wiki documents headless slicing for automation/batch/CI;
- PrusaSlicer CLI;
- CuraEngine for lower-level integration where profiles are explicitly controlled.

Never accept an unversioned GUI preset as production state. Store the complete process/material/printer profile or a hashable deterministic reference to it.

## Printer-control options

### OctoPrint

Documented REST API supports:

- file upload/storage,
- job commands,
- printer state,
- temperatures,
- printer profiles,
- system operations,
- direct commands where authorized.

Use it when the printer speaks normal serial/G-code and no better native API exists.

### Klipper + Moonraker

Moonraker exposes HTTP/WebSocket/JSON-RPC APIs around Klipper, including:

- printer objects/status,
- file management,
- job queue/history,
- webcam,
- device/sensor/switch control.

This is an excellent base for custom automated FDM fixtures because external sensors and cell devices can be integrated into the same control layer.

### PrusaLink / Prusa Connect

Prusa publishes an OpenAPI specification for PrusaLink Web and a Python Prusa Connect printer SDK. The OpenAPI spec includes printer info/status/telemetry endpoints.

### Hobby resin vendor LAN control

ELEGOO/CHITUBOX document:

- LAN network sending,
- ChituManager,
- printer association,
- remote control,
- Wi-Fi cluster printing on supported machines.

Because developer-level API stability is unclear, wrap all such calls in a replaceable adapter and record firmware/software versions.

## Agent-facing job object

Every manufacturing job should contain:

```json
{
  "job_id": "...",
  "part_revision": "...",
  "quantity": 0,
  "process": "msla|sla|fdm|cast|printed_injection_mold|outsourced_mold",
  "machine_profile_id": "...",
  "material_profile_id": "...",
  "connector_profile_ids": [],
  "orientation_profile_id": "...",
  "support_profile_id": "...",
  "slice_profile_id": "...",
  "postprocess_profile_id": "...",
  "qc_profile_id": "...",
  "source_geometry_hash": "...",
  "sliced_file_hash": "...",
  "rights_record_id": "...",
  "status": "...",
  "exceptions": []
}
```

## Automated process selection

Use constraints, not aesthetic preference.

### Resin score increases with

- very small decorative detail;
- organic curvature;
- engraved/raised microfeatures;
- short production run;
- complex accessory silhouette;
- need for smooth surface;
- high build-plate batching efficiency.

### FDM score increases with

- larger size;
- low microdetail requirement;
- fixture/jig purpose;
- low chemical-handling tolerance;
- need for cheap large structures;
- suitable thermoplastic mechanics.

### Printed-tooling score increases with

- design is stable;
- thermoplastic behavior matters;
- quantity exceeds comfortable direct-print labor;
- geometry has a moldable parting/ejection strategy;
- projected cost beats direct additive production.

### Traditional mold quote gate

Trigger a quote/review when:

- repeat sales consume substantial printer capacity;
- per-part postprocessing dominates;
- print yield is stable enough to know the true unit economics;
- the design is unlikely to change;
- color-through-material and mechanical consistency matter.

## Calibration service

The cell maintains **MachineMaterialProfile** records.

Recalibration triggers:

- new resin/filament SKU or lot;
- pigment recipe change;
- layer-height change;
- screen/FEP/film replacement;
- nozzle replacement;
- firmware/profile change;
- cure station change;
- temperature regime change;
- dimensional drift in QC;
- scheduled cycle/hour threshold.

Calibration output should be machine-readable compensation functions, not only prose.

For example:

```
target hand bar fit = removable friction
printer/resin/profile = M5U + resin-X + rev-7
orientation = grip-axis-Z30
CAD diameter -> measured diameter regression
CAD diameter -> insertion force regression
recommended CAD diameter = ...
confidence interval = ...
sample_count = ...
```

The exact number is learned from physical tests.

## Vision QC

Start with deterministic imaging before sophisticated AI.

Fixture requirements:

- fixed camera/microscope;
- fixed focus/distance;
- controlled diffuse light;
- matte reference background;
- fiducial scale;
- known part pose.

Inspection stages:

1. segmentation/presence,
2. silhouette match,
3. obvious missing supports/features,
4. warp/straightness estimate,
5. connector-surface defect detection,
6. surface scar/void/bubble detection,
7. decoration registration/color check.

OpenCV camera calibration and fiducial/ArUco tooling are suitable building blocks for pose/scale normalization. Vision should not replace physical gauging for critical connector fits until its uncertainty is proven adequate.

## Dimensional metrology

### Initial low-cost station

- 0.001 mm-reading micrometer where geometry allows;
- quality 0.01 mm caliper for noncritical dimensions;
- pin/plug gauge sets for bores;
- go/no-go custom fixtures;
- microscope for small feature inspection;
- force gauge for fit.

"Display resolution" is not measurement uncertainty. Each device needs calibration/check records.

### Scanner role

Consumer 3D scanners can assist surface comparison, but they are not automatically fit-gauge replacements. For example, Shining 3D lists Einstar Vega HD resolution down to 0.05 mm, which is useful for shape capture but relatively coarse versus connector changes that may occur in hundredths of a millimeter.

Use scanning for:
- gross shape/silhouette;
- wear mapping;
- reverse-engineering support;
- comparative surface deviation.

Use gauges/micrometry for critical pins/holes.

## Automated fit-force station

Build a small instrumented linear stage with:

- sacrificial standardized hand/head/neck fixtures;
- load cell/force gauge;
- repeatable insertion speed;
- displacement measurement;
- camera;
- cycle counter.

Capture:
- peak insertion force,
- average insertion force,
- peak removal force,
- hysteresis,
- cycles,
- visible strain/whitening,
- crack event,
- final retention.

The resulting force-vs-displacement curve is much more useful than "fits tight."

## Post-processing automation

### Resin washing

Automatable variables:

- solvent identity/lot,
- contamination proxy,
- wash time,
- agitation,
- temperature,
- first/second bath,
- drying time.

Do not over-wash by default; validated material instructions control the range.

### Cure

Record:

- wavelength/station,
- time,
- temperature,
- orientation/rotation,
- delay after wash.

A different cure schedule can change final dimensions and mechanics, so cure is part of the material profile.

### Support removal

This remains a major automation bottleneck for irregular tiny parts.

Design-for-automation responses:

- standardized support raft interfaces;
- orient supports onto hidden sacrificial surfaces;
- weak/tapered breakaway tips within validated limits;
- grouped support trees that detach predictably;
- clip/fixture that holds the raft during removal;
- robotic removal only after failure consequences are understood.

### Finishing

Sanding, filling, paint and support cleanup are highly variable and reduce full automation feasibility. The best automation strategy is often to **design the print so finishing is unnecessary**.

## Safety cell

NIOSH guidance makes chemical-handling automation a first-class design goal.

Minimum monitored state:

- enclosure door,
- exhaust flow,
- VOC/airflow alarm where appropriate,
- resin vat/dispense state,
- wash solvent container closed/open,
- cure chamber state,
- robot/actuator motion state,
- spill tray status,
- fire/smoke alarm integration,
- emergency stop.

Rules:

- printer cannot start without ventilation confirmation when required;
- robot cannot move in service mode;
- cure UV source cannot operate with interlock open;
- automated resin dispensing has maximum-volume/time safety cutoffs;
- any spill/unknown state halts the cell.

## Scheduling

MSLA/SLA scheduling is height-sensitive: adding more parts at the same layer height often increases material/peel load but does not scale time linearly with part count the way sequential processes do.

The nesting optimizer should minimize:

- tallest build height where practical,
- peel-force spikes,
- duplicated support waste,
- part-to-part collision,
- orientation-induced QC risk,

while maximizing:

- validated plate utilization,
- same-material/profile batching,
- traceable separation of revisions.

Never mix parts requiring incompatible exposure/post-cure profiles simply to fill the plate.

## Failure taxonomy

Digital:
- NONMANIFOLD
- THIN_FEATURE
- UNSUPPORTED
- ISLAND
- RESIN_TRAP
- SUCTION_CUP
- BOUNDS
- WRONG_SCALE
- WRONG_PROFILE

Print:
- DETACH
- DELAM
- WARP
- BLOOM
- OVEREXPOSE
- UNDEREXPOSE
- SUPPORT_FAIL
- LCD_PIXEL
- FILM_DAMAGE
- RESIN_LOW
- THERMAL
- STRING
- LAYER_SHIFT

Postprocess:
- OVERWASH
- UNDERWASH
- OVERCURE
- UNDERCURE
- SUPPORT_SCAR
- BREAK
- SAND_DAMAGE
- CONTAMINATION

QC:
- DIM_HIGH
- DIM_LOW
- FIT_TIGHT
- FIT_LOOSE
- FORCE_HIGH
- FORCE_LOW
- SURFACE
- COLOR
- REGISTRATION
- MISSING_FEATURE

## Autonomous-learning guardrail

The agent may propose a new compensation/profile after enough measurements, but should not silently overwrite the production profile.

State machine:

Observed -> Candidate Profile -> Validation Plate -> Repeatability Test -> Approved Profile -> Production.

Rollback every profile revision.

## Recommended implementation order

### Phase 0: data/control contracts
- schemas for machines, materials, profiles, jobs, coupons, measurements and failures;
- deterministic hashes;
- provenance.

### Phase 1: digital automation
- model preflight;
- connector insertion;
- process selection;
- PrusaSlicer/Orca/UVtools CLI adapters;
- slice validation.

### Phase 2: one resin printer + one FDM printer
- job dispatch;
- telemetry;
- camera capture;
- manual unload/wash/cure but fully logged.

### Phase 3: metrology feedback
- connector coupon generator;
- gauges;
- force test station;
- dimensional regression;
- automatic profile suggestions.

### Phase 4: postprocess cell
- monitored wash/cure;
- ventilation/interlocks;
- standardized trays;
- limited robotic transfer if economically justified.

### Phase 5: farm scheduling
- multiple printers;
- machine capability matching;
- build nesting;
- queue recovery;
- consumables/predictive maintenance.

### Phase 6: bridge manufacturing
- casting records;
- printed injection molds;
- mold-cycle QC;
- automatic mold-vs-print economic trigger.

## Key sources

- Formlabs API / PreForm: https://formlabs.com/software/preform/
- Formlabs Automation Ecosystem: https://formlabs.com/3d-printers/automation/
- Form Auto: https://formlabs.com/3d-printers/form-auto/
- UVtools: https://github.com/sn4k3/UVtools
- PrusaSlicer CLI: https://github.com/prusa3d/PrusaSlicer/wiki/Command-Line-Interface
- OrcaSlicer CLI: https://github.com/OrcaSlicer/OrcaSlicer/wiki/cli_mode
- OctoPrint REST API: https://docs.octoprint.org/en/main/api/index.html
- Moonraker API: https://moonraker.readthedocs.io/en/latest/external_api/introduction/
- PrusaLink OpenAPI: https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml
- Prusa Connect SDK: https://github.com/prusa3d/Prusa-Connect-SDK-Printer
- CHITUBOX network sending: https://docs.chitubox.com/en-US/chitu-manager/latest/ui-and-features/network-sending
- ELEGOO Mars 5 Ultra: https://www.elegoo.com/products/mars-5-ultra-9k-7inch-monochrome-lcd-resin-3d-printer
- NIOSH vat photopolymerization safety: https://www.cdc.gov/niosh/media/pdfs/2025/01/Safe-3D-Printing.pdf
- OpenCV calibration/ArUco: https://docs.opencv.org/
