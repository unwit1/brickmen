# Part-Aware 3D Generation, Segmentation, and Cross-Body Correspondence

Research snapshot: 2026-09-27

## Purpose

Give Brickmen a reliable bridge between:

- an architecture-conditioned character concept;
- generated 3D geometry;
- the FigureArchitecture component graph;
- deterministic joint/connector insertion.

The preferred output of the learned geometry stage is **not one fused mesh**. It is a set of semantically meaningful visual-shell components that can be mapped to:

- torso;
- left/right arm;
- left/right hand;
- pelvis/lower body;
- legs;
- head/headwear;
- armor;
- accessories.

Functional interfaces are then removed/replaced with Brickmen's validated deterministic geometry.

## Two generation paths

### Path A — structured generation from the start

```
CharacterBodyDesignSpec
 -> architecture-conditioned multiview/concept image
 -> part-aware 3D generator
 -> candidate component meshes
 -> semantic mapping to component graph
 -> deterministic joint insertion
 -> assembly/articulation/DFM
```

Preferred when the generator can create coherent separate parts.

### Path B — monolithic fallback

```
concept image
 -> conventional 3D generator
 -> monolithic mesh
 -> open-world 3D part segmentation
 -> semantic component mapping
 -> boundary cleanup/capping
 -> deterministic joint insertion
 -> assembly/articulation/DFM
```

Brickmen should benchmark both instead of assuming structured generation is always superior.

# PartCrafter

PartCrafter is a NeurIPS 2025 structured 3D generation model that jointly generates multiple geometrically distinct and semantically meaningful meshes from one RGB image.

Its current official repository is particularly relevant because it now exposes:

- part-level image-to-3D inference;
- caller-specified `--num_parts`;
- VLM-based automatic part-count suggestion;
- background removal;
- an optional image style-transfer stage intended to bridge real photographs to the rendered-image training domain;
- local pretrained weights;
- training scripts/configurations;
- MIT license;
- object- and scene-level generation.

The official README currently states a minimum CUDA GPU target of about 8 GB VRAM for inference, with part count/token count adjustable to reduce memory.

## Brickmen use

Rather than asking PartCrafter to discover the body decomposition freely, Brickmen should condition the expected part count from `FigureArchitecture.component_graph`.

Example Giant-like body:

```
expected visual parts:
- torso/body
- left arm
- right arm
- left hand
- right hand
- lower body
- optional head
```

PartCrafter output components are **candidate shells**, not final mechanical parts.

## Part-count planning

The generic PartCrafter VLM part-count suggestion is useful as a baseline, but Brickmen can do better:

```
FigureArchitecture
 + CharacterBodyDesignSpec
 + ComponentSplitPolicy
 -> target generation parts
```

This preserves architecture semantics.

For example, Brickmen should not allow a generic VLM to decide that a Giant hand and forearm are one piece when the selected architecture defines them as separate replaceable components.

## Part identity mapping

PartCrafter generates separated meshes, but Brickmen still needs to assign semantic identity.

For each generated part:

1. render canonical views;
2. compare location relative to body skeleton;
3. use silhouette/appearance;
4. retrieve nearest architecture component;
5. assign semantic role;
6. retain uncertainty.

Then align the shell to the corresponding skeleton envelope.

## Style-transfer feature

PartCrafter's current code includes a provider-based input stylization stage for real-world photographs because it was trained on rendered imagery.

Brickmen should **not use its generic stylization as the final LEGO abstraction layer**.

Instead benchmark:

1. literal source photo -> PartCrafter built-in style transfer;
2. Brickmen architecture-conditioned concept -> PartCrafter;
3. Brickmen multiview-derived canonical hero view -> PartCrafter.

Hypothesis:
Brickmen's own body-style translation should outperform generic domain stylization for minifigure-scale bodies because it encodes architecture-specific proportions and geometry-vs-decoration decisions.

# SAMPart3D

SAMPart3D is an open-source method for part segmentation of arbitrary 3D objects.

Its pipeline uses multi-view RGB/depth renders of a mesh and learns/returns part decompositions.

## Brickmen role

Use when:
- Tripo/Meshy/Hunyuan/TRELLIS returns a fused body;
- a physical 3D scan is fused;
- imported geometry has unknown component boundaries.

Pipeline:

```
mesh
 -> canonical multi-view RGB + depth
 -> SAMPart3D
 -> part labels
 -> semantic mapping
 -> boundary cleanup
```

It is a decomposition aid, not an authority for joint location.

# PartField

NVIDIA Toronto AI Lab's PartField (ICCV 2025) predicts a part-aware feature field for a 3D shape.

Its current implementation supports:
- mesh input;
- point clouds / Gaussian splats;
- clustering into a hierarchical part decomposition;
- cross-shape consistency;
- cosegmentation;
- correspondence;
- interactive selection.

The cross-shape consistency is especially valuable to Brickmen.

## Brickmen role 1 — stable component correspondence

Suppose we have:
- neutral Brickmen MidFig;
- generated Hulk shell;
- generated Colossus shell;
- generated Thing shell.

PartField can be benchmarked for whether the same feature region remains comparable across bodies:

```
left upper arm <-> left upper arm
chest <-> chest
hand <-> hand
```

That can help map generated shells onto the architecture skeleton without requiring a separate supervised segmentation network for every body family.

## Brickmen role 2 — cross-architecture style analysis

PartField correspondence may help measure:
- how pectoral volume changes;
- where shoulder mass moves;
- how arm/hand proportions differ;
- where armor panels correspond;

across:
- Giant;
- Axl-like hybrid;
- Brickmen MidFig;
- Alpha-style research samples.

It should not be used to assert mechanical equivalence.

## Brickmen role 3 — generated body repair

If a generated component split is poor, hierarchical PartField clusters can supply alternate cut candidates.

The compiler can choose a clustering depth that best matches the target component graph.

# Three-level part semantics

Brickmen should distinguish:

## Level 1 — visual region
Examples:
- chest;
- bicep;
- gauntlet;
- boot;
- armor panel.

Used for:
- style transfer;
- correspondence;
- sculpt/print decisions.

## Level 2 — manufacturing component
Examples:
- torso;
- complete arm;
- hand;
- lower body.

Used for:
- printing;
- assembly;
- material/color separation.

## Level 3 — mechanical interface
Examples:
- shoulder pin socket;
- wrist cartridge;
- neck stud/socket.

Used for:
- fit;
- movement;
- validation.

A neural part segmentation should primarily inform Levels 1–2.

Level 3 is deterministic.

# Architecture-guided segmentation

A generic part model may over- or under-segment a stylized figure.

Brickmen should supply an architecture target:

```json
{
  "architecture_id": "brickmen_midfig_v0",
  "expected_components": [
    "torso",
    "left_arm",
    "right_arm",
    "left_hand",
    "right_hand",
    "lower_body"
  ],
  "optional_components": ["head","armor"],
  "forbidden_split_regions": ["shoulder_joint_keepout","wrist_joint_keepout"]
}
```

Then reconcile model output with that graph.

# Component-boundary optimization

A visual body seam is also a manufacturing decision.

Objective terms:
- architecture correctness;
- visual concealment;
- print orientation;
- support damage;
- joint access;
- decoration seam;
- assembly;
- replaceability.

The compiler should be allowed to shift an AI-proposed split inside a bounded `ComponentSplitZone`.

Example:
an arm/hand split can move into a wrist cuff so the seam is visually natural and the joint cartridge remains accessible.

# Cross-body correspondence dataset

For each architecture/body sample derive:

- normalized mesh;
- PartField features;
- visual-region segmentation;
- manufacturing-component segmentation;
- skeleton landmarks;
- joint frames;
- canonical renders.

Create correspondence pairs:
- neutral architecture -> character body;
- same character across architectures;
- same architecture across characters;
- same mold family across decorated releases.

This supports both recognition and generation.

# Training strategy

Do not begin by training a body-specific part model.

## Stage 1
Benchmark:
- PartCrafter decomposition;
- SAMPart3D;
- PartField;
- deterministic spatial/component rules.

## Stage 2
Create reviewed Brickmen component labels.

## Stage 3
Train a light semantic mapper from generic clusters/parts to Brickmen component IDs.

## Stage 4
Only fine-tune part-aware 3D models if the benchmark shows a persistent domain gap.

PartCrafter currently exposes training scripts/configurations, making it a plausible long-term fine-tuning candidate.

# New provider-neutral APIs

```
geometry.generate_parts(design_spec, architecture)
geometry.segment_parts(mesh, architecture)
geometry.part_features(mesh)
geometry.correspond(source_mesh, target_mesh)
geometry.map_components(parts, architecture)
geometry.optimize_split(component, policy)
geometry.attach_skeleton(shell_parts, skeleton)
```

# Evaluation benchmark

For each test body record:

### Decomposition
- required component recall;
- over-segmentation;
- under-segmentation;
- left/right correctness;
- boundary error;
- disconnected fragments.

### Correspondence
- same-component retrieval;
- landmark transfer;
- region correspondence IoU;
- architecture-to-character mapping accuracy.

### Manufacturing
- ability to insert deterministic joint;
- post-split watertightness;
- minimum wall preservation;
- articulation pass;
- support/orientation quality;
- final physical print pass.

### Cost
- VRAM;
- runtime;
- human correction minutes.

# Immediate high-value experiment

Use a controlled Brickmen MidFig test before character generation:

1. render a neutral MidFig concept with six visible component groups;
2. PartCrafter generate with known part count;
3. map parts to architecture;
4. separately generate a fused version with a conventional model;
5. segment fused version with SAMPart3D and PartField;
6. compare boundary/component accuracy;
7. insert the same JointCartridges;
8. print both;
9. compare manual repair time and physical assembly.

This answers whether part-aware generation is actually worth becoming the default.

# Sources

- PartCrafter official repo: https://github.com/wgsxm/PartCrafter
- PartCrafter project: https://wgsxm.github.io/projects/partcrafter/
- PartCrafter paper: https://arxiv.org/abs/2506.05573
- SAMPart3D: https://github.com/Pointcept/SAMPart3D
- PartField: https://github.com/nv-tlabs/PartField
