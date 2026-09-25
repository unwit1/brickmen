# Official Minifigure Training Corpus Design

Research snapshot: 2026-09-24

## Core objective

The desired model behavior is not "memorize LEGO character artwork." It is:

SOURCE CHARACTER / COSTUME / PERSON
-> identify high-value visual cues
-> choose minifigure-form parts/mould strategy
-> translate colors/shapes/details through official LEGO visual grammar
-> output clean template-ready minifigure decoration and, where needed, new part concepts.

The best training data therefore contains **translation pairs**, not merely isolated minifigure pictures.

## Three complementary datasets

### 1. Official-style corpus

Input:
official LEGO minifigure visual sample.

Learns:
- face geometry;
- line hierarchy;
- detail density;
- use of negative space;
- print coverage;
- mould-vs-print responsibility;
- color-role relationships;
- era/theme differences.

Primary style weight comes from physical minifigures.

### 2. Source-to-LEGO translation corpus

Pair:
original source appearance -> official LEGO interpretation.

Examples:
- film costume -> physical minifigure;
- comic costume -> physical/game minifigure;
- game skin -> physical LEGO Fortnite minifigure;
- actor/real person -> official LEGO minifigure;
- Star Wars film frame -> physical/game LEGO character.

This is the highest-value dataset for the user's actual goal because it teaches what LEGO chooses to preserve, simplify, move into a mould, omit, recolor or exaggerate.

### 3. Official digital/film extension corpus

Contains official LEGO game/film visual samples that may not exist physically.

Learns:
- official translation decisions for unproduced characters;
- additional expressions;
- rare masks/helmets;
- back/side costume information;
- alternate outfits.

Digital/film samples are down-weighted for physical-print style when they contain shader, animation or geometry effects that cannot exist physically.

## TranslationPair entity

Fields:
- translation_pair_id
- source_appearance_id
- source_reference_asset_ids
- lego_sample_ids
- target_medium
- exactness: exact_same_appearance | close_adaptation | composite | uncertain
- source_silhouette_features
- source_color_roles
- source_identity_cues
- lego_part_choices
- lego_color_roles
- lego_print_regions
- lego_mould_newness
- preserved_features
- simplified_features
- omitted_features
- moved_to_mould_features
- moved_to_accessory_features
- exaggerated_features
- expression_translation
- mask_translation_route
- confidence
- provenance
- reviewer_status

## Pair quality

A translation pair is strongest when:
- the original source appearance is exact and well dated;
- the LEGO target is an official physical release;
- official documentation confirms the intended source;
- front/back/side references exist for the LEGO sample;
- the source itself has equivalent views.

Lower confidence:
- character/version inferred from costume resemblance;
- game-only LEGO target;
- source reference is fan-compiled rather than primary;
- LEGO design combines multiple source appearances.

Do not force ambiguous samples into exact pairs.

## Image normalization

Never destructively normalize the canonical raw image.

Create derived views:
- raw source
- color-managed normalized copy
- transparent/background-removed character crop
- head crop
- torso crop
- left/right arm crop
- hips/legs crop
- headgear/mask crop
- silhouette mask
- semantic part mask
- line-art extraction
- edge map
- optional depth/normal from structured 3D sources.

Every derived image points back to the raw ReferenceAsset and transform parameters.

## View labels

Use:
front
rear
left
right
front_3q_left
front_3q_right
rear_3q_left
rear_3q_right
top
bottom
unknown

For style statistics, front orthographic/near-orthographic samples should receive higher confidence than strong-perspective poses.

## Quality score

Per image derive:
- source authority
- resolution
- compression
- occlusion
- motion blur
- perspective distortion
- lighting neutrality
- background cleanliness
- component visibility
- view usefulness
- exact identity confidence

Never estimate print-line width or calibrated color from heavily compressed film/game frames.

## Duplicate control

Physical product media can repeat the same official render across LEGO, BrickLink, Rebrickable, Brickset, retailers and reviews.

Deduplicate at three levels:
- SHA-256 exact duplicate;
- perceptual hash near-duplicate;
- visual embedding duplicate/alternate crop.

Retain multiple SourceOccurrence records for provenance even if they resolve to the same canonical ReferenceAsset.

## Character-frequency control

Batman, Spider-Man, Harry Potter, Luke Skywalker and NINJAGO characters have many more samples than obscure characters. Uncontrolled training would make their specific visual vocabulary dominate the model.

Sampling should balance:
- style profile;
- year/era;
- theme;
- component type;
- expression family;
- gender presentation;
- skin/head color system;
- mask/headgear class;
- simple/dense decoration;
- common/rare character.

Character identity itself should not become the weighting axis for learning global style.

## Medium weights

Initial style-learning priors, subject to eval calibration:
- official physical isolated render/photo: 1.00
- official physical instruction/secondary official image: 0.90
- LDraw reconstruction validated against physical sample: 0.75
- exact physical match in official game: 0.70
- official digital-only game design: 0.55
- clean official film frame: 0.45
- compressed promotional/trailer frame: 0.30

These are starting priors, not permanent truth. Evals should optimize them.

For source-to-LEGO identity translation, exact game/film designs can receive much higher weight than their style-learning weight.

## Split strategy

Do not randomly split individual images from the same figure across train/test; that leaks the answer.

Use grouped splits by:
- OutfitDesign or OfficialVisualSample;
- and a harder leave-character-family-out benchmark.

Recommended evaluation sets:
1. held-out images of known figures — checks view consistency;
2. held-out official outfit designs — checks style generalization;
3. held-out characters — checks source-to-LEGO translation;
4. held-out themes — checks whether global grammar generalizes;
5. held-out masks/headgear — checks print-vs-new-part decisions.

## Retrieval plus training

A fully fine-tuned model should still use retrieval.

At generation time retrieve:
- exact source appearance;
- closest official physical analogues;
- same mask/garment/armor topology;
- same era/theme style profile;
- accepted custom extensions only when official coverage is sparse.

Training teaches the transformation grammar. Retrieval supplies exact precedent.

## Template-target supervision

The ideal target is not only a beauty render.

For each sufficiently resolved official design create:
- canonical rendered figure views;
- flattened/approximated head graphics;
- torso-front/back target regions;
- arm/leg regions;
- component masks;
- part IDs;
- decoration presence/absence labels.

Where true flat factory artwork is unavailable, derived flat art must be labeled reconstructed and never mistaken for original production artwork.

## Mask/headgear supervision

Each pair should carry:
- silhouette dependence
- graphic dependence
- expression dependence
- existing-part match
- new-part necessity
- head-print region
- helmet-print region
- attachment/accessory role

This directly teaches the earlier mask decision framework rather than relying on prompt instructions alone.

## Copyright/provenance storage

Raw official product/game/film images are research/training inputs and should remain in controlled local corpus storage. Git should contain metadata, hashes, source URLs, derived numerical features, schemas and validation reports rather than a wholesale mirrored media library.

LDraw data is governed by its own contributor licenses and requires attribution. Preserve each file's license metadata.

## Definition of a strong generation benchmark

Given an unseen source character/reference, the model should:
1. choose a plausible minifigure part/mould strategy;
2. preserve the correct version-specific identity cues;
3. match official face/line/detail distributions;
4. avoid excessive custom-style noise;
5. produce physically plausible flat templates;
6. decide correctly between print, existing headgear and new 3D part;
7. remain recognizable at real minifigure size.

The benchmark should be scored independently for reference fidelity, official LEGO likeness and production feasibility.
