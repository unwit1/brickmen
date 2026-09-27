# Articulated 3D Generation and Joint-Proposal Research

Research snapshot: 2026-09-27

## Purpose

Evaluate current articulated-asset research for use in Brickmen's full-body generation pipeline.

These systems are **proposal, decomposition, and critique engines**.

They do not replace:
- FigureArchitecture;
- validated joint frames;
- JointCartridges;
- connector compensation;
- physical force/cycle validation.

The key opportunity is to use modern articulated-object models to infer or propose:
- component decomposition;
- kinematic trees;
- likely rotation axes;
- motion constraints;
- code-defined part hierarchies;

then reconcile those proposals against a chosen Brickmen architecture.

# Why articulated models matter

The earlier 3D pipeline assumed:

```
generate visual mesh
 -> segment parts
 -> insert known joints
```

Newer research enables:

```
image / generated mesh / text
 -> propose parts + joints + motion
 -> compare to target FigureArchitecture
 -> retain useful shell/structure proposals
 -> replace mechanical interfaces deterministically
```

This can reduce manual work for:
- unfamiliar body architectures;
- scans of custom figures;
- unknown component graphs;
- first-pass skeleton placement;
- generation of Brickmen-original bodies.

# PAct — Part-Decomposed Single-View Articulated Object Generation

PAct is an accepted SIGGRAPH Asia 2026 system whose official repository currently includes:
- single-image inference;
- pretrained checkpoints;
- part-decomposed geometry generation;
- appearance generation;
- articulation parameter estimation;
- simulation-ready output;
- both training stages;
- raw-data preprocessing.

The project describes the output as an articulated, simulation-ready object from one image.

## Brickmen role

Use as a **hypothesis generator** for an unknown/custom body photograph:

```
catalog photo
 -> PAct
 -> proposed parts
 -> proposed joints
 -> compare with FigureArchitecture registry
```

Potential outputs:
- likely torso/arm/hand split;
- shoulder axis;
- wrist movement;
- lower-body segmentation.

Do not import the predicted joint surface directly into printable geometry.

Instead:

```
PAct joint proposal
 -> nearest Brickmen joint primitive
 -> evidence/confidence
 -> physical validation if architecture unknown
```

## Research experiment

Input the same canonical product image into:
- PartCrafter;
- PAct;
- conventional Hunyuan/TRELLIS + Particulate.

Compare:
- part count;
- semantic component correctness;
- joint graph;
- visual fidelity;
- time to deterministic Brickmen reconstruction.

# Particulate — feed-forward articulation estimation

Particulate (CVPR 2026) operates on an existing static 3D mesh and predicts:
- 3D parts;
- kinematic structure;
- motion constraints.

The official paper explicitly reports operation on AI-generated 3D assets. The current official repository exposes custom-mesh inference and describes roughly 10-second feed-forward articulation inference for its tested workflow.

This fits Brickmen especially well as a **post-generation critic/proposal stage**.

Pipeline:

```
Tripo / Hunyuan / Meshy / PartCrafter output
 -> Particulate
 -> inferred part/joint graph
 -> compare to target FigureArchitecture
 -> reject or reconcile
```

## Architecture mismatch detection

Example:
target = Brickmen MidFig with:
- torso;
- separate arms;
- separate hands;
- one shoulder axis per side;
- wrist rotation.

If Particulate proposes:
- fused hand/arm;
- elbow joint not present in architecture;
- knee articulation not present in architecture,

Brickmen can flag the generated shell as architecture-inconsistent.

This is valuable even if none of Particulate's geometry becomes final.

# ArtLLM — articulated assets via 3D LLM

ArtLLM (CVPR 2026) autoregressively predicts a variable number of parts and joints from an object's point cloud and uses the resulting articulation-aware layout to condition part geometry generation.

Its official repository currently includes:
- inference code;
- training code;
- preprocessing code;
- part geometry generation through XPart;
- URDF conversion.

## Brickmen role

ArtLLM is especially relevant for:
- scan/mesh -> component graph hypothesis;
- unknown custom body -> likely link/joint layout;
- architecture clustering.

A useful experiment:

```
physical scan of Alpha/G(2)/other body
 -> point cloud
 -> ArtLLM
 -> proposed component/joint graph
 -> compare with teardown/metrology
```

This could quantify whether learned articulation models can accelerate reverse-engineering without trusting them for dimensions.

# UniPart — joint geometry + segmentation latent generation

UniPart (CVPR 2026) uses a unified geometry/segmentation latent representation and performs image-guided part-level generation.

Its two-stage design:
1. whole-object geometry + latent part segmentation;
2. part-level generation conditioned on whole-object and part-specific latents.

## Brickmen role

UniPart is another strong candidate for:
- generating coherent separate body shells;
- controlling part granularity;
- avoiding post-hoc mesh cutting.

Benchmark directly against PartCrafter.

Key metric:
**Does the resulting part decomposition align with a stylized FigureArchitecture component graph?**

# LAM — Language Articulated Object Modelers

LAM (CVPR 2026) is architecturally important even if its benchmark domain is not minifigures.

It treats articulated object generation as **code generation**.

The official implementation coordinates specialized agents for:
- link hierarchy design;
- geometry code;
- articulation code;
- visual/geometry critique;
- articulation critique;
- self-correction;

and compiles output into URDF.

## Brickmen lesson

This is very close to the long-term Brickmen architecture, except Brickmen's compiler should target:
- CadQuery/build123d/Blender geometry;
- FigureArchitecture JSON;
- JointCartridge definitions;
- 3MF/STEP manufacturing output;

rather than trusting free-form generated joints.

Proposed Brickmen adaptation:

### BodyPlanner
Selects architecture and component graph.

### LinkDesigner
Creates character-specific component/shell plan inside that graph.

### GeometryCoder
Builds deterministic or hybrid shell geometry.

### JointCompiler
Attaches only known JointCartridges.

### GeometryCritic
Checks source/style/silhouette.

### ArticulationCritic
Checks collision, movement and architecture rules.

### ManufacturingCritic
Checks thickness, print orientation and material.

### Fixer
Revises code/geometry without changing locked mechanical interfaces.

This provides an interpretable path to fully automated body generation.

# Trellis SegPart

Trellis SegPart (released July 2026) produces per-part labels for 3D meshes using multi-view segmentation conditioning and TRELLIS latent representations.

Brickmen should benchmark it alongside:
- SAMPart3D;
- PartField;
- Particulate's own decomposition.

Use case:
monolithic generative mesh -> semantic part labels.

Important limitation:
part segmentation does not imply printable separated components; after cutting, Brickmen must:
- create/cap boundaries;
- preserve wall thickness;
- establish seam geometry;
- insert joints.

# Proposed JointProposal entity

Do not store learned articulation output as Connector.

Store it as:

```json
{
  "joint_proposal_id": "...",
  "target_geometry_id": "...",
  "source_model": "particulate",
  "parent_part_candidate": "...",
  "child_part_candidate": "...",
  "joint_type_candidate": "revolute",
  "axis_candidate": {},
  "range_candidate": {},
  "confidence": 0.0,
  "evidence": [],
  "architecture_match": "...",
  "promotion_status": "proposal_only"
}
```

Only mapping to an existing validated connector or physical engineering creates a manufacturing joint.

# Kinematic reconciliation

Given model proposal P and architecture A:

1. map proposed part labels to architecture components;
2. compare parent/child topology;
3. compare joint type;
4. compare axis;
5. compare movement range;
6. classify:
   - MATCH;
   - APPROXIMATE_MATCH;
   - EXTRA_JOINT;
   - MISSING_JOINT;
   - WRONG_PARENT;
   - UNKNOWN.

Actions:
- MATCH -> use architecture joint;
- APPROXIMATE -> shell/skeleton alignment aid;
- EXTRA/MISSING -> regenerate or re-segment;
- unknown architecture -> capture evidence, never manufacture directly.

# Unknown architecture discovery

Articulation models are most useful when Brickmen does **not** already know the architecture.

For an unknown body:

```
photos / scan
 -> PAct or ArtLLM / Particulate
 -> component + joint proposals
 -> cluster against known architectures
 -> create FigureArchitectureCandidate
 -> request most useful physical evidence
 -> teardown/metrology
 -> validate
```

This can make the body census much more scalable.

# Articulation benchmark

Build a benchmark using bodies with known component graphs:

- standard minifigure;
- LEGO Giant;
- Hagrid Half Giant;
- Axl hybrid;
- Fantasy Troll;
- Brickmen MidFig mechanical mule.

Then later:
- measured Alpha;
- measured G(2);
- measured custom BigFig.

Metrics:
- component count error;
- semantic part accuracy;
- parent/child graph accuracy;
- joint-type accuracy;
- axis angular error;
- joint-center distance;
- range error;
- architecture-reconciliation result;
- human correction minutes.

# Generator modes

Brickmen should support three body-generation modes.

## Known architecture
Do **not** ask a learned model to invent the skeleton.

Use:
```
known deterministic skeleton
 -> generate visual shells around it
```

## Architecture candidate
Use articulated models to assist component/joint interpretation, but block production joints.

## Original new architecture R&D
Articulated models may propose skeletons, but engineering/physical validation must convert them into a new FigureArchitecture.

# Most promising near-term combined experiment

```
Brickmen MidFig BodyStyle concept image
 -> PartCrafter or UniPart separated shells
 -> PartField correspondence/mapping
 -> Particulate articulation proposal
 -> compare to locked MidFig component graph
 -> align shells to deterministic MidFig skeleton
 -> insert JointCartridges
 -> render articulation sweep
 -> print mechanical mule
```

This uses ML for what it is good at while keeping manufacturing mechanics under control.

# Sources

- PAct official implementation: https://github.com/Mobiuslqm/PAct
- Particulate paper: https://openaccess.thecvf.com/content/CVPR2026/html/Li_Particulate_Feed-Forward_3D_Object_Articulation_CVPR_2026_paper.html
- Particulate official implementation: https://github.com/RuiningLi/particulate
- ArtLLM paper: https://openaccess.thecvf.com/content/CVPR2026/html/Wang_ArtLLM_Generating_Articulated_Assets_via_3D_LLM_CVPR_2026_paper.html
- ArtLLM official implementation: https://github.com/AuthorityWang/ArtLLM
- UniPart paper: https://openaccess.thecvf.com/content/CVPR2026/html/He_UniPart_Part-Level_3D_Generation_with_Unified_3D_Geom-Seg_Latents_CVPR_2026_paper.html
- LAM paper: https://openaccess.thecvf.com/content/CVPR2026/html/Gao_LAM_Language_Articulated_Object_Modelers_CVPR_2026_paper.html
- LAM official implementation: https://github.com/gaoypeng/LAM
- Trellis SegPart: https://github.com/YixinZhu042/Trellis_Seg
