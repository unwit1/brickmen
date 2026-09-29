# Brickmen Autonomous State

Last updated: 2026-09-28
Base commit before autonomous bootstrap: `bda2cac8ea8b68bb9e3e5b4d0cf380a9c6ee3ae6`
Status: active

## Current major objective

Turn Brickmen into a self-contained, evidence-backed system for custom-minifigure research, character-to-minifigure translation, visual-style understanding, model training/evaluation, 2D/3D generation, geometry validation, manufacturing, and continuous self-improvement.

## Current research frontier

The repository already contains substantial architecture, body-generation, reference-fitting, provider, manufacturing, and ingestion work.

The highest-value frontier is now corpus and evaluation completion rather than more general architecture prose.

Primary needs:
1. expand structured official visual-reference coverage;
2. build large source-appearance -> minifigure translation-pair corpora;
3. populate real benchmark cases rather than only benchmark schemas;
4. expand multi-view/cross-surface correspondence;
5. extract official visual grammar from evidence;
6. build negative/failure corpora;
7. keep current model/tool/dataset registries;
8. close specific reference-fitting evidence gaps;
9. search for ontology-breaking body architectures;
10. preserve provenance, uncertainty, and contradiction state.

## Important known technical gap

Current reference-fitting work can identify several useful parameters, but lower- versus upper-torso segment length remains underidentified until additional chest/torso-center landmarks are added. Treat this as a concrete evidence-acquisition target rather than a reason to stop unrelated work.

## Recommended next work

A fresh autonomous agent should:

1. inspect recent commits and this state;
2. audit current coverage for visual references, translation pairs, multi-view links, benchmarks, negative examples, model/tool registries, and unresolved fitting evidence;
3. select the highest expected-value executable gap;
4. begin closing it immediately;
5. commit useful work incrementally;
6. update this state and `data/autonomous-state.json`;
7. continue automatically into the next task.

## Highest-value queued work

### P0
- Official visual-reference corpus expansion.
- SourceAppearance -> minifigure translation pairs.
- Populate benchmark datasets with real cases.
- Multi-view exact-release correspondence.

### P1
- Official face/clothing/decoration grammar extraction.
- Negative/failure corpus.
- Current model/dataset/tool census.
- Cross-catalog minifigure-part/geometry crosswalks.

### P2
- Ontology-breaker searches for unsupported body systems.
- Specific manufacturing/process evidence gaps.
- Physical-evidence acquisition planning where software/research alone cannot resolve uncertainty.

## Continuation rule

Do not restart the project from first principles.

Resume the highest-value unfinished work from the repository. A completed batch, commit, source family, or research phase is not an endpoint. Validate, persist, update state, choose the next task, and continue.

## Blocker rule

If a task is blocked:
- record exactly why;
- try a materially different source/method when reasonable;
- do not repeat identical failed actions indefinitely;
- switch to another useful independent workstream;
- return later only when new evidence or capability changes the situation.

## Handoff requirement

Before a session ends or is likely to lose context, update this file with:
- completed work;
- current frontier;
- blockers;
- pending validation;
- highest-value next tasks;
- exact continuation point.

Keep this concise. Detailed evidence belongs in the canonical datasets and research files, not in this checkpoint.
