# Official Character and Visual Corpus Ingestion

Research snapshot: 2026-09-24

## Objective

Build an exhaustive, versioned census of official LEGO minifigure visual designs and official LEGO digital minifigure representations, then derive reusable visual grammar without turning copyrighted finished artwork into a redistributable art library.

The canonical data product is not a folder of copied images. It is:
- complete identity/catalog crosswalks;
- source URLs and hashes;
- part/decorated-part inventories;
- derived visual measurements and semantic features;
- era/theme/style profiles;
- source-appearance links;
- local research caches where permitted;
- exact provenance for every derived rule.

## Census scale

As of 2026-09-24:
- BrickLink's Minifigure reference catalog reports 19,250 minifigure catalog items.
- Brickset reports 19,240 minifigs across 53 years and states its displayed minifigure data is courtesy of BrickLink.

These are catalog assembly records, not unique character counts. They include alternate outfits, repeated characters, assembly variants, generic people, micro/alternate figures and other classifications. Agent OS must preserve the catalog record and separately resolve canonical character / incarnation / appearance / outfit design.

Sources:
https://www.bricklink.com/catalogList.asp?catType=M
https://brickset.com/minifigs

## Canonical census sources

### Rebrickable bulk catalog
Use as the bulk machine-readable base because Rebrickable documents that its LEGO catalog covers official Sets/Parts including Minifigs and explicitly instructs bulk users to use downloadable CSV files.

Import:
- minifigs.csv
- inventories.csv
- inventory_minifigs.csv
- inventory_parts.csv
- parts.csv
- part_relationships.csv
- elements.csv
- colors.csv
- sets.csv
- themes.csv

Do not use API pagination for a full refresh.

Source:
https://rebrickable.com/api/v3/docs/

### BrickLink reference catalog
Use for:
- minifigure item numbers;
- catalog categories/themes;
- inventory cross-check;
- decorated part identity;
- variant distinctions;
- current human-readable naming.

Do not equate BrickLink item count with unique characters.

### Brickset
Use for:
- year browsing;
- character-name facets;
- tag facets;
- theme/year sanity checks;
- secondary discovery.

### LEGO.com and official instructions
Use as primary visual/design evidence:
- product pages;
- building instructions;
- designer interviews;
- About Us/history;
- official character hubs;
- Pick a Brick / Create a Minifigure / Minifigure Factory.

### LDraw Official Parts Library
Use as a secondary structured geometry/pattern source where licensing permits. "Official" in LDraw means accepted into the LDraw library, not official LEGO authorship. Keep source authority explicit.

## Official digital/game sources

Digital samples are first-class records with a distinct medium.

Priority families:
- LEGO Island and early official digital minifigure history;
- LEGO Star Wars games;
- LEGO Marvel Super Heroes / Avengers / Super Heroes 2;
- LEGO Batman / DC Super-Villains / Legacy of the Dark Knight;
- LEGO Jurassic World;
- LEGO Harry Potter games;
- LEGO Dimensions;
- LEGO Movie games;
- LEGO NINJAGO games;
- other officially licensed LEGO games containing minifigure-style characters.

Primary page examples:
https://www.lego.com/en-us/themes/star-wars/games/skywalker-saga
https://www.lego.com/en-be/themes/marvel/games/super-heroes
https://www.lego.com/en-us/themes/marvel/games/avengers
https://www.lego.com/en-us/themes/jurassic-world/games/lego-jurassic-world
https://www.lego.com/en-us/aboutus/news/2019/november/lego-dimensions
https://www.lego.com/en-us/aboutus/news/2025/august/lego-batman-legacy-of-the-dark-knight

## OfficialVisualSample

Each physical or digital visual sample should normalize to:

- sample_id
- medium: physical | digital_game | digital_marketing | instruction_art
- authority: lego_primary | licensed_game_primary | structured_catalog | secondary_vector
- catalog_ids
- year
- theme
- subtheme
- figure_form
- character_id
- incarnation_id
- appearance_id
- outfit_design_id
- physical_release_id if applicable
- digital_title/version if applicable
- exact_source_url
- source_timestamp
- image_reference_url
- image_hash if locally cached
- rights_storage_policy
- base_part_colors
- component_part_ids
- decorated_part_ids
- headgear/hair/accessories
- print_surfaces
- expression labels
- derived_feature_record
- style_profile
- confidence
- review_status

## Image handling

Do not commit a mass mirror of LEGO catalog images to Git.

Prefer:
- URL
- stable catalog ID
- source timestamp
- optional checksum of a permitted local cache
- cropped/segmented derived measurements
- vector/landmark primitives where independently derived

High-volume raw visual material belongs in a local research store with provenance and retention policy. GitHub remains canonical for schemas, derived features, decisions, manifests and validated style rules.

## Derived visual feature extraction

### Head
- feature bounding box
- eye centers/separation
- eye dimensions
- pupil/highlight convention
- eyebrow geometry
- mouth geometry
- nose mark
- cheek/dimple/wrinkle/scar/freckle primitives
- beard/moustache/stubble regions
- eyewear/mask regions
- asymmetric marks
- secondary reverse expression
- hair/headwear occlusion

### Torso
- neckline
- layer graph
- major flat color regions
- emblem/icon bounding box
- belt/waist transition
- pocket/fastener count
- fold/wrinkle primitives
- outline hierarchy
- left/right symmetry
- front/back continuation
- side continuation

### Arms
- decoration occurrence
- sleeve boundary
- gauntlet/glove
- shoulder insignia
- tattoo/marking
- left/right asymmetry

### Hips/legs
- hip decoration
- belt continuation
- coat/tunic tails
- knee marker
- boot/shoe transition
- side-leg continuation
- rear-leg continuation

### Global
- number of visual color roles
- base-plastic negative-space ratio
- primary/secondary line-class ratios
- detail density per surface area
- symmetry
- largest identity cue
- number of identity-critical motifs
- physical-size readability score
- print-surface coverage

## Era/theme clustering

Never train one undifferentiated style mean.

At minimum cluster by:
- official_physical_classic_simple
- official_physical_expression_expansion
- official_physical_licensed_early
- official_physical_modern
- official_digital_game

Then learn subprofiles for themes with enough samples:
City/Town; Space; Castle/Fantasy; Pirates; Collectible Minifigures; Star Wars; Marvel; DC/Batman; Harry Potter; NINJAGO; Disney; LOTR; Jurassic; LEGO Movie; DREAMZzz; Fortnite; ONE PIECE; other licensed families.

Theme profile is secondary to the official core grammar.

## Physical/digital correspondence

For each official game character assign:
- exact_physical_match
- physical_release_variant
- digital_only_official_design
- game_embellished_physical_design
- digital_non_minifigure

Rules:
- exact/variant examples can reinforce physical grammar;
- digital-only examples can teach how LEGO/partners translate source characters;
- game embellishments are retained but excluded from print-style statistics unless also observed physically;
- animated mouth deformation, shader/specular behavior, impossible joints and bending are digital behavior features, not decal features.

## Identity resolution

Catalog names are not canonical character identity.

Resolve:
catalog record -> Character -> Incarnation/Continuity -> SourceAppearance -> OutfitDesign -> OfficialVisualSample

A Spider-Man, Batman, Luke Skywalker or Iron Man may have many official visual samples and outfit designs. Keep them separate until evidence shows the decoration represents the same source appearance.

## Full-corpus pipeline

1. ingest structured catalog metadata;
2. crosswalk BrickLink/Rebrickable/Brickset IDs;
3. identify all minifigure/decorated-part records;
4. resolve years/themes/forms;
5. retrieve or reference official imagery;
6. segment figure components;
7. extract measurable primitives;
8. cluster by era/theme/style profile;
9. resolve named characters and appearance variants;
10. add official game/digital-only samples;
11. calculate profile distributions;
12. manually audit outliers;
13. freeze a versioned official baseline;
14. only then admit custom style extensions through the custom-evaluation gate.

## Completeness metrics

Track separately:
- catalog_record_coverage
- inventory_crosswalk_coverage
- image_reference_coverage
- component_segmentation_coverage
- derived_feature_coverage
- character_resolution_coverage
- source_appearance_resolution_coverage
- physical_digital_crosswalk_coverage
- manual_audit_coverage

"Official corpus complete" must never mean merely "we have the names."

## Current technical limitation

The bulk Rebrickable CSV is the correct full-catalog path, but this research session has not materialized the compressed bulk files into the working environment. The schema and source are ready; do not falsely mark full-row ingestion complete until row counts and cross-file integrity checks pass.
