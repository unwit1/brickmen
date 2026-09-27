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
