# Custom BigFig Mold Families and Tooling Lineage

Research snapshot: 2026-09-27

## Core finding

A custom/compatible figure's **maker brand is not necessarily its mold origin**.

Current catalog evidence contains explicit examples where:
- one brand releases a body;
- another brand/factory later remakes or reuses the same mold;
- the decoration, print and seller identity change while the underlying mechanical geometry remains shared.

Therefore Brickmen needs a first-class:

**MoldFamily / ToolingLineage**

between FigureArchitecture and FigureRelease.

## Example — Blob SY577 -> RT062

HeroBloks' RT062 Blob record states:
- Xinh remade the Blob;
- it uses the same mold as the original Sheng Yuan Blob;
- the original Sheng Yuan release was SY577 in 2016;
- the later release changes print details.

This is important because a compatibility measurement on one physically identical mold family may potentially transfer to another release even when the visible brand changes.

However, transfer is allowed only after the mold-lineage claim is corroborated or physical parts match.

## Relationship model

```
FigureArchitecture
  -> MoldFamily
     -> MoldRevision
        -> ComponentRelease
           -> FigureRelease
```

Examples:

```
compatible_bigfig_unresolved
  -> blob_sy577_mold_family
     -> revision_unknown
        -> Sheng Yuan SY577
        -> RT RT062 / Xinh-remade release candidate
```

## Why FigureArchitecture and MoldFamily differ

FigureArchitecture answers:
- component graph;
- joint types;
- broad interface compatibility;
- articulation system.

MoldFamily answers:
- exact or near-exact physical shell/tool geometry;
- cavity/tooling lineage;
- component shapes shared across releases;
- likely identical dimensions where evidence supports it.

Two different molds may implement the same FigureArchitecture.

Example:
multiple compatible BigFig brands may all accept Giant-style hands/shoulder hardware while using distinct torso/arm molds.

## Why BodyStyleProfile and MoldFamily differ

A mold can receive:
- different paint;
- different printing;
- new hair/head attachment;
- different character identity.

Conversely, a maker style can span multiple molds.

Keep:
- mechanics;
- tooling;
- aesthetics;
- release identity

separate.

## Proposed MoldFamily fields

- mold_family_id
- canonical_name
- architecture_id
- manufacturer_or_factory_if_known
- maker_brand_claims
- first_observed_release
- component_scope
- source_mold_labels
- related_release_ids
- revision_ids
- cross_brand_reuse_claims
- distinguishing_geometry
- connector_profile_ids
- physical_equivalence_status
- evidence
- confidence
- valid_from / valid_to

## MoldRevision

Use when:
- hand socket changes;
- head becomes separate;
- torso ornament changes in mold rather than print;
- joint pin changes;
- tooling is repaired/re-cut;
- visible shell changes while architecture remains.

A change in printed graphics alone is **not** a MoldRevision.

## Cross-brand verification workflow

When catalog evidence claims "same mold":

1. link releases as `MOLD_EQUIVALENCE_CANDIDATE`;
2. compare normalized catalog silhouettes;
3. compare identifiable seam/ejector/tooling marks if photos allow;
4. compare component dimensions from physical samples;
5. compare joint fit/force;
6. only then promote to `validated_same_mold_family`.

## BigFig ecosystem discovery

The scan currently shows BigFig releases across many makers and character families.

Representative compatible/maker brands include:
- Decool;
- Sheng Yuan;
- Xinh;
- Lele;
- Kopf;
- Pogo;
- DLP;
- World Minifigures;
- Eagle;
- SX;
- RT;
- STUDIOGENESIS;
- Calypso Customs;
- MinifigureManiacs;
- Mattos Forgery;
- others.

Representative character families:
- Hulk / Red Hulk;
- Thanos;
- Darkseid;
- Bane;
- Gorilla Grodd;
- Killer Croc;
- Thing;
- Venom;
- Juggernaut;
- Abomination;
- Blob;
- Rhino;
- Kingpin;
- Solomon Grundy.

These are useful because repeated character/mold families can reveal:
- direct clone/reissue lineages;
- shared arm/hand tooling;
- specialized creature-body branches;
- maker-specific new bodies.

## Character-specific molds are valuable architecture evidence

Blob is especially useful because its body mass distribution differs from Hulk-style bodies.

Kingpin, Thing and Bane similarly stress different shape regimes:
- obese/round torso;
- rock-textured broad body;
- tall muscular body.

Brickmen should not define "BigFig style" exclusively from Hulk.

## Mold-family recognition

Possible visual features:
- seam line;
- hand silhouette;
- shoulder geometry;
- foot shape;
- head/body separation;
- finger/claw shape;
- back cavity/stud layout;
- tooling marks;
- exact silhouette landmarks.

Use a high-resolution crop/geometry comparison layer after architecture classification.

## Physical sample optimization

Mold lineage lets Brickmen buy fewer redundant samples.

Instead of purchasing every release:
1. cluster releases by likely mold family;
2. acquire one representative;
3. validate shared geometry from photos;
4. acquire a second only where evidence conflicts.

This makes exhaustive custom-body metrology financially practical.

## Training value

Mold families create positive/negative pairs for recognition:

Positive:
same mold, different paint/brand/character decoration.

Hard negative:
same architecture, different mold.

This helps a model learn geometry rather than color/graphics.

## Sources

- RT062 Blob / same mold note: https://www.herobloks.com/figures/32675/rt/rt062/blob-%28bigfig%29
- Sheng Yuan SY577 Blob: https://www.herobloks.com/figures/5395/sheng-yuan/-sy577/blob-%28bigfig%29
- representative BigFig discovery pages across HeroBloks.
