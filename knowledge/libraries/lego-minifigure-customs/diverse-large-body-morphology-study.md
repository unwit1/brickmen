# Diverse Large-Body Morphology Control Study

Research snapshot: 2026-09-27

## Purpose

Prevent Brickmen from learning the incorrect rule:

> non-standard large body = Hulk-shaped muscular humanoid

Large/custom figure systems represent many fundamentally different body grammars.

This study defines a control set that varies:
- mass distribution;
- stature;
- anatomy;
- surface material;
- clothing/armor;
- species;
- limb proportions.

FigureArchitecture remains separate from morphology.

A Blob and Hulk may share a mechanical BigFig architecture while requiring radically different visual-shell parameters.

# Control morphology families

## Muscular humanoid

Characters:
- Hulk;
- Red Hulk;
- Colossus;
- Juggernaut.

Typical semantic traits:
- broad shoulders;
- high chest mass;
- strong chest-to-waist taper;
- large upper arms/forearms;
- large hands;
- visible anatomical muscle groups.

Failure mode:
applying this V-taper to every heavy character.

Existing strongest corpus:
Hulk cross-architecture study.

## Heavy/round humanoid

Characters:
- Blob;
- Kingpin.

Semantic difference from Hulk:
- waist/abdomen remains large;
- low or reversed chest-to-waist taper;
- torso mass projects forward/laterally;
- arms may be massive without bodybuilder anatomy;
- clothing can dominate visual shell.

### Blob

HeroBloks documents Sheng Yuan SY577 and RT062 Blob BigFigs, with RT062 explicitly described as using the same mold as the original Sheng Yuan Blob.

This is valuable because it supplies:
- a stable heavy-round mold family candidate;
- cross-brand same-mold recognition training;
- a morphology that strongly differs from Hulk despite both being "large".

Character semantics:
- extreme abdomen/torso volume;
- smaller relative shoulder taper;
- large limbs;
- relatively compact head;
- soft/fat volume rather than sharply segmented muscle.

### Kingpin

HeroBloks catalogs multiple Kingpin BigFigs, including STUDIOGENESIS, Pogo/Kopf/Xinh and G (2) GH0318 variants.

Character semantics:
- broad/heavy body;
- suit/clothing is identity-critical;
- shoulders can be broad but torso often remains rectangular/round rather than tapered;
- surface is largely cloth/suit rather than exposed anatomical relief.

Style lesson:
large mass does **not** require exposed muscle relief.

## Armored massive humanoid

Characters:
- Thanos;
- Bane;
- Cull Obsidian-like characters.

### Thanos

HeroBloks catalogs broad LEGO/compatible BigFig coverage across:
- LEGO;
- Decool;
- Sheng Yuan;
- Xinh;
- Kopf;
- Pogo;
- others.

Thanos is useful because body mass often sits under:
- chest armor;
- shoulder armor;
- gauntlets;
- helmet/headgear.

The compiler must distinguish:
```
underlying body envelope
vs
armor shell
vs
printed decoration
```

### Bane

Decool/Pogo/LEGO BigFig interpretations provide another armored/equipped massive body.

Identity features can include:
- mask;
- tubes;
- backpack/venom apparatus;
- muscular mass under clothing/armor.

Generation lesson:
external equipment must be modeled as an accessory/overlay system rather than baked into every body architecture.

## Gorilla/primate large body

Character:
- Gorilla Grodd.

LEGO SH0147 provides an official BigFig example.

Critical differences:
- long arms relative to legs;
- forward shoulder placement;
- larger upper torso;
- non-human head/neck relation;
- potentially different hand/foot emphasis.

This control prevents humanoid skeleton assumptions from dominating all Giant-like bodies.

Architecture can still be Giant-related while morphology requires a different skeleton envelope.

## Reptilian/monster large body

Characters:
- Abomination;
- Killer Croc;
- Lizard-like large customs.

### Abomination

HeroBloks lists compatible BigFigs such as Sheng Yuan SY510/SY621 and Alpha Toys AF350 as a different custom interpretation.

Character semantics:
- Hulk-adjacent mass;
- scales/spines/ears or fins depending appearance;
- monster head;
- claw/hand variations;
- less clean human muscle anatomy.

### Killer Croc

Official LEGO specialized Giant component evidence already shows that creature BigFigs can use different hands/wrists/components from Hulk-family Giants.

Lesson:
monster morphology can force **architecture child variants**, not merely style changes.

## Rocky massive humanoid

Character:
- Thing.

Existing Thing control corpus covers:
- standard minifigure;
- Alpha standard-like;
- KDL 6.5 cm;
- TP BigFig;
- G (2) hybrid/BigFig.

Core lesson:
surface relief and mass are both identity-critical, but rock texture must be depth-budgeted for miniature manufacturing.

## Symbiote massive humanoid

Characters:
- Venom;
- Carnage;
- Riot;
- Anti-Venom.

Existing Venom study now covers:
- standard minifigure;
- Alpha 4–4.5 cm muscle hybrid;
- BigFig variants.

Core lesson:
overall stature and upper-body bulk are independent variables.

Organic tendrils/spikes can be:
- shell silhouette;
- separate accessory;
- shallow relief;
- print.

## Tall armored/metal humanoid

Characters:
- Colossus;
- Destroyer-like armor;
- large robotic/armored characters.

Key variables:
- high stature;
- moderate/high mass;
- surface paneling;
- metallic finish;
- less soft anatomical relief.

This control is useful for separating "muscle mass" from "metal body volume."

# Morphology feature vector

Every CharacterBodyFeatureSpec should expose:

### Scale/stature
- stature_class
- target_relative_height

### Mass
- shoulder_mass
- chest_mass
- abdomen_mass
- waist_mass
- pelvis_mass
- thigh_mass
- forearm_mass
- hand_mass

### Shape
- chest_to_waist_taper
- abdomen_projection
- torso_roundness
- back_projection
- shoulder_slope
- limb_length_ratios
- posture/hunch

### Species/anatomy
- humanoid
- primate
- reptilian
- mechanical
- hybrid
- other

### Surface
- exposed_skin_fraction
- fur_fraction
- rock_fraction
- scales_fraction
- armor_fraction
- cloth_fraction
- organic_symbiote_fraction
- metal_fraction

This vector is independent of FigureArchitecture.

# Example contrast

## Hulk
```
chest_mass = very_large
waist_mass = large
taper = high
abdomen_projection = medium
surface = skin
```

## Blob
```
chest_mass = very_large
waist_mass = very_large
taper = low_or_reverse
abdomen_projection = very_large
surface = skin/clothing
```

## Kingpin
```
chest_mass = very_large
waist_mass = very_large
taper = low
surface = suit_cloth
anatomy_relief = low
```

If the model turns all three into Hulk torsos, the style compiler has failed.

# Architecture interaction

The morphology vector compiles differently per architecture.

### Standard minifigure

Body dimensions are mostly locked.

Morphology moves into:
- torso/head print;
- armor/accessory;
- head choice;
- color;
- posture implication.

### Brickmen Broad

Good for:
- Venom Alpha-like mass;
- Bane;
- lighter Kingpin/Blob abstractions;
- armor-heavy standard-height bodies.

### Brickmen MidFig

Good for:
- Hulk/Colossus/Juggernaut;
- larger Thing;
- tall armor bodies;
- selected monster bodies.

### Giant-compatible

Good for:
- extreme mass;
- large creatures;
- Thanos;
- Grodd;
- Blob;
- oversized Thing.

Morphology never chooses architecture automatically; it contributes to architecture candidates.

# Training corpus design

For each morphology family collect:

1. same architecture / different morphology;
2. same character / different architecture;
3. same maker / different architecture;
4. same mold / different decoration where possible.

This supports disentangling:
- architecture;
- morphology;
- maker style;
- character identity;
- surface material.

# Priority benchmark pairs

### Giant architecture morphology test
Use:
- Hulk;
- Thanos;
- Grodd;
- Blob;
- Bane;
- Abomination.

Question:
Can a style model preserve common Giant mechanical language while producing distinct body distributions?

### Brickmen original architecture test
Generate the same six semantics on:
- Brickmen Broad;
- Brickmen MidFig;
- Giant-compatible blank.

Question:
Does each architecture preserve its own grammar while still reflecting morphology?

# Sources / current catalog examples

- Blob RT062 same-mold note: https://www.herobloks.com/figures/32675/rt/rt062/blob-%28bigfig%29
- Blob SY577: https://www.herobloks.com/figures/5395/sheng-yuan/-sy577/blob-%28bigfig%29
- Kingpin STUDIOGENESIS: https://www.herobloks.com/figures/18137/studiogenesis/61505/kingpin-%28bigfig%29
- Kingpin G (2) GH0318 referenced in HeroBloks Kingpin catalog
- Gorilla Grodd LEGO SH0147: https://www.herobloks.com/figures/3516/lego/sh147/gorilla-grodd-%28bigfig%29
- Thanos Sheng Yuan SY576: https://www.herobloks.com/figures/5386
- Bane Decool 0280: https://www.herobloks.com/figures/11144/decool/0280/bane-%28bigfig%29
- Abomination Sheng Yuan SY510: https://www.herobloks.com/figures/5447/sheng-yuan/sy510/abomination-%28bigfig%29
