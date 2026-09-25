# ChatGPT Image Generation Control-Group Protocol

Research snapshot: 2026-09-24

## Purpose

Use ChatGPT image generation as a repeatable **control arm** for the thesis/reference-fidelity experiments.

The control is not "whatever wording happened to be typed into chat." Every ChatGPT generation in this research project should first be normalized into the same structured generation schema used by the broader minifigure/reference-fidelity pipeline.

This makes ChatGPT useful as:
- a hosted-provider comparison point;
- a prompt-engineering control group;
- a way to measure whether better structure improves generation quality;
- a benchmark against local/open-weight pipelines;
- a source of failure cases that can be categorized and compared.

## Core rule

For project-related image generation, do not send an improvised one-line request to the image model.

First compile the request into a **Control Generation Packet** containing:

1. exact source/reference identity;
2. reference-image roles;
3. identity-critical features;
4. target transformation;
5. fixed geometry/structure;
6. allowed changes;
7. forbidden changes;
8. style target;
9. minifigure-specific abstraction rules;
10. mask/headgear translation decision;
11. camera/view;
12. lighting/background;
13. output type;
14. production constraints;
15. evaluation criteria.

The final image request should faithfully express that packet.

## ChatGPT-specific limitation

The exact internal image-generation model revision, seed and sampling parameters may not be exposed.

Therefore record:
- provider = ChatGPT;
- interface = image generation in chat;
- date/time;
- ChatGPT text model used to compile the request when known;
- prompt-schema version;
- reference-image identifiers;
- full normalized Control Generation Packet;
- generation iteration number;
- output asset identifier/hash when available;
- visible result scores.

Do not fabricate unavailable seed/model internals.

## Control Generation Packet

### Research identity

- experiment_id
- run_id
- schema_version
- provider
- provider_surface
- generated_at

### Reference package

For every reference:
- reference_id
- semantic_role:
  - identity_primary
  - identity_secondary
  - costume_front
  - costume_back
  - side_reference
  - face_closeup
  - mask_headgear
  - color_material
  - official_style_analogue
  - geometry_template
  - production_template
- provenance_id if available
- priority
- notes

References are not interchangeable. A side-view costume image should not compete with a face close-up for identity authority.

### Exact target identity

- character / subject
- incarnation/version
- source appearance
- exact outfit
- expression
- mask/headgear state
- accessories
- details that distinguish this version from similar versions

### Identity-critical feature list

Rank features:

P0 — must be exact
Failure makes the output the wrong subject/version.

P1 — strongly important
Meaningful fidelity loss if wrong.

P2 — useful supporting detail
May be simplified if required by the target style.

For minifigures, common P0 examples:
- hair/headgear silhouette
- mask geometry
- dominant costume colors
- primary emblem
- face-defining feature
- signature accessory
- version-specific armor/clothing shape

### Transformation target

State exactly what changes:
- convert to official-style minifigure
- change pose
- change view
- convert rendering style
- produce flat decal/template art
- create new helmet/mask part
- preserve character but alter background
- other

Everything not explicitly designated changeable is presumed stable when technically possible.

### Structural locks

Specify:
- target body geometry
- part/mould choices
- minifigure proportions
- head cylinder
- torso trapezoid
- limb positions
- mask/headgear silhouette
- camera view
- template boundaries

For minifigure work, structure comes from the official minifigure geometry/template, not from the source character's human anatomy.

### Official LEGO style profile

Include:
- official style profile
- era
- theme/subtheme
- closest official analogues
- acceptable detail density
- facial grammar target
- line hierarchy
- base-plastic/negative-space strategy
- mould-vs-print decisions

### Mask/headgear route

Explicit:
- head_print
- existing_headgear_plus_print
- new_3d_part_plus_print
- hybrid

Also specify why.

This prevents the image model from arbitrarily flattening a sculptural mask or inventing unnecessary geometry for a printed mask.

### Allowed changes

Examples:
- simplify micro-seams;
- convert realistic folds to graphic lines;
- map colors to official LEGO palette;
- change proportions to minifigure geometry;
- replace source hair shape with closest LEGO mould.

### Forbidden changes

Examples:
- do not change costume version;
- do not invent symbols;
- do not remove signature mask details;
- do not alter primary color blocking;
- do not replace the character with a generic analogue;
- do not humanize minifigure hands/limbs;
- do not add realistic fabric texture;
- do not add arbitrary gradients;
- do not add extra armor panels because empty space exists.

### View/render target

- orthographic / near-orthographic
- front/back/side/3/4
- full figure or component crop
- neutral catalog lighting or production-flat art
- background
- transparent-background preference where relevant

### Output target

One of:
- concept_render
- catalog_render
- flat_head_art
- torso_front
- torso_back
- arm_art
- leg_art
- helmet_art
- full_decal_sheet
- new_part_concept
- multi_view_sheet

### Evaluation target

Score separately:
- source/reference fidelity
- official LEGO likeness
- production feasibility
- edit locality when applicable
- critical-feature accuracy

Do not use "looks good" as the sole result.

## Prompt compilation order

The ChatGPT control prompt should be generated in this order:

1. transformation objective;
2. exact subject/version;
3. preservation directive;
4. P0/P1 visual features;
5. target geometry;
6. official-style rules;
7. mask/headgear decision;
8. permitted simplifications;
9. forbidden drift;
10. camera/render/output requirements.

This makes preservation priorities visible before decorative/style instructions.

## Prompt principle

Prefer:

"Preserve the exact identity and version-specific visual features of the supplied reference, then translate them through [target official style profile]."

over:

"Make a LEGO version of this."

The latter leaves too many decisions unspecified.

## Iterative prompt optimization

ChatGPT generations should support a controlled revision loop.

### Generation 0 — schema baseline
Use the current normalized schema without ad-hoc extra tricks.

### Review
Record:
- P0 failures
- P1 failures
- structural failures
- invented details
- style failures
- mask/headgear failures
- color failures
- expression failures
- production/template failures

### Generation N+1
Change the smallest possible instruction set that directly addresses observed failures.

Do not rewrite the whole prompt unless the schema itself failed.

This supports causal prompt research.

## Prompt versioning

Every meaningful schema/prompt revision gets:
- prompt_schema_version
- compiler_version
- change summary
- hypothesis
- expected improvement

Example:

v0.4 -> v0.5
change: move P0 preservation constraints before style instructions
hypothesis: fewer costume/version substitutions

This allows generation quality to be plotted against prompt-schema evolution.

## Control-group experimental design

When comparing ChatGPT to another model:

Keep constant:
- same reference files;
- same semantic reference roles;
- same source feature sheet;
- same target geometry;
- same requested output;
- same P0/P1 priorities;
- same evaluation rubric.

Translate only the **syntax** necessary for each model.

Do not give one model five well-labeled references and another one unlabeled image and call it a model comparison.

## Repetition

Because the hosted image generator may not expose deterministic seeds:
- generate multiple samples for important benchmark conditions;
- record iteration count;
- evaluate variance;
- compare median and failure rate, not only best-of-N.

Do not cherry-pick the single strongest output.

## ChatGPT as control, not ground truth

ChatGPT image generation is a benchmark arm.

Official LEGO corpus evidence remains the style ground truth.
The source reference remains identity ground truth.
Human-reviewed template/production constraints remain manufacturability ground truth.

## Future automatic logging

Agent OS should eventually intercept each project image-generation request and write:

generation_runs/<run_id>.json

containing:
- normalized Control Generation Packet;
- prompt-schema version;
- references;
- provider;
- output asset IDs/hashes;
- evaluation scores;
- failure labels;
- follow-up revision.

This allows ChatGPT prompts and local pipelines to be evaluated in the same experiment database.
