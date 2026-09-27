# Body Architecture Recognition and Cross-Architecture Style Transfer

Research snapshot: 2026-09-27

## Objective

Brickmen should be able to:

1. recognize what body architecture a figure/part uses from catalog metadata, photographs or 3D geometry;
2. select an appropriate architecture for a character;
3. translate a character design intelligently across architectures;
4. generate architecture-specific 2D decoration and 3D geometry;
5. manufacture the result using the correct digital twin, surfaces, joints and connector profiles.

The system must not assume that scaling a standard minifigure design produces a good BigFig or muscle-body design.

## Architecture resolution is separate from character resolution

Input:
```
Character + SourceAppearance + user preference
```

Output:
```
FigureArchitectureCandidate[]
```

Selection evidence may include:
- canonical source size/build;
- official precedent;
- closest analogous official/custom character;
- user's desired collection style;
- available donor body;
- manufacturability;
- articulation requirements;
- requested compatibility;
- visual fidelity.

There may be multiple correct results.

For Hulk, an official-style standard minifigure interpretation and an official-style Giant interpretation can both be valid depending on the requested aesthetic.

## Photo recognition pipeline

### Stage 1 — segmentation

Use SAM 2 or equivalent to isolate:
- full figure;
- head;
- torso/body;
- left/right arms;
- hands;
- lower body/legs;
- accessories.

Preserve uncertainty when parts overlap.

### Stage 2 — metadata priors

Use:
- maker;
- product code;
- catalog labels;
- known release;
- approximate year.

Example:
an `AF345` Alpha Toys record is strong evidence for the Alpha product family, but prefix recognition alone is never sufficient to infer joint geometry.

### Stage 3 — visual embedding retrieval

Create standardized canonical renders of every validated FigureArchitecture.

Embed:
- full front;
- back;
- side;
- 3/4;
- silhouette;
- component crops.

A modern vision-language encoder such as SigLIP 2 can provide image-image/text-image retrieval features.

Retrieve nearest architecture examples before classification.

### Stage 4 — deterministic proportion landmarks

Measure visible ratios where possible:

- total body height;
- head height/body height;
- shoulder width;
- torso width;
- waist width;
- arm length;
- hand envelope;
- hip/leg width;
- leg length;
- shoulder-to-hip distance;
- joint center locations.

Ratios are more robust than raw pixels when scale is unknown.

### Stage 5 — joint/topology cues

Detect:
- shoulder hinge/pin location;
- wrist seam;
- hip separation;
- independent legs;
- integrated feet;
- neck/head interface;
- visible anti-studs;
- standard minifig hands;
- Technic-like joint hardware.

These cues can separate visually similar large bodies.

### Stage 6 — confidence distribution

Output:
```json
{
  "candidates": [
    {"architecture_id": "custom_alpha_7cm_muscle", "probability": 0.0}
  ],
  "unknown_probability": 0.0,
  "evidence": [],
  "required_next_view": "rear|side|joint_closeup|null"
}
```

Never force an unknown body into the nearest registered class.

## 3D mesh / scan recognition

For a mesh:

1. normalize units if a known connector/part supplies scale;
2. separate connected/semantic components;
3. sample point cloud;
4. compute deterministic dimensions/proportions;
5. retrieve nearest 3D architecture embeddings;
6. compare joint topology;
7. align against canonical digital twins;
8. classify or create an unknown-family candidate.

### 3D embedding research

OpenShape supports open-world 3D shape retrieval/classification across text, image and 3D representations.

Uni3D is another strong candidate for unified/scalable 3D representation and open-world retrieval/part understanding.

These should be benchmarked on the Brickmen body registry rather than accepted from general-object benchmarks.

## Part-level recognition

Architecture recognition must work on detached parts too.

Examples:
- identify a loose Alpha arm;
- recognize a LEGO Giant hand;
- distinguish Giant arm from maker-specific muscle arm;
- decide whether a torso accepts standard hips;
- recognize an architecture-specific head/neck.

Part classifier output:
- component semantic type;
- architecture candidates;
- connector candidates;
- left/right;
- orientation;
- color/material;
- decoration;
- uncertainty.

This enables automatic scan/import and physical-inventory management.

## BodyStyleProfile

Each FigureArchitecture needs its own style grammar.

Do not merely rescale standard-minifigure decoration.

Store:

### Proportions
- canonical head/body ratio;
- shoulder/waist ratio;
- arm/leg proportions;
- hand/accessory scaling.

### Geometry-vs-decoration balance
- which musculature is sculpted;
- which clothing folds become relief;
- where armor should become geometry;
- which details remain printed.

### Sculptural depth classes
- silhouette-defining;
- major relief;
- shallow relief;
- printed-only;
- omit.

### Decoration surfaces
- semantic surface IDs;
- UV/flattening maps;
- printable region;
- wrap continuity;
- joint/contact keepouts.

### Graphic grammar
- line hierarchy;
- detail density;
- face scale;
- muscle/armor line treatment;
- shading expectations;
- base-color negative space.

### Architecture-specific exaggeration
- acceptable head size;
- chest width;
- hand size;
- foot size;
- muscle mass;
- weapon scale.

## Cross-architecture StyleTransferPair

Create paired observations of the same Character/SourceAppearance across architectures.

Example:

```
Hulk source appearance
 -> standard minifigure interpretation
 -> Giant interpretation
 -> Alpha 7cm interpretation
 -> Bigguy interpretation
```

Extract:
- shared identity-critical features;
- differences caused by architecture;
- what became molded geometry;
- what remained decoration;
- proportion transforms;
- detail simplification;
- accessory scaling.

Schema:

```json
{
  "pair_id": "...",
  "character_id": "...",
  "appearance_id": "...",
  "from_architecture": "...",
  "to_architecture": "...",
  "source_release_ids": [],
  "landmark_transform": {},
  "geometry_translation": [],
  "decoration_translation": [],
  "identity_features_preserved": [],
  "confidence": "...",
  "sources": []
}
```

## Why Hulk is the first benchmark

Hulk has unusually rich cross-architecture supervision:
- official Giant/BigFig;
- standard minifigure;
- Mighty Micros short-leg;
- third-party Alpha Toys 7 cm;
- G (2);
- Bigguy;
- Mr.J/Heart;
- many compatible/premium BigFig releases.

This makes Hulk a natural controlled test for separating:
- character identity;
- source appearance;
- architecture;
- maker style.

Then repeat on:
- Red Hulk;
- Thing;
- Beast;
- Colossus;
- Juggernaut;
- Abomination.

## Architecture-conditioned generation

Target generation pipeline:

```
SourceAppearance
 -> ArchitectureResolver
 -> FigureArchitecture
 -> BodyStyleProfile
 -> architecture-specific ReferenceSet
 -> CharacterBodyDesignSpec
 -> canonical multiview concept
 -> geometry/decoration generation
 -> validated architecture joints/connectors
 -> articulation check
 -> architecture-style critic
 -> manufacturing DFM
```

The prompt/model receives architecture-specific context rather than a generic "LEGO style" request.

## CharacterBodyDesignSpec

Include:
- target architecture;
- exact source appearance;
- target overall scale;
- semantic body parts;
- identity-critical silhouette;
- architecture landmarks;
- geometry-vs-decoration decisions;
- molded relief plan;
- print/decor plan;
- base colors;
- joint graph;
- connector revisions;
- accessory scale rules;
- allowed creative freedom;
- manufacturing profile.

## Architecture-specific generation strategies

### Standard minifigure
Prefer canonical donor/digital-twin geometry. Generate:
- decorations;
- new headwear/hair/accessories only when required.

### LEGO Giant
Use validated Giant component templates/joints and generate character-specific visual shells around them.

### Axl hybrid
Preserve standard head/hip/leg compatibility and generate oversized torso/arm geometry inside the Axl-style architecture.

### Alpha / maker-specific muscle body
Do not generate final bodies until physical joint metrology exists.

Once validated:
- use architecture-specific parametric skeleton;
- generate surface/muscle/clothing shell;
- preserve exact joint centers and keepouts.

### Unknown architecture
Allow concept generation, but block production geometry until joints/scale are resolved.

## Style recognition

The system should also answer:

> "This custom figure is using what body style?"

Classifier outputs two layers:
1. mechanical FigureArchitecture;
2. aesthetic BodyStyleProfile/maker style.

A maker could reuse the same mechanical architecture with different surface/sculpt style, so these are not the same entity.

## Learning body style from the corpus

For each architecture, render normalized figures and extract:

- silhouettes;
- 2D landmarks;
- 3D landmarks;
- component proportions;
- curvature maps;
- relief depth;
- semantic surface masks;
- decoration density;
- line features;
- color roles;
- joint visibility.

Cluster releases within the architecture to identify:
- base architecture grammar;
- maker-specific style;
- character-specific deviations.

Do not label a one-off sculptural choice as a universal body rule.

## Geometry template strategy

Every physically validated architecture should eventually have:

- neutral blank body;
- exploded assembly;
- joint center coordinate system;
- parametric skeleton;
- canonical pose;
- articulation sweeps;
- collision volumes;
- standard accessory anchors;
- semantic surface regions;
- UV maps;
- render cameras;
- printable CAD/mesh templates;
- process-specific manufacturing profiles.

This becomes the foundation for both recognition and generation.

## Recognition benchmark

Create a frozen benchmark containing:
- clean catalog front views;
- product photos;
- rear/side photos;
- assembled figures;
- detached parts;
- partially occluded figures;
- low-resolution listings;
- 3D scans/meshes when available.

Test:
- known architecture classification;
- unknown rejection;
- part classification;
- cross-maker confusion;
- source-label normalization.

## Physical feedback

When a scanned/measured figure differs from the digital twin:
- do not overwrite canonical geometry;
- create measurement observation;
- determine whether it is normal manufacturing variance, another mold revision, or another architecture;
- promote only after corroboration.

## Research tools

Image:
- SAM 2 or equivalent for segmentation;
- SigLIP 2 / strong vision embeddings for canonical-render retrieval.

3D:
- OpenShape for open-world 3D retrieval/classification research;
- Uni3D for unified 3D representation/part understanding;
- deterministic ICP/alignment and geometric landmark extraction.

These models are retrieval/classification aids. Joint identity and manufacturing-critical compatibility must remain evidence/measurement backed.

## End-state behavior

The desired user interaction is:

> "Make me a Thing from Fantastic Four: First Steps."

Brickmen should be able to respond internally:

1. resolve the exact appearance;
2. detect that multiple body architectures are plausible;
3. select or present the user's preferred architecture policy;
4. retrieve the matching BodyStyleProfile;
5. generate body and accessories at the correct scale;
6. insert validated joints/connectors;
7. generate decoration mapped to that body;
8. render the finished figure;
9. critique source fidelity and architecture style;
10. produce printable/manufacturable files.

The choice of body architecture becomes a deliberate design decision, not a side effect of whichever AI model happened to generate the mesh.

## Current part-recognition research stack — 2026-09-27

Use an ensemble; do not make one foundation model authoritative.

### 2D / catalog photography

**SAM 2**
- promptable segmentation across images and video;
- useful for isolating full figures and tracking the same body/component across turntable/video frames.

Use with:
- canonical landmark detector;
- architecture nearest-neighbor retrieval;
- maker/release metadata priors.

### 3D retrieval

**OpenShape**
- text/image/point-cloud retrieval and zero-shot 3D representation;
- suitable candidate for finding the closest known body/part digital twin.

**Uni3D**
- scalable 3D representation aligned with image/text features;
- benchmark as an alternative retrieval embedding.

### 3D part segmentation

Candidates:
- SAMPart3D;
- PartSLIP++;
- Find Any Part in 3D / successor open-world part models;
- Tripo semantic mesh segmentation for generated/provider-hosted meshes;
- Pointcept backbones for a future Brickmen-trained part segmenter.

Expected semantic queries:
- head;
- hair;
- upper arm;
- forearm;
- hand;
- torso/chest;
- pelvis;
- thigh;
- lower leg;
- foot;
- shoulder pin;
- wrist connector;
- tail;
- centaur body;
- tentacle.

### Articulation estimation research

Newer articulated-object research such as SPLART and dynamic 3D-Gaussian part/motion methods suggests a future workflow in which Brickmen photographs a physical custom figure in two or more poses and estimates:
- moving components;
- joint centers;
- articulation axes;
- static versus dynamic parts.

Treat this as a research accelerator, not manufacturing metrology. Physical gauges/scans still establish final connectors.

### Hybrid recognition decision

```
catalog/photo
 -> SAM2 masks
 -> landmark/topology features
 -> image retrieval
 -> metadata prior
 -> candidate architectures

mesh/scan
 -> part segmentation
 -> OpenShape/Uni3D retrieval
 -> deterministic measurements
 -> joint/topology comparison
 -> candidate architectures

candidate architectures
 -> evidence reconciliation
 -> known architecture OR unknown candidate
```

The final output always exposes evidence and unknown probability.

### Style application after recognition

Once architecture is resolved:

1. retrieve its `BodyStyleProfile`;
2. retrieve architecture surface schema and neutral digital twin;
3. extract character identity features independently;
4. decide per feature: sculpt, print, separate accessory, cloth, or omit;
5. apply normalized style features to the target surfaces;
6. regenerate architecture-specific multiview concepts;
7. attach deterministic joints/connectors;
8. score source fidelity and architecture-style fidelity separately.

A style profile is descriptive and can be transferred. Proprietary mechanical geometry is not implied by stylistic similarity.
