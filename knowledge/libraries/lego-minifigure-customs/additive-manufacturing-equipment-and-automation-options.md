# Additive Manufacturing Equipment and Automation Options

Research status: current-market architecture survey, 2026-09-27.

## Decision objective

Choose equipment by **automation surface + validated part quality + total labor**, not headline printer resolution.

For Brickmen there are four distinct needs:

1. high-detail minifigure-scale resin R&D;
2. open/headless FDM for fixtures and larger parts;
3. metrology/functional validation;
4. eventual unattended production and post-processing.

No single current machine is clearly best at all four.

## Architecture recommendation

Use a provider-independent controller and expect hardware to change.

```
Brickmen Manufacturing Controller
  |- CAD/connector service
  |- slicer adapters
  |- slice-file validator
  |- printer adapters
  |- post-process adapters
  |- inspection adapters
  |- inventory/consumables
  |- scheduling
  |- safety interlocks
  |- empirical profile store
```

Never let a vendor cloud or slicer project become canonical process state.

## Resin path A — fine-pixel hobby R&D

### Representative hardware: ELEGOO Mars 5 Ultra class

Current manufacturer specs include:
- 18 x 18 micrometer XY pixel pitch;
- 0.01-0.2 mm layer range;
- Wi-Fi;
- AI-camera functions;
- resin shortage/residue/leveling alarms;
- automatic leveling;
- power-loss resume.

Advantages:
- very high image sampling/detail for the price class;
- ideal for large numbers of tiny accessory experiments;
- inexpensive enough to dedicate machines to specific materials later;
- useful built-in failure/resin sensing.

Automation limitations:
- vendor LAN/network software is primarily operator-oriented;
- a stable public developer API comparable to Moonraker/Formlabs is not established in the reviewed official documentation;
- automatic unload/wash/cure is not native.

Use for:
**Phase-1 material, connector and geometry R&D.**

### CHITUBOX / ChituManager

CHITUBOX documents network sending and printer management/remote-control functions for supported printers.

Treat this as an adapter, not the architecture:
- record exact CHITUBOX/ChituManager version;
- keep sliced-file hashes;
- expose only capabilities the adapter can verify;
- preserve a manual fallback.

## Resin path B — professional API-centered workflow

### Formlabs Form 4 generation

Formlabs currently exposes:
- Web API for status, consumables and history;
- Local API for automated job preparation, local printer status and sending jobs;
- batch preparation;
- orientation/layout/support automation;
- slicing/upload;
- printer/MES integration;
- Open Material Mode for 405 nm photopolymers on Form 3/Form 4 generation printers, subject to the vendor's licensing/terms.

Advantages:
- strongest documented developer surface among researched resin ecosystems;
- characterized dimensional performance;
- automated resin handling;
- validated materials and process controls;
- straightforward MES-style integration.

Tradeoffs:
- substantially higher capital/material ecosystem cost than hobby MSLA;
- headline XY pixel pitch is not as small as some hobby LCD printers;
- full unattended part removal is not currently a generic Form 4 feature in the documented Form Auto product.

Use for:
**production process where API/repeatability/labor outweigh cheapest raw print.**

### Important Form Auto compatibility distinction

Form Auto is documented for:
- Form 3/3+;
- Form 3B/3B+.

It automatically:
- removes parts from Build Platform 2;
- deposits them in a UV-blocking container;
- starts the next queued print;
- captures part-removal images/video.

Do **not** assume Form Auto works with Form 4. It is a separate older-generation automation route.

Thus the present trade:
- Form 4: newer print engine + developer platform;
- Form 3 + Form Auto: native automatic ejection/continuous queue.

This may change; capability detection must query current vendor documentation before procurement.

## Resin path C — custom robotic Form 4 cell

A 2025 DHR Engineering proof of concept documents:
- Form 4 build-platform swapping;
- robotic transfer to Form Wash V2;
- automatic preparation for next job;
- custom robot grippers, including FDM TPU contact parts;
- roadmap to automated cure/expanded Form 4L systems.

This demonstrates that Form 4 hardware can be integrated into a robotic cell even without Form Auto.

For Brickmen, this is a **future phase**, because:
- robot safety adds substantial engineering burden;
- tiny loose parts complicate support/removal;
- support removal/inspection remain downstream bottlenecks;
- capital only pays off after demand exists.

But software contracts should be robot-ready from the beginning.

## Emerging integrated print-to-cure systems

RIPP publicly describes a working prototype integrating:
- MSLA print;
- drain;
- wash;
- UV cure;
- final unload;

with the build platform remaining in the machine through stages.

This is evidence that compact print-to-cure architecture is technically plausible. Treat emerging systems as watchlist candidates rather than production dependencies until shipping/support/API/quality are validated.

## Industrial automated resin post-processing

PostProcess Technologies currently markets systems for:
- automated excess-resin removal;
- automated support removal for supported processes;
- software-controlled recipes;
- safer reduced-touch operation;
- all-in-one clean/rinse/dry/cure in some product families.

The DEMI X 200 Plus is notable as a compact architecture example: its published workflow automates cleaning, rinsing, drying and curing in one system.

This class of equipment is likely overkill for early Brickmen production but proves that post-processing is automatable and gives the controller a future adapter target.

## Flexible build plates

Formlabs' Form 4 Flex Build Platform and third-party hobby flex plates show a useful mechanical concept: **bend the surface to release the raft instead of scraping each part.**

For tiny parts:
- group/overlap rafts where appropriate;
- standardize raft geometry;
- catch released parts in a contained basket;
- design the removal action around the raft, not individual accessories.

Formlabs specifically notes that very small parts may not release reliably from its flex platform unless grouped into larger overlapping rafts.

This strongly supports a Brickmen rule:
**automation-friendly raft design is part of the manufacturing contract.**

## FDM printer-control options

### Klipper + Moonraker

Best fit for custom factory hardware when openness matters.

Moonraker provides:
- HTTP;
- WebSocket;
- JSON-RPC;
- printer object/status;
- file management;
- queues/history;
- webcam;
- extensible sensors/devices.

Role:
**automation fixtures, jigs, machine parts, custom cell hardware.**

### OctoPrint

Mature REST adapter for many conventional FDM machines:
- files;
- jobs;
- state;
- temperatures;
- system operations.

Role:
**vendor-neutral bridge for serial/G-code printers.**

### PrusaLink / Prusa Connect

Official API/SDK surfaces make Prusa hardware attractive for a controlled production fleet.

### Bambu

High-quality automated consumer printers can be useful, but the Brickmen controller should not depend on an undocumented cloud protocol. Use supported/local interfaces or an isolated adapter and keep process artifacts portable.

## Open-source resin control

Open Resin Alliance Odyssey is an active open-source backend for Apollo/Prometheus-style MSLA hardware and currently documents a REST API.

This is strategically interesting for a **future fully controllable custom resin printer**, but it remains a specialist/open-hardware route and should not displace proven commercial printers during early materials research.

## Print-farm scheduler principles

Each machine reports capabilities:

```json
{
  "process": "msla",
  "build_volume_mm": [153.36, 77.76, 165],
  "materials_approved": ["profile-id"],
  "network_dispatch": true,
  "remote_start": true,
  "camera": true,
  "resin_level_sensor": true,
  "automatic_unload": false,
  "automatic_wash": false,
  "automatic_cure": false,
  "inspection_station": null
}
```

Scheduler chooses only a machine that matches:
- process;
- material;
- layer/profile;
- volume;
- connector validation;
- post-process chain;
- safety state.

## Practical Brickmen equipment ladder

### Phase 1 — learn cheaply

Resin:
- one fine-pixel hobby MSLA printer;
- enclosed ventilation;
- wash/cure station;
- UVtools-based slice QA;
- manual plate transfer.

FDM:
- one reliable modern FDM printer;
- 0.20/0.25 and standard nozzle capability;
- headless network path where possible.

Metrology:
- quality micrometer;
- caliper;
- pin gauges/custom go-no-go gauges;
- microscope/camera;
- scale;
- manual low-force gauge initially.

Objective:
**learn connector/material/process physics before buying production automation.**

### Phase 2 — instrument

Add:
- motorized force/displacement test station;
- standardized camera inspection;
- temperature/resin conditioning;
- barcode/QR sample tracking;
- automatic profile analysis.

Objective:
**turn subjective iteration into data.**

### Phase 3 — production queue

Add:
- multiple printers;
- local scheduler;
- automatic job dispatch;
- camera failure detection;
- consumables/maintenance tracking;
- standardized rafts/trays.

Keep:
- manual unload/wash/support removal if labor remains tolerable.

### Phase 4 — automate wet handling

Choose based on economics:
- professional integrated wash/cure;
- robotic platform transfer;
- custom enclosed gantry;
- automated resin dispensing;
- automatic part collection.

Objective:
**reduce exposure and labor, not simply add robots.**

### Phase 5 — mold crossover

When stable SKUs consume too much print/post-process capacity:
- printed injection tooling test;
- cast process;
- aluminum/steel mold quotes;
- outsource comparison.

## Procurement scoring model

Score every candidate machine on:

- smallest validated feature, not advertised pixel count;
- dimensional repeatability;
- material range;
- tough-material support;
- local API quality;
- offline operation;
- slicer CLI/API;
- file-format openness;
- remote dispatch/start;
- camera;
- material sensing;
- failure sensing;
- automatic dispensing;
- automatic unload;
- wash/cure integration;
- consumables cost;
- serviceability;
- replacement film/screen/nozzle cost;
- vendor lock-in;
- safety integration;
- empirical Brickmen yield.

Do not convert the score into one permanent universal "best printer." The preferred machine is process/part dependent.

## Sources

- Formlabs API/PreForm: https://formlabs.com/software/preform/
- Formlabs API developer portal: https://formlabs.com/support/Formlabs-API-developer-portal/
- Formlabs Developer Platform: https://formlabs.com/support/Formlabs-Developer-Platform-overview/
- Form Auto: https://formlabs.com/3d-printers/form-auto/
- Form 4 Flex Build Platform: https://formlabs.com/support/Printing-with-the-Form-4-Build-Platform-Flex/
- DHR Form 4 automation proof of concept: https://dhr.is/projects/automated-resin-printing-with-formlabs-form-4
- ELEGOO Mars 5 Ultra: https://www.elegoo.com/products/mars-5-ultra-9k-7inch-monochrome-lcd-resin-3d-printer
- PostProcess: https://www.postprocess.com/
- PostProcess DEMI X 200 Plus: https://www.postprocess.com/product/demi-x-200-plus/
- RIPP: https://ripp3d.com/
- Open Resin Alliance Odyssey: https://openresin.org/projects/odyssey/
