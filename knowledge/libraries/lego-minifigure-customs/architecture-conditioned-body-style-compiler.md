# Architecture-Conditioned Body Style Compiler

Research snapshot: 2026-09-27

## Purpose

Convert an architecture-neutral character/body description into an architecture-specific, generation-ready design.

Input:

```
CharacterBodyFeatureSpec
+ exact SourceAppearance
+ FigureArchitecture
+ BodyStyleProfile
+ ArchitectureSurfaceSchema
+ validated component/joint library
+ manufacturing profile
```

Output:

```
CharacterBodyDesignSpec
```

This is the layer that lets Brickmen **recognize what a body system is and intelligently apply its visual language** instead of merely scaling geometry.

## Core principle

The character says **what must be communicated**.

The architecture says **what shapes and interfaces exist**.

The style profile says **how that architecture tends to communicate information**.

Manufacturing says **what can survive physically**.

The compiler decides **where each feature goes**.

# Compilation stages

## C0 — architecture resolution

Resolve:
- exact architecture revision;
- BodyStyleProfile;
- mechanical skeleton;
- component graph;
- surface schema;
- accessory anchors;
- validated joint/connector revisions.

If architecture is unknown:
- concept-only output allowed;
- manufacturing output blocked.

## C1 — semantic feature inventory

Read CharacterBodyFeatureSpec.

Example Thing:
- large total mass;
- rock plates;
- heavy brow;
- large hands;
- orange surface;
- trousers.

Example Beast:
- athletic/hunched mass;
- fur;
- long-looking arms;
- claws/hands;
- hair/head silhouette.

No geometry is chosen yet.

## C2 — identity priority

Every feature receives:
- identity importance;
- source certainty;
- view relevance;
- architecture feasibility;
- manufacturing risk.

Classes:
- must_preserve;
- strongly_prefer;
- optional;
- omit_if_needed.

When constraints conflict, preserve high-identity features before generic texture.

## C3 — existing component retrieval

Before generating anything, search:

1. exact architecture reusable component;
2. same architecture + similar semantic role;
3. compatible cross-architecture donor;
4. parameterizable Brickmen component;
5. new generated shell required.

Example:
if the target architecture already has a validated large C-grip hand, do not generate a new hand for every muscular character.

This is crucial for mechanical reuse.

## C4 — representation assignment

Assign every source/body feature to one representation:

- `existing_component`
- `silhouette_geometry`
- `major_relief`
- `shallow_relief`
- `printed_decoration`
- `color_material_only`
- `soft_goods`
- `separate_accessory`
- `omit`

This assignment is architecture-conditioned.

### Example: pectoral muscles

Standard minifigure:
`printed_decoration`

LEGO Giant:
`major_relief / existing torso mold`

Brickmen anatomical MidFig:
`major_relief`

### Example: tiny rock cracks

Standard minifigure:
`printed_decoration`

Giant:
`printed_decoration + sparse shallow_relief`

Fine resin display body:
`shallow_relief` only if minimum-feature and cleaning rules permit.

## C5 — body parameter compilation

Map semantic mass/stature to architecture parameters.

Example generic semantic:
```
shoulder_mass = very_large
waist_mass = large
hand_emphasis = very_large
```

Brickmen MidFig may compile to:
```
shoulder_width = profile.p95
chest_width = profile.p95
waist_width = profile.p75
hand_scale = profile.p90
torso_taper = high
```

A standard minifigure architecture cannot change those dimensions substantially, so it redirects mass communication into decoration and accessory choice.

## C6 — surface-material compilation

Surface semantics are separate from body architecture.

Supported semantic classes should include:
- skin;
- rock;
- fur;
- metal;
- scales;
- bark/wood;
- cloth;
- bone;
- slime/organic;
- energy/translucent;
- armor plating.

Each material has:
- relief strategy;
- print strategy;
- minimum feature;
- preferred region scale;
- gloss/finish;
- color role;
- joint-contact exclusions.

Example `rock`:
- major plates may become shallow relief;
- fine cracks usually become print/texture;
- no deep crack across a shoulder socket;
- relief fades near assembly seam.

Example `fur`:
- silhouette tufts carry more information than dense micro-hair;
- surface grooves are depth-limited;
- high-wear areas remain smooth enough to handle.

## C7 — anatomy/relief budget

Every architecture/style has a finite **geometry complexity budget**.

Store:
- silhouette complexity budget;
- major relief density;
- shallow relief density;
- printable line/detail density;
- minimum clear region.

This prevents a detailed real reference from turning into noisy miniature geometry.

The compiler spends complexity on the highest-identity features first.

## C8 — component split plan

Given final semantic geometry:
- choose manufacturing components;
- reuse architecture-defined splits;
- optionally place character-specific splits inside allowed ComponentSplitZones.

Example:
armor gauntlet can hide a wrist seam.

Split optimization considers:
- style;
- printing;
- assembly;
- color separation;
- repair;
- surface decoration.

## C9 — accessory scaling

Accessory dimensions depend on:
- architecture hand/grip family;
- body height;
- visual style;
- source relationship.

Store separately:
- mechanical grip dimensions — deterministic connector profile;
- visual weapon scale — BodyStyleProfile;
- source-specific exaggeration — CharacterBodyFeatureSpec.

Example:
one sword design can have:
- standard-minifigure shell;
- Giant shell;
- MidFig shell;

while each uses the correct grip connector.

## C10 — reference retrieval

Retrieve references in separate roles:

### identity references
Exact source appearance.

### architecture references
Blank/canonical body and joints.

### style analogues
Same architecture, similar morphology/material.

### same-character cross-architecture pairs
Useful for preserving identity while changing body language.

Never let a visually similar custom overwrite exact source identity.

## C11 — generation plan

Output a per-component generation method.

Example:
```json
{
  "torso": {
    "method": "part_aware_mesh_generation",
    "locked_interfaces": ["left_shoulder","right_shoulder","neck","waist"]
  },
  "hands": {
    "method": "reuse_validated_component",
    "component_id": "brickmen_midfig_large_hand_v2"
  },
  "belt": {
    "method": "printed_decoration"
  }
}
```

Router chooses:
- existing component;
- parametric CAD;
- neural shell generation;
- sculpt modifier;
- print artwork.

## C12 — deterministic compile

Generated shells are:
- aligned to skeleton;
- trimmed at component split zones;
- joint keep-outs subtracted;
- JointCartridges inserted;
- minimum wall/feature enforced.

The result is now an architecture-valid candidate.

## C13 — architecture style critic

Evaluate independently:

1. source identity;
2. architecture geometry;
3. BodyStyleProfile;
4. surface-material treatment;
5. manufacturing;
6. articulation.

Do not collapse into one score.

A visually beautiful output with the wrong body language should fail style even if source fidelity is high.

# Rule format

A reusable StyleMappingRule:

```json
{
  "rule_id": "muscle_pectoral_standard_minifig",
  "when": {
    "feature_semantic": "pectorals",
    "architecture": "minifig_standard"
  },
  "representation": "printed_decoration",
  "reason": "architecture shell is canonical/fixed",
  "confidence": "validated_style_rule"
}
```

Another:

```json
{
  "rule_id": "muscle_pectoral_midfig_anatomical",
  "when": {
    "feature_semantic": "pectorals",
    "architecture": "brickmen_midfig_v0",
    "style_profile": "anatomical_custom_midfig"
  },
  "representation": "major_relief",
  "parameter_mapping": {
    "mass": "chest_depth",
    "width": "chest_width"
  }
}
```

# Learning mapping rules

Three evidence sources:

## Official architecture corpus
Strongest style authority for official-like profiles.

## Same-character cross-architecture pairs
Teach feature migration:
- print -> relief;
- standard hand -> large hand;
- fixed torso -> expanded shell.

## Same-architecture different-character corpus
Teach what is architecture/style versus character-specific.

For example:
within one Giant architecture:
- Hulk;
- Thanos;
- Darkseid;
- Gorilla Grodd.

Shared geometry tendencies reveal architecture grammar.

# Statistical profile instead of one template

BodyStyleProfile should contain distributions:
- head/body ratio;
- shoulder/body ratio;
- hand/head ratio;
- torso taper;
- relief density;
- surface feature scale.

Generation then selects within the validated distribution based on the character semantics.

This avoids producing the exact same muscular shell for Hulk, Colossus and Beast.

# Style-distance model

For candidate geometry derive normalized features:

- silhouette landmarks;
- proportion vector;
- curvature/relief histogram;
- surface-detail scale;
- component-size ratios;
- accessory ratio;
- head ratio.

Compare against:
- target BodyStyleProfile distribution;
- closest architecture examples.

Output:
`architecture_style_distance`.

Use it as one critic signal, not an absolute aesthetic score.

# Controlled creativity

The compiler should expose:

- source_fidelity_strict;
- official_abstraction;
- maker_style_research;
- Brickmen_original;
- experimental.

These control:
- how much geometry may deviate;
- whether custom style profiles are allowed;
- how strongly analogues influence design.

Mechanical interfaces remain locked in every mode.

# Example — Thing

Input:
```
morphology = rocky_massive_humanoid
shoulders = large
hands = large
surface = rock
```

### Standard minifigure
Output:
- canonical torso/arms/legs;
- rock pattern through print;
- character head/face;
- standard hands.

### Brickmen MidFig
Output:
- wider torso/arms;
- large-hand module;
- medium plate-scale relief;
- fine cracks mostly print;
- standard head or architecture-scaled head per design mode.

### Giant-compatible
Output:
- Giant mass envelope;
- large hand;
- large rock planes in shell;
- print/paint fine crack network;
- commodity shoulder joint retained.

One semantic source becomes three coherent designs.

# Example — Colossus

Input:
```
morphology = muscular_humanoid
surface = metal_skin
stature = tall
hands = moderately_large
```

Compiler should not apply Hulk's extreme forearm/hand proportions merely because both use the same muscle-body architecture.

It adjusts architecture parameters from CharacterBodyFeatureSpec.

# API

```
body_features.extract(source_appearance)
body_style.retrieve(architecture_id, mode)
body_style.compile(feature_spec, architecture, style_profile)
body_style.map_feature(feature, architecture, style_profile)
body_style.select_component(feature, architecture)
body_style.plan_surface(material_semantic, region)
body_style.plan_components(design)
body_style.score(candidate, profile)
body_style.learn_rule(transfer_pairs)
```

# Validation

A BodyStyleProfile or StyleMappingRule progresses:

```
observed
 -> candidate
 -> corpus_supported
 -> human_validated
 -> generation_validated
 -> physical_validated
```

Aesthetic rules do not require the same physical validation as joints, but manufacturing-relevant depth/thickness rules do.

# End state

The user's prompt:

> "Make Beast as an Alpha-like muscular custom, but use Brickmen-printable joints."

should compile conceptually as:

```
Beast SourceAppearance
 -> CharacterBodyFeatureSpec
 -> selected research BodyStyleProfile inspired by observed Alpha proportions
 -> Brickmen independent MidFig/Giant-compatible FigureArchitecture
 -> map fur/muscle/silhouette semantics
 -> reuse validated hands/joints
 -> generate character shell
 -> apply deterministic interfaces
 -> critic loop
 -> printable parts
```

This lets Brickmen learn from the visual language of existing custom figures without making their proprietary body mechanics or exact sculpt the canonical manufacturing geometry.


# BodyGenerationConditioning handoff

The fitted skeleton, visual envelope and mechanical-interface layers now compile into a provider-neutral intermediate artifact before learned 3D generation:

```
CharacterBodyDesignSpec
 + selected Brickmen skeleton
 + optional skeleton/reference fit
 + optional BodyEnvelopeProfile fit
 + JointProfile / JointCartridge evidence
 -> BodyGenerationConditioning
 -> part-aware image/mesh generation
 -> deterministic interface compile
```

Implementation:
- `data/body-generation-conditioning.schema.json`
- `tools/geometry/compile_body_generation_conditioning.py`
- `tests/test_body_generation_conditioning.py`

## Why this intermediate representation exists

A generation model should receive enough structure to create the correct shell without being allowed to reinterpret mechanical evidence.

The payload therefore carries four parallel control channels:

### Skeleton landmarks
Normalized and target-height coordinates for:
- root/pelvis/waist/chest/neck/head;
- shoulders;
- arm/hand landmarks;
- hips/knees/ankles;
- architecture bones and joint semantics.

These guide alignment/proportions.

They are **not** printable connector geometry.

### Visual envelopes
Independent box/capsule-style targets for visual mass:
- torso width/depth;
- abdomen width/depth;
- head width/depth/height;
- later shoulder/arm/hand/lower-body envelopes.

These may change without moving joint centers.

### Component plan
Carries:
- editable shell regions;
- locked architecture regions;
- default lower-body mode;
- later component split zones and expected generated component graph.

### Mechanical constraints
Each JointProfile/JointCartridge arrives with an explicit authority class.

Current classes:
- `reference_only_not_manufacturing_authority`;
- `validated_prototype_not_production`;
- `production_approved_deterministic_interface`.

A CAD reference or validation-pending profile can contribute:
- hardware identity;
- orientation;
- alignment;
- reference keep-out;
- validation requirements.

It cannot contribute an implied printable socket tolerance.

## Scale rule

Reference scale and target design scale are separate.

For example, the official pinned Giant/Hulk reference is about 71.1 mm tall. Brickmen Giant's current design target is 62 mm.

The reference may fit normalized proportions while generation remains targeted at 62 mm.

Commodity hardware such as 43093 is even stricter:
- its physical dimensions remain fixed;
- a normalized keep-out copy may be supplied to a generator for spatial conditioning;
- the hardware itself never scales with body height.

## Current Giant example

The current official Giant conditioning path can combine:

- official shoulder-center shape evidence from `lego-giant-ldraw-shoulders-fit.json`;
- official body width/depth evidence from `lego-giant-10128-ldraw-body-profile.json`;
- Brickmen Giant skeleton;
- `lego_giant_43093_shoulder_reference_v0`.

The resulting visual torso envelope can match the official reference distribution while the shoulder hardware profile remains explicitly reference-only until physical force/torque/cycle validation.

## Generator responsibilities

A learned image/3D system may:
- satisfy normalized body proportions;
- fill visual envelopes;
- propose shell surfaces;
- propose relief/material language;
- propose component-local shape inside editable regions.

It may not:
- resize commodity hardware;
- invent fit tolerances;
- erase keep-outs;
- convert a reference-only profile into a production joint;
- change architecture component count without an explicit architecture/compiler decision;
- move a locked interface because a source silhouette is wider.

## Deterministic post-processing

After shell generation:

```
generated visual shell
 -> align to BodyGenerationConditioning
 -> trim/repair component boundaries
 -> subtract keep-outs
 -> insert validated deterministic interfaces
 -> collision/articulation checks
 -> DFM/manufacturing checks
```

This keeps learned geometry useful without giving it authority over fit-critical mechanics.
