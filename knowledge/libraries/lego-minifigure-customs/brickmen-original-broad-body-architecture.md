# Brickmen Original Broad Body Architecture — Research Specification

Status: concept architecture / not physically validated  
Created: 2026-09-27

## Purpose

Define an original **standard-height to mildly intermediate broad-body architecture** for characters that need much more torso/arm mass than a normal minifigure without automatically becoming a tall MidFig or full Giant.

This architecture is now strongly justified by:
- LEGO Axl's official oversized-torso hybrid precedent;
- Alpha Toys AF321–AF332 symbiote bodies, which remain about 4–4.5 cm tall while radically increasing upper-body mass;
- custom muscle hybrids such as G (2);
- characters such as Venom, Bane, Kingpin and some armored/monster designs.

The body must be independently engineered rather than copying Alpha/G(2)/other proprietary geometry.

## Design goals

1. Approximate standard minifigure overall stature in the base variant.
2. Standard minifigure head compatibility where visually appropriate.
3. Standard lower-body adapter as a primary configuration.
4. Much broader/deeper torso envelope.
5. Replaceable enlarged arms/hands.
6. Standard 3.18-family accessory grip.
7. Architecture-specific back/accessory anchors.
8. Deterministic replaceable shoulder/wrist joints.
9. Resin-friendly visual shells.
10. Optional mild-height lower-body variant without changing upper-body architecture.

## Why Broad is not MidFig

`brickmen_broad_v0`:
- prioritizes width/depth;
- can stay around standard minifigure height;
- standard legs remain a first-class option.

`brickmen_mid_v0`:
- intentionally increases overall stature and/or leg length;
- has a larger independent lower-body design space.

A character can therefore be:
- broad but short/standard-height;
- tall but not extremely broad;
- both tall and broad.

This prevents size from collapsing into one scalar.

## Best target characters

Strong:
- Venom;
- Carnage;
- Riot;
- Bane;
- Kingpin;
- heavy armor suits;
- broad aliens/monsters.

Possible:
- Thing in stylized standard-height treatment;
- Beast;
- squat trolls/ogres;
- large fantasy armor.

Usually prefer Mid/XL/Giant:
- extreme Hulk interpretations;
- very tall Colossus;
- classic Giant-scale Thanos;
- Gorilla Grodd if full primate proportions are required.

## Proposed component graph

```
standard_head_or_custom_head
          |
        neck
          |
    broad_torso
     /       \
 L shoulder  R shoulder
    |           |
 L broad arm  R broad arm
    |           |
 L hand       R hand
          |
    waist_adapter
          |
 standard_lower_body
 OR broad_lower_variant
```

## Head

Default target:
standard minifigure head interface.

Reasons:
- enormous existing character/head ecosystem;
- preserves standard hair/headgear where appropriate;
- reduces custom geometry;
- official Axl/Hagrid precedents support broad bodies with standard-scale heads.

Optional:
architecture-specific enlarged head shell on the same neck interface if silhouette demands it.

## Lower body

### B0 — standard lower adapter

Primary early prototype:
- standard hips/legs;
- standard foot/stud behavior;
- simplest interoperability.

This is especially relevant to Alpha AF321–AF332's visual strategy.

### B1 — broad lower body

Future:
- slightly widened pelvis;
- thicker/shorter legs;
- retains near-standard overall stature.

Do not automatically use the MidFig long-leg module.

## Arms

Broad-body identity depends heavily on arms.

Parameters:
- shoulder sphere/mass;
- upper arm width/depth;
- forearm width/depth;
- arm length;
- wrist position;
- elbow visual break.

Initial mechanical version may keep:
- one shoulder rotation;
- wrist rotation/hand insertion;
- no functional elbow.

Optional later elbow articulation becomes an architecture revision rather than an invisible change.

## Hands

Two modes:

### standard compatible
Use standard minifigure hand when source/style permits.

### broad hand
Larger outer hand shell but:
- validated 3.18-family C-grip;
- replaceable wrist cartridge;
- standardized accessory axis.

The hand shell may vary aesthetically while the inner grip remains a shared mechanical primitive.

## Joint strategy

Shoulder priority:
1. thermoplastic/commodity cartridge;
2. independently designed replaceable pin/socket;
3. resin friction joint only after cycle validation.

Wrist:
- replaceable cartridge;
- allow standard hand adapter.

Waist:
- standard torso-to-hip interface target for B0.

## Parametric variables

- torso_height
- shoulder_width
- chest_width
- chest_depth
- waist_width
- abdomen_projection
- shoulder_mass
- arm_length
- upper_arm_bulk
- forearm_bulk
- hand_scale
- neck_position
- back_projection

Lower-body variables are separate.

## Style modes

### official_broad_simple
- large smooth planes;
- minimal muscle segmentation;
- decoration carries most fine detail.

### symbiote_broad
- strong upper-body anatomy;
- optional shoulder/back spike anchors;
- organic relief/tendril accessory zones.

### heavy_round_broad
- low taper;
- larger abdomen/waist;
- suitable for Kingpin/Blob-like semantics.

### armored_broad
- simpler underlying body;
- layered armor shell;
- separate backpack/shoulder components.

Same mechanics, different BodyStyleProfiles.

## Alpha AF325 research lesson

Do not copy AF325 geometry.

Use it to validate the design-space proposition:
**standard stature + huge upper body is visually coherent and commercially used.**

Brickmen should independently optimize:
- standard interfaces;
- printability;
- joint durability;
- style flexibility.

## First prototypes

### B-P0 mechanical mule
- blank broad torso;
- standard head;
- standard lower body;
- simple arms/hands;
- no character sculpt.

Test:
- shoulder;
- waist;
- wrist;
- grip;
- arm sweep.

### B-P1 mass sweep
Generate torso/arm variants:
- mild broad;
- muscular broad;
- heavy-round broad;
- armored broad.

No licensed character styling required.

Evaluate:
- style readability;
- articulation;
- wall thickness;
- print orientation.

### B-P2 symbiote surface study
Use a generic original organic creature:
- smooth;
- shallow veins;
- tendril anchors;
- large hand.

Purpose:
validate the `surface_symbiote_organic` profile without relying on a proprietary sculpt.

## Automated generation

```
CharacterBodyFeatureSpec
 -> architecture candidate scoring
 -> brickmen_broad_v0
 -> selected BodyStyleProfile
 -> BroadSkeleton(parameters)
 -> part-aware visual shell generation
 -> deterministic joints
 -> surface compiler
 -> articulation/DFM
 -> render/critic
 -> print
```

## Relationship to Alpha Venom

The Alpha AF321–AF332 family becomes a useful **recognition/style reference**, not a manufacturing master.

Physical acquisition can answer:
- how much shoulder width works visually at ~4.5 cm;
- whether standard hips/legs are actually reused;
- how Alpha handles arm/wrist articulation;
- how accessory grip scales.

Brickmen can then choose independent joint dimensions and shell geometry.

## End-state example

Prompt:

> Make Venom on a chunky standard-height body.

Possible resolver output:
```
architecture: brickmen_broad_v0
style: symbiote_broad
stature: standard
shoulder_mass: very_large
forearm_mass: very_large
lower_body: standard_adapter
surface: symbiote_organic
```

This is fundamentally different from simply requesting a 7 cm MidFig or Giant.
