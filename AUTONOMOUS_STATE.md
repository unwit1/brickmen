# Brickmen Autonomous State

Last updated: 2026-09-28
Base commit before autonomous bootstrap: `bda2cac8ea8b68bb9e3e5b4d0cf380a9c6ee3ae6`
Last meaningful corpus checkpoint: `51001f45ed1cbddf624c5b7dc774e4ab776a2bce`
Latest validated knowledge-tool test checkpoint: `393c7aa9de572a27cb60df4f5ef2f8913c4747c1`
Status: active

## Current major objective

Turn Brickmen into a self-contained, evidence-backed system for custom-minifigure research, character-to-minifigure translation, visual-style understanding, model training/evaluation, 2D/3D generation, geometry validation, manufacturing, and continuous self-improvement.

## Current research frontier

Corpus and evaluation completion remains the highest-value frontier.

Current priority order:
1. resolve/materialize remaining body-architecture benchmark visual evidence;
2. execute the now-operational Fortnite source-appearance -> LEGO semantic review pipeline;
3. expand exact-release multi-view/cross-surface correspondence;
4. expand official visual-reference coverage and official visual grammar;
5. build negative/failure corpora;
6. keep model/tool/dataset registries current;
7. close specific reference-fitting evidence gaps;
8. search for ontology-breaking body architectures.

## Latest completed autonomous batches

### Body-architecture benchmark population and reference routing
- 27 real benchmark records remain populated:
  - 18 closed-set architecture-classification cases;
  - 9 open-set unknown-rejection cases;
  - 11 core-evidence cases;
  - 7 provisional-evidence cases.
- Character-corpus holdouts remain Hulk=development, Venom=validation, Thing=test.
- All 27 records have explicit source references.
- Four BrickLink cases now have verified exact image URLs:
  - SH0037 Hulk;
  - SH0252 Mighty Micros Hulk;
  - SH0371 Giant Hulk;
  - SH0542 Venom.
- Acquisition state is now:
  - 4 ready for content-addressed materialization;
  - 22 still require exact image-URL resolution;
  - 1 blocked on a direct release locator (G (2) GH0304).
- Catalog-page locators are never treated as image assets.

### Fortnite semantic translation supervision pipeline
- Canonical ranked queue: 2,494 pairs, 744 current high-priority records (score >= 6).
- Added uncertainty-safe semantic review schema and validator.
- Added disagreement-preserving adjudication queue.
- Added explicit adjudicated-only promotion gate for canonical supervision.
- Added deterministic first-review / second-review / adjudication work batching.
- Added end-to-end integration tests covering review -> conflict -> adjudication -> promotion.
- Materialized first ranked first-review batch:
  - 25 pairs;
  - priority range 14 down to 11.5;
  - batch ID `fortnite-review-first_review-056fd3e0773faee9`.
- Added deterministic 30-batch plan for all 744 high-priority pairs:
  - 29 batches of 25 plus final batch of 19;
  - batch 0001 materialized, remaining batches generated on demand.
- Added standalone local browser review UI:
  - source and LEGO images side-by-side;
  - localStorage draft persistence;
  - explicit observed-feature annotations;
  - reviewer/model provenance;
  - JSONL export;
  - no automatic semantic labels from measurement signals.
- Added manual GitHub Actions workflow that can build any planned first-review batch by index and upload a standalone reviewer artifact without paid AI API usage.
- Latest knowledge-tool CI for the full batch plan is green.

## Active blockers / constraints

1. **GH0304 direct locator** — HeroBloks identity/version graphs confirm G (2) GH0304 Hulk (Avengers), but a direct release page was not verified. Keep it indirect; do not guess a URL.
2. **Architecture benchmark materialization** — four exact BrickLink image URLs are known, but this chat/runtime could not directly fetch/checksum those external image bytes. Keep them ready-for-materialization rather than claiming hashes.
3. **Remaining page-media resolution** — 21 reviewed custom-catalog/retailer page locators plus SH1051 still need exact image URLs.
4. **Wider physical multi-view ground truth** — exhaustive physical capture and some BrickLink enrichment depend on external physical assets/credentials. Do not synthesize missing rear/side evidence.
5. **Semantic review labels** — infrastructure is complete, but actual submitted/adjudicated labels require direct visual inspection. Measurement heuristics remain prioritization only.

## Important known technical gap

Current reference-fitting work can identify several useful parameters, but lower- versus upper-torso segment length remains underidentified until additional chest/torso-center landmarks are added. Treat this as a concrete evidence-acquisition target rather than a reason to stop unrelated work.

## Highest-value next work

### P0
1. Resolve exact image URLs for the remaining architecture benchmark cases using source-specific supported/reviewed methods.
2. Materialize/checksum the four already-resolved BrickLink image URLs when a runtime with external image download is available.
3. Keep GH0304 blocked unless a direct release locator is actually verified.
4. Use the Fortnite batch plan/UI to perform first reviews, second reviews, and adjudication; only promote explicit adjudicated records.
5. Expand exact-release multi-view ReferenceSets and cross-surface correspondence without inventing hidden views.

### P1
- Official face/clothing/decoration grammar extraction.
- Negative/failure critic corpus.
- Current model/dataset/tool census.
- Cross-catalog minifigure-part/geometry crosswalks.

## Exact continuation point

For architecture references:
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-reference-acquisition-queue.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-source-registry.json`

For Fortnite semantic supervision:
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-plan.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0001.json`
- `tools/knowledge/build_fortnite_semantic_review_work_batch.py`
- `tools/knowledge/build_fortnite_semantic_review_ui.py`
- `tools/knowledge/validate_fortnite_semantic_reviews.py`
- `tools/knowledge/build_fortnite_semantic_adjudication_queue.py`
- `tools/knowledge/promote_fortnite_semantic_supervision.py`

Try a materially different exact-image resolution method for remaining benchmark pages. If that still blocks, continue another independent corpus/evaluation task; do not restart from first principles.

## Continuation rule

A completed batch, commit, source family, or research phase is not an endpoint. Validate, persist, update state, choose the next task, and continue.

## Blocker rule

If a task is blocked:
- record exactly why;
- try a materially different source/method when reasonable;
- do not repeat identical failed actions indefinitely;
- switch to another useful independent workstream;
- return later only when new evidence or capability changes the situation.
