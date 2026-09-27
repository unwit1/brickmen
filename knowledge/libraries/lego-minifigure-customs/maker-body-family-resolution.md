# Maker Body-Family Resolution

Research snapshot: 2026-09-27

## Purpose

Prevent Brickmen from making a false assumption that one maker prefix equals one mechanical body architecture.

Current evidence shows that major compatible/custom brands can release multiple architecture families under the same brand and even under nearby product-code ranges.

The architecture resolver therefore works at:

**release -> body-family cluster -> FigureArchitecture**

not:

**maker -> FigureArchitecture**.

## Alpha Toys

Alpha Toys provides a clear counterexample to maker-level inference.

### AF333-AF341 Fantastic Four family

AF336 Thing (First Steps) is visually standard/minifigure-like:
- conventional minifigure-style torso/leg proportions;
- normal-scale hands;
- no 7 cm comparison marker in the catalog image;
- release is part of AF333-AF341 Fantastic Four series.

This release should **not** be mapped to the 7 cm Alpha muscle architecture merely because its prefix is AF.

Current classification:
`alpha_standard_or_standard_compatible / visual evidence`.

### AF344-AF347 Hulk family

AF344 Avengers Hulk and AF345 Comics Hulk use the newer large muscle body.

AF345 catalog imagery includes:
- explicit 7 cm height marker;
- explicit ~4 cm normal minifigure comparison;
- large segmented muscular arms;
- long custom legs;
- much wider anatomical torso.

Current classification:
`custom_alpha_7cm_muscle`.

### AF360-AF363 family

Public catalog records:
- AF360 Compound Hulk;
- AF361 Beast — explicitly 7 cm;
- AF362 Thing — product image uses the same 7 cm comparison graphic and large muscular body;
- AF363 Colossus — explicitly 7 cm.

This is strong evidence of a reusable Alpha large-body family.

Current classification:
`custom_alpha_7cm_muscle` with release-level verification.

### AF364+ muscular releases

AF364 Red Hulk and nearby Hulk-family releases visually/catalog-wise continue the large-body line, but Brickmen should preserve release-level evidence rather than inferring that every later AF serial uses the same mechanics.

## G (2)

G (2) also demonstrates multiple architecture families.

### GH0303 / GH0304 muscle hybrid

Red Hulk GH0303 and Hulk GH0304 use:
- enlarged sculpted torso;
- muscular arms;
- minifigure-like C-grip hands;
- rectangular separated legs;
- relatively standard/minifigure-derived head language.

This is provisionally:
`custom_g2_muscle_hybrid`.

### GH0348 Thing

GH0348 Thing uses a visually similar enlarged-torso/arm treatment with separated rectangular legs and C-grip hands.

This supports a broader G(2) hybrid family beyond Hulk.

### GH0435 / GH0440 explicit BigFig

G(2) also sells releases explicitly cataloged as BigFig, including:
- GH0435 Thing (Fall of the Fantastic Four) BigFig;
- GH0440 Thing (Future Foundation) BigFig.

GH0440 product imagery is a classic broad BigFig silhouette and is visually distinct from GH0348.

Therefore:
**G(2) is not one body architecture.**

Current classes:
- `custom_g2_muscle_hybrid`
- `compatible_bigfig_unresolved` or future G(2)-specific BigFig architecture after metrology.

## TP

TP sells both ordinary/minifigure-style Thing releases such as TP178 and explicit BigFig releases such as TP349 / TP348.

TP therefore requires release-level architecture classification.

## KDL

KDL K2302 Thing is explicitly listed as 6.5 cm and visually differs from both a normal minifigure and classic Giant/BigFig.

It remains:
`custom_kdl_65mm_large`
until physical metrology establishes whether this is a reusable KDL family.

## Architecture resolver inputs

The resolver should combine:

- maker;
- product code;
- product-code series/range;
- explicit source label;
- known height;
- catalog image;
- silhouette embedding;
- normalized body proportions;
- visible joint/component layout;
- known release cluster;
- physical family evidence.

Maker/code can raise prior probability but cannot force the result.

## Body-family cluster entity

Proposed internal record:

```json
{
  "cluster_id": "alpha_af360_af363_large_body",
  "maker_id": "alpha_toys",
  "release_codes": ["AF360","AF361","AF362","AF363"],
  "architecture_candidate": "custom_alpha_7cm_muscle",
  "cluster_evidence": [
    "same catalog series",
    "shared 7 cm product graphics",
    "matched visible joint/proportion layout"
  ],
  "mechanical_equivalence_status": "physical_validation_pending"
}
```

## Promotion policy

A cluster can reach:

- visual_cluster;
- catalog_cluster;
- physical_component_cluster;
- validated_mechanical_family.

Only the last state allows one release's connector dimensions to be reused for another release without a fresh full metrology pass.

## Why this matters for generation

When the user asks for:

> an Alpha-style custom body

Brickmen must resolve whether they mean:
- Alpha's normal minifigure treatment;
- Alpha's 7 cm muscle body;
- a specific Alpha release architecture.

When the user asks:

> make it like G(2)

the request is still under-specified because G(2) uses at least a muscle-hybrid and BigFig architecture.

The system should retrieve the relevant body family from character/visual context or ask/propose alternatives when necessary.

## Research sources

- HeroBloks Alpha AF336, AF344, AF345, AF361, AF362, AF363
- HeroBloks G(2) GH0303/GH0304/GH0348/GH0440
- HeroBloks TP Thing/BigFig variants
- product images and known height notes
- KDL K2302 height note
