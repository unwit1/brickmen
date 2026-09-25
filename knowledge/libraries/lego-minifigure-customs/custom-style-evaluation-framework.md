# Custom Minifigure Style Evaluation Framework

Research snapshot: 2026-09-24

## Gate

Custom designs are not allowed to teach the canonical official baseline until the relevant official era/theme profile has sufficient coverage.

Customs are evaluated after the official corpus establishes what "official" means for the requested target. A custom can contribute a useful style-extension pattern, but it can never become evidence that LEGO itself uses that pattern.

## Purpose

Rate custom figures, decal sheets and printed parts along independent axes so Agent OS can identify work that helps generation become:
1. more faithful to a source character;
2. more plausibly official LEGO;
3. more technically usable as template artwork.

Do not collapse these into one score.

## Axis A — Reference fidelity (0–100)

### Source-version correctness — 15
Does the custom target the correct comic issue, movie costume, episode, game skin, artwork version or other intended appearance?

### Defining color blocks — 15
Are the largest color regions and their proportions faithful to the source?

### Iconic symbols and motifs — 15
Are emblems, stripes, armor shapes, masks, logos and other identity-critical cues correct?

### Garment / armor topology — 15
Are layers, closures, panels, belts, boots, gloves and major seams structurally faithful?

### Face identity / expression — 15
Does it preserve the character's defining face/hair/expression cues within minifigure abstraction?

### Part / silhouette choice — 10
Do the selected official/custom moulds produce the closest LEGO-scale silhouette?

### Cross-surface fidelity — 10
Are front/back/arm/leg/helmet details consistent with the same source?

### Color/material relationships — 5
Are metallic, cloth, transparent, armored, fabric and skin/hair relationships represented appropriately?

## Axis B — Official LEGO likeness (0–100)

### Large-shape composition — 15
Would the design remain readable if most micro-detail were removed?

### Feature prioritization — 15
Does it choose the same kind of high-information cues an official graphic designer would likely prioritize?

### Physical-scale readability — 15
Does the artwork survive at actual minifigure size?

### Facial grammar — 15
Do eyes, brows, mouth, facial hair, wrinkles/scars and negative space fit the relevant official profile?

### Line hierarchy — 10
Are defining lines, structural lines and micro-detail visually differentiated rather than equally heavy?

### Detail discipline — 10
Is detail present because it communicates character, rather than because blank space was available?

### Color / negative-space use — 5
Does the base plastic and official-like palette carry part of the design?

### Surface / geometry logic — 5
Does artwork respect head curvature, torso shape, arm curvature and leg segmentation?

### Part/mould plausibility — 5
Would the component choices plausibly exist in the LEGO system or as a deliberate new mould?

### Era/theme coherence — 5
Does it fit the expected official detail language of the target release era/theme?

## Axis C — Template / production quality (0–100)

### Correct surface mapping — 20
Front/back/side/wrap pieces correspond to real printable surfaces.

### Registration tolerance — 15
Critical features do not rely on impossible perfect alignment across joints/seams.

### Minimum feature survivability — 15
Lines, gaps and tiny fills remain printable at target process/scale.

### Vector/edge cleanliness — 15
No raster noise, accidental halos, jagged edges or AI texture.

### Color/opacity planning — 10
Artwork anticipates substrate color, white underbase and opaque-vs-transparent behavior.

### Wrap continuity — 10
Side/arm/leg/helmet transitions align where intended.

### Separation of process layers — 10
CMYK/spot color, white, varnish/clear, primer/mask and cut/registration information are separable.

### Sheet usability — 5
Parts are clearly identified, oriented and grouped for application/production.

## Admission classes

### official_baseline
Reserved exclusively for official LEGO physical/digital evidence. Custom work can never receive this class.

### custom_style_extension
A custom-derived pattern may enter retrieval if:
- source provenance is known;
- reference fidelity is strong;
- official-likeness is strong for the target profile;
- the pattern contributes something absent or sparse in the official corpus;
- the derived lesson can be expressed abstractly without copying the finished design.

Initial calibration threshold:
- official_likeness >= 80;
- reference_fidelity >= 75;
- no critical production failure for template use.

Thresholds are provisional and must be recalibrated after scoring a large official/control set.

### custom_reference_only
Useful for character research or source identification but not style training.

### custom_negative_example
Retain explicit failure patterns such as excessive anatomical realism, over-dense line work, incorrect facial scale, noisy gradients, impossible wraps or reference inaccuracies.

## What can be learned from an accepted custom

Allowed derived lessons:
- useful decomposition of an unusual costume into LEGO-scale regions;
- successful treatment of an obscure garment or armor topology;
- clever but official-compatible wrap continuation;
- template organization;
- a new expression construction that still matches official feature distributions;
- a source-appearance identification;
- production/process technique.

Do not copy:
- a customizer's complete proprietary artwork;
- a distinctive finished decal verbatim;
- watermarks/logos;
- source-specific line paths when an abstract feature description is sufficient.

## Bob's Customs and decal-sheet references

Bob's Customs is a valuable historical reference for template organization and broad Marvel character coverage. Current discovery evidence includes HeroBloks records, Flickr traces, Mecabricks attribution and social/archive references. Direct primary-site availability is inconsistent, so every sheet must retain exact provenance and confidence.

Use Bob's and similar decal archives primarily to learn:
- how torso/hip/leg/arm/head regions are separated;
- how a full character is decomposed into printable flat components;
- wrap orientation;
- sheet labeling;
- how base part color is assumed.

Do not admit a Bob's design into the style-extension corpus until it has been scored against the corresponding official era/theme profile and source reference.

## Evaluation workflow

1. identify the exact source appearance the custom claims to represent;
2. retrieve authoritative source-reference imagery;
3. identify the nearest official LEGO style profile;
4. identify all official versions of the same or analogous character/costume;
5. score reference fidelity;
6. score official likeness;
7. score template/production quality if applicable;
8. list divergences from official grammar;
9. extract only novel, reusable lessons;
10. classify baseline/extension/reference-only/negative;
11. preserve source and reviewer confidence.

## Generation use

When generating a new character:
- official baseline has highest style weight;
- exact source reference has highest identity weight;
- approved custom extensions may fill gaps where official examples are sparse;
- custom examples must never outvote a well-covered official pattern.

Recommended retrieval weighting:
official exact character/version > official analogous character/theme > official era-wide grammar > approved custom extension > unscored custom reference.
