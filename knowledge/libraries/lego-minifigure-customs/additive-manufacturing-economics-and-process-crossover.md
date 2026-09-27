# Additive Manufacturing Economics and Process Crossover

Research status: deep research pass, 2026-09-27.

## Core rule

Brickmen must **never hard-code a universal quantity threshold** such as:

- "resin until 100 parts";
- "injection molding after 1,000 parts";
- "steel after 10,000 parts".

The economically correct process depends on the specific part, plate utilization, height, material, post-processing labor, reject rate, tooling quote, cavity count, design stability, inventory risk, final material requirements and available equipment.

The controller should calculate the crossover for every stable SKU and periodically recompute it from observed production data.

## Why minifigure accessories are unusual economically

Tiny accessories are unusually favorable for vat photopolymerization because:

- many parts can share one build plate;
- print time is primarily a function of the number of layers/build height and the machine's per-layer process, rather than simply multiplying linearly with XY part count;
- the material mass per part can be extremely small;
- no dedicated hard tooling is required;
- revisions cost almost nothing compared with re-cutting a mold.

However, adding more parts is not literally free:
- total exposed cross-section affects peel/separation forces and reliability;
- support/raft resin increases;
- washing/support removal/QC labor scales with the number of parts;
- a failed full plate can destroy more work;
- handling hundreds of tiny objects can dominate economics.

Therefore Brickmen should optimize **plate-level economics**, not only resin grams.

## Cost-per-part model: direct resin printing

For a production run:

```
C_resin_direct =
  (material
   + support_and_raft_material
   + tank_film_screen_wear
   + solvent_and_wash_consumables
   + cure_consumables
   + machine_depreciation
   + energy
   + operator_labor
   + support_removal_labor
   + finishing_labor
   + inspection_labor
   + packaging_handling
   + failed_build_cost
   + rejected_part_cost)
  / accepted_parts
```

Track actuals by job rather than relying indefinitely on estimates.

### Machine utilization

Machine cost per successful part should account for:
- purchase price;
- expected useful service life;
- maintenance/spares;
- screen/light engine/film/tank consumption;
- percentage of time available;
- production utilization;
- scheduled calibration downtime.

### Labor

Labor is likely to become the largest controllable cost as print speed rises.

Formlabs' published 2024 "Race to 1,000" case is useful precisely because its model found labor to be the biggest Form 4 cost factor and a smaller number of larger builds reduced operator time.

That case reported:
- a $3,600 injection mold;
- $0.32 outsourced molded-part variable cost;
- approximately $600 total modeled cost for 1,000 printed mixer-latch parts on two Form 4L machines;
- approximately $3,920 outsourced molding cost for that same 1,000-part scenario;
- a modeled crossover at 13,050 parts.

These values are **case-study inputs, not Brickmen thresholds**. The part used 6 mL of resin, whereas many minifigure accessories will be smaller, but tiny parts may incur disproportionately more handling and support-removal labor.

The correct lesson is:
**measure labor minutes per accepted unit and batch operations aggressively.**

## Build-plate model

Store for every part orientation:

- part envelope;
- effective support footprint;
- build height;
- estimated material;
- estimated support material;
- expected plate count;
- maximum validated parts/plate;
- expected print time;
- wash batch capacity;
- cure batch capacity;
- support-removal seconds/part;
- inspection seconds/part.

Then calculate:

```
plate_accepted_yield =
  loaded_parts * historical_plate_yield * historical_part_acceptance_rate
```

```
effective_machine_minutes_per_part =
  plate_print_minutes / plate_accepted_yield
```

```
effective_operator_minutes_per_part =
  (setup_minutes
   + unload_minutes
   + wash_transfer_minutes
   + cure_transfer_minutes
   + batch_cleanup_minutes) / plate_accepted_yield
  + per_part_support_minutes
  + per_part_finish_minutes
  + per_part_qc_minutes
```

This exposes why automatic unloading or better support design can be more valuable than buying a faster printer.

## FDM economics

FDM is generally less attractive for tiny highly detailed accessories but excellent for:
- jigs;
- fixtures;
- trays;
- stands;
- buildings;
- large props.

Cost model includes:
- filament;
- purge/waste;
- nozzle wear;
- machine time;
- energy;
- support;
- post-process;
- failure;
- labor.

FDM time often scales more directly with deposited volume/path length than MSLA build time, so packing more parts into one FDM plate does not have the same weak time scaling as vat printing.

For fixtures, that is acceptable because:
- detail requirements are lower;
- no resin wash/cure;
- thermoplastic mechanics are useful;
- unattended printing can be easier to automate.

## Silicone mold + urethane/vacuum casting crossover

A printed master can be used to create a silicone mold for repeated rigid casts.

This route becomes interesting when:
- direct-print support cleanup is costly;
- a cast resin has better desired mechanics/appearance;
- a highly polished master can amortize finishing work;
- the quantity is large enough to amortize mold preparation but too low for hard tooling.

Cost model:

```
C_cast =
  master_creation
  + master_finishing
  + silicone_mold_material
  + mold_labor
  + casting_equipment_amortization
  + cast_material
  + mixing/degassing labor
  + cure time/capacity
  + demold/trim labor
  + mold replacement
  + reject cost
```

Formlabs describes vacuum/urethane casting as a small-batch production method using a silicone mold made around a master. Silicone reproduces fine surface detail, which means the master must be finished to the desired surface quality.

Automation implications:
- automated dispensing by weight;
- vacuum/pressure recipe control;
- timed cure queues;
- mold identity/barcode;
- camera inspection;
- automated trim remains difficult for arbitrary tiny parts.

## Printed injection tooling crossover

Printed injection molds are strategically important because they can produce **actual thermoplastic** accessories while avoiding immediate metal-tool investment.

Formlabs currently describes 3D-printed molds as capable of producing hundreds to thousands of parts depending on mold geometry, material and process. Supported thermoplastics in its published guidance include ABS, ASA, PA, PC, PE, POM, PP, TPE and TPU.

A Formlabs/Holimaker case says orders over roughly 1,000 parts moved toward machined aluminum tooling in that particular workflow, while printed molds were used for smaller runs. Again, this is a workflow-specific data point.

Use printed tooling when:
- connector fatigue/material behavior requires thermoplastic;
- the design is stable enough for a mold;
- quantity exceeds comfortable direct-print labor;
- draft/parting/ejection are feasible;
- a benchtop/contract molding path exists;
- tool iteration is still likely.

Automate:
- DFM for draft/undercuts;
- parting-line candidate generation;
- gate/vent/ejector suggestions;
- mold insert generation;
- tool-life/cycle log;
- molded-part dimensional SPC.

## Aluminum and steel injection tooling

Current Protolabs guidance positions:
- aluminum as low/medium-volume or bridge tooling;
- aluminum molds as commonly capable of 10,000 cycles or more, depending strongly on geometry and resin;
- steel for substantially higher-volume production, with a 2025 article using roughly million-part scale as the context where steel becomes compelling.

Those figures are supplier-specific rules of thumb, not Brickmen triggers.

For very small minifigure accessories:
- multi-cavity tooling could radically reduce unit cost;
- tiny cavities may make sprue/runner waste significant;
- automation/ejection and gating can dominate tool design;
- exact ABS/PP/POM/other material choice changes shrinkage and tool design;
- decoration and packaging remain separate costs.

## Design-stability penalty

A key advantage of printing is avoiding stranded tooling.

Define:

```
tooling_revision_risk =
  probability_of_revision * unrecoverable_tooling_cost
```

Add this expected cost when comparing molding during an unstable design phase.

Also model:
- expected SKU lifetime;
- expected annual demand;
- number of variants/colors;
- probability of art/geometry revision;
- inventory carrying cost;
- obsolete stock risk.

This strongly favors digital inventory for long-tail obscure minifigure accessories.

## Variant explosion

A catalog can contain thousands of rarely ordered designs.

For each SKU, classify:

- **digital-stock**: CAD/3MF only, print on demand;
- **micro-stock**: keep a tiny finished buffer;
- **batch-stock**: periodically plate-batch;
- **molded-stock**: stable, high-demand part;
- **outsourced**: external production has superior economics.

The manufacturing controller should forecast demand and choose the state per SKU.

## Color economics

Color-through-material reduces painting labor but can fragment production into many material changes.

Model:
- vat/cartridge change labor;
- flush/waste;
- small-batch pigment mixing;
- calibration cost per color;
- inventory of colored resins;
- cure/mechanical profile variants.

For a low-demand color, it may be cheaper to:
- print neutral + decorate;
- batch many same-color designs;
- use donor/molded colored parts.

For a frequently used color, dedicated material/vat/printer capacity can be justified.

## Automation ROI model

For each automation project:

```
annual_value =
  labor_minutes_eliminated * loaded_labor_rate
  + reject_cost_reduction
  + machine_uptime_value
  + safety/exposure_reduction_value
  + avoided_rework
```

Compare against:
- capital cost;
- engineering cost;
- maintenance;
- floor space;
- additional failure modes;
- safety burden.

Prioritize automation that removes repetitive batch handling:
1. job preparation;
2. slicing/preflight;
3. scheduling;
4. part tracking;
5. resin/material monitoring;
6. standardized wash/cure;
7. vision inspection;
8. data capture;
9. build-platform transfer/unload;
10. arbitrary support removal/finishing last.

## Quote trigger

Automatically request/evaluate an external tooling or production quote when a SKU meets a configurable combination such as:

- validated design revision stable for N builds;
- trailing demand exceeds direct-print capacity threshold;
- operator minutes/part exceed target;
- annualized printer opportunity cost is high;
- thermoplastic mechanics are desired;
- moldability gate passes.

Do not trigger only from unit count.

## Process-choice output

The process-selection service should return an auditable explanation:

```json
{
  "recommended_process": "direct_msla",
  "alternatives": [
    {"process": "urethane_cast", "reason": "..."},
    {"process": "printed_injection_tool", "reason": "..."}
  ],
  "run_quantity": 240,
  "cost_per_accepted_part_estimates": {},
  "capacity_hours": {},
  "operator_hours": {},
  "tooling_risk": {},
  "quality_constraints": [],
  "assumptions": [],
  "confidence": "candidate",
  "quote_required": false
}
```

Never return a process recommendation without listing assumptions and uncertainty.

## Sources

- Formlabs Race to 1,000: https://formlabs.com/blog/race-to-1000-parts-3d-printing-injection-molding/
- Formlabs low-volume printed injection molds: https://formlabs.com/white-papers/low-volume-rapid-injection-molding-with-3d-printed-molds/
- Formlabs injection molding workflow/materials: https://formlabs.com/support/Injection-molding/
- Formlabs silicone mold making: https://formlabs.com/support/Silicone-mold-making-and-silicone-part-production/
- Formlabs vacuum/urethane casting: https://formlabs.com/uk/blog/vacuum-casting-urethane-casting-polyurethane-casting/
- Protolabs aluminum vs steel tooling: https://www.protolabs.com/resources/blog/aluminum-vs-steel-tooling/
- Protolabs 2026 soft vs hard tooling: https://www.protolabs.com/resources/blog/soft-vs-hard-tooling/
