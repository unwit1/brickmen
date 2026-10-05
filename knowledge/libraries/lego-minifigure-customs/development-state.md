# Development state — 2026-10-05

## Implemented in this continuation

- Reusable minifigure/standalone-part brief scaffolding and deterministic prompt/preflight compilation using the existing provider packet and output contracts. Incomplete source/geometry/view/feature declarations and explicit conflicts block prompt creation. Local attachment hashes are checked; metadata-only references remain warnings.
- Reference selection v2: preserve zero confidence, reject invalid values/missing identifiers, distinguish side/unknown/rear evidence, retain source occurrences, collapse byte-identical alternates, expose missing roles and explicit conflicts, and support standalone part coverage.
- Training splits v2: join identity groups and confirmed duplicate relationships transitively; fail missing grouping identities by default and flag explicit fallback. Existing v1 assignments need regeneration.
- LDView manifest compatibility: sample IDs now feed the reference builder; source-file hashes are checked; derived asset IDs/filenames include renderer settings and the declared dependency-library revision. Failure reports return a failing exit code.
- Restored the missing source-tree inventory utility invoked by bulk-ingestion automation. It is copied from the original Agent OS tool; provenance is recorded in the migration log. No source-side deletion was performed.
- Consolidated 20 identical-requirement manufacturing descriptors into a single backlog with legacy pointers. Corrected misleading `schema_ready` labels to `specification_pending`; no empirical calibration or real field specification was lost.
- Added offline repository integrity validation, regression tests, CI and generated-file ignores. Updated automation checkout/user-agent naming to Brickmen.
- Registered Brickmen in Agent OS with development metadata only, restoring context routing. Raw reference corpora were not migrated into Agent OS.

## Critical assessment

The migrated corpus is documentation-rich and runtime-light. Research coverage and acquisition counts should not be interpreted as model capability, unique visual-design coverage, calibrated geometry or manufacturing readiness. Many records describe desired fields or pending measurements; they are not formal executable schemas. Historical snapshots remain historical evidence.

Provider/model recommendations and license statements in research notes are dated claims and were not reverified in this code-focused continuation. Verify primary sources and model revisions when selecting an actual runtime; no production model was selected here.

The new preflight establishes traceable declarations, not semantic truth. It cannot verify a catalog crosswalk, whether an image shows the claimed view, or whether a reference supports a feature. Actual visual generation and real LDView execution have not been benchmarked in this continuation. Synthetic renderer tests verify manifest plumbing only.

## Next implementation priorities

1. **Geometry and template authority:** establish one small, versioned canonical assembly/part fixture with resolved dependency hashes, exact transforms, cameras, part/material masks and calibrated print-surface IDs. Add a broader arbitrary-part index without creating a second source inventory stack.
2. **Observable evaluation:** implement geometry/landmark/safe-area checks against that fixture and reviewed feature annotations. Freeze a small, rights/provenance-backed benchmark spanning asymmetry, back/side graphics, short legs, alternate head expressions, masks, headgear, accessories and non-minifigure parts. Record denominators and failures, not just a best example.
3. **Evidence adapters:** crosswalk source manifests into the shared DerivedAsset fields and canonical part/color identities; keep originals. Resolve source appearance/style applicability before accepting scored evidence. Turn reviewed near-duplicate candidates into explicit clusters before splits.
4. **Manufacturing specifications:** promote backlog descriptors one at a time into typed field/units/revision specifications with valid/invalid examples and executable validators. Link physical measurement and print/fit proof; never fill missing dimensions or tolerances from a model guess.
5. **Controlled generation:** connect one evaluated runtime to the existing packet, keeping run provenance and region-edit revisions. Compare hosted/local results under the same brief and benchmark. Add multi-view/template projection only after the first fixture and scorer are reliable.

These priorities cover identity, geometry, decoration, materials, evidence, multiview consistency and physical feasibility. The broader research backlog remains the topic inventory; this list sequences executable work.

## Validation and continuation

Run `python tools/validate_repo.py` and `python -m pytest tests -q`. CI uses Python 3.12. Local validation in this continuation uses Python 3.14; full runtime/model dependencies are not installed by the integrity check.

Next prompt: “Continue Brickmen from development-state.md. Implement a versioned canonical geometry/template fixture and observable geometry checks using the existing generation packet and output contracts. Check Agent OS context/inbox/claims, preserve provenance and unresolved physical measurements, and validate the actual fixture before connecting a model.”

Recommended capability: ordinary coding and deterministic tests; use medium reasoning for the CAD/template interface. Additional agents or model training are unnecessary until a measured bottleneck justifies them.
