# Brickmen Research Priorities

This file defines durable research priorities for autonomous agents. The current exact continuation point belongs in `AUTONOMOUS_STATE.md`.

## P0 — Corpus and benchmark assets

### Official visual-reference corpus
Expand structured, provenance-aware coverage for official physical and useful official digital/game minifigure designs, especially:
- front/rear/side/3/4 exact-release views;
- head/hair/headgear;
- torso, arm, hip, leg, and back decoration;
- unusual materials and transparent/metallic parts;
- alternate expressions;
- disassembled component views;
- unusual body architectures.

Prefer linked multi-view records for one exact release over unrelated image accumulation.

### Source appearance -> minifigure translation pairs
Build structured pairs that capture:
- preserved identity features;
- omitted/simplified details;
- mold-vs-print choices;
- accessory choices;
- color abstraction;
- face/clothing/armor/footwear abstraction;
- front/back/side mapping;
- theme/era conventions.

### Populate benchmarks
Convert benchmark designs into real cases for:
- architecture recognition;
- unknown rejection;
- low-resolution/occluded inputs;
- detached components;
- source-to-minifigure translation;
- multi-view consistency;
- geometry-vs-decoration decisions;
- style/identity disentanglement.

Preserve hard held-out splits by character, maker, family, franchise, release code, or source-target pair where appropriate.

## P1 — Grammar, failure, and tool intelligence

### Official visual grammar
Extract evidence-backed patterns for:
- faces and expressions;
- clothing and armor abstraction;
- print density;
- symmetry;
- folds, belts, pockets, gloves, boots;
- headgear and facial-hair treatment;
- theme/year/style variation.

### Multi-view correspondence
Link exact matching examples across front/back/side/head/arms/legs/headgear/accessories.

### Negative/failure corpus
Store invalid outputs and explain why they fail:
- anatomy;
- topology;
- connector/joint hallucinations;
- wrong print zones;
- mold-vs-print errors;
- front/back inconsistency;
- style leakage;
- label leakage;
- perspective-distorted flat art.

### Model/data/tool registry
Track useful current models, datasets, papers, repos, licenses, revisions, VRAM, inputs/outputs, limitations, Brickmen use cases, and test status.

## P2 — Crosswalks and ontology stress tests

Improve LEGO/BrickLink/Rebrickable/LDraw/Studio/custom-catalog crosswalks for minifigure-relevant parts and assemblies.

Actively search for examples that do not fit existing FigureArchitecture categories. Prefer ontology-breaking evidence over more examples of already saturated classes.

## Evidence rule

More data is not automatically better. Prefer new information that increases diversity, closes a known gap, strengthens provenance, enables a benchmark, or tests an important assumption.
