# Brickmen Original MidFig Architecture — Research Specification

Status: concept architecture / not physically validated  
Created: 2026-09-27

## Purpose

Define an **independent, automation-first intermediate muscular body architecture** that Brickmen can eventually generate and 3D print without depending on the exact proprietary geometry of Alpha Toys, G (2), Bigguy, Mr.J/Heart, or another custom maker.

The architecture should learn from:
- official LEGO interoperability patterns;
- official Axl and Hagrid Half Giant precedents;
- modern Giant/BigFig hardware patterns;
- community printable MidFig successes/failures;
- cross-architecture Hulk/Thing/Beast/Colossus style observations.

But its visual shell and joint system should be independently designed.

## Design goals

1. Visually between a standard minifigure and classic Giant.
2. Suitable for characters whose identity depends on increased body mass.
3. Retain as much standard-system interoperability as is practical.
4. Separate visual shell from mechanical skeleton.
5. Make wear-critical joints replaceable.
6. Optimize for resin visual shells but allow thermoplastic joint cartridges.
7. Allow architecture-specific style generation.
8. Make every major dimension parametric.
9. Avoid whole-model scale hacks such as 101-102%.
10. Support automated generation, slicing, assembly and QC.

## Proposed interoperability targets

These are desired interface families, not yet approved production dimensions.

### Head

Preferred baseline:
**standard minifigure head/headwear compatibility where visually appropriate.**

Why:
- enormous donor/head/hair ecosystem;
- existing Brickmen decoration pipeline;
- simplifies character generation;
- official Axl/Hagrid precedents demonstrate oversized bodies with minifigure-scale heads.

Optional future:
- enlarged architecture-specific head for characters requiring it.

### Hands

Two interchangeable hand classes:

1. **standard-hand module**
   - supports a genuine/compatible standard minifigure hand when body proportions allow.

2. **MidFig large hand**
   - larger visual shell;
   - retains validated 3.18-family accessory grip;
   - replaceable wrist cartridge.

This lets a design decide whether character scale demands larger hands without changing weapon compatibility.

### Accessory anchors

Prefer:
- standard bar family;
- studs/anti-studs;
- standard back accessory anchor where proportionally viable;
- optional Technic pin/axle anchor.

### Shoulder

Research candidates:
- commodity Technic pin/axle cartridge;
- independently designed thermoplastic friction cartridge;
- resin socket only for low-cycle display variants.

The shoulder should be replaceable independently from the sculpted torso.

### Wrist

Research candidates:
- standard minifigure hand peg interface where feasible;
- larger keyed/round cartridge with internal standard bar grip in large hand.

### Lower body

Create at least two modules:

**M1 — standard lower-body adapter**
- accepts standard hips/legs;
- visually analogous to Axl-style hybrid approach.

**M2 — MidFig lower body**
- wider pelvis;
- longer/thicker legs;
- architecture-specific hip joint;
- maintains stud-compatible foot/base behavior where possible.

This allows the same torso style to serve both mildly bulky and very muscular characters.

## Skeleton structure

Conceptual graph:

```
head_interface
      |
     neck
      |
torso_skeleton
 |          |
L shoulder  R shoulder
 |          |
L arm       R arm
 |          |
L wrist     R wrist
 |          |
L hand      R hand
      |
  waist_adapter
      |
 lower_body_module
```

Visual geometry wraps these deterministic joint frames.

## Parametric body variables

The generation system should not directly edit mesh vertices for basic proportion changes.

Expose:

- total_height_target
- shoulder_width
- chest_width
- chest_depth
- waist_width
- torso_height
- neck_height
- shoulder_height
- arm_length
- upper_arm_bulk
- forearm_bulk
- hand_scale
- pelvis_width
- leg_length
- thigh_bulk
- calf_bulk
- head_scale_mode
- torso_taper
- stance_width

Values are constrained by:
- joint locations;
- articulation;
- minimum wall;
- style profile;
- standard-system anchors.

## Architecture style modes

The same mechanical skeleton can support several BodyStyleProfiles.

### official_simple_midfig
Inspired by official LEGO abstraction:
- fewer muscle groups;
- broad simple planes;
- restrained surface relief;
- strong color/print role.

### anatomical_custom_midfig
Higher sculptural density:
- pectoral/abdominal/deltoid mass;
- stronger limb anatomy;
- still simplified enough for minifigure-scale reading.

### armored_midfig
- smoother base anatomy;
- armor volumes layered over skeleton;
- character-specific panels/accessory anchors.

These are style profiles, not different mechanical architectures unless component/joint graphs diverge.

## Geometry generation architecture

```
CharacterBodyFeatureSpec
 + BrickmenMidFigSkeleton(parameters)
 + BodyStyleProfile
 -> shell envelopes
 -> generated/sculpted torso/limbs
 -> joint keep-out subtraction
 -> deterministic JointCartridge insertion
 -> minimum-wall enforcement
 -> articulation simulation
 -> canonical render bundle
 -> style/source critic
 -> printable components
```

## JointCartridge interface

Every joint defines:
- parent_frame;
- child_frame;
- insertion_axis;
- hardware;
- replaceable_insert_geometry;
- visual_keepout;
- movement_range;
- force/torque target;
- validated materials;
- cycle life evidence.

The visual shell cannot modify these fields.

## Component splitting strategy

Preferred splits:

- torso;
- left arm;
- right arm;
- left/right hand;
- waist/lower body;
- left/right leg if articulated;
- head/hair/accessories as separate existing architecture assets.

Benefits:
- orient each resin print optimally;
- replace broken pieces;
- mix colors/materials;
- share limbs across characters;
- easier surface decoration;
- reuse the same validated skeleton.

## Character scaling policy

Do not map character height literally to real-world scale.

Instead derive:
- **mass class**
- **stature class**
- **silhouette class**
- **hand/accessory emphasis**
- **head proportional treatment**

Examples:

Hulk:
- very large shoulder/chest mass;
- large hands;
- strong taper;
- high limb bulk.

Colossus:
- tall and broad;
- less extreme hand exaggeration;
- strong cylindrical limb mass.

Beast:
- hunched/athletic proportion target;
- potentially longer arm visual envelope;
- hair/fur shell emphasis.

Thing:
- high torso/limb volume;
- low waist taper;
- rock relief as shallow/major surface structure.

These map into architecture parameters rather than creating entirely separate skeletons.

## First prototype variants

### P0 — blank mechanical mule

No character styling.
Purpose:
- joints;
- articulation;
- print orientation;
- assembly;
- cycle testing.

### P1 — simple Hulk-style mass study

Original generic muscular shell, not a character replica.
Purpose:
- body proportion test;
- architecture style read;
- hand/weapon scale.

### P2 — architecture-conditioned character proof

Use a source-grounded character only after P0/P1 mechanics are stable.

## Physical validation order

1. shoulder cartridge alone;
2. wrist/hand cartridge;
3. neck/head interface;
4. waist/lower-body interface;
5. blank torso + arms;
6. arm swing collision;
7. grip accessory;
8. cycle test;
9. complete blank body;
10. styled shell.

Do not print a fully decorated character first.

## Data Brickmen should learn

For every prototype:
- exact CAD parameters;
- connector revision;
- resin/material;
- orientation;
- measured dimensions;
- force/torque;
- cycle count;
- breakage;
- fit;
- user visual preference;
- silhouette/style metrics.

Over time this becomes a training set for predicting:
- viable body parameters;
- joint failure risk;
- preferred proportions;
- character-to-architecture translation.

## Relationship to external custom bodies

Alpha Toys/G(2)/Bigguy/Mr.J/etc. should contribute:
- observed scale;
- proportional distributions;
- sculpture-vs-print strategy;
- component-layout observations;
- user/market style vocabulary.

They should **not** silently become CAD masters for Brickmen's original body.

## End-state

A request such as:

> "Make Colossus using the Brickmen MidFig body."

should resolve to:

1. Colossus source appearance;
2. Brickmen MidFig skeleton;
3. appropriate stature/mass parameters;
4. architecture style profile;
5. generated metal-skin/body visual shell;
6. validated joint cartridges;
7. correct hand/accessory anchors;
8. print-ready components;
9. assembled digital proof;
10. physical manufacturing job.

The body architecture remains stable while character shells change.
