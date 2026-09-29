# Brickmen Autonomous State

Last updated: 2026-09-29
Base commit before autonomous bootstrap: `bda2cac8ea8b68bb9e3e5b4d0cf380a9c6ee3ae6`
Last meaningful benchmark/development checkpoint: `6bf84ca33cbbf3ecbd3ee6845333c38e45c3d2d6`
Latest test-lock checkpoint: `6bf84ca33cbbf3ecbd3ee6845333c38e45c3d2d6`
Status: active

## Current major objective

Turn Brickmen into a self-contained, evidence-backed system for custom-minifigure research, character-to-minifigure translation, visual-style understanding, model training/evaluation, 2D/3D generation, geometry validation, manufacturing, and continuous self-improvement.

## Current research frontier

Architecture challenge v4 now contains 23 character-disjoint official/specialized architecture cases. All 23 exact source images are byte-verified, 21 are currently approved as raw model inputs, and architecture-target evaluation coverage is 34/49 registered families. The last concrete official P0 architecture gap, legacy LEGO Homemaker/maxifigure, is now represented; remaining official challenge work is exact-byte visual input approval, not source acquisition.

Current priority order:
1. directly review the exact challenge-v4 Homemaker 276 nurse bytes and the still-blocked Woody `toy003` bytes without weakening exact-hash review rules;
2. finish the original 27-case benchmark's 15 deterministic derivative reviews and 8 SAM2 segmentation reviews in a capable local pixel/runtime environment;
3. execute Fortnite source-appearance -> LEGO semantic first-review/second-review/adjudication;
4. expand exact-release multi-view/cross-surface correspondence;
5. evaluate the three remaining concrete custom architecture gaps;
6. expand official visual grammar and negative/failure corpora;
7. keep model/tool/dataset registries current and resolve ontology gaps.

## Latest completed autonomous batches

### Architecture challenge v4 — 23 architecture cohort
- Challenge v4 is a strict evaluation-only superset of v3 and adds `lego_homemaker_maxifigure_legacy`.
- 23/23 exact source images are byte-verified and hash-pinned.
- The new Homemaker case is anchored to LEGO set 276-1, Nurse and Child / Doctor's Office (1977).
- Its isolated nurse image is byte-verified at SHA-256 `2385f7c7627bb1b5b7412f107d6a2b15ec727e1a13bef8b920809d3504e7a737`.
- Challenge-v3 exact-hash approvals carry forward only where source hashes are unchanged.
- Current challenge-v4 model-input gate:
  - 23 total cases;
  - 21 approved raw model inputs;
  - 0 approved sanitized derivatives;
  - 2 blocked exact raw reviews.
- The blocked cases are:
  - Homemaker 276 nurse — exact bytes verified and release-cross-checked, but direct leakage/sanitization review is still pending;
  - Woody `toy003` — exact verified BrickLink bytes still could not be rendered.
- Byte verification or release identity alone never authorizes model input.

### Architecture coverage refresh
- Registry architectures: 49.
- Evaluation-covered architectures: 34.
- Uncovered architectures: 15.
- Coverage fraction: 0.693878.
- Remaining gap priorities:
  - P0 official: 0;
  - P1 custom evaluation: 3;
  - P2 ontology/unresolved: 12.
- Coverage tooling, checked-in report, and regression expectations now use challenge v4.
- The last concrete official P0 gap is closed at architecture-target evaluation coverage; this does not override raw-image safety gates.

### Homemaker/maxifigure evidence
- Set 276-1 provides strong assembled-identity evidence:
  - BrickLink inventory records the Homemaker torso/head counterpart assembly and underlying body components;
  - surviving instructions define the assembled nurse/child figures;
  - an isolated collector photograph is explicitly identified as the 276 nurse.
- The exact isolated nurse image is registered and byte-verified.
- The figure is admitted to challenge v4 for held-out architecture evaluation metadata.
- Raw visual model input remains blocked until direct inspection of the exact verified bytes passes the normal leakage/sanitization checks.

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

1. **Challenge-v4 Homemaker exact visual approval** — source hash `2385f7c7627bb1b5b7412f107d6a2b15ec727e1a13bef8b920809d3504e7a737` is byte-verified and release-cross-checked, but the exact bytes still require direct visual leakage/sanitization review before raw model input.
2. **Challenge-v4 Woody exact visual approval** — source hash `777fd93e31997b912debb734bf0be461c6795210649370bd6be92717f948e7c9` is byte-verified, but the exact source image could not be rendered in the current review environment. Keep blocked until that exact asset is inspected.
3. **Original architecture sanitized derivatives** — 15 deterministic candidates require direct local pixel review.
4. **Original architecture segmentation candidates** — 8 cases require a configured SAM2 runtime/checkpoint plus direct review.
5. **Fortnite semantic supervision labels** — review infrastructure is complete, but canonical supervision requires actual reviews/adjudication.
6. **Physical multi-view ground truth** — exact rear/side/physical evidence remains limited; do not synthesize hidden views.
7. **Reference-fit torso segmentation** — lower-vs-upper torso segment length remains underidentified until additional landmarks are available.

## Highest-value next work

### P0
1. Directly inspect the exact byte-verified Homemaker 276 nurse asset and approve raw input only if all leakage/sanitization checks pass.
2. Resolve the exact-hash Woody `toy003` raw visual review without substituting an alternate image.
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

For challenge v4:
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-challenge-cases-v4.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-challenge-sanitization-reviews-v4.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-challenge-sanitization-queue-v4.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-challenge-sanitization-candidates-v4.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-challenge-model-input-manifest-v4.json`
- `tests/test_body_architecture_challenge_v4_model_input.py`

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

Do not restart completed source acquisition, challenge-v3 expansion, or Homemaker source verification. Preserve challenge-v4 held-out/leakage-safe split logic, provenance, uncertainty, and exact-hash approval gates.

## Validation note

Challenge-v4 input-gate tests and v4 coverage regression tests are committed, and checked-in artifacts were built against the same deterministic contracts. No fresh full CI execution has yet been observed for this direct-push checkpoint, so do not claim the suite is green until CI or a capable local runtime actually executes it.

## Continuation rule

A completed batch, commit, source family, or research phase is not an endpoint. Validate, persist, update state, choose the next task, and continue.

## Blocker rule

If a task is blocked:
- record exactly why;
- try a materially different source/method when reasonable;
- do not repeat identical failed actions indefinitely;
- switch to another useful independent workstream;
- return later only when new evidence or capability changes the situation.
