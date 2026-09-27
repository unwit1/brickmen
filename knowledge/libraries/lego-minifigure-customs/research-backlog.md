# Exhaustive Research Backlog

This file tracks remaining gaps so exhaustive has a measurable meaning rather than relying on memory.

## Collector/catalog coverage

- ingest BrickLink minifigure identifiers and inventories for user-priority themes
- ingest Rebrickable minifig/part crosswalks and external IDs
- ingest Brickset theme/year/character/tag facets as secondary discovery metadata
- build Brickognize-assisted photo identification workflow with confirmation step
- ingest HeroBloks brand facet into a long-tail MakerCandidate registry
- ingest HeroBloks figure/product-code relationships without allowing HeroBloks IDs to become canonical IDs
- backfill discontinued compatible makers and historical code families
- map maker aliases, collaborations, factory/brand claims and evidence strength
- ingest Brick4/other compatible catalogs for parent brand/set relationships
- evaluate BrickFigures and other emerging catalogs as supplemental discovery sources
- recover historical DownTheBlocks-like brand lists/archives where still accessible
- build release-monitor adapters for maker storefronts and public social announcement feeds
- preserve deleted/disappeared maker pages through metadata/hash/archive references where legally/technically available

## Character, theme and reference coverage

- normalize DC, Marvel, Image/independent, Star Wars, Dragon Ball, One Piece and other existing user trackers into Character/Incarnation/SourceAppearance
- expand anime/manga, film/TV, games, fantasy, historical/military, horror, music/celebrity, sports, LEGO-original and novelty taxonomies
- resolve obscure custom designs to exact comic issue/panel, film/episode/frame, game skin, toy/statue, promo art or other source
- distinguish maker-original/composite designs from source-accurate appearances
- preserve competing source hypotheses and confidence
- attach reference assets with provenance/usage notes rather than copying unlicensed imagery into distributable datasets

## Customizer/maker coverage

- primary-source profile for every high-priority maker: aliases, region, status, processes, genuine-part policy, code patterns, collaboration behavior, product forms
- premium customs: Citizen Brick, FireStar, Brickmania, United Bricks, The Minifig Co., Minifigs4u, BrickTactical, EclipseGRAFX, BigKidBrix, AV Figures, Minifigs.me, Orbital, BrothersFigure, KO Custom Minifigs, MRM, UG/CrazyMinifigs, Calypso, Penzora, Engineerio, JONAK, Grandpa Clone Customs, Clone Army Customs, ChipChipCustom and discovered successors
- compatible brands: WM, XINH, Koruit, KDL, Kopf, POGO, G-family codes, Decool, Bela, SY/Sheng Yuan, Lele and the full HeroBloks/Brixtoy long tail
- accessory specialists: BrickArms, BrickWarriors, BrickForge, CapeMadness and maker-specific helmet/cloth/weapon lines
- determine active/inactive status from dated primary evidence rather than stale marketplace stock

## Release/product modeling

- FigureRelease IDs independent from maker code and seller SKU
- ComponentRelease records for heads, torsos, arms/hands, hips/legs, helmets/hair, armor/bodywear, cloth, weapons/props and stands
- code alias crosswalk: maker code, reseller SKU, HeroBloks serial, official BrickLink/Rebrickable counterpart and internal ID
- collaboration/exclusive relationship model
- preorder/drop/restock/sold-out/retired event history
- edition size, numbered card, collector case, first edition, chase/variant and event-exclusive metadata
- generic army-builder versus named-character semantics

## Market/pricing

- build append-only PriceObservation store
- BrickLink sold-vs-asking ingestion for official figures
- maker direct-price snapshots for priority customs
- reseller asking-price snapshots for compatible figures
- completed-sale capture where marketplace terms and access permit
- normalize currency but preserve original currency
- capture condition, completeness, accessories, edition, stock and shipping/tax semantics
- never use one model/aggregate estimate as a transaction
- alert on meaningful restock/discount/price change for wanted figures once monitoring rules exist

## Compatibility and quality

- build CompatibilityObservation matrix across official LEGO and common compatible brands
- test hands, heads, headgear, neck gear, torso/arms, hips/legs, bars/clips and custom modular interfaces
- record fit direction, tightness, stress/cracking and repeated-cycle effects
- quality observations per release/batch: registration, opacity, detail, texture, color, rub resistance, clutch, joint tension, mold seams/flash, brittleness, cloth finish and completeness
- separate maker claims, reviewer observations and user physical tests
- no permanent maker quality score from anecdotes

## Geometry and catalog

- ingest official LDraw minifigure-related part index and dependencies
- map common body-part assemblies
- map mold variants
- map BrickLink/Rebrickable/LEGO identifiers
- record licenses and source hashes
- build physical-measurement queue for print surfaces and connectors

## Color/material

- ingest LDConfig color definitions
- ingest Rebrickable color table
- build BrickLink crosswalk
- reconcile LEGO official names where obtainable
- create physical swatch measurement workflow
- build UV target/profile tables

## Decoration/style

- classify official decoration families without copying protected artwork
- derive statistical line-weight/feature-placement grammar from permitted observations
- head-face landmarks
- torso garment landmarks
- leg/boot/belt landmarks
- arm print zones
- wraparound seam rules
- metallic/transparent/dual-mold visual semantics

## UV manufacturing

- printer-specific research once machine model is selected
- RIP spot-color naming
- white/primer/varnish layer order
- jig CAD library
- registration calibration
- adhesion tests
- abrasion tests
- color profiling
- curved-surface indexed printing
- static/dust handling
- maintenance and nozzle-health records
- production costing and throughput

## Resin

- printer/resin selection profiles
- exposure calibration
- dimensional coupons
- connector library
- support/orientation library
- hollowing/drainage
- warpage
- post-cure
- sanding/priming/painting
- UV print adhesion on resin
- durability and repeated-fit testing

## AI

- canonical Blender scene generator
- automatic LDraw-to-render conversion
- deterministic camera library
- depth/normal/mask export
- prompt schema
- image-reference workflow
- multi-control structural workflow
- multi-view consistency evaluation
- automated geometry-error scoring
- artwork-to-template projection
- vector cleanup assistance
- CMYK/white/varnish mask generation
- RAG retrieval tests
- provenance on every generation
- source-appearance resolver that returns evidence/confidence rather than hallucinating a reference

## Business/workflow

- inventory and storage/bin tracking
- BOM/costing
- supplier validation
- batch traceability
- photography
- packaging
- rights review
- product catalog
- defect/rework tracking
- collection reconciliation against Bootlego MASTER and franchise trackers
- move verified missing variants directly into the custom-design backlog with provenance

## Definition of done

A topic is not done merely because prose exists. It is exhausted only when authoritative/primary sources are indexed, important secondary discovery sources are covered, contradictory claims are reconciled or explicitly retained, structured records exist, time-sensitive observations have dates, unknowns are explicit, and any value requiring physical validation has an experiment or measurement task.

## Additive manufacturing research status — 2026-09-27

### Research/architecture completed in current deep pass

- [x] resin-versus-FDM process-role analysis
- [x] current hobby high-detail MSLA capability review
- [x] professional resin API/automation review
- [x] FDM small-nozzle/material/automation review
- [x] resin tough/flexible-material candidate research
- [x] 3.18-family held-accessory connector research and calibration policy
- [x] orientation/support/warpage design rules
- [x] standards-inspired AM qualification framework
- [x] metrology strategy: micrometer, pin/plug gauges, go/no-go fixtures
- [x] automated insertion/removal force-test architecture
- [x] camera/vision QC architecture
- [x] headless slicer and slice-validation architecture
- [x] OctoPrint/Moonraker/Prusa/Formlabs control-surface research
- [x] hobby-resin network-control limitations documented
- [x] automatic unload/build-platform-transfer research
- [x] automated resin-cleaning/postprocess research
- [x] silicone casting / printed injection mold / traditional mold crossover research
- [x] U.S. children's-product safety gate research
- [x] provider-independent machine-readable manufacturing contracts
- [x] machine-readable physical validation plan

### Physical evidence still required

These cannot be truthfully closed through web research alone:

- [ ] select first actual resin printer and record exact serial/firmware
- [ ] select first FDM printer/nozzle configuration
- [ ] procure at least three mechanically distinct resin candidates
- [ ] create and print Brickmen generic geometric benchmark
- [ ] create and print 3.18-family bar ladder
- [ ] create headwear/neck/clip coupon families
- [ ] measure pre-cure/post-cure dimensional change
- [ ] characterize build-position variation
- [ ] characterize orientation variation
- [ ] perform repeated insertion/removal cycle testing
- [ ] establish conservative donor-safe force limits
- [ ] run thin sword/spear/horn fracture study
- [ ] run controlled drop comparison
- [ ] run creep/long-term retention study
- [ ] run UV/light and moderate-temperature aging study
- [ ] validate paint/primer/UV-print adhesion on selected resin
- [ ] qualify a production raft/support strategy
- [ ] establish actual yield, labor minutes and true per-part cost
- [ ] quote/calculate crossover to casting/printed tooling/traditional molding for stable SKUs

### Implementation work enabled by the research

- [ ] build CadQuery parametric connector/coupon package
- [ ] build `manufacturing.preflight`
- [ ] build slicer adapter interface
- [ ] build UVtools issue-policy adapter
- [ ] build FDM printer adapter(s)
- [ ] build resin printer adapter(s)
- [ ] build manufacturing job scheduler
- [ ] build QR/barcode sample traceability
- [ ] build metrology ingestion
- [ ] build force-curve ingestion and pass/fail classifier
- [ ] build camera inspection fixture and deterministic image capture
- [ ] build profile-candidate/regression service
- [ ] build consumables/maintenance/drift tracker
- [ ] build mold-crossover economics service

### Definition of done for a connector/material profile

A profile is not complete until it has:
1. exact machine/material/build/postprocess revisions;
2. multiple physical specimens;
3. dimensions measured with a capable gauge;
4. insertion/removal force where applicable;
5. repeated-cycle evidence where applicable;
6. photographs/raw data;
7. acceptance limits;
8. repeatability evidence;
9. rollback/supersession history.

Digital research can design the experiment; only physical evidence can promote a profile to production-approved.

## Agentic character-to-accessory 3D generation — 2026-09-27

### Research architecture completed

- [x] modular character -> accessory -> printable geometry architecture
- [x] accessory-opportunity planner design separating geometry vs print/cloth/existing parts
- [x] structured AccessoryDesignSpec concept
- [x] structured AccessoryReferenceSet concept
- [x] multiview-first generation strategy
- [x] current Tripo API/capability survey
- [x] current Meshy API/capability survey
- [x] Hunyuan3D 2.1 local/fine-tuning research
- [x] TRELLIS local/multi-image/editing research
- [x] SPAR3D / Stable Fast 3D fast-candidate research
- [x] direct CAD-as-code strategy using CadQuery/build123d
- [x] CAD-Recode point-cloud -> CadQuery research
- [x] Zoo/KCL text-to-CAD research
- [x] hybrid generative-shell + deterministic-connector architecture
- [x] semantic mesh decomposition strategy
- [x] deterministic mesh repair/normalization strategy
- [x] render-critic-repair loop design
- [x] provider-neutral 3D generation registry
- [x] common accessory benchmark suite
- [x] physical-print feedback integration concept
- [x] staged retrieval -> routing -> ranking -> fine-tuning research program

### Highest-priority implementation

- [ ] define JSON schemas for AccessoryDesignSpec, AccessoryReferenceSet, GeometryCandidate and GeometryEvaluation
- [ ] implement canonical accessory digital-twin coordinate system
- [ ] implement AccessoryPlanner geometry-vs-decoration-vs-existing-part classifier
- [ ] build canonical accessory render harness in Blender
- [ ] implement source-object segmentation/cropping pipeline
- [ ] implement controlled front/back/left/right concept-view generator
- [ ] implement Tripo adapter
- [ ] implement Meshy adapter
- [ ] deploy Hunyuan3D 2.1 local evaluation environment
- [ ] deploy TRELLIS local evaluation environment
- [ ] deploy SPAR3D local evaluation environment
- [ ] implement CadQuery/build123d CAD-agent executor sandbox
- [ ] implement generated-mesh normalization and diagnostics with Trimesh/CGAL
- [ ] implement semantic/generated connector removal
- [ ] connect validated Brickmen connector insertion
- [ ] implement articulation/keep-out Boolean tests
- [ ] implement automated local wall-thickness/minimum-feature checks
- [ ] implement canonical render + critic loop
- [ ] run the first frozen cross-provider accessory benchmark
- [ ] record exact model snapshots/cost/latency/success metrics
- [ ] connect accepted models to the additive manufacturing experiment queue

### Research experiments

- [ ] compare literal source-image conditioning vs LEGO-abstracted concept conditioning
- [ ] compare single-image vs multiview per accessory class
- [ ] test best-of-N generation scaling
- [ ] test provider specialization by accessory class
- [ ] test Tripo semantic segmentation for removing generated connectors
- [ ] test Meshy printability repair against local deterministic repair
- [ ] test CAD-Recode on generated hard-surface accessory point clouds
- [ ] test direct text-to-CadQuery/build123d on shields/backpacks/mechanical props
- [ ] determine which visual metrics correlate with human "official-like accessory" judgments
- [ ] build accepted/rejected candidate ranking dataset
- [ ] build source-object -> minifigure-accessory translation pairs
- [ ] evaluate fine-tuning only after retrieval/ensemble baseline is frozen

### Long-term ML candidates

- [ ] provider router trained from benchmark/history
- [ ] candidate ranker trained from accepted/rejected geometry
- [ ] manufacturability-risk predictor from geometry + print outcomes
- [ ] minifigure-accessory abstraction model trained on source -> accepted accessory pairs
- [ ] open-model adapter/fine-tune for Brickmen accessory geometry
- [ ] geometry simplification model that preserves identity-critical features while enforcing minifigure-scale readability

### Definition of done

The system is not "fully automated" merely because it can return an STL from a prompt. The target is reached when a character request can autonomously produce a source-grounded accessory set whose geometry:
1. is tied to a resolved source appearance;
2. passes LEGO/minifigure style and scale checks;
3. uses only validated functional connector geometry;
4. passes articulation and deterministic DFM gates;
5. is watertight/manufacturable;
6. can be reproduced from stored inputs/model snapshots;
7. passes the selected physical validation level;
8. feeds observed print results back into future routing/ranking.


## Non-standard figure architecture program — 2026-09-27

### Research mapped

- [x] establish FigureArchitecture as separate from character/body label
- [x] resolve AF Hulk family to Alpha Toys and document ~7 cm examples
- [x] distinguish modern LEGO Giant/BigFig architecture from custom 7 cm muscle bodies
- [x] identify Axl oversized-torso hybrid as an official intermediate precedent
- [x] identify Hagrid giant-body hybrid and legacy Troll giant architecture
- [x] map provisional G (2), Bigguy, Mr.J/Heart, KDL and maker-specific BigFig families
- [x] classify MidFig as a loose community label rather than one mechanical standard
- [x] create FigureArchitecture registry/schema additions
- [x] design image/mesh architecture recognition pipeline
- [x] design BodyStyleProfile and StyleTransferPair system
- [x] create cross-architecture recognition/style benchmark
- [x] create physical sample/metrology queue
- [x] create unified implementation roadmap

### Next research/implementation

- [ ] ingest release-level architecture observations from HeroBloks/BrickLink/Rebrickable/maker sources
- [ ] build official Giant exploded digital twin and joint graph
- [ ] build Axl and Hagrid hybrid digital twins
- [ ] acquire/measure Alpha Toys AF body
- [ ] acquire/measure G (2), Bigguy, Mr.J/Heart and KDL representatives
- [ ] test compatible BigFig releases against LEGO Giant joints/components
- [ ] build standardized body landmark extractor
- [ ] benchmark SigLIP-style image retrieval across known body systems
- [ ] benchmark OpenShape and Uni3D on scans/meshes
- [ ] construct Hulk cross-architecture translation corpus
- [ ] construct Thing/Beast/Colossus follow-up pairs
- [ ] build architecture-specific neutral blank bodies and surface maps
- [ ] connect BodyStyleProfile to image/3D generation retrieval
- [ ] connect FigureArchitecture joints to parametric connector library
- [ ] prototype architecture-conditioned full-body generation
- [ ] physically print and cycle-test first custom articulated body

Detailed implementation sequencing is canonical in `agentic-custom-parts-and-body-architecture-roadmap.md`.

### Continued topology/census pass — 2026-09-27

- [x] reconcile BodyArchitecture draft into canonical FigureArchitecture
- [x] add release-level FigureArchitectureObservation contract
- [x] add architecture-selection contract
- [x] add architecture-conditioned CharacterBodyDesignSpec
- [x] define original Brickmen Broad/Mid/XL/Giant design targets
- [x] distinguish early integrated-head Giant from later modular-head Giant
- [x] add specialized Giant creature family
- [x] add stacked-torso multi-arm architecture
- [x] add specialized mechanical/droid architecture
- [x] add ghost, serpent, merfolk, tentacle, roller and centaur lower-body topologies
- [x] add specialized integrated character-body umbrella and Jabba-style tail body
- [x] document that maker/product prefix cannot define architecture
- [x] create continuous non-standard body census/ingestion strategy
- [x] create provisional BodyStyleProfile registry
- [x] expand recognition benchmark beyond humanoid size classes
- [x] add SAM2/OpenShape/Uni3D/SAMPart3D/PartSLIP++/Tripo segmentation research path
- [x] expand physical acquisition queue for topology variants
- [ ] ingest release-level architecture observations at scale
- [ ] materialize canonical digital twins for the first official architectures
- [ ] acquire and physically measure Alpha AF/G (2)/official Giant representatives
- [ ] train/evaluate first architecture recognition baseline
- [ ] create first architecture-specific surface maps
- [ ] implement CharacterBodyDesignSpec compiler
- [ ] generate first original Brickmen Mid static prototype
- [ ] validate Brickmen Mid joints before articulated generation

### Body generation / learning stack additions — 2026-09-27

- [x] add ball-jointed standard-scale custom architecture family
- [x] add MegaFig/buildable separation
- [x] identify OA2201-OA2204 16 cm family candidate
- [x] record DY very-large scale variation
- [x] record same-maker 4.3 cm vs 8 cm Renzaima evidence
- [x] add non-Marvel BigFig evidence
- [x] add faceted figure-architecture feature schema
- [x] add reusable JointProfile/joint validation subsystem
- [x] add adjacent articulated figure reference systems
- [x] add PartCrafter/PAct/ArtLLM/Particulate/UniPart/Trellis SegPart research
- [x] add factorized BodyCorpusSample training design
- [x] add body generation evaluation contract
- [ ] ingest first 500 release-level FigureArchitectureObservation records
- [ ] materialize first Hulk cross-architecture BodyCorpusSample set
- [ ] run maker-held-out architecture classification baseline
- [ ] test PartCrafter on canonical body reference images
- [ ] test PAct/Particulate articulation proposals against known digital twins
- [ ] build first JointProfile coupon generator
- [ ] measure commercial ball-joint-arm torso adapter
- [ ] acquire one OA 16 cm family sample
- [ ] acquire one Mega Construx modern micro-action figure as adjacent articulation reference
- [ ] generate first Brickmen Mid static component set


### Continued generation/body intelligence pass — 2026-09-27

Completed research/architecture:
- [x] build Hulk cross-architecture control corpus
- [x] build Thing cross-architecture matched-source control corpus
- [x] add architecture-neutral CharacterBodyFeatureSpec
- [x] separate maker identity from release-level body-family architecture
- [x] add MoldFamily / MoldRevision / mold-equivalence model
- [x] map broader compatible/custom BigFig ecosystem beyond Hulk
- [x] derive hybrid printed-shell + commodity-joint engineering patterns
- [x] separate legacy Hagrid Body Giant from later Hagrid Half Giant architecture
- [x] define component-level non-standard digital-twin ingestion queue
- [x] define Brickmen-original MidFig v0 concept
- [x] add image/scan architecture recognition model registry
- [x] add PartCrafter part-aware generation research
- [x] add SAMPart3D / PartField segmentation and correspondence research
- [x] add OmniPart and SAM3D-Part selective/part-aware generation research
- [x] add PAct / Particulate / ArtLLM / UniPart / LAM articulated generation research
- [x] add Articulate AnyMesh / URDF-Anything+ / SPARK / Kinematify survey
- [x] define learned JointProposal safety boundary
- [x] define architecture-conditioned BodyStyleCompiler
- [x] define StyleMappingRule schema

Highest-priority next implementation:
- [ ] materialize Giant LDraw component digital twin
- [ ] materialize Hagrid Half Giant digital twin
- [ ] finish Axl component geometry/source resolution
- [ ] implement CharacterBodyFeatureSpec extractor
- [ ] implement BodyStyleCompiler prototype
- [ ] implement PartCrafter/PartField/SAMPart3D experiment harness
- [ ] implement JointProposal -> FigureArchitecture reconciliation
- [ ] implement Brickmen MidFig parametric skeleton generator
- [ ] generate MidFig P0 mechanical mule geometry
- [ ] build first JointCartridge coupons
- [ ] acquire official/compatible Giant + Alpha AF + G(2) physical samples
- [ ] run first architecture recognition benchmark
- [ ] ingest MoldFamily equivalence observations at scale
- [ ] build statistical BodyStyleProfile measurements from canonical images
- [ ] add Bane/Thanos/Darkseid/Gorilla Grodd/Blob/Kingpin control corpora
- [ ] add fur/rock/metal/scales/armor surface-material grammars
- [ ] benchmark selective component regeneration after one-body-part revisions


### Alpha Venom and morphology continuation — 2026-09-27

- [x] verify Alpha Toys Venom AF321/AF325 body was missing as a distinct architecture
- [x] establish ~4–4.5 cm Alpha muscular/symbiote hybrid architecture candidate
- [x] separate AF321-AF326 from Alpha ~7 cm Hulk-family body
- [x] treat AF327-AF332 as related symbiote revision/family candidate
- [x] preserve MaxiFig as source terminology rather than scale truth
- [x] add Alpha body-family census
- [x] add Alpha symbiote same-family/different-character corpus
- [x] add Venom cross-architecture study
- [x] add Alpha Venom physical metrology target
- [x] refine Brickmen Broad body target
- [x] create Brickmen Broad architecture specification
- [x] add diverse morphology control corpus
- [x] add morphology archetype registry
- [x] add surface-material profile registry
- [x] add frozen non-standard morphology benchmark

Next:
- [ ] acquire AF325/AF321 physical sample
- [ ] acquire AF328 second sample to resolve AF321-326 vs AF327-332 mechanical equivalence
- [ ] compare AF325 physically against AF345/AF362 7 cm body
- [ ] build Brickmen Broad P0 mechanical mule
- [ ] add Broad shoulder/wrist/waist JointCartridge coupons
- [ ] materialize Blob/Kingpin/Grodd/Thanos/Bane/Abomination canonical image records
- [ ] measure morphology feature vectors from normalized images
- [ ] implement SurfaceMaterialProfile compiler
- [ ] run nonstandard_body_morphology_v0 benchmark across Broad/Mid/Giant targets
- [ ] train no morphology model until reviewed feature labels and unknown handling are stable


### Skeleton implementation continuation — 2026-09-27

- [x] second-pass distinct architecture census
- [x] add Si-Dan full-ball-joint poseable reference architecture
- [x] add ball-jointed custom MidFig upper architecture
- [x] add single-torso four-arm custom architecture
- [x] separate skeleton/bony official architecture
- [x] separate Battle Droid and Super Battle Droid architectures
- [x] add Faun/digitigrade lower-body architecture
- [x] preserve legacy Homemaker/maxifigure as separate terminology/architecture
- [x] define donor torso-shell overlay as augmentation rather than automatic new architecture
- [x] implement BodySkeleton schema
- [x] implement Broad/Mid/XL/Giant v0 normalized skeletons
- [x] implement skeleton compiler and tests
- [x] add reusable topology modules
- [x] update ontology/data model

Next engineering:
- [ ] implement image-landmark skeleton fitter
- [ ] add architecture-specific envelope generation
- [ ] create JointCartridge schema instances for Broad/Giant P0
- [ ] create printable joint coupons
- [ ] create Broad P0 blank mechanical mule
- [ ] create Giant P0 blank mechanical mule
- [ ] run articulation sweep/collision tests
- [ ] generate first part-aware neutral shells around locked skeletons
- [ ] then progress to Mid P0 and XL P0


### Reference fitting continuation — 2026-09-27

- [x] implement bounded landmark skeleton fitter
- [x] implement batch fitting
- [x] add parameter-bound diagnostics
- [x] add scale-aware cross-skeleton comparison
- [x] seed AF325 Venom, AF345 Hulk, LEGO Giant Hulk, KDL Thing, and Axl references
- [x] record first fit results and revision candidates
- [x] separate visual silhouette observations from skeletal pivots
- [x] add visual-envelope measurement tool
- [x] add normalized seed envelope summary

Next:
- [ ] reannotate seed references with manual-review UI
- [ ] add side/back views and Y-depth observations
- [x] add official LDraw-derived Giant landmark ground truth
- [x] add standard-minifigure/Axl donor-component landmark ground truth
- [x] implement BodyEnvelopeProfile fitting against visual width/depth observations
- [x] add skeleton-to-reference SVG/image overlay renderer
- [ ] fit head scale and separate torso/leg segment lengths
- [x] connect fitted skeleton/envelope outputs to part-aware generation prompts/conditioning


### Official geometry fitting anchors — 2026-09-27

- [x] add LDraw 10128 Giant shoulder-socket anchor metadata
- [x] add LDraw 10154/10124 hand-socket anchor metadata
- [x] preserve 43093 as commodity hardware reference
- [x] separate official Giant EngineeringSkeleton evidence from Brickmen Giant design skeleton

Next:
- [x] ingest full 10128/10154/10124/10127/10126 mesh geometry into reproducible component digital-twin references
- [x] ingest complete official `10128p01c01` component assembly frames into digital twin
- [x] derive complete default-pose local transforms and component frames
- [ ] reconcile LDraw frames with physical sample measurements
- [x] map optional Giant-compatible 43093 shoulder hardware reference profile
- [ ] physically validate/promote Giant-compatible Brickmen shoulder JointCartridge

### Standard minifigure / Axl donor frames — 2026-09-27

- [x] ingest official standard torso/arm assembly frames from LDraw
- [x] ingest current official standing lower-body assembly frame
- [x] resolve Axl as standard-lower-body + standard-torso-core + oversized-shell + dedicated-arm hybrid
- [x] preserve current 23763/24128 LDraw geometry as provisional while it remains unofficial
- [x] separate donor assembly frames from visual silhouette landmarks

Next:
- [ ] acquire/scan physical Axl 23763/24128 and 24101/24104 components
- [ ] replace provisional Axl arm-pinhole hypotheses with physical measurements
- [x] add fixed/reference-parameter constraints to skeleton fitting
- [x] fit Axl outer envelope without scaling locked/default donor frames


### Independent BodyEnvelopeProfile fitting — 2026-09-27

- [x] decouple torso visual width from skeletal shoulder-joint spacing in Broad/Mid/XL/Giant skeletons
- [x] add independent head width/depth and abdomen width envelope parameters
- [x] add BodyEnvelopeProfile fit schema and fitter
- [x] add tests proving envelope fitting does not move mechanical shoulder nodes
- [x] fit the five seed references and record diagnostics
- [x] preserve outer shoulder and hip widths as unmapped visual diagnostics rather than coercing them into joint parameters

Key result:
- Axl front seed fits chest mass with ~1.98x Broad torso envelope width while its outer shoulder silhouette is ~2.93x the default Broad shoulder-joint span. This quantitatively confirms that shell mass and joint spacing must remain independent.

Next:
- [ ] add side/back references and depth observations
- [ ] add dedicated shoulder-mass and lower-body visual envelope primitives where evidence supports them
- [x] add fixed donor/reference-parameter constraints to fitting
- [ ] render skeleton + envelope overlays for manual review


### Locked donor-frame fitting — 2026-09-27

- [x] add reference-level `locked_parameters` contract
- [x] add CLI/API locked-parameter support to skeleton fitting
- [x] exclude locked parameters from optimization
- [x] exclude envelope-only parameters from default skeleton optimization
- [x] add regression coverage for locks, override precedence, bounds, and envelope exclusion

This supports hybrid bodies where a known donor frame must remain unchanged while other body proportions are fitted. It is intentionally parameter/frame locking rather than pretending a visual landmark is exact mechanical metrology.

Next:
- [ ] map physically measured donor frames into explicit locks when target-skeleton parameter semantics are validated
- [ ] add component-frame constraints beyond scalar parameter locks where needed


### Reference overlay renderer — 2026-09-27

- [x] add transparent SVG skeleton/reference review renderer
- [x] render fitted visual envelopes behind skeleton
- [x] render reference landmarks, fitted nodes, and residual vectors
- [x] render silhouette-width annotations
- [x] keep source images external rather than embedding them in generated SVG
- [x] emit a machine-readable fit report alongside optional SVG output

Next:
- [ ] add manual-review annotation editing workflow around the overlay
- [ ] add side/back projection modes when depth references are available


### Fine-grained proportions and view-aware envelopes — 2026-09-27

- [x] add downstream-preserving segment scaling rule
- [x] add independent lower-torso and upper-torso length controls
- [x] add independent thigh and shin length controls
- [x] add independent neck-to-head offset control
- [x] expose visual head height independently from skeletal proportions
- [x] support front/back X-width envelope fitting
- [x] support left/right Y-depth envelope fitting
- [x] support vertical head-envelope span fitting
- [x] add regression coverage for segment independence and view-aware envelope mapping

Still needed before the original seed-refit item is complete:
- [ ] add/review head-height silhouette annotations on real seed references
- [ ] add side/back real reference observations
- [ ] rerun seed skeleton fits using segment-level variables where landmarks support them
- [ ] compare coarse-vs-segment fit residuals and keep only identifiable parameters


### LDraw geometry ingestion pipeline — 2026-09-27

- [x] implement recursive local-library LDraw resolver
- [x] compose type-1 affine subfile transforms
- [x] flatten type-3 triangles and triangulate type-4 quads
- [x] preserve BFC winding/mirror signals needed for reference mesh export
- [x] capture per-source SHA-256, author, !LDRAW_ORG class, license, help, and history
- [x] compute LDU and nominal-mm bounding boxes
- [x] add optional deduplicated OBJ export
- [x] add strict unresolved-dependency handling
- [x] add synthetic recursive-ingestion tests and CI coverage
- [x] create Giant/Axl geometry ingestion target queue

Actual Giant geometry remains open:
- [x] run against a pinned official LDraw library release
- [x] commit/retain manifests for 10128p01c01, 10128, 10154, 10124, 10127, and 10126
- [x] generate source-license-aware reproducible flattened reference-mesh build artifacts
- [x] derive orthographic front/side reference profiles from flattened Giant body/assembly geometry
- [ ] derive decoration-aware back/front regional surface maps where needed


### Official Giant CAD reference promotion — 2026-09-27

- [x] normalize raw LDraw coordinates into the Brickmen semantic body frame
- [x] preserve canonical source frame separately from fitter/view mirroring
- [x] derive normalized official shoulder-center engineering anchors
- [x] add fitter-facing official shoulder reference with explicit left/right convention transform
- [x] derive body-only multi-view normalized envelope evidence from 10128
- [x] add direct normalized CAD/physical/render envelope evidence path
- [x] fit official Giant body width/depth without moving mechanical joints
- [x] expand Giant visual-only torso/abdomen depth ranges from official CAD evidence
- [x] map 43093 as local commodity shoulder hardware reference without coupling it to the official body's 32 mm shoulder spacing
- [x] keep reference CAD authority separate from physical fit/tolerance authority

Measured/reference findings:
- official normalized shoulder-center separation ≈ 0.44996 body heights;
- Brickmen Giant default shoulder span = 0.44, requiring only ~1.023x width adjustment;
- official 10128 upper-torso width mean ≈ 0.44822 body heights;
- official 10128 upper-torso depth mean ≈ 0.41733 body heights;
- official 10128 waist-band width mean ≈ 0.38169 body heights;
- official 10128 waist-band depth mean ≈ 0.34055 body heights.

Still intentionally open:
- [ ] physical 10128/10154/10124/43093 metrology;
- [ ] insertion/removal force and torque measurements;
- [ ] cycle/wear validation;
- [ ] production-approved shoulder cartridge geometry.


### BodyGenerationConditioning compiler — 2026-09-27

- [x] add provider-neutral generation-conditioning schema
- [x] compile skeleton/proportion, visual-envelope, component-plan and mechanical-constraint layers separately
- [x] preserve reference height separately from Brickmen target design height
- [x] preserve fixed-mm commodity hardware independently from normalized generator keep-outs
- [x] propagate per-joint mechanical authority class
- [x] block validation-pending/reference CAD from becoming production mating geometry
- [x] add Giant official-CAD + 43093 conditioning regression
- [x] add Axl Broad-envelope regression proving shell width can change without shoulder movement
- [x] add canonical generated Giant and Axl conditioning fixtures
- [x] integrate conditioning into BodyStyleCompilation and CharacterBodyDesignSpec contracts
- [x] update CLI/documentation flow through part-aware generation

Canonical fixtures:
- `data/generation-conditioning/brickmen-giant-official-cad-v0.json`
- `data/generation-conditioning/brickmen-broad-axl-envelope-v0.json`

Next:
- [x] extend visual conditioning beyond torso/head/abdomen to arms, hands and lower body
- [x] add component-specific keep-out placement frames rather than bbox-only reference sizes
- [ ] route conditioning payloads into provider adapters/benchmarks for PartCrafter and monolithic+segmentation paths


### Limb/lower-body conditioning and engineering-reference split — 2026-09-27

- [x] add official Giant ReferenceEngineeringSkeleton separate from brickmen_giant_v0
- [x] preserve intrinsic 3D shoulder->hand-socket reference vectors
- [x] derive official arm/hand component envelope statistics from pinned LDraw meshes
- [x] add bone-aligned visual arm envelopes
- [x] add independent hand visual envelopes
- [x] add root-to-waist lower-body visual envelope independent from hip/stance spacing
- [x] fit official arm/hand/lower-body CAD evidence to rounded Brickmen visual baselines
- [x] carry oriented envelope endpoints and lengths into BodyGenerationConditioning
- [x] place two fixed-mm 43093 reference keep-outs on selected Brickmen shoulder nodes
- [x] prove hardware keep-out mm dimensions do not scale with body target height

Key findings:
- official Giant arm shoulder->hand-socket vector length ≈ 0.3601 body heights and includes substantial Y-depth offset;
- rounded Brickmen arm cross-section baseline 0.18 x 0.28 differs from official central-profile means by ~1% or less;
- rounded hand baseline 0.175 x 0.25 x 0.21 similarly tracks official reference statistics;
- rounded lower-body width/depth baseline 0.56 x 0.33 is within ~1% of official lower-body profile-band means.

Still open:
- [ ] decide whether Brickmen Giant itself should adopt a fixed-bend arm topology, segmented arm topology, or selectable variants;
- [ ] add articulation-sweep volumes around placed shoulder hardware;
- [ ] physically validate all shoulder/arm mating geometry.


### Fit parameter identifiability — 2026-09-27

- [x] add numerical landmark-parameter Jacobian/sensitivity analyzer
- [x] flag unobserved parameters
- [x] flag near-collinear/confounded parameter pairs
- [x] estimate local Jacobian rank without external numeric dependencies
- [x] batch current five seed references
- [x] prove current 5-parameter seed fits are full-rank
- [x] prove current + neck-head offset + thigh length + shin length is full-rank 8/8 for all five seeds
- [x] prove lower_torso_length_scale + upper_torso_length_scale is rank-deficient 8/9 for all five seeds because no chest landmark separates them
- [x] automate current-vs-safe-expanded fit comparison report

Policy:
- do not promote lower/upper torso segment fitting until chest/torso-center landmarks are annotated;
- safe expanded v1 may be evaluated because it is locally identifiable on every current seed;
- lower RMSE alone never authorizes architecture or mechanical changes.
