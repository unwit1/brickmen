# Brickmen Autonomous State

Last updated: 2026-09-30
Base commit before autonomous bootstrap: `bda2cac8ea8b68bb9e3e5b4d0cf380a9c6ee3ae6`
Last meaningful benchmark/development checkpoint: `dcf43cb327e22a101400d2dd90a64d9e0842d896`
Latest validated test-lock checkpoint: `4c69a64cd21754ce6dbdd3f3adb252228d4958e7`
Status: active

## Current major objective

Turn Brickmen into a self-contained, evidence-backed system for custom-minifigure research, character-to-minifigure translation, visual-style understanding, model training/evaluation, 2D/3D generation, geometry validation, manufacturing, and continuous self-improvement.

Architecture input-safety work that previously blocked the main official evaluation corpora is now complete. Resume the next highest-value evidence-producing work rather than reopening completed architecture review gates.

## Current research frontier

Two major architecture evaluation gates are now fully runnable:

- **Architecture challenge v4:** 23/23 exact source images are byte-verified and 23/23 are explicitly approved raw model inputs.
- **Original 27-case architecture benchmark:** 27/27 cases are model-input allowed: 4 approved raw inputs plus 23 exact-hash approved sanitized derivatives, including 10 SAM2 segmentation candidates.
- Architecture-target evaluation coverage remains 34/49 registered architecture families, with zero remaining P0 official gaps.

Current priority order:
1. execute Fortnite source-appearance -> LEGO semantic first-review/second-review/adjudication and promote only explicit reviewed supervision;
2. expand exact-release multi-view/cross-surface correspondence;
3. finish custom-architecture evaluation acquisition/review: visually review the two byte-pinned Titanic sources and resolve genuine high-resolution Si-Dan media;
4. expand official visual grammar and negative/failure critic corpora;
5. keep model/tool/dataset registries current and continue ontology-breaker searches;
6. close reference-fitting evidence gaps without inventing hidden geometry or physical measurements.

## Latest completed autonomous batches

### Original 27-case architecture benchmark — model-input gate complete

- Reference acquisition remains complete at 27/27 exact byte-verified images.
- Source sanitization review remains complete: 4 clean raw approvals and 23 sanitization-required sources.
- Final model-input gate is now:
  - 27 total cases;
  - 27 model-input allowed;
  - 4 approved raw;
  - 23 approved sanitized;
  - 0 blocked.
- The deterministic sanitization path contributes 13 current approved derivatives.
- The SAM2 path contributes 10 current approved derivatives.
- Canonical SAM2 metadata is checked in at:
  - `knowledge/libraries/lego-minifigure-customs/data/body-architecture-benchmark-sam2-candidates.json`
- The canonical review corpus contains 30 records:
  - 23 current approvals;
  - 7 retained historical `revise` records as failure/audit evidence.
- All SAM2 approvals are exact-hash bound to visually inspected derivatives. Canonical run 13 reproduced the reviewed run-12 pixel and PNG hashes exactly.
- ShengYuan SY288 required a reusable deterministic post-selection cleanup:
  - visually reviewed SAM2 mask 0;
  - source-normalized exclusion rectangles for the branded center stand/logo and bottom base;
  - largest-connected-component cleanup;
  - exact exclusion coordinates and removed-area statistics preserved in candidate provenance.
- The SAM2 workflow now canonicalizes successful zero-error run metadata after artifact upload and commits the metadata-only candidate manifest automatically. Candidate generation itself never auto-approves model input.

### Architecture challenge v4 — input gate complete

- Challenge v4 remains a strict evaluation-only 23-case character-disjoint cohort.
- 23/23 exact source images are byte-verified.
- 23/23 are now explicitly approved as raw model inputs.
- Woody `toy003` and Homemaker 276 nurse were materialized through exact-byte review paths and visually approved without weakening hash rules.
- Current challenge-v4 model-input gate:
  - 23 total;
  - 23 approved raw;
  - 0 sanitized;
  - 0 blocked.
- Architecture-target evaluation coverage remains:
  - 49 registered architectures;
  - 34 evaluation-covered;
  - 15 uncovered;
  - coverage fraction 0.693878;
  - P0 official gaps: 0;
  - P1 custom evaluation gaps: 3;
  - P2 ontology/unresolved gaps: 12.

### Custom architecture acquisition v1

- Product evidence for all three P1 custom architecture gaps is normalized to dedicated product pages.
- Titanic Bricks MidFig ball-joint upper-body source is byte-verified:
  - `DSC_0303.jpg`;
  - 1000x1000 JPEG;
  - SHA-256 `c79fc80eba86f18b155c358bfc900923f5743777bdd215a51b9828142b8d08b2`.
- Titanic Bricks standard-compatible single-torso four-arm source is byte-verified:
  - `untitled.1159.jpg`;
  - 1280x1280 JPEG;
  - SHA-256 `eb3649ca3c8c331bec1e42f15b6326bb47253b4bba8ec13ae57e2db0d3c2af14`.
- Both still require exact visual sanitization/model-input review.
- Si-Dan product evidence confirms a 43 mm poseable figure with ball joints at arms, legs, feet and neck, but only 50x50 thumbnails are currently resolved. Do not admit an upscaled thumbnail as exact evaluation media.

### Fortnite semantic translation supervision pipeline

- Ranked corpus: 2,494 pairs.
- High-priority records: 744.
- First-review plan: 30 deterministic batches (29 x 25, final x 19).
- Batch 0001 is materialized.
- Review schema/validator, conflict-preserving adjudication, adjudicated-only promotion, batching, and local review UI are implemented.
- Measurement heuristics remain prioritization context only; they never become semantic labels automatically.

## Active blockers / constraints

1. **Fortnite semantic supervision labels** — infrastructure is complete, but canonical supervision requires actual first reviews, second reviews where appropriate, and explicit adjudication.
2. **Custom Titanic model-input review** — two exact media assets are byte-pinned but still need direct visual leakage/sanitization review.
3. **Si-Dan evaluation media** — current product evidence is strong but only 50x50 media are resolved; require a genuine high-resolution exact asset rather than upscaling.
4. **Physical multi-view ground truth** — exact rear/side/physical evidence remains limited; do not synthesize hidden views.
5. **Reference-fit torso segmentation** — lower-vs-upper torso segment length remains underidentified until additional landmarks are available.

## Highest-value next work

### P0
1. Execute Fortnite first-review, second-review, and adjudication batches; promote only explicit adjudicated supervision.
2. Expand exact-release multi-view ReferenceSets and cross-surface correspondence without inventing hidden views.
3. Directly visually review the two byte-pinned Titanic custom-architecture assets and build exact-hash model-input decisions.
4. Resolve a genuine high-resolution exact Si-Dan product asset for evaluation.

### P1
- Extract official face/clothing/decoration grammar from evidence.
- Build negative/failure critic data from rejected and revised examples.
- Maintain the current model, dataset, paper, and tool registry.
- Expand cross-catalog minifigure-part/geometry crosswalks.
- Continue ontology-breaker searches.
- Improve reference-fitting evidence where additional measured/visible landmarks can reduce ambiguity.

## Exact continuation point

For the completed original benchmark safety gate:
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-benchmark-model-input-manifest.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-benchmark-sanitization-candidates.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-benchmark-sam2-candidates.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-benchmark-sanitized-asset-reviews.jsonl`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-benchmark-segmentation-prompts.json`
- `tools/knowledge/generate_body_architecture_sam2_candidates.py`
- `tools/knowledge/canonicalize_body_architecture_sam2_report.py`
- `tools/knowledge/validate_body_architecture_sanitized_asset_reviews.py`
- `tools/knowledge/build_body_architecture_model_input_manifest.py`

For challenge v4:
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-challenge-cases-v4.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-challenge-sanitization-reviews-v4.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-challenge-sanitization-queue-v4.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-recognition-challenge-model-input-manifest-v4.json`
- `tests/test_body_architecture_challenge_v4_model_input.py`

For custom architecture acquisition:
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-custom-acquisition-candidates-v1.json`
- `.github/workflows/verify-body-architecture-custom-media.yml`
- `tests/test_body_architecture_custom_acquisition.py`

For Fortnite semantic supervision:
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-plan.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0001.json`
- `tools/knowledge/build_fortnite_semantic_review_ui.py`
- `tools/knowledge/build_fortnite_semantic_adjudication_queue.py`
- `tools/knowledge/promote_fortnite_semantic_supervision.py`

Do not restart completed challenge-v4 raw review or original 27-case sanitization/SAM2 approval work. Preserve held-out/leakage-safe splits, provenance, exact-hash approvals, uncertainty, and the distinction between generated candidates and approved model inputs.

## Validation note

Fresh validation observed on the current architecture checkpoint:
- LEGO Knowledge Tool Tests run `36807156707` completed successfully on commit `4c69a64cd21754ce6dbdd3f3adb252228d4958e7`;
- Body geometry tests run `36807156814` completed successfully on the same commit;
- SAM2 canonical generation run `36806483552` completed successfully and persisted the canonical 10-record metadata-only candidate manifest;
- run-13 canonical SAM2 pixel and PNG hashes exactly matched all 10 visually inspected run-12 derivatives.

## Continuation rule

A completed batch, commit, source family, or research phase is not an endpoint. Validate, persist, update state, choose the next task, and continue.

## Blocker rule

If a task is blocked:
- record exactly why;
- try a materially different source/method when reasonable;
- do not repeat identical failed actions indefinitely;
- switch to another useful independent workstream;
- return later only when new evidence or capability changes the situation.
