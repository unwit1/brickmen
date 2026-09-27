# Thing Cross-Architecture Control Study

Research snapshot: 2026-09-27

## Why Thing is the second control character

Hulk is ideal for learning muscular body translations.

Thing adds a different problem:
- very high body mass;
- rock-like surface material;
- less waist/chest differentiation than Hulk in many interpretations;
- identity distributed across silhouette **and** surface relief;
- multiple standard, intermediate, custom-large and explicit BigFig releases.

It is particularly useful because the custom ecosystem demonstrates that **one maker can place Thing on more than one body treatment**, proving again that maker identity is not architecture.

## Exact-source control: Fantastic Four: First Steps

Current catalog evidence gives a strong matched-source set.

### LEGO SH1051 Ben Grimm

BrickLink catalogs SH1051 as the 2025 Ben Grimm minifigure in The Fantastic Four: First Steps.

Architecture:
`minifig_standard`.

Translation implication:
- body mass cannot expand mechanically;
- rock texture and Thing identity must be carried mostly through head/body decoration and color;
- normal minifigure silhouette remains authoritative.

This is the strongest official baseline for the same source appearance.

### Alpha Toys AF336 Thing (First Steps)

HeroBloks catalogs:
- maker: Alpha Toys;
- serial: AF336;
- year: 2025;
- release group AF333–AF341.

Current imagery places AF336 in Alpha's standard/minifigure-like family, not the later 7 cm body.

Architecture candidate:
`minifig_standard_or_custom_standard`.

This is important because Alpha Toys itself is not synonymous with the 7 cm muscle architecture.

### KDL K2302 Thing (First Steps)

HeroBloks explicitly notes:
**6.5 cm big**.

Architecture candidate:
`custom_kdl_65mm_large`.

This gives a matched-source large/intermediate interpretation directly comparable with SH1051 and AF336.

### TP TP178 Thing (First Steps)

HeroBloks catalogs TP178 as a First Steps Thing in a normal custom-minifigure context.

Architecture candidate:
`minifig_standard_or_custom_standard`.

### TP TP349 Thing (First Steps) BigFig

HeroBloks separately catalogs TP349 as:
`Thing (First Steps) (BigFig)`.

That gives a particularly useful **same maker / same source / different architecture** contrast against TP178.

Mechanical equivalence with the classic LEGO Giant is not yet proven.

Architecture:
`compatible_bigfig_unresolved` pending body-family resolution/metrology.

## General/comics architecture set

### G (2) GH0348 Thing

HeroBloks catalogs GH0348 as Thing and separately lists G(2)'s BigFig Thing releases.

Visual research places GH0348 in the enlarged-torso/muscle-hybrid candidate family.

Architecture candidate:
`custom_g2_muscle_hybrid`.

### G (2) GH0435 / GH0440

HeroBloks labels:
- GH0435 Thing (Fall of the Fantastic Four) **BigFig**;
- GH0440 Thing (Future Foundation) **BigFig**.

Therefore G(2) clearly spans at least:
- muscle/hybrid body candidate;
- explicit BigFig family.

This is a key negative example for any model trying to infer architecture from brand/code prefix.

### Compatible classic BigFig ecosystem

HeroBloks lists Thing BigFigs from:
- Sheng Yuan SY288;
- Xinh 1421;
- Lele variants;
- Kopf KF913;
- LEBQ;
- JinRun;
- Esquare Brick;
- Decool;
- TP;
- others.

These are candidates for mold-family clustering.

Do not assume all share exact tooling or joint dimensions.

## What Thing teaches the style system

### Architecture-neutral Thing semantics

Candidate identity/body semantics:

```json
{
  "morphology": "rocky_massive_humanoid",
  "mass_distribution": {
    "shoulders": "large",
    "chest": "large",
    "waist": "large",
    "arms": "large",
    "hands": "large"
  },
  "surface_material": "segmented_rock",
  "identity_features": [
    "orange_rock_surface",
    "heavy_brow",
    "large_mass",
    "rock_plate_segmentation"
  ]
}
```

These semantics should exist **before architecture selection**.

### Standard minifigure mapping

```
large body mass
 -> implied by graphics/head treatment, not expanded silhouette

rock plates
 -> printed line/region pattern

large hands
 -> standard hands

heavy brow
 -> face/head decoration
```

### BigFig mapping

```
large body mass
 -> actual torso/arm/hand geometry

rock plates
 -> combination of sculpted relief + decoration

large hands
 -> dedicated large hand geometry

heavy brow/head
 -> molded/sculpted or architecture-specific head treatment
```

### Intermediate large custom mapping

Potential:
```
body mass
 -> custom torso/limb proportions

rock plates
 -> medium/high relief over shell

hands
 -> architecture-specific larger hands

surface
 -> relief density tuned so it survives minifigure-scale printing
```

## Rock surface is a separate semantic layer

Thing shows why `BodyStyleProfile` is not enough by itself.

We also need a `CharacterSurfaceMaterialSpec` or equivalent semantic layer.

Rock surface attributes:
- plate scale;
- crack width;
- relief depth;
- regional density;
- edge roundness;
- high-stress/joint exclusions;
- face feature integration.

The same architecture could render:
- smooth skin;
- fur;
- rock;
- metal;
- armor.

Therefore material/surface grammar belongs downstream of character identity but upstream of final shell generation.

## Geometry-vs-decoration rule

For each semantic surface feature classify:

- silhouette;
- major relief;
- shallow relief;
- print only;
- omit.

Rock cracks should not automatically become deep grooves.

At small scale, deep cracks:
- weaken thin sections;
- trap resin/support artifacts;
- create noisy visual texture.

A style critic should compare:
- source fidelity;
- architecture style;
- manufacturable relief depth.

## Cross-maker pair opportunities

### TP First Steps pair
- TP178 normal/minifigure-like;
- TP349 BigFig.

High-value because:
- same maker;
- same source appearance;
- architecture differs.

### Alpha family contrast
- AF336 First Steps Thing: standard/minifigure-like;
- AF362 Thing: later large-body Thing listing/family candidate.

High-value for:
- same brand;
- same character;
- different product/body family.

Source appearances may differ, so do not attribute every visual difference to architecture.

### G (2) contrast
- GH0348 hybrid candidate;
- GH0435 / GH0440 explicit BigFig.

High-value same-maker architecture contrast.

## Dataset requirements

For each pair:
- exact source appearance;
- architecture candidate;
- normalized front/back/side images;
- silhouette;
- landmark ratios;
- rock-region segmentation;
- sculpt-vs-print annotation;
- component graph;
- source/maker style notes;
- confidence.

Only matched-source pairs enter the strongest architecture-transform training subset.

## First style-transfer experiments

### Experiment T1
Input:
First Steps SH1051 reference/design semantics.

Targets:
- standard minifigure;
- Brickmen MidFig;
- Giant-compatible body.

Question:
Can the system preserve the same Thing identity while moving rock/mass information from print into geometry?

### Experiment T2
Compare TP178 -> TP349.

Question:
Which visual features are stable across same-maker/same-source architecture change?

### Experiment T3
Generate the same neutral `rocky_massive_humanoid` CharacterBodyFeatureSpec through:
- official_simple_midfig;
- anatomical_custom_midfig;
- Giant-like profile.

Question:
Can the architecture/style system produce different but semantically equivalent bodies without reference copying?

## Sources

- LEGO/BrickLink First Steps 2025 catalog: https://www.bricklink.com/catalogList.asp?catID=1339&catType=M&itemYear=2025
- Alpha Toys AF336: https://www.herobloks.com/figures/37284/alpha-toys/af336/thing-%28first-steps%29
- KDL K2302: https://www.herobloks.com/figures/38962/kdl/k2302/thing-%28first-steps%29
- G (2) GH0348: https://www.herobloks.com/figures/36599/g-%282%29/gh0348/thing
- G (2) GH0440: https://www.herobloks.com/figures/38552/g-%282%29/gh0440/thing-%28future-foundation%29-%28bigfig%29
- TP TP178: https://www.herobloks.com/figures/31646/tp/tp178/thing-%28first-steps%29
- TP TP349: https://www.herobloks.com/figures/37476
- Sheng Yuan SY288: https://www.herobloks.com/figures/2306/sheng-yuan/-sy288/thing-%28bigfig%29
