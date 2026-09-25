# Historical Minifigure Decal Design Practice

Research snapshot: 2026-09-24

## Purpose

Preserve historically important custom-minifigure decal knowledge as a **production/reference corpus**, not as official LEGO design authority.

The strongest source in this pass is Jared Burks' "Minifig Customization 101: Minifig Decal Design" in *BrickJournal*, Issue 4, Volume 1, Spring 2006. Burks was associated with Kaminoan's Fine Clonier and the Minifig Customization Network.

Source:
https://lego.brandls.info/bj/brickjournal04.pdf

## Why this source matters

The article predates modern UV printing and therefore should not be treated as a current manufacturing standard. It is still valuable because it documents explicit design decisions from a historically important customizer who was intentionally trying to stay visually close to LEGO's design language.

## Quantitative historical template dimensions

The article gives:
- torso: 1.422 cm wide × 1.201 cm tall
- legs: 1.4 cm wide × 1.1 cm tall
- belt: 1.4 cm wide × 0.2 cm tall

Store these as **historical decal template dimensions**, not authoritative mould measurements.

They should be compared against:
- BrickLink Studio reference canvases;
- Mecabricks UV layouts;
- physical caliper measurement;
- printer/jig calibration.

## Historical line-weight guidance

Burks states:
- very fine highlights/folds may go down to about 0.3 pt;
- many printers struggle below about 0.3 pt;
- 0.5–1.0 pt is a useful detail range for his workflow.

This is useful as:
- a historical print-survivability prior;
- a lower-bound candidate for waterslide/home-printer workflows;
- a negative check against AI-generated hairline clutter.

It is **not** a universal modern UV/pad-print minimum. Every current production process still needs empirical coupons.

## Vector-first design

The article strongly recommends vector artwork because:
- curves/lines stay clean when scaled;
- detail is not tied to source pixels;
- designs can be resized and adapted to print limitations.

This independently agrees with the later SVG custom community and the current template-first Agent OS architecture.

## Recognizability-first workflow

The article's core character-design advice is structurally aligned with modern LEGO designer interviews:

1. collect/reference the subject;
2. identify the few features that make the character recognizable;
3. build the design around those features;
4. treat torso/base color as part of the design;
5. add only supporting details.

This makes the article useful as **customizer evidence converging with LEGO's primary large-shape/iconic-feature design guidance**.

Do not use it to claim LEGO copied or endorsed the custom methodology.

## Substrate color as a design layer

For clear media, Burks explicitly designs around the underlying torso color showing through.

This should be represented in generation as:
- substrate/base-plastic color;
- transparent/no-ink regions;
- printed color regions;
- white-underbase regions where a modern process requires them.

The generator should not assume every apparent color must be printed.

## Print testing

Historical guidance:
- print on inexpensive/test material first;
- verify colors because screen colors do not equal print colors;
- verify whether fine details actually survive;
- dark substrates can make clear-media inks unreadable;
- white media/underbase changes the required artwork and edge treatment.

This maps directly to the existing process-calibration and downsample-survivability framework.

## Historical ecosystem sources

### Minifig Customization Network (MCN)
Historically important template/tutorial community. The original site is largely archival/dead and should be recovered through:
- Brickshelf references;
- Eurobricks links;
- BrickJournal;
- Internet Archive / Wayback where legally appropriate.

### Kaminoan's Fine Clonier
Jared Burks' custom decal operation. Historical sources describe:
- waterslide decals;
- white / metallic gold / metallic silver ink capability;
- thousands of combinable designs in later accounts;
- deliberate LEGO-like styling when appropriate.

Use archived material primarily for:
- historical template practice;
- line hierarchy;
- print-process constraints;
- creator/maker history.

### Saber-Scorpion's Lair
Active historical site/news archive documents custom minifig decals dating back into the early 2000s and sales of character-specific sticker/decal sheets.

Use:
- historical custom style evolution;
- decal/product taxonomy;
- long-tail character translation examples.

Do not assume reuse rights from public availability.

### Red Bean Studio
Historically cited in BrickJournal/MCN material for high-quality printing and decal comparisons. Treat as archival research target.

### Brickshelf
Large historical user gallery/image host. Current site reports hundreds of thousands of hosted files and explicitly says copyrights to galleries belong to uploaders.

Use:
- discovery;
- dead-link recovery;
- provenance;
- historical template/scan leads.

Do not bulk-promote user images to a training set without per-item rights.

### Eurobricks Minifig Customisation Workshop
Long-running forum contains:
- decal template indexes;
- custom/decal indexes by theme;
- print/application reviews;
- SVG repository discussions;
- historical maker references.

Use mainly as an index/provenance layer to locate original creators/files/licenses.

## Current custom corpus role

Historical custom material can enter one of:
- custom_style_extension
- custom_reference_only
- custom_negative_example
- production_method_reference

It can never enter:
- official_baseline

## High-value feature extraction from decal sheets

For permitted/approved sheets derive:
- torso boundary
- belt/waist boundary
- leg segmentation
- arm wrap orientation
- head/helmet wrap orientation
- line-class distribution
- symmetry
- base-color/transparent regions
- emblem scale
- edge-safe zones
- printable minimum-feature statistics
- source-reference fidelity labels

Store derived measurements independently from redistribution of the complete sheet.
