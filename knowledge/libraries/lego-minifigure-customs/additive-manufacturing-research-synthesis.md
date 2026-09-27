# Additive Manufacturing for Custom Minifigure Accessories — Research Synthesis

Research snapshot: 2026-09-27.

## Bottom line

The project is technically feasible today.

The best near-term architecture is:

1. **keep donor/molded body parts for articulation;**
2. **MSLA/SLA-print novel fine-detail accessories;**
3. **use FDM for jigs, fixtures, larger parts and factory hardware;**
4. **treat decoration as a separate UV/pad/decal/paint stage;**
5. **calibrate every functional connector empirically;**
6. **measure insertion/removal force and cycle life, not only dimensions;**
7. **store all process/material/build/postprocess details as versioned profiles;**
8. **automate digital preparation, traceability, inspection and data analysis first;**
9. **automate wet handling/unload only after the stable process is measured;**
10. **move successful high-demand SKUs toward casting or molded thermoplastic only when the economics/material requirement justify it.**

The biggest risk is not whether a modern printer can render a helmet or sword. It is **repeatable mechanical compatibility and long-term durability at tiny interfaces**.

## What is already feasible

### Excellent direct-resin targets
- helmets;
- hair;
- hats;
- armor;
- pauldrons;
- backpacks;
- shields;
- swords;
- guns/blasters;
- tools;
- ornate props;
- creature parts;
- rigid robes/skirts;
- specialty heads;
- masters for casting/molding.

### Good FDM targets
- stands;
- storage/part trays;
- inspection nests;
- calibration fixtures;
- force-test fixtures;
- mold boxes;
- wash/cure carriers;
- large backpacks/props;
- terrain/buildings;
- vehicles;
- automation-cell components.

### R&D targets rather than first production targets
- hands;
- arms;
- torsos;
- hips/legs;
- fully articulated printed figures.

Those pieces are printable geometrically but combine multiple friction joints, fatigue interfaces and tolerance stacks.

## Core technical insight

A nominal connector dimension is not a production specification.

For example, the documented LEGO bar connection family is commonly described around 3.18 mm. But the correct CAD value for a printed accessory depends on:

- printer;
- material;
- layer height;
- exposure;
- orientation;
- build position;
- supports;
- wash;
- cure;
- pigment/blend;
- wear target.

The production target is therefore:

**desired physical fit / force / durability -> empirically learned CAD compensation**

not:

**internet nominal dimension -> print unchanged.**

## Material conclusion

Do not default to brittle "standard resin."

The first qualification program should compare mechanically different materials:

- miniature-focused tough resin: AmeraLabs TGM-7;
- stiffer tough resin: Siraya Tech Blu Tough or Blu Nylon Black;
- economical ABS-like baseline;
- controlled Tenacious blend only after the base resin is understood;
- Formlabs Tough 1500/2000-class materials later if professional API-driven production is justified.

Datasheets are screening evidence only.

The material winner must survive:
- dimensions;
- insertion/removal force;
- repeated cycles;
- thin-feature testing;
- drops where relevant;
- creep/retention;
- aging;
- finishing/decorating.

## Color conclusion

Color-through-material is worth pursuing because it can eliminate painting labor and hides wear.

But color and mechanics are coupled.

A pigment recipe that matches a target color but makes a sword brittle or changes grip diameter is not a valid recipe.

Optimize:
- measured cured color;
- dimensional fit;
- mechanics;
- surface finish;
- repeatability

together.

## Automation conclusion

### Automate immediately

- job/spec schemas;
- CAD connector generation;
- coupon generation;
- process selection;
- slicer invocation;
- slice preflight;
- manifest/hash generation;
- printer queue where API exists;
- QR/barcode traceability;
- camera capture;
- measurement ingestion;
- force-curve analysis;
- compensation regression;
- cost/yield/labor tracking;
- profile-candidate generation.

### Standardize before automating physically

- plate unload;
- wash transfer;
- cure;
- support removal;
- sample sorting;
- final finishing.

### Automate physically later

- build-platform swap;
- wet transfer;
- washing;
- curing;
- batch collection;
- vision sorting;
- robotic handling.

Do not robotize a process that is still changing every experiment.

## Best software abstraction

```
manufacturing.plan()
geometry.compose()
connector.generate()
dfm.preflight()
process.select()
slicer.slice()
slice.validate()
printer.enqueue()
printer.monitor()
postprocess.execute()
inspection.measure()
fit_test.run()
quality.classify()
economics.record()
profile.propose()
profile.validate()
profile.promote()
```

Every function should accept provider-independent records.

## Preferred geometry architecture

### Parametric precision geometry
CadQuery/OpenCascade.

Use for:
- connectors;
- coupons;
- gauges;
- fixtures;
- jigs;
- simple hard-surface accessories;
- tooling.

### Organic shells
Blender or equivalent mesh/sculpt workflow.

Before manufacturing:
- normalize;
- repair;
- remove untrusted functional interfaces;
- insert validated parametric connector;
- apply keep-outs/articulation;
- run deterministic DFM.

### Files
- source Python/native CAD;
- STEP where practical;
- 3MF manufacturing exchange;
- STL only for compatibility.

## Process decision

### Direct resin
Best default for high-detail, low-volume, high-variant accessories.

### FDM
Best for macro geometry and production infrastructure.

### Silicone mold / urethane casting
Evaluate when one polished master can amortize finishing and casting material/process offers an advantage.

### Printed injection tooling
Evaluate when:
- design is stable;
- thermoplastic properties matter;
- direct-print labor becomes expensive;
- quantity is beyond comfortable direct printing but hard tooling is premature.

### Aluminum/steel molds
Evaluate from actual quotes/demand/cavity count and revision risk.

There is no universal quantity crossover.

## Economic insight

Tiny MSLA parts can be plate-batched efficiently, so the largest avoidable production cost may become **human handling rather than resin**.

Measure:
- setup minutes/plate;
- unload minutes;
- wash/cure transfer minutes;
- support-removal seconds/part;
- inspection seconds/part;
- reject rate;
- accepted parts/plate.

That data determines whether the next dollar should buy:
- another printer;
- larger build area;
- automatic unload;
- better support design;
- vision QC;
- molding tooling.

## Quality standard

A production-approved component needs:

- exact part revision;
- exact material/lot;
- machine/build profile;
- slice hash;
- wash/cure profile;
- critical dimensions;
- functional fit/force;
- relevant cycle/durability evidence;
- cosmetic acceptance;
- golden sample/images;
- batch traceability;
- acceptance limits.

A beautiful first print is a prototype, not a manufacturing process.

## First implementation

Follow:
- `additive-manufacturing-first-cell-plan.md`
- `data/additive-first-experiments.json`

The physical program deliberately begins with exposure/dimensional coupons, then the hand-held bar, force curves, cycle testing, orientation, headwear, neck armor, thin weapons, support strategy, repeatability, materials, aging and finally finished accessories/small-batch economics.

## Key unresolved questions

Only physical experiments can now resolve:

1. Which resin gives the best detail/toughness/fit for the actual printer?
2. What CAD bar/socket dimensions produce the desired force?
3. What is the safe upper fit force for donor parts?
4. How fast do printed connectors wear or creep?
5. Which orientation/support policy minimizes warping/scarring?
6. How much post-processing labor remains after DFM optimization?
7. What is the real accepted yield?
8. What is the true cost per accepted part?
9. At what demand does molding beat printing for each SKU?
10. Does color-through resin retain the same functional profile?

These are intentionally retained as experiments rather than filled with unsupported assumptions.

## Research files

Core:
- `additive-manufacturing-feasibility.md`
- `resin-custom-parts.md`
- `resin-fit-calibration.md`
- `fused-filament-custom-parts.md`
- `parametric-cad-and-connector-automation.md`
- `additive-manufacturing-validation-program.md`
- `automated-additive-manufacturing-cell.md`
- `additive-manufacturing-equipment-and-automation-options.md`
- `additive-manufacturing-economics-and-process-crossover.md`
- `additive-manufacturing-product-safety.md`
- `additive-manufacturing-first-cell-plan.md`

Structured:
- `data/additive-material-candidates.json`
- `data/additive-manufacturing-automation-contracts.json`
- `data/additive-manufacturing-validation-plan.json`
- `data/additive-process-selection-rules.json`
- `data/additive-first-experiments.json`

The research backlog explicitly distinguishes completed desk research from physical-validation work that remains.
