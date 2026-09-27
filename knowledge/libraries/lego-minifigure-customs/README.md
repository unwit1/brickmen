# LEGO Minifigure Customs Knowledge Repository

Purpose: a provenance-aware working knowledge base for collecting, identifying, comparing, designing, prototyping, sourcing, producing, cataloging, pricing, and eventually commercializing original custom minifigure work.

## Scope

This library covers official and compatible catalog crosswalks; customizer/maker ecosystems; characters, continuities and source appearances; collection/wishlist state; colors/materials; part anatomy and donor selection; accessories; artwork/templates; decals/finishing; printing/production; tools/workbench; release/edition tracking; historical/current price observations; compatibility and quality observations; sourcing/catalogs; quality control; and business/IP considerations.

The collector/market layer is intentionally linked to the production layer. A discovered missing character variant can become a design candidate; a known third-party helmet can become a component in a custom BOM; a poor compatibility observation can prevent an unsuitable donor from entering production.

## Operating principles

- Keep a vector master for every design and derive process-specific exports.
- Treat physical test prints as authoritative for scale/color; screen RGB is only a reference.
- Cross-reference LEGO, BrickLink, Rebrickable, LDraw, maker, reseller and community identifiers instead of assuming names/codes are identical.
- Never use seller SKU or HeroBloks serial as the internal canonical figure identity.
- Model Character -> Incarnation -> SourceAppearance -> OutfitDesign -> FigureRelease -> ComponentRelease -> MarketObservation.
- Preserve source wording while also storing normalized terminology.
- Record genuine/compatible/unknown provenance per component rather than applying one label to an entire mixed figure.
- Price is an observation with source/date/type, never a timeless property.
- Quality and compatibility are observations tied to a release/batch/source, not permanent maker scores.
- Record substrate color, part/design ID, element ID where known, artwork revision, printer/process, media/ink batch, clear coat, calibration profile and finished photos.
- Version templates and jigs like software.
- Preserve source URLs, dates and confidence for every imported fact.
- Promote personal experiments into recommended practice only after repeatable tests.
- Preserve contradictions and competing source-appearance hypotheses until resolved.

## Core collector/reference sources

- LEGO: official elements/themes and legal material
- BrickLink: official catalog identifiers/inventories plus sold/current price guide
- Rebrickable: structured official catalog/API and bulk downloads
- Brickset: theme/year/character/tag browsing
- Brickognize: image-based candidate identification
- HeroBloks: custom/compatible discovery and historical archive
- Maker storefronts: primary product/release/process/retail evidence
- Review/community sources: secondary release, quality, compatibility and historical evidence

See data/customizer-source-registry.json for the growing source registry.

## Target capabilities

The finished repository should answer questions such as: which exact comic/movie/game appearance a figure represents; every known commercial release of a character; which maker/code/reseller aliases refer to the same release; whether it is already owned; what is missing from a franchise roster; which donor parts fit a character; which accessories can upgrade an existing figure; how colors map across catalog systems; what a figure cost over time; how reliable a compatibility or QC claim is; which process fits one prototype versus a production run; how to generate front/back/arm/head artwork; what went wrong in a prior print batch; what parts are currently obtainable; and what rights/provenance apply to a proposed product.

Structured catalogs should grow through the Knowledge Engine rather than becoming an unrelated ingestion stack.


## Official visual-reference corpus

The library has a dedicated acquisition/training subsystem for official minifigure visual references.

Primary documents:
- `official-minifigure-visual-style.md`
- `official-character-corpus-ingestion.md`
- `official-theme-style-profiles.md`
- `official-reference-acquisition.md`
- `game-and-film-visual-corpus-pipeline.md`
- `official-training-corpus-design.md`
- `reference-image-deduplication.md`
- `custom-style-evaluation-framework.md`

Machine-readable records:
- `data/official-style-schema.json`
- `data/official-visual-source-registry.json`
- `data/official-reference-source-registry.json`
- `data/official-media-corpus-scope.json`
- `data/official-theme-style-profiles.json`
- `data/translation-pair-schema.json`

Target coverage is every practical official standard-minifigure visual design found in physical product catalogs, official/licensed games, and in-scope LEGO films. Catalog records, unique characters, unique outfits, and unique visual states are measured separately.

High-volume raw official images, extracted local game assets, and film frames stay in controlled local corpus storage. Git stores schemas, manifests, hashes, source relationships, derived features, coverage reports, and validated visual rules.

## Additive manufacturing / physical production

Deep-research and automation architecture:
- `additive-manufacturing-feasibility.md` — resin/FDM feasibility, materials, connector engineering, hybrid/crossover manufacturing and safety.
- `fused-filament-custom-parts.md` — FDM-specific materials, small-nozzle engineering, automation and factory-fixture strategy.
- `resin-custom-parts.md` — resin design rules and connector-oriented part records.
- `resin-fit-calibration.md` — empirical fit calibration and reusable connector library.
- `additive-manufacturing-validation-program.md` — standards-inspired validation hierarchy, metrology, force/cycle testing and profile promotion.
- `automated-additive-manufacturing-cell.md` — closed-loop CAD-to-print-to-postprocess-to-QC architecture.
- `additive-manufacturing-equipment-and-automation-options.md` — current printer/control/postprocessing architecture and phased equipment strategy.
- `additive-manufacturing-product-safety.md` — U.S.-focused gate preventing prototypes from being silently treated as compliant children's products.

Machine-readable contracts:
- `data/additive-manufacturing-automation-contracts.json`
- `data/additive-manufacturing-validation-plan.json`

Core principle: additive manufacturing is a measured closed-loop process. A nominal connector dimension, advertised printer resolution, or successful single print is not a production qualification.

Additional implementation documents:
- `additive-manufacturing-economics-and-process-crossover.md` — empirical cost model and automatic direct-print/cast/printed-tooling/metal-tool crossover.
- `parametric-cad-and-connector-automation.md` — deterministic connector insertion, CadQuery/STEP/3MF strategy, DFM and process compensation.
- `additive-manufacturing-first-cell-plan.md` — recommended first physical cell and ordered validation program.
- `data/additive-material-candidates.json` — current mechanically distinct resin candidate matrix.
- `data/additive-process-selection-rules.json` — machine-readable process selection inputs, constraints and outputs.
- `data/additive-first-experiments.json` — dependency-ordered E001-E020 physical experiment queue.

Canonical additive-manufacturing decision summary:
- `additive-manufacturing-research-synthesis.md` — concise current conclusions, recommended architecture, automation priorities, and unresolved physical experiments.

## Agentic 3D accessory generation

Research and architecture for the target workflow "ask for a character -> automatically generate printable compatible accessories":
- `agentic-character-to-accessory-3d-generation.md` — end-to-end character resolution, accessory planning, multiview concept generation, provider ensemble, CAD/mesh hybridization, critics, DFM, physical feedback and self-improvement.
- `data/3d-generation-provider-registry.json` — exact-version provider/capability registry for Tripo, Meshy, Hunyuan3D, TRELLIS, SPAR3D, Stable Fast 3D, CadQuery/build123d, CAD-Recode and Zoo/KCL.
- `data/accessory-generation-benchmark.json` — common accessory suite, input modes and metrics for empirical model routing.

Core rule: learned 3D systems generate/propose visual shells; deterministic Brickmen CAD, keep-out geometry and validated connector profiles remain authoritative for functional interfaces and manufacturing dimensions.


## Non-standard body architectures

Figure/body architecture is now modeled separately from character identity and loose market labels.

Primary documents:
- `nonstandard-figure-architectures.md` — official/custom architecture taxonomy, Alpha Toys AF research, mechanical modeling and 3D-print strategy.
- `body-architecture-recognition-and-style-transfer.md` — image/mesh recognition, BodyStyleProfile, cross-architecture style transfer and architecture-conditioned generation.
- `agentic-custom-parts-and-body-architecture-roadmap.md` — unified G/B/R/M implementation roadmap from accessory generation through complete printable custom bodies.

Structured records:
- `data/figure-architecture-registry.json`
- `data/body-style-transfer-schema.json`
- `data/body-architecture-recognition-benchmark.json`
- `data/body-architecture-physical-acquisition-queue.json`

Rule: labels such as BigFig, midfig, mega fig, Giant, 7CM and muscle body remain source terminology until a component/joint graph establishes the normalized FigureArchitecture.

## Figure architecture, non-standard bodies, and body style

Canonical subsystem for standard, Giant/BigFig, mid-scale, custom muscle bodies, alternate morphologies and future printable Brickmen bodies:

Research:
- `nonstandard-figure-architectures.md` — canonical architecture taxonomy and custom-market findings.
- `body-architecture-recognition-and-style-transfer.md` — image/mesh recognition, style profiles and cross-architecture translation.
- `nonstandard-body-census-and-ingestion.md` — continuous official/custom architecture census and evidence promotion rules.
- `agentic-custom-parts-and-body-architecture-roadmap.md` — unified implementation roadmap covering accessory generation plus full body intelligence.

Canonical structured data:
- `data/figure-architecture-registry.json`
- `data/figure-architecture-observation-schema.json`
- `data/figure-architecture-selection-schema.json`
- `data/character-body-design-schema.json`
- `data/body-architecture-source-registry.json`
- `data/body-architecture-recognition-benchmark.json`
- `data/body-style-profile-registry.json`
- `data/body-style-transfer-schema.json`
- `data/body-architecture-physical-acquisition-queue.json`
- `data/brickmen-body-family-targets.json`

Canonical identity layers:

```
Character / SourceAppearance
 -> FigureArchitecture
 -> BodyStyleProfile
 -> CharacterBodyDesignSpec
 -> component geometry + decoration
 -> deterministic joints/connectors
 -> manufacturing validation
```

Terms such as BigFig, midfig, muscle body, 7CM and mega fig are preserved as source labels; they are not mechanical standards.

### Body learning, joints, and adjacent articulation references

- `body-architecture-training-corpus.md` — factorized architecture/style/character corpus, anti-leakage splits, negative examples and training progression.
- `data/body-corpus-sample-schema.json` — canonical multimodal training sample contract.
- `data/body-generation-evaluation-schema.json` — separate architecture/style/identity/geometry/physical evaluation axes.
- `printable-body-joint-engineering.md` — reusable joint primitives, replaceable insert strategy, torque/cycle validation and scale-aware joint selection.
- `data/body-joint-primitive-schema.json`
- `data/body-joint-validation-plan.json`
- `data/figure-architecture-feature-schema.json` — faceted morphology/mechanics representation for known and novel body systems.
- `adjacent-articulated-figure-systems.md` — Mega Construx/Kre-O/Minimates articulation references kept separate from LEGO-compatible architectures.
- `data/adjacent-articulated-system-registry.json`

The recognition/generation stack can now reason separately about:
```
scale
construction method
head integration
torso topology
arm segmentation
shoulder/elbow/wrist joints
lower-body topology
compatibility
visual style
```
instead of reducing every figure to a single body-label class.


## Advanced body generation / part-aware articulation

New research layers supporting architecture-aware printable full bodies:

- `hulk-cross-architecture-study.md` — first same-character architecture control corpus.
- `thing-cross-architecture-study.md` — matched-source standard/intermediate/BigFig control set and rock-surface translation research.
- `maker-body-family-resolution.md` — release/body-family clustering; maker prefix is not architecture.
- `custom-bigfig-mold-lineage.md` — cross-brand mold/tooling lineage and MoldFamily model.
- `printable-nonstandard-body-engineering.md` — hybrid printed-shell + commodity-joint patterns and JointCartridge strategy.
- `brickmen-original-midfig-architecture.md` — independent automation-first Brickmen MidFig concept.
- `body-architecture-recognition-implementation.md` — image/scan recognition implementation stack.
- `nonstandard-digital-twin-ingestion.md` — component-level architecture digital-twin ingestion.
- `part-aware-3d-generation-and-correspondence.md` — PartCrafter/SAMPart3D/PartField/OmniPart/SAM3D-Part research.
- `articulated-3d-generation-and-joint-proposals.md` — PAct/Particulate/ArtLLM/LAM and learned JointProposal workflow.
- `architecture-conditioned-body-style-compiler.md` — compiler from architecture-neutral body semantics to geometry/relief/print/component decisions.

Key structured records:
- `data/hulk-cross-architecture-corpus.json`
- `data/thing-cross-architecture-corpus.json`
- `data/character-body-feature-schema.json`
- `data/maker-body-family-clusters.json`
- `data/mold-family-schema.json`
- `data/custom-bigfig-ecosystem-registry.json`
- `data/printable-body-engineering-patterns.json`
- `data/brickmen-midfig-v0.json`
- `data/body-recognition-model-registry.json`
- `data/part-aware-3d-model-registry.json`
- `data/articulated-generation-research-registry.json`
- `data/joint-proposal-schema.json`
- `data/body-style-compiler-contract.json`
- `data/style-mapping-rule-schema.json`

Generation principle:
**character semantics are architecture-neutral; style compilation is architecture-specific; final mechanical interfaces remain deterministic and physically validated.**


### Alpha Venom / Broad-body continuation

The non-standard-body subsystem now explicitly includes Alpha Toys' standard-height muscular/symbiote family, separate from Alpha's ~7 cm muscle body.

Research:
- `alpha-toys-body-family-census.md` — Alpha release/body-family census proving AF prefix != one architecture.
- `venom-cross-architecture-study.md` — standard Venom vs Alpha ~4–4.5 cm hybrid vs BigFig translation study.
- `diverse-large-body-morphology-study.md` — muscular, heavy-round, armored, primate, reptilian, rocky and symbiote control morphologies.
- `brickmen-original-broad-body-architecture.md` — independent standard-height broad-body architecture target.

Structured:
- `data/alpha-toys-body-family-census.json`
- `data/alpha-symbiote-family-corpus.json`
- `data/venom-cross-architecture-corpus.json`
- `data/nonstandard-morphology-control-plan.json`
- `data/diverse-large-body-control-corpus.json`
- `data/morphology-archetype-registry.json`
- `data/surface-material-profile-registry.json`
- `data/nonstandard-body-morphology-benchmark.json`

Important distinction:
**stature, upper-body mass, lower-body mass, surface material and FigureArchitecture are independent variables.**


## Executable body skeletons

Brickmen now has parametric generation/alignment skeletons rather than only body-family prose.

Core:
- `body-skeleton-system.md`
- `data/body-skeleton-schema.json`
- `data/skeletons/registry.json`
- `data/skeleton-topology-modules.json`
- `tools/geometry/generate_body_skeleton.py`

Implemented skeletons:
- `data/skeletons/brickmen-broad-v0.json`
- `data/skeletons/brickmen-mid-v0.json`
- `data/skeletons/brickmen-xl-v0.json`
- `data/skeletons/brickmen-giant-v0.json`

The compiler accepts target height and bounded body parameters and can export compiled JSON or an OBJ line skeleton.

These are **nonproduction generation skeletons**. Fit-critical joints remain locked behind validated JointCartridge / ConnectorProfile data.

Second-pass architecture census:
- `distinct-body-architecture-census-pass-2.md`

Newly separated references include full ball-joint poseable standard figures, ball-jointed MidFig uppers, single-torso four-arm bodies, bony skeletons, Battle/Super Battle Droid bodies, digitigrade Faun lower bodies, and legacy Homemaker/maxifigure architecture.


## Reference fitting

Implemented reference-fitting tools:
- `reference-fitting-pipeline.md`
- `data/body-reference-landmarks.schema.json`
- `data/reference-landmarks/manifest.json`
- `tools/geometry/fit_body_skeleton.py`
- `tools/geometry/fit_body_skeleton_batch.py`
- `tools/geometry/compare_body_skeletons.py`

Seed references:
- Alpha Toys AF325 Venom
- Alpha Toys AF345 Hulk
- LEGO SH0371 Giant Hulk
- KDL K2302 Thing
- LEGO Axl

Seed diagnostics are stored under:
- `data/reference-landmarks/seed-fit-results.json`
- `data/reference-landmarks/seed-comparative-fit-results.json`
- `data/skeleton-fit-revision-candidates.json`

Rule:
**shape residual, known scale, topology, source metadata and physical evidence are separate signals. A low image-fit RMSE never proves mechanical architecture or connector compatibility.**


### Official Giant fitting anchors

Image-only Giant fitting is now supplemented by official LDraw reference metadata:
- `official-giant-reference-anchors.md`
- `data/engineering-reference-anchors/lego-giant-ldraw.json`

These records provide published shoulder/hand socket frames for the official Giant digital-twin workflow while keeping physical tolerances separate.


### Standard minifigure / Axl donor anchors

Reference fitting now has component-frame evidence for standard minifigure donor parts and a hybrid-body interpretation for Axl:
- `standard-minifig-and-axl-reference-anchors.md`
- `data/engineering-reference-anchors/lego-standard-minifig-ldraw.json`
- `data/engineering-reference-anchors/lego-axl-hybrid-reference.json`

Axl is treated as a hybrid architecture: standard lower-body and torso-core frames can remain locked while an oversized upper shell and dedicated arms define the broader visual/mechanical body. Unofficial 23763/24128 LDraw geometry remains provisional until physical measurement or official promotion.


### Independent visual envelope fitting

Visual body mass is now parameterized separately from skeletal joint spacing:
- `data/body-envelope-profile.schema.json`
- `tools/geometry/fit_body_envelope_profile.py`
- `data/reference-landmarks/seed-envelope-fit-results.json`

The Broad, Mid, XL and Giant generation skeletons now expose independent torso/head/abdomen envelope parameters. Fitting a wider chest no longer moves the shoulder joints. Outer-shoulder and hip silhouette measurements remain visual diagnostics until explicit visual-envelope primitives exist for them.


## Body generation conditioning

Reference fitting now compiles into a provider-neutral generation handoff instead of passing raw measurements directly to an image/3D model.

Core:
- `data/body-generation-conditioning.schema.json`
- `tools/geometry/compile_body_generation_conditioning.py`
- `data/generation-conditioning/brickmen-giant-official-cad-v0.json`
- `data/generation-conditioning/brickmen-broad-axl-envelope-v0.json`

The payload keeps four layers separate:
1. skeleton/proportion landmarks;
2. visual body envelopes;
3. editable/locked component regions;
4. mechanical constraints with explicit authority state.

Reference-only or validation-pending mechanical profiles may provide alignment/hardware/keep-out context, but they do not authorize printable mating geometry. Reference scale also does not silently replace the selected Brickmen design height.


## Reference engineering skeletons and fit identifiability

Official/reference component mechanics are modeled separately from Brickmen-original generation skeletons.

Key additions:
- `data/reference-engineering-skeleton.schema.json`
- `data/engineering-skeletons/lego-giant-modular-2303.json`
- `official-giant-reference-engineering-skeleton.md`
- `tools/geometry/analyze_body_fit_identifiability.py`
- `tools/geometry/analyze_body_fit_identifiability_batch.py`
- `data/reference-landmarks/seed-identifiability-report.json`

The official Giant reference captures a fixed-bend 3D arm/component topology and exact reference frames without forcing `brickmen_giant_v0` to copy that architecture.

Generation conditioning now also supports:
- bone-aligned arm envelopes;
- independent hand envelopes;
- lower-body visual mass independent from hip spacing;
- fixed-mm mechanical keep-outs placed at selected skeleton nodes.

Parameter expansion is gated by landmark identifiability. The current seed corpus supports adding head-offset, thigh-length and shin-length fitting, but cannot separately identify lower- versus upper-torso segment length until chest/torso-center landmarks are added.
