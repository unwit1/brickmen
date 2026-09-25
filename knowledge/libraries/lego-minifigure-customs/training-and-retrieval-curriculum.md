# Training and Retrieval Curriculum for Official-Style Minifigure Translation

Research snapshot: 2026-09-24

## Principle

Do not begin with one giant fine-tune over every image.

The corpus contains fundamentally different supervision:
- official physical style;
- official digital/game extensions;
- film animation states;
- source-character references;
- flat decoration/component images;
- 3D mould geometry;
- customs admitted later as style extensions.

A staged curriculum preserves what each source is good at.

## Phase 0 — retrieval-only baseline

Before training anything generative, build a strong retrieval system.

For every new request retrieve:
1. exact source appearance;
2. official physical versions of the same character/version;
3. same-character official variants;
4. visual analogues via DINOv3;
5. semantic analogues via SigLIP2;
6. same era/theme/style-profile samples;
7. accepted custom extensions only if official precedent is sparse.

Why:
- establishes a measurable baseline;
- catches metadata problems before expensive training;
- prevents a fine-tune from becoming the only memory mechanism;
- allows new official releases to become useful immediately without retraining.

## Phase 1 — discriminative officialness models

Train small/cheap models first.

Tasks:
- physical vs digital vs custom;
- official vs custom/unofficial;
- style era/profile;
- theme/subtheme;
- component type;
- front/back/side view;
- mask/headgear class;
- expression family;
- detail-density band;
- likely print vs mould identity carrier.

Purpose:
make the corpus self-cleaning and provide objective evaluation signals for generation.

Do not use this classifier as the sole judge of quality; maintain human-reviewed benchmarks.

## Phase 2 — source-to-LEGO decision model

Train on TranslationPair records.

Input:
- source-reference features/image embedding;
- target style profile;
- theme/era;
- known official part vocabulary.

Targets:
- preserved feature list;
- simplified feature list;
- omitted feature list;
- moved-to-mould decisions;
- moved-to-accessory decisions;
- mask translation route;
- approximate color-role mapping;
- surface allocation.

This is more valuable than asking an image model to infer all design decisions implicitly.

A structured decision model can be:
- rules + retrieval initially;
- gradient-boosted/tree or small neural model after enough reviewed pairs;
- multimodal LLM/VLM planner later.

## Phase 3 — flat template generation

Prioritize **flat component artwork** over beauty renders.

Condition on:
- calibrated target surface template;
- base plastic color;
- source reference;
- selected official analogues;
- style profile;
- component mask;
- identity-critical feature list.

Targets:
- head print;
- torso front/back;
- arms;
- hips/legs;
- helmet/headgear decoration.

Generation should remain constrained by the template boundary.

### Structural conditioning

Current Diffusers supports ControlNet-style structural conditioning and IP-Adapter image guidance for several modern diffusion families. IP-Adapter decouples image-reference features from text conditioning; ControlNet can condition on edges/depth/layout. These mechanisms make them useful research candidates for keeping minifigure geometry fixed while giving the model source-character imagery.

Sources:
https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter
https://huggingface.co/docs/diffusers/main/en/using-diffusers/controlnet

Model-specific licensing and commercial-use terms must be reviewed before choosing a production base model.

### Recommended conditioning channels

- exact surface mask/template;
- edge/silhouette condition;
- optional official-part UV/depth/normal render;
- source image via image adapter;
- official analog image(s) via separate adapter/retrieval embedding;
- text/structured prompt with exact appearance identity.

The model should not be allowed to move the template geometry.

## Phase 4 — new 3D part generation

Use only when the translation planner concludes print/existing parts cannot carry the identity.

Training/retrieval supervision:
- official existing hair/helmet/mask/headgear geometry;
- source silhouette;
- minifigure attachment envelope;
- collision/clearance constraints;
- official shape-complexity examples.

The first generated output should be a constrained concept mesh, not assumed printable geometry.

Validate:
- neck/head interfaces;
- stud/bar/clip compatibility;
- wall thickness;
- manufacturing method;
- minifigure face visibility;
- print/decal surfaces;
- silhouette from canonical views.

## Phase 5 — joint generation

Only after flat-art and part-generation benchmarks are strong, allow a planner to jointly select:
- official existing parts;
- custom/new part;
- head print;
- helmet print;
- accessory;
- cloth/bodywear;
- color assignment.

The result should remain decomposable into manufacturing assets.

## Fine-tuning strategy

Start with adapters/LoRA rather than a full base-model retrain where supported.

Reasons:
- faster experiments;
- versionable style modules;
- easier rollback;
- separate modules for physical official style versus optional custom extensions;
- less risk of catastrophically overwriting general image understanding.

Keep official-style adaptation separate from:
- character/franchise identity adaptation;
- production-process-specific adaptation;
- customizer style extensions.

## Reference image adapters

For source fidelity, image guidance should represent **what to preserve**.

For LEGO-style reference, retrieved official analogues represent **how to abstract**.

Do not use the same uncontrolled image-conditioning channel for both roles if the model/framework supports separated adapters/weights.

Conceptually:
- source adapter weight -> identity;
- official-style adapter/retrieval -> abstraction;
- template/ControlNet -> geometry.

## Data weighting

Default style authority:
- official isolated physical figure/component: highest;
- LEGO-hosted physical render/photo: highest;
- validated structured patterned part: high but secondary authority;
- exact physical figure in official game: medium-high;
- digital-only official game: medium;
- official film frame: lower for print style, high for expression/identity;
- approved custom extension: lowest style authority and only for known gaps.

Do not let sample count override authority.

## Leakage-safe training splits

Never random-split images.

Group by:
1. OutfitDesign for normal evaluation;
2. Character for hard identity generalization;
3. Theme for hard style transfer;
4. mask/headgear family for part-route testing.

All images, crops and duplicate source occurrences of one group stay in the same split.

## Evaluation suite

### Official reconstruction
Given an official source sample, can the system recreate its flat design decisions from another view/source?

### Unseen appearance translation
Given a character appearance with no official minifigure, can it produce a design that human reviewers find:
- source-faithful;
- official-looking;
- physically plausible?

### Simplification benchmark
Give the system increasingly complex costumes. Measure whether it preserves identity while reducing low-value detail.

### Mask routing benchmark
Evaluate:
- head print;
- existing headgear + print;
- new 3D part;
- hybrid.

### Real-size readability
Downsample/print at target scale and score identity retention.

### Negative custom benchmark
Include deliberately over-detailed or anatomically realistic customs to ensure "more detail" is not rewarded automatically.

## Human review

Build a blinded pairwise interface:
- generated A vs B;
- which looks more official?
- which better matches the exact source?
- which would you believe was an official LEGO release?
- what is the first visible failure?

Pairwise judgments are easier to calibrate than arbitrary 1–100 scores.

Use review results to recalibrate automated metrics.

## Model-version inheritance

Every training run records:
- corpus snapshot ID;
- train/eval grouping;
- base model;
- base model revision;
- adapter/training code revision;
- hyperparameters;
- random seed;
- checkpoint hashes;
- benchmark scores;
- regression failures.

No model is promoted because screenshots "look good."

## Continuous update

New official release:
- ingest metadata/images;
- deduplicate;
- derive features/embeddings;
- resolve character/appearance;
- run benchmark impact;
- make it immediately available to retrieval;
- schedule retraining only when enough new data or a meaningful style shift exists.

Retrieval should update far more frequently than model weights.
