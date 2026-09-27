# Hulk Cross-Architecture Control Study

Research snapshot: 2026-09-27

## Purpose

Hulk is Brickmen's first controlled character for learning how the **same identity** is translated across different figure architectures.

This study deliberately separates four layers:

1. **Character/source identity** — what must remain recognizably Hulk.
2. **FigureArchitecture** — component/joint/scale system.
3. **BodyStyleProfile** — how one architecture/maker distributes volume, relief, print and exaggeration.
4. **Release-specific art/sculpt** — one product's particular interpretation.

The goal is not to choose the "best" Hulk. It is to learn what changes because the **architecture changes**.

## Current control examples

### LEGO standard minifigure — SH0037

Catalog evidence:
- LEGO;
- 2012;
- standard minifigure architecture.

Visual/translation observations:
- Hulk's extreme mass is mostly communicated through decoration and character identity rather than body width;
- standard head/torso/arms/hands/legs remain authoritative;
- muscle anatomy is compressed into torso/face graphics;
- silhouette remains almost completely standard-minifigure;
- purple trousers are communicated through lower-body color/print.

Training lesson:
**when the body architecture is fixed and narrow, identity must move into print, face, color and accessory cues.**

### LEGO Mighty Micros — SH0252

Catalog evidence:
- short-leg Hulk;
- Mighty Micros;
- standard upper minifigure body with short lower-body architecture.

Visual/translation observations:
- proportions become intentionally more caricatured;
- shorter total height does not imply reducing head scale;
- muscle graphics remain simple;
- expression becomes more exaggerated/cartoon-readable.

Training lesson:
**architecture can demand stronger caricature while preserving the same identity-critical color/face/muscle cues.**

### LEGO Giant / BigFig — representative Hulk SH0371 family

Catalog/component evidence:
- Giant arm and hand families;
- Technic 43093 shoulder hardware in representative inventories;
- distinct large torso/lower-body architecture.

Visual/translation observations:
- shoulder width and hand mass carry identity directly in geometry;
- chest/abdomen become molded/sculpted volume instead of relying on flat print;
- hand scale increases dramatically relative to head;
- lower body becomes much wider than standard minifigure;
- graphic decoration becomes supplementary rather than the sole carrier of muscular anatomy.

Training lesson:
**as sculptural capacity increases, identity information migrates from decoration into silhouette and relief.**

### Alpha Toys AF344 / AF345 family

Catalog evidence:
- Alpha Toys;
- AF344 Avengers Hulk and AF345 Comics Hulk;
- 2025 family;
- AF345 public product imagery explicitly presents a 7 cm body with a 4 cm minifigure scale comparison.

Visual inference, pending physical teardown:
- markedly longer legs than LEGO Giant;
- narrower waist relative to chest;
- more human/anatomical chest and abdominal proportions;
- shoulder and arm segmentation is visually more action-figure-like;
- separate-looking hands/wrist seams;
- smaller head-to-body ratio than standard minifigure;
- greater anatomical relief density than LEGO Giant;
- torso tapers toward waist rather than using the blockier Giant massing.

Training lesson:
**Alpha's style is not "scaled BigFig"; it is a different humanoid proportion language with higher anatomical articulation/detail.**

Manufacturing status:
joint graph and connector dimensions unverified.

### G (2) GH0304

Catalog evidence:
- G (2);
- GH0304 Hulk (Avengers);
- distinct catalog release family from both BigFig and Alpha.

Visual inference:
- standard-like minifigure head and rectangular lower legs remain visually dominant;
- torso is significantly widened and sculpted;
- arms are enlarged/muscular but remain closer to an oversized minifigure hybrid than Alpha's 7 cm action-figure-like proportions;
- hands retain a minifigure-like C-grip silhouette;
- body reads as an **oversized-torso muscle hybrid** rather than classic BigFig.

Training lesson:
**intermediate architecture can preserve standard head/lower-body language while moving chest/arms into sculpted mass.**

Physical status:
joint and component compatibility unverified.

### Bigguy Minifigs — Hulk (Ragnarok)

Catalog evidence:
- Bigguy Minifigs;
- 2025 custom Hulk family.

Visual inference:
- very broad shoulder/chest silhouette;
- huge forearms/hands;
- compact head relative to upper-body mass;
- pronounced sculpted pectoral/abdominal structure;
- lower body remains visually more leg-separated/humanoid than classic LEGO Giant;
- visual style favors extreme upper-body exaggeration.

Training lesson:
**maker style can be separated from mechanical architecture: Bigguy's recognizable mass distribution is itself a BodyStyleProfile.**

Mechanical status:
unverified.

### Mr.J Brick × Heart — Hulk / Hulk (Comics)

Catalog evidence:
- Mr.J Brick X Heart;
- 2024 custom Hulk releases.

Visual inference:
- long separated legs;
- broad chest with clearly sculpted abdominal mass;
- oversized forearms/hands;
- strong trapezoid chest-to-waist taper;
- rear sculpt emphasizes large upper-back planes;
- visually distinct from Bigguy even though both occupy a muscular-large category.

Training lesson:
**two similarly sized muscular customs should not be merged if their proportion and relief grammars differ.**

Mechanical status:
unverified.

## Character invariants observed across architectures

These are **candidate Hulk identity features**, not universal immutable rules.

Repeated high-value cues:
- green skin for baseline Hulk incarnations;
- black/dark hair;
- large apparent upper-body strength;
- strong brow/angry or intense expression vocabulary;
- torn or purple trousers in many classic interpretations;
- exposed torso/muscle language;
- larger-than-average body semantics even when a standard minifigure body must encode that only graphically.

The generation system should preserve source-appearance evidence over these generic cues whenever the exact appearance differs.

## Architecture-dependent variables

### Head-to-body ratio

Expected ordering from current visual evidence:
- standard/short minifigure: largest relative head;
- Giant: reduced relative head size;
- G (2) muscle hybrid: minifigure-derived head but widened body;
- Alpha/Bigguy/Mr.J: smaller relative head against more humanized muscular body.

Do not hard-code numeric ratios until canonical images/digital twins are measured.

### Shoulder width

Architecture-specific, not character-specific.

Same Hulk identity can occupy:
- standard torso width;
- Giant broad shoulders;
- intermediate oversized torso;
- highly exaggerated Bigguy/Alpha/Mr.J shoulders.

### Leg strategy

Observed modes:
- standard articulated minifigure legs;
- short static legs;
- Giant dedicated lower body;
- rectangular but lengthened/custom lower legs;
- longer anatomical/action-figure-like custom legs.

### Hand strategy

Observed modes:
- normal minifigure hand;
- Giant oversized dedicated hand;
- minifigure-like enlarged C-grip;
- custom large stylized hand/wrist.

This should be explicitly represented because it changes accessory-generation scale and connector choice.

### Musculature strategy

```
standard minifigure:
mostly printed

Mighty Micros:
simplified printed/caricatured

LEGO Giant:
major sculpted torso/limb volumes + selected print

G(2):
sculpted oversized chest/arms + minifigure-derived graphic language

Alpha:
high sculpt density + anatomical volume + print/paint accents

Bigguy / Mr.J:
high sculpt density with maker-specific proportion grammar
```

This is a core style-transfer feature.

## Proposed architecture-neutral CharacterBodyFeature model

Before selecting an architecture, resolve a character into semantic body features:

```json
{
  "character": "Hulk",
  "source_appearance": "...",
  "identity_features": [
    {"feature": "extreme_upper_body_mass", "importance": "high"},
    {"feature": "torn_trousers", "importance": "appearance_dependent"},
    {"feature": "exposed_musculature", "importance": "high"},
    {"feature": "dark_hair", "importance": "appearance_dependent"}
  ],
  "relative_mass_intent": {
    "shoulders": "very_large",
    "chest": "very_large",
    "waist": "large",
    "hands": "large"
  }
}
```

Then map those semantics through a BodyStyleProfile.

Example:

```
extreme_upper_body_mass
 -> standard minifigure:
      torso muscle print + intense face

 -> LEGO Giant:
      broaden sculpted torso + giant arms/hands

 -> Alpha:
      broad pectoral shell + anatomical deltoids/biceps/forearms + longer legs

 -> G(2):
      widened sculpted torso/arms but retain minifigure-derived head/lower-body cues
```

This is preferable to mapping one mesh directly into another.

## Geometry-vs-decoration translation matrix

| Identity feature | Standard minifig | Giant | Alpha-style | G(2)-style |
|---|---|---|---|---|
| pectoral mass | print | geometry | geometry | geometry |
| abdominal definition | print | shallow/major geometry | stronger geometry | geometry |
| veins/fine texture | usually omit/print sparingly | mostly omit/limited | shallow relief/print depending style | mostly print/relief |
| torn trousers | print/color | print/geometry boundary | geometry edge + print/color | print/color |
| large hands | impossible beyond standard | dedicated Giant geometry | custom geometry | enlarged custom/minifig-like geometry |
| shoulder mass | print implication | geometry | strong geometry | strong geometry |
| back muscles | print or omit | geometry/limited print | pronounced geometry | geometry/print |
| facial intensity | print | print/sculpt context | print/sculpt context | standard-like head print |

This is an initial research hypothesis and should be refined from larger paired datasets.

## Accessory scaling consequence

Accessory scale must be resolved **after architecture**.

A weapon appropriate for:
- standard Hulk;
- Giant Hulk;
- Alpha 7 cm Hulk

cannot be assumed to share one grip size or overall silhouette scale.

Each BodyStyleProfile should define:
- grip connector family;
- hand envelope;
- weapon length factor relative to body height;
- weapon thickness floor;
- visual exaggeration range.

This means the accessory generator depends on `FigureArchitecture`, not only Character.

## Dataset strategy

For each Hulk release:

1. source catalog identity;
2. exact source appearance if resolvable;
3. architecture candidate;
4. canonical front/rear/side views;
5. 2D landmarks;
6. silhouette;
7. segmentation masks;
8. visible joint seams;
9. geometry-vs-print annotations;
10. semantic identity features;
11. confidence/provenance;
12. physical measurements when acquired.

Then create pairwise StyleTransferPairs only when two records represent sufficiently comparable source appearances.

Do **not** pair an MCU Ragnarok Hulk and a comics Hulk as if every difference were architecture-caused.

## First clean pair sets

Highest-value comparisons:

### Pair A
Hulk classic/comics-like:
- standard/minifigure interpretation;
- LEGO Giant comic-like representative;
- Alpha AF345 Comics Hulk;
- Mr.J Comics Hulk.

### Pair B
MCU Avengers:
- official/standard where available;
- official BigFig;
- Alpha AF344 Avengers;
- G (2) GH0304 Avengers.

### Pair C
Red Hulk / Brave New World:
- LEGO BigFig SH1001;
- Alpha AF364;
- G (2) GH0303;
- Bigguy Red Hulk.

These paired families reduce source-appearance confounds.

## Immediate extraction work

- materialize canonical images where repository policy permits;
- segment figures/components;
- compute normalized landmarks;
- manually validate first 20 records;
- create architecture/style embeddings;
- train no model until labels are reviewed;
- test whether simple ratios + image retrieval already separate architectures.

## Sources used in this pass

Catalog/discovery evidence:
- HeroBloks Alpha Toys AF344/AF345/AF346/AF364 records
- HeroBloks G (2) GH0303/GH0304 references
- HeroBloks Bigguy Hulk/Red Hulk records
- HeroBloks Mr.J Brick X Heart Hulk records
- BrickLink Mighty Micros Hulk SH0252 inventory/category
- BrickLink/HeroBloks LEGO Giant Hulk references
- current product/catalog imagery retrieved 2026-09-27

Visual observations in this document are explicitly provisional until canonical image normalization and physical metrology.
