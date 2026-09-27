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
