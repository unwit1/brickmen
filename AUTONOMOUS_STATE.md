# Brickmen Autonomous State

Last updated: 2026-09-29
Base commit before autonomous bootstrap: `bda2cac8ea8b68bb9e3e5b4d0cf380a9c6ee3ae6`
Last meaningful benchmark/development checkpoint: `2bc3239dccfdf8cf4f5f632eaa7a69ffdf4589fc`
Latest test-lock checkpoint: `2bc3239dccfdf8cf4f5f632eaa7a69ffdf4589fc`
Status: active

## Current major objective

Turn Brickmen into a self-contained, evidence-backed system for custom-minifigure research, character-to-minifigure translation, visual-style understanding, model training/evaluation, 2D/3D generation, geometry validation, manufacturing, and continuous self-improvement.

## Current research frontier

Architecture breadth has advanced materially. Challenge v3 now covers 22 character-disjoint official/specialized architectures and the architecture registry has evaluation coverage for 33/49 registered families.

Current priority order:
1. close the final concrete official architecture gap, legacy LEGO Homemaker/maxifigure, if a specific assembled figure can be tied to an exact byte-pinned clean source;
2. finish the one remaining challenge-v3 raw-input review blocker (Woody `toy003`) without weakening exact-hash review rules;
3. finish the original 27-case benchmark's 15 deterministic derivative reviews and 8 SAM2 segmentation reviews in a capable local pixel/runtime environment;
4. execute Fortnite source-appearance -> LEGO semantic first-review/second-review/adjudication;
5. expand exact-release multi-view/cross-surface correspondence;
6. expand official visual grammar and negative/failure corpora;
7. keep model/tool/dataset registries current and resolve high-value custom/ontology gaps.

## Latest completed autonomous batches

### Architecture challenge v3 — 22 architecture cohort
- Challenge v3 contains 22 evaluation-only, character-disjoint cases across 22 unique architectures.
- 22/22 exact source images are byte-verified and hash-pinned.
- The manifest was repaired after the source registry had advanced beyond stale v3 verification metadata.
- 16 exact-hash approvals were inherited from challenge v2 because their source hashes are unchanged.
- Five new v3 references were directly visually reviewed and approved raw:
  - baby/toddler `cty0668`;
  - legacy Fantasy Era troll `cas424`;
  - Heroica microfigure `85863pb063`;
  - Friends mini-doll `frnd0010`;
  - skeleton `gen001`.
- Woody `toy003` remains deliberately blocked because the exact verified BrickLink source image could not be rendered in the current review environment. Alternate images are not accepted as a substitute for exact-hash approval.
- Current challenge-v3 model-input gate:
  - 22 total cases;
  - 21 approved raw model inputs;
  - 0 approved sanitized derivatives;
  - 1 blocked exact raw review.
- The generic model-input compiler now preserves raw-review blockers as `pending_visual_sanitization_review` rather than incorrectly reporting them as missing sanitization candidates.
- Regression tests lock byte verification, queue state, exact blocker identity, manifest state, and builder drift.

### Architecture coverage refresh
- Registry architectures: 49.
- Evaluation-covered architectures: 33.
- Uncovered architectures: 16.
- Coverage fraction: 0.673469.
- Remaining gap priorities:
  - P0 official: 1;
  - P1 custom evaluation: 3;
  - P2 ontology/unresolved: 12.
- The only remaining concrete official P0 gap is `lego_homemaker_maxifigure_legacy`.
- Coverage tooling and tests now use challenge v3 rather than challenge v2.

### Homemaker/maxifigure evidence progress
- Existing component-graph evidence remains valid for sets 55-1, 200-1 and 231-1.
- A stronger exact-release path has been identified in LEGO Homemaker set 276-1 (1977, Nurse and Child / Doctor's Office):
  - BrickLink inventory explicitly records blue and white Homemaker torso/head counterpart assemblies and the underlying arm/hand/head parts;
  - surviving instructions visibly define the nurse and child assemblies;
  - an external collector archive has isolated front photos explicitly labeled as the 276 nurse and child.
- This materially reduces the identity/assembly uncertainty, but the benchmark gap is not yet closed because Brickmen still lacks a byte-pinned exact clean single-figure asset admitted through the normal leakage/input gate.

### Original 27-case architecture benchmark
- Reference acquisition remains complete at 27/27 exact byte-verified images.
- Source sanitization review remains complete:
  - 4 clean raw approvals;
  - 23 sanitization-required.
- Deterministic derivative path:
  - 15 generated candidates;
  - exact-hash visual approval still pending in a local pixel environment.
- Segmentation path:
  - 8 SAM2 cases;
  - prompt seeds and wrapper exist;
  - execution/visual approval still require a capable local SAM2 runtime.
- Do not weaken exact-hash or visual-review gates to increase runnable count.

### Fortnite semantic translation supervision pipeline
- Ranked corpus: 2,494 pairs.
- High-priority records: 744.
- First-review plan: 30 deterministic batches (29 x 25, final x 19).
- Batch 0001 is materialized.
- Review schema/validator, conflict-preserving adjudication, adjudicated-only promotion, batching, and local review UI are implemented.
- Measurement heuristics remain prioritization context only; they never become semantic labels automatically.

## Active blockers / constraints

1. **Challenge-v3 Woody exact visual approval** — source hash `777fd93e31997b912debb734bf0be461c6795210649370bd6be92717f948e7c9` is byte-verified, but the exact source image could not be rendered in the current review environment. Keep blocked until that exact asset is inspected.
2. **Legacy Homemaker benchmark admission** — set 276-1 now provides strong assembled-identity evidence, but a clean exact single-figure source must still be byte-pinned and reviewed before the architecture enters the evaluation cohort.
3. **Original architecture sanitized derivatives** — 15 deterministic candidates require direct local pixel review.
4. **Original architecture segmentation candidates** — 8 cases require a configured SAM2 runtime/checkpoint plus direct review.
5. **Fortnite semantic supervision labels** — review infrastructure is complete, but canonical supervision requires actual reviews/adjudication.
6. **Physical multi-view ground truth** — exact rear/side/physical evidence remains limited; do not synthesize hidden views.
7. **Reference-fit torso segmentation** — lower-vs-upper torso segment length remains underidentified until additional landmarks are available.

## Highest-value next work

### P0
1. Attempt to byte-pin and sanitize a specific 276-1 nurse or child Homemaker figure reference; admit it only if exact-release identity and visual-safety gates pass.
2. Resolve the exact-hash Woody `toy003` raw visual review when the verified asset can be rendered.
3. Run/review the original 15 deterministic sanitization candidates locally; validate review JSONL and rebuild the model-input manifest.
4. Run/review the 8 SAM2 segmentation candidates in a capable local runtime.
5. Execute Fortnite first-review/second-review/adjudication batches and promote only explicit adjudicated supervision.
6. Expand exact-release multi-view ReferenceSets and cross-surface correspondence.

### P1
- Evaluate the three concrete custom-architecture gaps:
  - `custom_midfig_balljoint_upper`;
  - `custom_sidan_full_balljoint_poseable`;
  - `custom_standard_four_arm_single_torso`.
- Official face/clothing/decoration grammar extraction.
- Negative/failure critic corpus.
- Current model/dataset/tool census.
- Cross-catalog minifigure-part/geometry crosswalks.
- Further ontology-breaker searches.

## Exact continuation point

For challenge v3:
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-challenge-cases-v3.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-challenge-sanitization-reviews-v3.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-challenge-sanitization-queue-v3.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-challenge-model-input-manifest-v3.json`
- `tests/test_body_architecture_challenge_v3_model_input.py`

For architecture gaps:
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-coverage-gaps.json`
- `knowledge/libraries/lego-minifigure-customs/data/figure-architecture-registry.json`
- `tools/knowledge/build_body_architecture_coverage_gaps.py`
- `tests/test_build_body_architecture_coverage_gaps.py`

For original benchmark safety:
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-benchmark-model-input-manifest.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-benchmark-sanitization-candidates.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-benchmark-segmentation-prompts.json`
- `tools/knowledge/prepare_body_architecture_sanitization_review.py`
- `tools/knowledge/validate_body_architecture_sanitized_asset_reviews.py`
- `tools/knowledge/generate_body_architecture_sam2_candidates.py`

For Fortnite semantic supervision:
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-plan.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0001.json`
- `tools/knowledge/build_fortnite_semantic_review_ui.py`
- `tools/knowledge/build_fortnite_semantic_adjudication_queue.py`
- `tools/knowledge/promote_fortnite_semantic_supervision.py`

Do not restart completed source acquisition or architecture-v3 expansion. Preserve held-out/leakage-safe split logic, provenance, uncertainty, and exact-hash approval gates.

## Validation note

The new v3/gap regression tests have been committed, and checked-in artifacts were built against the same deterministic logic. The connected GitHub status endpoint exposed no CI status for the direct-push checkpoint, so do not claim a fresh full CI run until one is observed or executed.

## Continuation rule

A completed batch, commit, source family, or research phase is not an endpoint. Validate, persist, update state, choose the next task, and continue.

## Blocker rule

If a task is blocked:
- record exactly why;
- try a materially different source/method when reasonable;
- do not repeat identical failed actions indefinitely;
- switch to another useful independent workstream;
- return later only when new evidence or capability changes the situation.
