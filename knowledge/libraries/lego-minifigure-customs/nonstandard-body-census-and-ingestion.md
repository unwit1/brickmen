# Non-Standard Figure Body Census and Ingestion

Research snapshot: 2026-09-27

## Purpose

Build a repeatable scan that discovers non-standard minifigure/custom body architectures instead of relying on memory or a one-time Hulk survey.

The census covers:

1. official LEGO figure/body systems;
2. compatible/clone body systems;
3. custom manufacturer body systems;
4. premium sculpted bodies;
5. community 3D-printable bodies;
6. brick-built intermediate bodies;
7. unknown/new market architectures.

The output is **release-level architecture evidence**, not a flat list of labels.

## Canonical entity

Use `FigureArchitecture`.

Do not create new writes under the older `BodyArchitecture` draft name. The legacy body-architecture ontology is retained only as an alias bridge.

## Why release-level classification is mandatory

Three labels are especially dangerous:

### BigFig
Used for:
- official LEGO Giant bodies;
- compatible clones of those bodies;
- custom designs merely inspired by the large scale;
- maker-specific proprietary bodies.

It does not prove joint compatibility.

### Midfig
Community/custom shorthand for "between minifigure and BigFig." It can mean:
- custom molded/printed torso + arms;
- a brick-built body;
- standard lower body + oversized torso;
- an entirely new articulated body.

It is not one mechanical standard.

### Maker/code prefix
A maker can ship multiple architectures. For example, G (2) GH0304 Hulk is visually a near-standard muscular hybrid, while HeroBloks separately classifies G (2) GH0318 Kingpin as a BigFig. A prefix cannot be promoted directly to a body architecture.

## Official census dimensions

Scan BrickLink/Rebrickable/LDraw for component families that alter:

- torso construction;
- shoulder count;
- arm segmentation;
- hand system;
- head integration;
- hip/lower-body system;
- leg count;
- locomotion footprint;
- tail/tentacle/centaur geometry;
- figure scale.

Initial official architecture families now include:

- standard minifigure;
- short/medium/long limbs;
- stacked-torso multi-arm;
- Axl oversized-torso hybrid;
- Hagrid giant-body hybrid;
- early integrated-head Giant;
- later modular-head Giant;
- specialized creature Giant;
- baby/toddler;
- microfigure;
- mini-doll;
- mechanical/droid specialized bodies;
- ghost lower body;
- serpent lower body;
- merfolk tail;
- tentacle lower body;
- robotic roller lower body;
- centaur hybrid;
- Jabba-style tail body;
- integrated character-specific bodies such as Angry Birds/Gollum-like forms.

This is not a claim that every mold in a family is mechanically interchangeable. The family only defines enough shared architecture to route recognition/generation.

## Custom census sources

### HeroBloks

Use as a discovery graph for:
- maker;
- serial;
- year;
- character;
- source labels such as BigFig;
- related versions;
- likely body-family clusters.

Do not use it as metrology.

High-value queries:
- characters known to force body variation: Hulk, Red Hulk, Thing, Colossus, Beast, Juggernaut, Abomination, Bane, Kingpin, Thanos, Venom/Carnage, Killer Croc;
- labels: BigFig, midfig, mega fig, large figure;
- maker clusters: Alpha Toys, G (2), Bigguy, Mr.J/Heart, KDL, Decool, Xinh, Sheng Yuan, Pogo, Kopf, Lele, Calypso, Shadow Studio, STUDIOGENESIS.

### Retailers

Useful for:
- stated height;
- comparison photography;
- packaging/set grouping;
- seller compatibility claims.

Store claims as `retailer_claim`, not empirical validation.

### Maker storefronts

Higher authority for:
- intended body name;
- product generation/revision;
- assembly;
- replacement parts;
- customization options.

Still do not infer precise connector dimensions without geometry/measurement.

### Community 3D models

Useful for:
- printable joint strategies;
- scale conventions;
- comments about sanding, glue, shrink/scale compensation;
- modularization choices.

Respect model licenses and keep exact third-party geometry separate from Brickmen-original parametric bodies.

## Automated ingestion pipeline

```
source discovery
 -> release record
 -> source label extraction
 -> image bundle
 -> maker/product-code normalization
 -> known-architecture retrieval
 -> visual/component classifier
 -> architecture observation
 -> evidence reconciliation
 -> known architecture OR unknown candidate cluster
 -> review/physical acquisition queue
```

### ArchitectureObservation

Required fields:

- observation_id;
- figure_release_id;
- maker_id;
- maker_product_code;
- source_body_label;
- source_height_claim;
- observed component graph;
- observed joint cues;
- observed standard-part compatibility;
- architecture_candidates;
- confidence;
- unknown_probability;
- evidence assets/sources;
- physical validation state.

## Automatic clustering

Unknown/custom bodies should be clustered by:

- maker;
- time period;
- product-code neighborhood;
- normalized front/side silhouettes;
- height estimate;
- landmark ratios;
- visible joint count/locations;
- head family;
- hand shape;
- leg/lower-body shape.

A cluster can become a candidate architecture only after multiple releases show the same structural pattern or one physical sample verifies the joint graph.

## Image evidence levels

### Level I0 — catalog thumbnail
Can support:
- rough morphology;
- maker/release;
- broad family candidate.

Cannot support:
- connector dimensions;
- exact articulation;
- hidden joint topology.

### Level I1 — multiview catalog photography
Can additionally support:
- component seams;
- joint locations;
- approximate scale/proportion;
- standard-part visual matches.

### Level I2 — disassembly / close-up
Can support:
- component graph;
- connector form candidate;
- stronger compatibility hypotheses.

### Level I3 — physical sample
Can support:
- dimensions;
- insertion/rotation force;
- actual interchangeability;
- material observations;
- wear/cycle behavior.

Only I3 or authoritative engineering geometry should promote manufacturing-critical connectors.

## Full-scan strategy

The census should be incremental rather than "finished once."

### Pass A — official architecture seed
Build high-confidence official body families and parts.

### Pass B — Hulk graph
Hulk has exceptionally dense cross-architecture coverage:
- standard minifigure;
- Mighty Micro/short;
- early/late official Giant;
- compatible BigFig;
- Alpha 7 cm;
- G (2) muscle body;
- premium custom bodies.

Use Hulk to establish the first cross-architecture style dataset.

### Pass C — pressure-test characters
Add:
- Thing;
- Beast;
- Colossus;
- Juggernaut;
- Abomination;
- Bane;
- Kingpin;
- Killer Croc;
- Thanos.

Each exposes different scale/body decisions.

### Pass D — non-humanoid topology
Add:
- centaur;
- serpent;
- ghost;
- merfolk;
- tentacle;
- robot/mechanical;
- multi-arm;
- integrated creature bodies.

This prevents the learned architecture selector from becoming merely a "how muscular is the character?" classifier.

### Pass E — maker-wide cluster expansion
Once a release is assigned to a verified architecture:
- search adjacent codes;
- compare visual/joint evidence;
- create architecture observations;
- do not auto-promote the whole prefix.

## Generation implications

The architecture census directly feeds generation.

A character request should first retrieve:
- plausible FigureArchitectures;
- same-character examples in other architectures;
- same-architecture examples of similar characters;
- BodyStyleProfile;
- surface schema;
- connector/joint graph.

Then generation decides separately:

1. **architecture** — physical body system;
2. **style** — sculpt/decoration visual grammar;
3. **character design** — identity/costume;
4. **manufacturing process** — resin/FDM/molding.

This separation is mandatory for reliable style transfer.

## Data retention

Git stores:
- architecture records;
- source manifests;
- provenance;
- structured observations;
- benchmark definitions;
- validated rules.

Local/object storage stores high-volume:
- marketplace images where permitted;
- normalized crops;
- embeddings;
- scans;
- photogrammetry;
- render bundles.

Git records hashes/links rather than noisy bulk binaries.

## Research stop condition

The scan is "coverage-complete" for a target source/period only when:
- all relevant release records have an architecture observation;
- known labels are normalized without being treated as standards;
- unknowns are clustered;
- mechanically consequential unknowns are queued for physical acquisition;
- no architecture assignment used unsupported maker-prefix propagation.

The global census remains open-ended because new custom body systems continue to appear.
