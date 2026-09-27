> **CANONICAL ROADMAP NOTE (2026-09-27):** The unified implementation roadmap is `agentic-custom-parts-and-body-architecture-roadmap.md`. This earlier B0-B14 roadmap remains historical/supporting detail but should not be treated as a separate execution plan.

# Non-Standard Body Systems Roadmap

Created: 2026-09-27

## Objective

Build a reusable Brickmen subsystem that can discover, identify, model, generate, decorate and eventually manufacture non-standard LEGO-compatible humanoid/body architectures.

This roadmap also incorporates the previously researched character-to-accessory generation benchmark as a prerequisite capability.

## Phase B0 — finish geometry-generation benchmark foundation

Priority: high

- implement AccessoryDesignSpec / GeometryCandidate schemas;
- freeze canonical accessory benchmark;
- add Tripo/Meshy/local-model/CAD adapters;
- canonical render + critic harness;
- deterministic connector insertion;
- DFM/printability gate.

Reason:
the same geometry router, render harness and critic infrastructure will generate non-standard body components.

## Phase B1 — body architecture ontology

Priority: immediate

- create BodyArchitecture entity;
- create component graph schema;
- create joint graph schema;
- separate source labels from canonical architecture IDs;
- establish scale profile;
- establish standard-part compatibility matrix;
- establish architecture lineage/supersession.

Initial canonical classes:
- standard minifigure;
- elongated-limb minifigure;
- oversized-torso hybrid;
- Hagrid-style broad giant with standard head;
- classic integrated-head giant;
- modular-head giant;
- specialized creature giant;
- baby/toddler;
- microfigure;
- minidoll;
- custom muscle-body hybrid;
- community printable midfig;
- Alpha-style articulated 7 cm XL body;
- brick-built midfig;
- unknown/proprietary custom body.

## Phase B2 — source scan and architecture census

Priority: high

- scan BrickLink/Rebrickable official body-part families;
- scan HeroBloks releases for body labels and makers;
- scan priority customizer storefronts;
- cluster figures by body architecture rather than product title;
- collect exact examples for Hulk/Thing/Bane/Venom/Kingpin/Colossus/Juggernaut/Beast/Abomination/Killer Croc;
- preserve maker/year/product code;
- maintain unresolved architecture queue.

Deliverable:
`BodyArchitectureObservation` corpus.

## Phase B3 — physical reference acquisition

Priority: high once hardware/sample purchasing begins

Acquire one or more examples of each high-value architecture.

Measure:
- dimensions;
- component graph;
- joints;
- compatibility;
- articulation;
- connector geometry;
- material;
- assembly force.

Do not declare third-party architectures mechanically compatible from catalog images.

## Phase B4 — canonical digital twins

Build neutral digital twins for:
- standard;
- Axl-style oversized hybrid;
- Hagrid broad body;
- classic giant;
- modular-head giant;
- Alpha 7 cm reference architecture;
- Brickmen original Mid prototype;
- Brickmen original XL prototype.

Each twin must contain:
- coordinate frame;
- component segmentation;
- joint axes;
- articulation sweeps;
- connector definitions;
- print/decor surfaces;
- canonical cameras.

## Phase B5 — recognition

Build:
- release lookup;
- visual body detector;
- component segmentation;
- architecture classifier;
- ratio/landmark classifier;
- nearest-neighbor retrieval;
- unknown-body clustering.

Benchmark using held-out figures and makers.

Never collapse uncertain examples into a known architecture solely from visual resemblance.

## Phase B6 — architecture-aware style corpus

For each body:
- normalized face landmarks;
- chest/shoulder/arm ratios;
- sculpted muscle density;
- blockiness/rounding;
- relief/detail density;
- decoration surface grammar;
- print-vs-sculpt decisions.

Create same-character cross-architecture sets, beginning with Hulk.

Goal:
learn style separately from body dimensions.

## Phase B7 — architecture selection agent

Given character/source appearance:
- evaluate standard;
- broad hybrid;
- mid;
- XL;
- giant;
- specialized architecture;
- existing donor availability.

Return candidates + rationale + uncertainty.

Do not infer purely from canonical character height; consider visual language and compatibility.

## Phase B8 — cross-architecture generation

Implement:
`body_style.translate(source, source_architecture, target_architecture)`

Capabilities:
- standard -> mid;
- standard -> giant;
- giant -> XL;
- source realism -> selected Brickmen architecture;
- preserve identity-critical features;
- adapt detail density and articulation boundaries.

## Phase B9 — printable Brickmen Mid

Original, parametric, not a direct clone.

Targets:
- standard head compatibility;
- broad sculpted torso;
- custom arms/hands;
- optional standard lower body or enlarged lower body;
- validated hand-accessory interface;
- swappable body surfaces.

Validate static -> modular -> articulated.

## Phase B10 — printable Brickmen XL

Approximately 7 cm class, inspired by the useful scale/articulation concept rather than copied geometry.

Targets:
- modular head/hair;
- shoulder;
- elbow;
- wrist;
- hips/legs;
- accessory-compatible hands;
- body-wide style map;
- resin/moldable versions.

## Phase B11 — giant modular system

Develop original giant architecture:
- separate head;
- hair/headgear;
- chest/lower body;
- arms;
- hands;
- optional separate legs;
- defined accessory interfaces.

Use official modular-head giant principles as compatibility reference.

## Phase B12 — physical closed-loop generation

Prompt:
"Make [character] as a Brickmen Mid / XL / Giant."

Pipeline:
character -> appearance -> architecture -> body twin -> style translation -> geometry/art -> DFM -> print -> measurement -> correction.

## Phase B13 — learned architecture router

Train from:
- accepted/rejected architecture choices;
- same-character comparisons;
- user preferences;
- print outcomes.

It may recommend, but the selected architecture remains explicit and auditable.

## Phase B14 — manufacturing crossover

Once a body architecture is stable:
- resin prototypes;
- printed-tooling experiments;
- thermoplastic molding;
- part-level cost model;
- replace wear-critical resin joints with molded parts where justified.

## Definition of done

A non-standard body architecture is reusable only when Brickmen has:

1. unique architecture ID;
2. source/provenance;
3. component graph;
4. joint graph;
5. scale profile;
6. connector map;
7. standard-part compatibility matrix;
8. canonical digital twin;
9. surface/style map;
10. articulation/keep-out map;
11. physical validation for manufacturing claims;
12. recognition benchmark samples;
13. generation benchmark samples;
14. revision history.
