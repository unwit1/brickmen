# Brickmen Autonomous State

Last updated: 2026-09-29
Base commit before autonomous bootstrap: `bda2cac8ea8b68bb9e3e5b4d0cf380a9c6ee3ae6`
Last meaningful benchmark checkpoint: `9314cb352296556ff624a7d0045f2db7c318fe74`
Latest validated knowledge-tool test checkpoint: `9314cb352296556ff624a7d0045f2db7c318fe74`
Status: active

## Current major objective

Turn Brickmen into a self-contained, evidence-backed system for custom-minifigure research, character-to-minifigure translation, visual-style understanding, model training/evaluation, 2D/3D generation, geometry validation, manufacturing, and continuous self-improvement.

## Current research frontier

Corpus and evaluation completion remains the highest-value frontier, but architecture **reference acquisition is complete**. The body-architecture benchmark now needs safe model inputs and broader architecture coverage, not more URL hunting.

Current priority order:
1. finish leakage-safe model-input preparation for the architecture benchmark;
2. broaden architecture benchmark coverage beyond Hulk/Venom/Thing;
3. execute Fortnite source-appearance -> LEGO semantic review/adjudication;
4. expand exact-release multi-view/cross-surface correspondence;
5. expand official visual grammar and negative/failure corpora;
6. keep model/tool/dataset registries current;
7. close specific reference-fitting evidence gaps and ontology gaps.

## Latest completed autonomous batches

### Architecture benchmark acquisition — complete
- 27 benchmark cases remain populated:
  - 18 closed-set architecture-classification cases;
  - 9 open-set unknown-rejection cases;
  - 11 core-evidence cases;
  - 7 provisional-evidence cases.
- Existing character-corpus holdouts remain Hulk=development, Venom=validation, Thing=test.
- **27/27 cases now have exact image URLs.**
- **27/27 exact images are byte-verified with SHA-256, dimensions, format, and provenance.**
- All 27 verified images have unique source hashes.
- Acquisition queue has zero unresolved or blocked cases.
- GH0304 still preserves its weaker HeroBloks identity-graph evidence, but exact KongBricks GH0304 visual media removes it as a benchmark-image blocker.

### Architecture benchmark leakage-sanitization — planned end to end
- All 27 verified source images received explicit visual sanitization review:
  - 4 approved as clean raw model inputs;
  - 23 require sanitization.
- All 23 cleanup-required cases have explicit implementation plans:
  - 15 deterministic crop/mask candidates;
  - 8 primary-figure segmentation cases.
- Metadata-only deterministic candidate workflow completed successfully:
  - 15 generated candidates;
  - 8 segmentation blockers;
  - 0 errors;
  - workflow run `36516743830`;
  - artifact `11010858897`.
- Canonical candidate metadata preserves source hashes/dimensions, transform operations, output dimensions, sanitized pixel hashes, sanitized PNG hashes, and review status without storing image bytes in Git.
- Hash-pinned sanitized-asset review schema and validator are implemented.
- Local sanitization review UI:
  - keeps derivative bytes local;
  - computes PNG SHA-256 in-browser;
  - refuses approval unless the exact canonical candidate hash is loaded;
  - requires all visual safety checks;
  - exports metadata-only review JSONL.
- One-command local review preparation regenerates derivatives, verifies canonical hash equality, and builds the local reviewer.
- Canonical model-input manifest currently admits only:
  - 4 approved raw assets;
  - 0 sanitized derivatives;
  - 23 blocked assets.
- The 8 segmentation blockers now have hash-pinned SAM 2 box/point prompt seeds and an executable `SAM2ImagePredictor` wrapper. SAM score chooses a candidate only; no segmentation result is auto-approved.
- Latest full knowledge-tool and body-geometry CI is green at `9314cb352296556ff624a7d0045f2db7c318fe74`.

### Fortnite semantic translation supervision pipeline
- Ranked corpus: 2,494 pairs, 744 current high-priority records.
- Uncertainty-safe review schema/validator, conflict-preserving adjudication, adjudicated-only promotion, deterministic work batching, and local review UI are implemented.
- High-priority first-review plan is 30 deterministic batches:
  - 29 batches of 25;
  - final batch of 19.
- Batch 0001 is materialized (25 pairs, priority 14 to 11.5).
- Measurement heuristics remain prioritization context only and never become semantic labels automatically.

## Active blockers / constraints

1. **Architecture sanitized derivative approval** — the 15 deterministic candidates require direct local pixel review before they can enter the model-input manifest.
2. **Architecture segmentation candidates** — the 8 segmentation cases require a capable local SAM 2 environment/checkpoint, candidate generation, then the same exact-hash visual review. Prompt seeds are explicitly unvalidated.
3. **Fortnite semantic supervision labels** — review infrastructure is complete, but canonical supervision still requires actual first reviews, second reviews where required, and explicit adjudication.
4. **Physical multi-view ground truth** — exact rear/side/physical evidence still requires additional source access, credentials, or controlled capture; do not synthesize hidden views.
5. **Reference-fit torso segmentation** — lower- versus upper-torso segment length remains underidentified until additional chest/torso-center landmarks are available.

## Highest-value next work

### P0
1. Expand body-architecture recognition benchmark coverage beyond the three current character corpora using only evidence-backed architecture/release records, especially official Hagrid/Axl/Giant variants, specialized creatures, alternate lower bodies, multi-arm bodies, and mechanical bodies.
2. Run/review the 15 deterministic sanitization candidates locally when derivative pixels are available; validate review JSONL and rebuild the model-input manifest.
3. Run the 8 SAM 2 segmentation prompt seeds in a capable local environment; visually review exact outputs; bind only approved hashes.
4. Execute Fortnite first-review/second-review/adjudication batches and promote only explicit adjudicated supervision.
5. Expand exact-release multi-view ReferenceSets and cross-surface correspondence.

### P1
- Official face/clothing/decoration grammar extraction.
- Negative/failure critic corpus.
- Current model/dataset/tool census.
- Cross-catalog minifigure-part/geometry crosswalks.
- Further ontology-breaker searches.

## Exact continuation point

For architecture benchmark safety:
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-benchmark-model-input-manifest.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-benchmark-sanitization-candidates.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-benchmark-segmentation-prompts.json`
- `tools/knowledge/prepare_body_architecture_sanitization_review.py`
- `tools/knowledge/validate_body_architecture_sanitized_asset_reviews.py`
- `tools/knowledge/generate_body_architecture_sam2_candidates.py`

For benchmark expansion:
- `knowledge/libraries/lego-minifigure-customs/data/figure-architecture-registry.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-source-registry.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-benchmark-cases.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-physical-acquisition-queue.json`

For Fortnite semantic supervision:
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-plan.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0001.json`
- `tools/knowledge/build_fortnite_semantic_review_ui.py`
- `tools/knowledge/build_fortnite_semantic_adjudication_queue.py`
- `tools/knowledge/promote_fortnite_semantic_supervision.py`

Do not restart source acquisition. Select the highest-value executable corpus/evaluation gap, preserve provenance and uncertainty, commit useful increments, update state, and continue.

## Continuation rule

A completed batch, commit, source family, or research phase is not an endpoint. Validate, persist, update state, choose the next task, and continue.

## Blocker rule

If a task is blocked:
- record exactly why;
- try a materially different source/method when reasonable;
- do not repeat identical failed actions indefinitely;
- switch to another useful independent workstream;
- return later only when new evidence or capability changes the situation.
