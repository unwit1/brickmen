# Agentic Custom Part and Non-Standard Body Roadmap

Created: 2026-09-27

## Goal

Reach the point where a user can ask Brickmen:

> "Make a LEGO-compatible version of this character."

and the system can intelligently choose a body architecture, generate or select the required body/accessory components, apply the appropriate architecture-specific visual style, create printable geometry with validated connectors, render/critique the result, and route it into physical manufacturing.

This roadmap combines:
1. the previously researched character-to-accessory geometry pipeline; and
2. the new non-standard FigureArchitecture / body-style system.

## Design principles

- Character identity and body architecture are independent decisions.
- Source labels such as BigFig, midfig, muscle body, 7CM and mega fig are evidence, not mechanical standards.
- Generative models propose visual geometry; deterministic Brickmen CAD owns joints, connectors, keep-outs and manufacturing-critical dimensions.
- Style is architecture-conditioned. Standard-minifigure art is not uniformly scaled onto a Giant or muscle body.
- Unknown architectures stay unknown until evidence supports a mapping.
- Physical testing is required before a printable joint profile becomes production-approved.
- Every provider/model/body architecture remains replaceable behind provider-independent interfaces.

# Track G — Agentic custom accessory generation

## G0 — Canonical schemas and benchmark harness

Deliver:
- AccessoryDesignSpec schema;
- AccessoryReferenceSet schema;
- GeometryCandidate schema;
- GeometryEvaluation schema;
- provider registry;
- fixed accessory benchmark;
- canonical Blender render harness;
- exact provider/model/seed/input/output provenance.

Acceptance:
- identical benchmark tasks can be run across multiple providers;
- every output is normalized, rendered and scored in the same coordinate system.

## G1 — Commercial generator adapters

Implement:
- Tripo adapter;
- Meshy adapter;
- asynchronous task/status handling;
- mesh download/normalization;
- provider cost/latency logging.

Benchmark:
- text;
- source image;
- LEGO-abstracted image;
- source multiview;
- LEGO-abstracted multiview.

Acceptance:
- Brickmen can generate and compare multiple candidate shells from one AccessoryDesignSpec.

## G2 — Local open-model lab

Deploy/evaluate:
- Hunyuan3D 2.1;
- TRELLIS;
- SPAR3D;
- Stable Fast 3D where useful.

Acceptance:
- same frozen benchmark as G1;
- GPU/time/memory recorded;
- model/version weights hashed;
- local results directly comparable to API providers.

## G3 — Parametric CAD agent

Implement:
- sandboxed CadQuery/build123d generation;
- code execution;
- deterministic renders;
- visual critic/revision loop;
- STEP/3MF output.

Initial classes:
- shields;
- scabbards;
- backpacks;
- mechanical weapons/tools;
- simple armor;
- connector-bearing fixtures.

Evaluate CAD-Recode and Zoo/KCL as complementary routes.

## G4 — Hybrid geometry compiler

Implement:
- mesh normalization;
- semantic segmentation;
- generated-connector removal;
- validated connector insertion;
- local thickness enforcement;
- articulation keep-outs;
- robust Booleans;
- 3MF/STEP/STL packaging.

Acceptance:
- an AI shell can be replaced around an unchanged validated connector;
- malformed/invented joints cannot enter production silently.

## G5 — Render/critic/regeneration loop

Separate critics:
- source fidelity;
- LEGO/minifigure abstraction;
- topology/geometry;
- architecture compatibility;
- DFM/printability.

Actions:
- accept;
- edit;
- regenerate;
- switch provider;
- switch to parametric CAD;
- simplify;
- split into components.

## G6 — Physical manufacturing feedback

Connect accepted GeometryCandidates to:
- resin/FDM process selection;
- print queue;
- dimensional/force tests;
- defect records;
- physical photos;
- accepted/rejected outcome.

Every print becomes generator evidence.

## G7 — Learned router and ranker

Train from Brickmen history:
- provider/task-class router;
- best-of-N candidate ranker;
- manufacturability-risk predictor;
- likely-human-acceptance model.

No fine-tuning of 3D generator yet unless benchmark proves retrieval/routing has plateaued.

## G8 — Brickmen-specific 3D fine-tuning

Candidate open systems:
- Hunyuan3D;
- TRELLIS;
- successor models with suitable weights/training code.

Training data:
- accepted source -> accessory translations;
- canonical views;
- geometry;
- semantic masks;
- physical print outcomes.

Functional connectors remain outside the learned model.

# Track B — Figure architecture and custom body intelligence

## B0 — FigureArchitecture foundation

Completed research foundation:
- first FigureArchitecture registry;
- body variant vs architecture distinction;
- BodyStyleProfile schema;
- ArchitectureSurfaceSchema;
- StyleTransferPair;
- architecture observation schema;
- recognition benchmark design;
- physical sample acquisition queue.

Next implementation:
- JSON Schema validation;
- stable architecture IDs;
- architecture version/supersession rules;
- component/joint graph serialization.

## B1 — Official architecture digital twins

Build validated neutral twins for:
- standard minifigure;
- short legs;
- medium legs;
- long-limb variants;
- modern LEGO Giant/BigFig;
- Fantasy Era Troll Giant;
- Hagrid giant-body hybrid;
- Axl oversized-torso hybrid.

For each:
- exploded parts;
- coordinates;
- landmarks;
- joints;
- articulation sweeps;
- standard-system connections;
- surface schemas;
- canonical cameras.

Priority: use official/catalog geometry plus physical measurement where manufacturing-critical.

## B2 — Third-party/custom physical metrology

Acquire and characterize:
- Alpha Toys AF ~7 cm body;
- G (2) muscle body;
- Bigguy body;
- Mr.J Brick x Heart body;
- KDL 6.5 cm body;
- representative compatible BigFig;
- community printed MidFig.

For each:
- teardown;
- scan;
- dimensions;
- joint graph;
- compatibility tests;
- force/cycle characterization;
- component-family comparison.

Acceptance:
- either promote to a concrete architecture or preserve as a separate unresolved family with documented evidence.

## B3 — Architecture image recognition

Implement:
- figure/component segmentation;
- canonical-render retrieval;
- maker/product-code prior;
- proportion/landmark extraction;
- joint/topology cues;
- unknown rejection.

Benchmark:
- catalog images;
- real photos;
- low-resolution listings;
- occlusion;
- detached components.

Candidate embeddings:
- SigLIP 2 or successor for image retrieval.

## B4 — 3D/scan architecture recognition

Implement:
- mesh normalization;
- point-cloud sampling;
- OpenShape/Uni3D benchmark;
- deterministic landmarks;
- joint/topology matching;
- digital-twin alignment;
- unknown-family clustering.

Goal:
a loose scanned arm/torso/body should resolve to architecture candidates and connector families.

## B5 — BodyStyleProfile corpus

For every architecture:
- proportions;
- geometry-vs-decoration balance;
- sculptural depth;
- surface map;
- line/detail density;
- face/head scaling;
- muscle/armor grammar;
- accessory scaling;
- maker-style overlays.

Do not merge mechanical architecture with visual style.

## B6 — Cross-architecture translation corpus

First controlled character set:
- Hulk;
- Red Hulk;
- Thing;
- Beast;
- Colossus;
- Juggernaut;
- Abomination;
- Thanos.

Create same-character StyleTransferPairs across available architectures.

Study:
- what becomes sculpted;
- what remains printed;
- proportion transforms;
- feature simplification;
- accessory resizing;
- face/head changes;
- silhouette preservation.

Hulk is the first benchmark because it has unusually broad official/custom architecture coverage.

## B7 — Architecture-conditioned character generation

Implement:

```
SourceAppearance
 -> architecture resolver
 -> FigureArchitecture
 -> BodyStyleProfile
 -> CharacterBodyDesignSpec
 -> body-specific multiview concept
 -> geometry + decoration generation
 -> deterministic joints/connectors
 -> articulation/DFM
 -> architecture critic
```

The user may:
- request a specific architecture;
- request "most official-like";
- request "Alpha-style 7 cm";
- allow Brickmen to propose multiple architectures.

The system should explain the choices rather than pretending one body is objectively correct.

## B8 — Printable custom body generation

After joint validation:
- blank architecture skeleton/template;
- AI-generated surface shell;
- parametric joint insertion;
- modular component splitting;
- support/orientation planning;
- process/material selection;
- force/cycle validation.

Prefer hybrid commodity hardware at wear-critical joints where it improves reliability.

Goal:
generate not only accessories but complete custom figures using validated body systems.

# Track R — Recognition and ingestion

## R0 — Catalog metadata normalization

Ingest:
- maker;
- product code;
- source body label;
- dimensions;
- architecture candidate;
- release images;
- confidence.

Never make AF/KDL/etc. prefixes universal architecture truth without component evidence.

## R1 — Automatic architecture candidate extraction

When a new release enters Brickmen:
1. resolve maker/code;
2. inspect images;
3. classify body morphology;
4. retrieve nearest architecture;
5. detect mismatch;
6. create ArchitectureObservation;
7. queue physical review if novel/high-value.

## R2 — Novel architecture detection

If a release does not match known families:
- cluster with other unknowns;
- assign candidate family;
- collect evidence;
- recommend one representative physical sample;
- promote only after joint/component evidence.

This prevents a new custom body ecosystem from remaining invisible simply because the ontology predates it.

# Track M — Manufacturing

Architecture-specific manufacturing extends the existing additive-manufacturing roadmap.

Each validated body system needs:
- machine/material profiles;
- connector coupons;
- joint force/cycle limits;
- component orientation rules;
- support strategy;
- post-cure dimensional compensation;
- replacement/wear strategy.

For Giant/custom articulated bodies, resin may be used for visual shells while standardized ABS/Technic/thermoplastic hardware handles wear-critical joints.

# Immediate implementation order

1. Finish G0 schemas/render harness.
2. Begin G1 Tripo/Meshy benchmark.
3. Build B1 standard + LEGO Giant + Axl digital-twin architecture records.
4. Acquire Alpha AF and one official/compatible Giant sample for B2.
5. Implement architecture image-recognition baseline B3.
6. Build Hulk cross-architecture corpus B5/B6.
7. Connect G4 hybrid geometry compiler to FigureArchitecture.
8. Prototype one architecture-conditioned Hulk accessory/body generation.
9. Run first printed architecture joint experiments.
10. Expand to Thing/Beast/Colossus and newly discovered body systems.

# End-state acceptance test

Prompt:

> "Make a First Steps Thing figure and printable accessories."

Brickmen should:
- resolve the target appearance;
- detect that multiple body architectures are plausible;
- select or propose standard, large/muscle and/or custom architectures according to user preference;
- retrieve the appropriate style profile;
- generate the correct body-specific sculpt/decor decisions;
- insert validated architecture joints/connectors;
- generate accessories at the appropriate scale;
- pass articulation and DFM;
- render and critique;
- output reproducible printable files;
- log manufacturing evidence;
- learn from the physical result.

At that point body architecture is a deliberate reusable system rather than an emergent property of a prompt.

## B1A — topology expansion

Expand official digital twins beyond humanoid size variants:

- stacked-torso multi-arm;
- mechanical/droid body;
- ghost lower body;
- serpent lower body;
- merfolk tail;
- tentacle lower body;
- robot roller lower body;
- centaur hybrid;
- specialized integrated character bodies;
- Jabba-style tail body;
- mini-doll adjacent architecture.

Reason:
architecture recognition and generation must learn *topology*, not merely body size/bulk.

## B2A — continuous body census

Implement the pipeline defined in `nonstandard-body-census-and-ingestion.md`.

For every newly ingested custom release:
1. preserve maker/code/source body labels;
2. create `FigureArchitectureObservation`;
3. run known-architecture retrieval;
4. inspect component/joint cues;
5. assign confidence distribution;
6. create unknown cluster when necessary;
7. queue one representative physical sample when mechanical resolution is valuable.

Do not propagate architecture automatically across all releases sharing a maker/prefix.

## B5A — architecture-conditioned style registry

Build and validate `data/body-style-profile-registry.json`.

Separate:
- mechanical FigureArchitecture;
- visual BodyStyleProfile;
- character-specific CharacterBodyDesign.

Initial style studies:
- official standard minifigure;
- official Giant;
- Axl broad hybrid;
- Hagrid broad body;
- Alpha AF ~7 cm muscular visual grammar;
- G (2) muscular hybrid;
- premium custom muscular families.

For proprietary custom bodies, learn normalized descriptive style features without treating the original sculpt geometry as the manufacturing template.

## B6A — topology-aware style transfer

Cross-architecture translation tests must include non-biped bodies.

Examples:
- humanoid -> serpent lower body;
- humanoid -> centaur;
- standard -> multi-arm;
- standard -> mechanical droid;
- standard -> Giant;
- standard -> Brickmen Mid/XL.

Acceptance:
- correct component count/topology;
- no hallucinated standard legs/hands where the architecture forbids them;
- source identity preserved;
- target architecture surface rules respected.
