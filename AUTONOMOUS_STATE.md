# Brickmen Autonomous State

Last updated: 2026-09-28
Base commit before autonomous bootstrap: `bda2cac8ea8b68bb9e3e5b4d0cf380a9c6ee3ae6`
Last meaningful benchmark checkpoint: `2571c8a6358b5f7c6fa82b3f1e547ad9c50306bd`
Latest validated knowledge-tool test checkpoint: `e0ad93922f7bbb81646a6354e1f6254a95cc8ea4`
Status: active

## Current major objective

Turn Brickmen into a self-contained, evidence-backed system for custom-minifigure research, character-to-minifigure translation, visual-style understanding, model training/evaluation, 2D/3D generation, geometry validation, manufacturing, and continuous self-improvement.

## Current research frontier

The highest-value frontier remains corpus and evaluation completion. The body-architecture benchmark is no longer schema-only: it now has a reproducible real-case manifest and an explicit visual-reference acquisition path.

Current priority order:
1. resolve/materialize visual evidence for populated benchmark cases;
2. continue source-appearance -> minifigure semantic translation supervision;
3. expand exact-release multi-view/cross-surface correspondence;
4. expand official visual-reference coverage and official visual grammar;
5. build negative/failure corpora;
6. keep model/tool/dataset registries current;
7. close specific reference-fitting evidence gaps;
8. search for ontology-breaking body architectures.

## Latest completed autonomous batch

- Populated the body-architecture recognition benchmark with 27 real corpus records:
  - 18 closed-set architecture-classification cases;
  - 9 open-set unknown-rejection cases;
  - 11 core-evidence cases;
  - 7 provisional-evidence cases.
- Preserved character-corpus holdouts: Hulk=development, Venom=validation, Thing=test.
- Explicitly prohibited maker/release/character/catalog-label leakage into model inputs.
- Expanded the architecture source registry from 38 to 59 sources and linked all 27 benchmark records through `source_refs`.
- Achieved reference-page coverage for 27/27 cases:
  - 26 direct or family-level release references;
  - 1 indirect identity-graph reference (G (2) GH0304 Hulk).
- Added `body-architecture-reference-acquisition-queue.json`:
  - 26 cases ready for exact-image URL resolution;
  - 1 case blocked on a direct release locator;
  - 5 BrickLink/catalog-adapter actions;
  - 21 reviewed page-media resolution actions.
- Added reproducible builders plus checked-in-manifest drift tests and source-integrity tests.
- Latest relevant GitHub knowledge-tool CI is green.

## Active blockers / constraints

1. **GH0304 direct locator** — HeroBloks identity/version graphs confirm G (2) GH0304 Hulk (Avengers), but a direct release page was not verified. Keep it indirect; do not guess a URL.
2. **Image materialization** — catalog-page URLs are provenance locators, not image URLs. Resolve exact reviewed image URLs before using `materialize_lego_reference_images.py`.
3. **Wider physical multi-view ground truth** — exhaustive physical capture and some BrickLink enrichment still depend on external physical assets/credentials. Do not let this block independent corpus work.

## Important known technical gap

Current reference-fitting work can identify several useful parameters, but lower- versus upper-torso segment length remains underidentified until additional chest/torso-center landmarks are added. Treat this as a concrete evidence-acquisition target rather than a reason to stop unrelated work.

## Highest-value next work

### P0
1. Resolve exact image URLs for the 26 ready architecture benchmark cases; preserve source occurrence and rights/provenance, then bind materialized hashes when available.
2. Find a verified direct release locator for G (2) GH0304 or retain it as explicitly blocked.
3. After materialization, add canonical-view validation plus low-resolution, occlusion, and detached-component benchmark variants without changing held-out groups.
4. Continue the ranked Fortnite source->LEGO semantic review queue, prioritizing the highest-information pairs and preserving uncertainty.
5. Expand exact-release multi-view ReferenceSets and cross-surface correspondence.

### P1
- Official face/clothing/decoration grammar extraction.
- Negative/failure critic corpus.
- Current model/dataset/tool census.
- Cross-catalog minifigure-part/geometry crosswalks.

## Exact continuation point

Start from:
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-benchmark-cases.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-reference-acquisition-queue.json`
- `tools/knowledge/build_body_architecture_benchmark_cases.py`
- `tools/knowledge/build_body_architecture_reference_acquisition_queue.py`

First try to advance exact-image resolution/materialization for the 26 ready cases using supported/reviewed source-specific paths. If that is externally blocked, switch immediately to the ranked Fortnite semantic translation queue or exact-release multi-view correspondence. Do not restart from first principles.

## Continuation rule

A completed batch, commit, source family, or research phase is not an endpoint. Validate, persist, update state, choose the next task, and continue.

## Blocker rule

If a task is blocked:
- record exactly why;
- try a materially different source/method when reasonable;
- do not repeat identical failed actions indefinitely;
- switch to another useful independent workstream;
- return later only when new evidence or capability changes the situation.
