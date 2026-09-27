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

# Track J — Reusable articulated joint engineering

## J0 — JointProfile contracts

Completed research:
- joint primitive taxonomy;
- JointProfile schema;
- force/torque/cycle validation plan;
- replaceable joint insert strategy.

Files:
- `printable-body-joint-engineering.md`
- `data/body-joint-primitive-schema.json`
- `data/body-joint-validation-plan.json`

## J1 — Joint coupon generator

Implement parametric CAD generators for:
- rotational pin/bore ladders;
- captured pins;
- C-socket ball joints;
- replaceable socket inserts;
- shoulder ball-adapter pins;
- elbow hinge;
- wrist peg;
- detents.

Every generator accepts:
- machine/material profile;
- orientation;
- sweep parameters;
- sample labels.

## J2 — Instrumented torque testing

Extend the additive force station with:
- rotary axis;
- torque measurement or calibrated lever/force method;
- angle encoder;
- automated cycling.

Store torque-angle curves and cycle drift.

## J3 — standard articulated shoulder

Acquire one current custom ball-joint-arm figure and characterize it.

Then design an **original** Brickmen standard-scale articulated shoulder preserving as much normal minifigure compatibility as possible.

Do not clone proprietary custom joint geometry.

## J4 — Brickmen Mid joint set

Select and validate:
- shoulder;
- elbow;
- wrist;
- optional hip/lower-body joints.

## J5 — Brickmen XL replaceable joint set

Prioritize replaceable wear inserts and/or commodity hardware.

Validate static load and long-term pose retention.

## J6 — Mega-scale joint research

Large figures require joint selection by required torque, not visual scale alone.

Test:
- detents;
- large replaceable ball/socket inserts;
- pinned hinges;
- commodity hardware.

# Track X — Mega-scale and buildable figures

## X0 — source-label separation

Completed:
- MegaFig retained as source label;
- OA 16 cm family candidate;
- DY variable 22.5-28.5 cm evidence;
- buildable treated separately from molded/printed large bodies.

## X1 — OA 16 cm family resolution

Acquire/scan at least one OA2201-OA2204 body, then compare multiview catalog evidence across all four.

Determine:
- shared blank platform;
- joints;
- components;
- materials;
- standard system attachment.

## X2 — DY large-scale clustering

Create release-level observations before inferring any shared architecture.

## X3 — buildable CharacterArchitecture

Represent buildable bodies as:
```
component/subassembly graph
 + LEGO-system connection graph
 + semantic anatomy map
 + articulation map
 + style surfaces
```

Generation can then choose to create:
- molded/printed body;
- or a brick-built character.

## X4 — cross-scale character benchmark

Use characters represented at many scales:
- Ant-Man / Giant Man;
- Galactus;
- Sentinel;
- Hulk;
- Thing.

Evaluate whether the architecture selector chooses scale and construction method from explicit intent rather than learned popularity bias.

# Track C — Body intelligence corpus and learning

## C0 — Corpus contracts

Completed research:
- BodyCorpusSample schema;
- architecture/style/character factorization;
- anti-leakage split policy;
- BodyGenerationEvaluation schema.

## C1 — Release-level corpus build

Build samples from the architecture census.

Prioritize:
1. Hulk cross-architecture set;
2. Thing/Beast/Colossus/Juggernaut/Abomination;
3. Sentinel/Giant Man/Galactus scale variants;
4. non-humanoid topology;
5. ball-joint standard-scale figures;
6. non-Marvel compatible BigFig examples.

Generate:
- normalized crops;
- masks;
- landmarks;
- architecture observations;
- canonical evidence bundles.

## C2 — Architecture classifier baseline

Benchmark:
- visual-only;
- visual + non-identifying geometry metadata;
- visual + catalog prior.

Report held-out performance by:
- maker;
- character;
- franchise;
- architecture family.

Unknown detection is mandatory.

## C3 — Part/component segmentation

Map 2D/3D proposals to canonical component roles.

Candidate research models:
- SAM2;
- SAMPart3D / PartSLIP++ / successor;
- Trellis SegPart;
- Tripo semantic segmentation.

## C4 — BodyStyleProfile predictor

Predict interpretable normalized features before training an opaque style latent.

Prevent:
- character costume;
- logos;
- color;
from becoming the primary body-style signal.

## C5 — style retrieval/ranker

Train from:
- same-style pairs;
- deliberately different style pairs;
- accepted/rejected style transfers.

## C6 — structured part generation

Benchmark:
- PartCrafter;
- UniPart;
- PAct;
- general 3D generators + segmentation.

Output remains a **visual/component proposal**.

## C7 — articulation proposal/critic

Benchmark:
- PAct;
- ArtLLM;
- Particulate;
- future articulation models.

Reconcile every proposed joint against:
- target FigureArchitecture;
- JointProfile library;
- manufacturing constraints.

## C8 — original Brickmen fine-tuning

Only after enough original Brickmen body data exists:
- fine-tune/adapt part-aware open models;
- train on Brickmen-original parametric bodies and approved outputs;
- keep third-party proprietary body geometry out of the canonical manufacturing target.

## C9 — physical manufacturability predictor

Use print/joint outcomes to predict:
- fracture risk;
- insufficient wall;
- likely sag;
- bad support region;
- joint wear risk.

This becomes another critic before automatic print dispatch.


# Track P — Part-aware and articulated generation

## P0 — Part-aware generation benchmark

Implement/evaluate:
- PartCrafter;
- UniPart;
- OmniPart;
- conventional monolithic generator + SAMPart3D;
- conventional monolithic generator + PartField/Trellis SegPart.

Use the same FigureArchitecture target and canonical body concepts.

Measure:
- required-component recall;
- over/under segmentation;
- component semantic mapping;
- boundary error;
- shell quality;
- deterministic joint insertion success;
- manual correction minutes.

## P1 — selective component regeneration

Evaluate SAM3D-Part or successors for:
- regenerate one arm while retaining approved torso/other arm;
- generate a missing part from a scan/body mesh;
- selectively replace a component after print failure or design revision.

Locked JointCartridges must survive unchanged.

## P2 — articulation proposal/critique

Evaluate:
- PAct;
- Particulate;
- ArtLLM;
- Articulate AnyMesh;
- SPARK;
- URDF-Anything+;
- Kinematify.

Known architecture:
use only as critics/proposal models.

Unknown architecture:
use to propose component/joint graphs before physical metrology.

All learned joints are stored as JointProposal, never production Connector.

## P3 — multi-agent articulated CAD compiler

Adapt the useful LAM pattern:

```
BodyPlanner
 -> LinkDesigner
 -> GeometryCoder
 -> JointCompiler
 -> GeometryCritic
 -> ArticulationCritic
 -> ManufacturingCritic
 -> Fixer
```

Brickmen differences:
- FigureArchitecture supplies the skeleton;
- JointCompiler can only instantiate validated JointCartridges;
- manufacturing output targets STEP/3MF/CadQuery/build123d/Blender assets rather than generic URDF alone;
- every revision is hashable/reproducible.

## P4 — part correspondence learning

Use PartField/related features to establish correspondence:
- neutral architecture <-> character shell;
- same architecture across characters;
- same character across architectures;
- same mold family across decorated releases.

Train a lightweight semantic mapper only after reviewed correspondence data exists.

# Track S — Architecture-conditioned style compiler

## S0 — CharacterBodyFeatureSpec

Extract architecture-neutral semantics:
- morphology archetype;
- stature;
- regional mass;
- limb/hand emphasis;
- surface material;
- identity-critical body features;
- geometry/relief/print candidates.

## S1 — StyleMappingRule library

For each feature + architecture/style profile, learn whether it becomes:
- existing component;
- silhouette geometry;
- major relief;
- shallow relief;
- print;
- material/color;
- soft goods;
- separate accessory;
- omitted detail.

Seed from Hulk and Thing cross-architecture corpora.

## S2 — surface material grammars

Create reusable profiles for:
- skin;
- rock;
- fur;
- metal;
- scales;
- wood/bark;
- cloth;
- bone;
- organic/slime;
- translucent/energy;
- armor plating.

Each profile defines relief/print/finish strategy and joint/contact exclusions.

## S3 — statistical BodyStyleProfiles

Move from prose profiles to measured distributions:
- head/body;
- shoulder/body;
- hand/head;
- torso taper;
- limb mass;
- relief density;
- surface feature scale;
- accessory proportions.

## S4 — compiler implementation

```
CharacterBodyFeatureSpec
 + FigureArchitecture
 + BodyStyleProfile
 + SurfaceMaterialProfile
 -> CharacterBodyDesignSpec
```

Then route every component to reuse/CAD/neural generation/decoration.

# Track T — Mold/tooling lineage

## T0 — MoldFamily ontology

Model:
`FigureArchitecture -> MoldFamily -> MoldRevision -> ComponentRelease -> FigureRelease`.

## T1 — cross-brand mold equivalence

Ingest explicit same-mold/remake claims and compare:
- silhouette;
- seam/tooling marks;
- dimensions;
- joint fit.

Use validated mold-family equivalence to reduce redundant physical sample acquisition.

## T2 — recognition hard pairs

Train recognition using:
- same mold, different brand/decoration = positive;
- same architecture, different mold = hard negative.

# Expanded control characters

After Hulk and Thing, prioritize:
- Bane;
- Thanos;
- Darkseid;
- Gorilla Grodd;
- Blob;
- Kingpin;
- Abomination;
- Juggernaut;
- Venom;
- Rhino;
- Beast;
- Colossus.

Purpose:
avoid a "Hulk = all large figures" bias and learn multiple mass/material/morphology distributions.
