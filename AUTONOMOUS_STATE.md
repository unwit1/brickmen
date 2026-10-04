# Brickmen Autonomous State

Last updated: 2026-10-01
Base commit before autonomous bootstrap: `bda2cac8ea8b68bb9e3e5b4d0cf380a9c6ee3ae6`
Last meaningful benchmark/development checkpoint: `1202069d1b0877428f009c9613b9f8cea4dde315`
Latest validated test-lock checkpoint: `b698200220e4b87430af8b2c7794aea75fd4243c`
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
1. continue Fortnite source-appearance -> LEGO semantic first-review coverage from batch 0006 onward while preserving the requirement for a genuinely independent second review/adjudication before canonical promotion;
2. expand exact-release multi-view/cross-surface correspondence beyond the new reviewed flat-art ReferenceSet layer;
3. expand official visual grammar and negative/failure critic corpora;
4. keep model/tool/dataset registries current and continue ontology-breaker searches;
5. close reference-fitting evidence gaps without inventing hidden geometry or physical measurements.

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

### Custom architecture acquisition v1 — complete

- All three P1 custom architecture evaluation cases now have exact byte-pinned media and a complete model-input gate.
- Titanic Bricks MidFig ball-joint upper body:
  - source SHA-256 `c79fc80eba86f18b155c358bfc900923f5743777bdd215a51b9828142b8d08b2`;
  - exact source required logo sanitization;
  - exact reviewed sanitized derivative is approved.
- Titanic Bricks single-torso four-arm body:
  - source SHA-256 `eb3649ca3c8c331bec1e42f15b6326bb47253b4bba8ec13ae57e2db0d3c2af14`;
  - approved raw after exact visual review.
- Si-Dan full ball-joint poseable:
  - genuine 301x500 exact product zoom recovered and byte-pinned at SHA-256 `2ac7f9ba8793107e58892205ea56cc772b876cd63cd2fda08e51e1a0ec8e831e`;
  - approved raw after exact visual review.
- Custom model-input manifest is 3/3 runnable: 2 raw + 1 sanitized, 0 blocked.
- Do not reopen the earlier 50x50-thumbnail or pending-Titanic-review blockers; they are obsolete.

### Exact-release flat-art ReferenceSets v1

- A deterministic compiler now converts reviewed one-to-one flat-art/catalog crosswalks into exact physical-release ReferenceSets.
- Current evidence layer:
  - 61 reviewed crosswalk source records;
  - 47 records resolve one-to-one to a single BrickLink + Rebrickable physical release;
  - 23 exact-release ReferenceSets;
  - 13 multi-surface ReferenceSets;
  - 5 releases with explicit torso-front + torso-rear evidence;
  - 5 same-decorated-component multi-surface correspondences.
- Surface linkage is provenance-only: no hidden surface, pixel alignment, or geometry equivalence is inferred.
- A deterministic multi-view acquisition queue now ranks missing exact-release rear/side evidence without asserting unseen decoration exists: 15 torso-rear targets, 10 head-rear targets, 7 lower-body rear/side targets, and left/right physical side-view targets for all 23 releases.
- Highest-priority current acquisition targets are Jungle Boy (col106) and Princess Leia - Slave Outfit (sw0070), where multiple exact front surfaces are already known but complementary rear/side evidence is absent.
- Exact-release Rebrickable rear-photo leads for both top targets are now preserved in `exact-release-multiview-source-candidates-v1.json` as noncanonical, unpinned acquisition candidates. They are explicitly byte-unverified and training-ineligible until the exact image assets are fetched, hashed, and reviewed.
- `materialize_exact_release_multiview_candidates.py` now attempts byte-pinned acquisition without promotion, records per-candidate provider failures as structured blocked state, and supports an explicit direct-image URL when a trustworthy asset URL is known. GitHub-hosted acquisition currently receives HTTP 403 from the two seeded Rebrickable page URLs, so no bytes or hashes have been accepted for those candidates.
- Canonical artifacts:
  - `knowledge/libraries/lego-minifigure-customs/data/exact-release-flat-art-reference-sets-v1.jsonl`
  - `knowledge/libraries/lego-minifigure-customs/data/exact-release-flat-art-reference-sets-v1-summary.json`
  - `tools/knowledge/build_exact_release_flat_art_reference_sets.py`
  - `knowledge/libraries/lego-minifigure-customs/data/exact-release-multiview-gap-queue-v1.json`
  - `knowledge/libraries/lego-minifigure-customs/data/exact-release-multiview-source-candidates-v1.json`
  - `tools/knowledge/build_exact_release_multiview_gap_queue.py`

### Fortnite semantic translation supervision pipeline

- Ranked corpus: 2,494 pairs.
- High-priority records: 744.
- First-review plan: 30 deterministic batches (29 x 25, final x 19).
- Batch 0001 has now completed a first model-review pass over 25 exact materialized source/LEGO pairs.
- The first-review corpus contains 25 submitted review records and 117 explicit semantic annotations, all bound to the exact source/LEGO SHA-256 values from workflow run `36807686000`, artifact `11137649234`.
- These records are deliberately non-canonical: `review_status=submitted`, training-eligible count 0.
- A second pass must be genuinely independent; do not manufacture reviewer independence by having the same reviewer simply repeat its own first pass.
- Review schema/validator, conflict-preserving adjudication, adjudicated-only promotion, batching, and local review UI are implemented.
- Deterministic machine-readable progress is now derived at `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-semantic-review-progress.json` by `tools/knowledge/build_fortnite_semantic_review_progress.py`; use that artifact as the source of truth for coverage counts and next-batch selection instead of hand-edited prose.
- Measurement heuristics remain prioritization context only; they never become semantic labels automatically.

### Fortnite semantic first-review batch 0002

- Batch 0002 now has 25 submitted GPT-5.6 Sol first reviews with 100 explicit semantic annotations.
- Exact review media came from workflow run `36888310826`, artifact `11174174737`; source and LEGO bytes were SHA-256 verified before review.
- Multi-style source composites are explicitly limitation-scoped rather than being treated as hidden/rear-view evidence.
- The corpus remains non-canonical and training-ineligible pending independent second review and adjudication.
- Regression validation passed in LEGO Knowledge Tool Tests run `36890371822` on commit `8157095062e87b36c5cd3b03ad50d57edbacbfaa`.
- Across batches 0001-0002, first-review coverage is now 50/744 high-priority pairs with 217 annotations; 694 high-priority pairs remain for first-review coverage.

### Fortnite semantic first-review batch 0003

- Batch 0003 adds 25 submitted GPT-5.6 Sol first reviews with 100 explicit semantic annotations.
- Exact review media came from workflow run `36891164586`, artifact `11175719705`; the deterministic batch itself was auto-persisted by the review workflow at commit `f3a84c542d83ac6ca07b29f8103a33367e637ac8`.
- A stale review-ID draft was rejected by regression tests; the reusable canonical-ID normalizer repaired the exact committed records at `e01f2c5bec8cdc8caa3c4b9343028b81b87dbbbc` without changing annotations, evidence, reviewer identity, status, or training eligibility.
- Multi-style composites remain explicitly limitation-scoped; hidden/rear surfaces are never inferred.
- The corpus remains non-canonical and training-ineligible pending independent second review and adjudication.
- Exact-hash and canonical-ID regression validation passed in LEGO Knowledge Tool Tests run `36892803590` on commit `8c182c21c9c81b89abcfda018f9ab8ce8176c9ab`.
- Across batches 0001-0003, first-review coverage is now 75/744 high-priority pairs with 317 annotations; 669 high-priority pairs remain.

### Fortnite semantic first-review batch 0004

- Batch 0004 adds 25 submitted GPT-5.6 Sol first reviews with 100 explicit semantic annotations.
- Exact review media came from workflow run `36892963786`, artifact `11177481661`, batch `fortnite-review-first_review-606e51443a942a92`.
- The canonical-ID workflow mechanically normalized the submitted corpus at commit `93301c3a3e720a08ef9476b8ee8c8ea027c611fa`.
- Multi-style source composites are explicitly limitation-scoped; rear and hidden surfaces are never inferred.
- The batch remains non-canonical and training-ineligible pending a genuinely independent second review and adjudication.
- LEGO Knowledge Tool Tests run `37143420363` passed **428 tests** on commit `4991692cc21b40eadac7fce01a0936d6e59b8c88`.
- Across batches 0001-0004, first-review coverage is now 100/744 high-priority pairs with 417 annotations; 644 high-priority pairs remain.

### Fortnite semantic first-review batch 0005

- Batch 0005 adds 25 submitted GPT-5.6 Sol first reviews with 100 explicit semantic annotations.
- Exact review media came from workflow run `37143503917`, artifact `11281935166`, batch `fortnite-review-first_review-6d278dbd84ee5b33`.
- The deterministic batch was materialized at commit `03d05a45c366b105f5a0801cc325e69b92b27f23`.
- The canonical-ID workflow mechanically normalized the submitted corpus at commit `6860ef0da292098ce63ee17ad75d0cc740cff363`.
- Rear and hidden surfaces are never inferred; observations remain bound to the exact source/front and LEGO wide/front evidence.
- The batch remains non-canonical and training-ineligible pending a genuinely independent second review and adjudication.
- LEGO Knowledge Tool Tests run `37143855221` passed **430 tests** on commit `b698200220e4b87430af8b2c7794aea75fd4243c`.
- Across batches 0001-0005, first-review coverage is now 125/744 high-priority pairs with 517 annotations; 619 high-priority pairs remain.

### Fortnite semantic first-review batch 0006

- Deterministic batch 0006 was materialized at commit `1202069d1b0877428f009c9613b9f8cea4dde315`.
- Exact hash-pinned review media came from workflow run `37151433717`, artifact `11284491078`.
- Batch 0006 adds 25 submitted GPT-5.6 Sol first reviews with 100 explicit semantic annotations.
- Compact visual decisions are byte-locked at `fortnite-first-review-batch-0006-gpt56sol-decisions.json.gz`; the canonical JSONL and summary are deterministically compiled from that evidence.
- The reusable compiler `tools/knowledge/build_fortnite_semantic_review_submission.py` validates pair membership, annotation schema, SHA-256 fields, canonical review IDs, and non-canonical submission status before emitting review records.
- Rear and hidden surfaces are never inferred; observations remain limited to the exact source/front and LEGO wide/front evidence.
- The batch remains non-canonical and training-ineligible pending a genuinely independent second review and explicit adjudication.
- Across batches 0001-0006, first-review coverage is now 150/744 high-priority pairs with 617 annotations; 594 high-priority pairs remain.

### Fortnite semantic first-review batch 0007

- Deterministic batch 0007 was materialized at commit `ccda444e7e32ad76fbc58caf3b899187669028be`.
- Exact hash-pinned review media came from workflow run `37154311505`, artifact `11284279940`, batch `fortnite-review-first_review-ffb51cb7d7edc343`.
- Batch 0007 adds 25 submitted GPT-5.6 Sol first reviews with 100 explicit semantic annotations.
- Compact visual decisions are byte-locked at `fortnite-first-review-batch-0007-gpt56sol-decisions.json.gz`; canonical JSONL and summary are deterministically compiled through the existing submission builder.
- One composite source image is explicitly limitation-scoped; rear, hidden, and inset-only surfaces are not inferred.
- The batch remains non-canonical and training-ineligible pending a genuinely independent second review and explicit adjudication.
- Across batches 0001-0007, first-review coverage is now 175/744 high-priority pairs with 717 annotations; 569 high-priority pairs remain.

### Fortnite semantic first-review batch 0008

- Deterministic batch 0008 was materialized at commit `388d53207265368a5c4363d0e3f5044ca65c8760`.
- Exact hash-pinned review media came from workflow run `37155139511`, artifact `11286060233`, batch `fortnite-review-first_review-7130481fcfc0f582`.
- Batch 0008 adds 25 submitted GPT-5.6 Sol first reviews with 100 explicit semantic annotations.
- Compact visual decisions are byte-locked at `fortnite-first-review-batch-0008-gpt56sol-decisions.json.gz`; canonical JSONL and summary are deterministically compiled through the existing submission builder.
- Observations remain limited to directly visible source/front and LEGO wide/front evidence; rear and hidden surfaces are not inferred.
- The batch remains non-canonical and training-ineligible pending a genuinely independent second review and explicit adjudication.
- Across batches 0001-0008, first-review coverage is now 200/744 high-priority pairs with 817 annotations; 544 high-priority pairs remain.

### Fortnite semantic first-review batch 0009

- Deterministic batch 0009 was materialized at commit `6011bec56aef75e8208eeed23670d3d7a1ad6df0`.
- Exact hash-pinned review media came from workflow run `37169949760`, artifact `11290956141`, batch `fortnite-review-first_review-9408e74046366c60`.
- Batch 0009 adds 25 submitted GPT-5.6 Sol first reviews with 100 explicit semantic annotations.
- Compact visual decisions are byte-locked at `fortnite-first-review-batch-0009-gpt56sol-decisions.json.gz`; canonical JSONL and summary are deterministically compiled through the existing submission builder.
- Observations remain limited to directly visible source/front and LEGO wide/front evidence. Rear and hidden surfaces are not inferred, and lower-body equivalence is not claimed where the LEGO render is upper-body framed.
- The batch remains non-canonical and training-ineligible pending a genuinely independent second review and explicit adjudication.
- Across batches 0001-0009, first-review coverage is now 225/744 high-priority pairs with 917 annotations; 519 high-priority pairs remain.
- The provisional critic-evidence corpus now contains 772 noncanonical transformation/loss items across 225 pairs; all remain canonical- and training-ineligible pending the same independence/adjudication gates.

### Independent second-review gate hardening — validated

- Adjudication queue semantics are now `fortnite-semantic-adjudication-queue/v2`.
- Two submitted reviews only count as an independent second-review pair when their declared reviewer IDs are distinct.
- An adjudicated record is blocked if it does not reference at least two independent submitted reviewers.
- Canonical supervision promotion now re-checks the same independence requirement instead of trusting the adjudication queue alone.
- Second-review work-batch selection now recognizes both `needs_second_review` and `needs_independent_second_review`, excludes pairs already reviewed by the assigned reviewer identity, and refuses unassigned second-review batches.
- First-review batch IDs/policy output remain byte-stable; reviewer identity only affects second-review batch IDs.
- Regression coverage was added for duplicate same-reviewer submissions and promotion attempts that try to reuse the same reviewer twice.
- Validated implementation checkpoint: `30dc8e5d01bce9a0b118e33e5290aa1b9aba628f`.
- The end-to-end `prepare_fortnite_semantic_second_review.py` helper now composes adjudication-state building and blind second-review selection while keeping prior semantic annotations out of the reviewer batch.
- LEGO Knowledge Tool Tests run `37142721848` passed the full suite at this checkpoint: **426 passed**.
- Build Fortnite Semantic Review UI run `37142712478` completed successfully after the workflow integration.
- Batch 0009 first review is complete; batch 0010 is the next first-review coverage target.


## Active blockers / constraints

1. **Fortnite semantic supervision adjudication** — batches 0001-0009 now provide 225 submitted first reviews (917 annotations total), but canonical supervision still requires independent second reviews and explicit adjudication. The remaining 519 high-priority pairs still lack submitted first-review coverage.
2. **Physical multi-view ground truth** — structured exact-release flat-art correspondence has improved, but exact rear/side physical photography remains limited; do not synthesize hidden views.
3. **Reference-fit torso segmentation** — lower-vs-upper torso segment length remains underidentified until additional landmarks are available.

## Highest-value next work

### P0
1. Continue Fortnite first-review coverage with batch 0010 next; obtain genuinely independent second reviews for existing submitted batches and adjudicate before any canonical promotion.
2. Expand exact-release multi-view ReferenceSets and cross-surface correspondence beyond structured flat-art, without inventing hidden views.

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

For completed custom architecture evaluation:
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-custom-acquisition-candidates-v1.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-custom-model-input-manifest-v1.json`
- `knowledge/libraries/lego-minifigure-customs/data/body-architecture-custom-sanitization-reviews-v1.json`

For exact-release cross-surface evidence:
- `knowledge/libraries/lego-minifigure-customs/data/exact-release-flat-art-reference-sets-v1.jsonl`
- `knowledge/libraries/lego-minifigure-customs/data/exact-release-flat-art-reference-sets-v1-summary.json`
- `tools/knowledge/build_exact_release_flat_art_reference_sets.py`

For Fortnite semantic supervision:
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-plan.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-semantic-review-progress.json`
- `tools/knowledge/build_fortnite_semantic_review_progress.py`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0001.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0001-gpt56sol-submitted.jsonl`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0001-gpt56sol-summary.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0002.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0002-gpt56sol-submitted.jsonl`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0002-gpt56sol-summary.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0003.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0003-gpt56sol-submitted.jsonl`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0003-gpt56sol-summary.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0004.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0004-gpt56sol-submitted.jsonl`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0004-gpt56sol-summary.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0005.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0005-gpt56sol-submitted.jsonl`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0005-gpt56sol-summary.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0006.json`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0006-gpt56sol-decisions.json.gz`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0006-gpt56sol-submitted.jsonl`
- `knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-first-review-batch-0006-gpt56sol-summary.json`
- `tools/knowledge/build_fortnite_semantic_review_submission.py`
- `.github/workflows/compile-fortnite-semantic-review-submissions.yml`
- `tools/knowledge/canonicalize_fortnite_semantic_review_ids.py`
- `tools/knowledge/build_fortnite_semantic_review_ui.py`
- `tools/knowledge/build_fortnite_semantic_adjudication_queue.py`
- `tools/knowledge/promote_fortnite_semantic_supervision.py`

Do not restart completed challenge-v4 raw review or original 27-case sanitization/SAM2 approval work. Preserve held-out/leakage-safe splits, provenance, exact-hash approvals, uncertainty, and the distinction between generated candidates and approved model inputs.

## Validation note

Fresh validation observed on the current checkpoint:
- LEGO Knowledge Tool Tests run `36890371822` completed successfully on commit `8157095062e87b36c5cd3b03ad50d57edbacbfaa`, validating all 25 batch-0002 submitted reviews and their canonical review IDs;
- LEGO Knowledge Tool Tests run `36878401937` completed successfully on commit `7a8fcf226eb53b0187cbff922692b554afcb26e9`, including the exact-release ReferenceSet compiler/tests;
- Fortnite batch-0001 review regression coverage passed in LEGO Knowledge Tool Tests run `36877400586` on commit `430eea29fbcf999c3c808d9138d590b0617fefe4`;
- LEGO Knowledge Tool Tests run `36807156707` completed successfully on commit `4c69a64cd21754ce6dbdd3f3adb252228d4958e7`;
- Body geometry tests run `36807156814` completed successfully on the same commit;
- SAM2 canonical generation run `36806483552` completed successfully and persisted the canonical 10-record metadata-only candidate manifest;
- run-13 canonical SAM2 pixel and PNG hashes exactly matched all 10 visually inspected run-12 derivatives.

## Validation update — 2026-10-03\n\n- LEGO Knowledge Tool Tests run `37142532406` completed successfully on commit `b28c9b892f3b2c2f0ca283c1613e6513a4d6346e`: 425 tests passed.\n- This validates the v2 reviewer-independence gate, promotion defense, identity-safe second-review selection, explicit reviewer assignment, blind second-review preparation helper, and preservation of deterministic first-review output.\n\n## Validation update — second-review workflow integration\n\n- LEGO Knowledge Tool Tests run `37142721848` completed successfully on commit `30dc8e5d01bce9a0b118e33e5290aa1b9aba628f`: 426 tests passed.\n- Build Fortnite Semantic Review UI run `37142712478` completed successfully on workflow commit `ec941f9be836b941880968176d4d5d6b4e8f061a`.\n- Manual second-review preparation is therefore wired end-to-end without weakening the independent-review or adjudication gates.\n\n## Continuation rule

A completed batch, commit, source family, or research phase is not an endpoint. Validate, persist, update state, choose the next task, and continue.

## Blocker rule

If a task is blocked:
- record exactly why;
- try a materially different source/method when reasonable;
- do not repeat identical failed actions indefinitely;
- switch to another useful independent workstream;
- return later only when new evidence or capability changes the situation.
