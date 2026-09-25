# Official LEGO Minifigure Reference Acquisition Program

Research snapshot: 2026-09-24

## Goal

Build the largest practical provenance-aware visual reference corpus of **official LEGO minifigure-form characters** across:

1. physical LEGO products and promotional material;
2. official/licensed LEGO video games;
3. official LEGO feature/direct-to-video films and other film-form productions;
4. official digital marketing/character art when it represents minifigure-form characters.

The corpus exists to teach Agent OS how official LEGO translates source characters into minifigure geometry, decoration, facial grammar, mould choices, masks/headgear, accessories and color blocking.

The target is not a Git repository full of copied copyrighted images. Git stores manifests, hashes, identifiers, schemas, derived features, source relationships and validated rules. High-volume raw reference imagery belongs in a local research corpus with provenance and retention metadata.

## Fundamental identity model

One character can have many visual samples.

Character
-> Incarnation / continuity
-> SourceAppearance
-> OutfitDesign
-> OfficialVisualSample
-> ReferenceAsset(s)

An OfficialVisualSample is one particular LEGO visual design in one medium/version.

Examples:
- physical Batman 2012 minifigure;
- physical Batman 2017 movie minifigure;
- game-only Batman suit;
- film-only expression or damaged state;
- exact physical figure rendered inside a game.

Do not merge these because the name is the same.

## Acquisition tracks

### A. Physical product census

Primary machine-readable spine:
- Rebrickable bulk LEGO catalog;
- BrickLink minifigure reference catalog and inventories;
- Brickset year/character/tag facets.

As of 2026-09-24:
- BrickLink exposes 19,250 minifigure catalog records.
- Brickset exposes 19,240 minifigure records over 53 years.
- Rebrickable documents that its LEGO Catalog contains all official Sets/Parts data including Minifigs and instructs full-catalog users to use bulk CSV downloads.

Catalog-record count is not unique-character count.

Sources:
- https://www.bricklink.com/catalog.asp
- https://www.bricklink.com/catalogList.asp?catType=M
- https://brickset.com/minifigs
- https://rebrickable.com/api/v3/docs/

#### Rebrickable bulk files

Ingest at minimum:
- minifigs.csv.gz
- inventories.csv.gz
- inventory_minifigs.csv.gz
- inventory_parts.csv.gz
- sets.csv.gz
- themes.csv.gz
- parts.csv.gz
- elements.csv.gz
- colors.csv.gz
- part_relationships.csv.gz

The minifigs dataset provides a stable fig_num plus name, part count and image URL. Inventory relationships connect figure records to sets; set/theme ancestry provides release context.

#### BrickLink enrichment

For every figure:
- BrickLink minifigure ID;
- name/category;
- inventory;
- year/theme;
- catalog image reference(s);
- decorated component identities;
- alternate/replacement relationships where exposed.

BrickLink currently shows both catalog listings and inventory-specific coverage. The inventory view is useful because the whole catalog contains entries that do not appear in normal set inventories, including promotional/corporate figures.

#### Brickset enrichment

Use:
- year facets;
- named-character facets;
- tag facets;
- no-set-inventory lists;
- random/outlier discovery;
- secondary check that catalog joins did not miss unusual records.

Brickset says its displayed minifigure data is courtesy of BrickLink; therefore it is not an independent authority for the underlying figure identity, but its facets are useful.

### B. Official LEGO source imagery

Prefer direct LEGO-hosted assets whenever available:
- product page image galleries;
- set media/press assets;
- building instructions PDFs;
- LEGO Kids character pages;
- official theme character pages;
- official collector-series pages;
- official design articles/interviews;
- Minifigure Factory / Create a Minifigure;
- official catalogs and archived product PDFs.

LEGO's building-instruction service exposes downloadable PDFs for thousands of sets. Those PDFs can provide additional front/back/assembly context even when catalog photography is insufficient.

Store:
- source page URL;
- asset URL;
- asset role;
- publication/set year;
- retrieval date;
- content hash if materialized locally;
- crop/component metadata.

### C. Structured decoration/geometry references

LDraw is a community-run, unofficial system representing official LEGO parts. Its library is exceptionally useful because patterned minifigure components are explicit records and the part-number specification has dedicated minifigure pattern namespaces for themes such as Star Wars, Harry Potter, Middle-earth, CMF, Super Heroes and others.

Use LDraw for:
- patterned head/torso/hip/leg/arm identification;
- reusable 3D geometry;
- vector-like pattern geometry where present;
- front/side/back surface study;
- mould-vs-decoration separation.

Never label LDraw's "Official" status as LEGO authorship or LEGO approval. It means accepted into the LDraw Official Parts Library.

Sources:
- https://library.ldraw.org/
- https://www.ldraw.org/part-number-spec.html
- https://www.ldraw.org/article/512.html

### D. Official/licensed game corpus

A game is a separate medium, not a substitute for physical evidence.

Current primary title inventory sources:
- LEGO Games: https://www.lego.com/en-us/games
- TT Games catalog: https://www.ttgames.com/games

TT Games' current catalog spans the major minifigure-based titles from LEGO Star Wars: The Video Game (2005) through current releases. The TT catalog should be the canonical title inventory for TT-developed games; LEGO theme pages provide additional current/legacy references.

Important official game families include:
- LEGO Star Wars series;
- LEGO Indiana Jones;
- LEGO Batman / DC;
- LEGO Harry Potter;
- LEGO Pirates of the Caribbean;
- LEGO Lord of the Rings / Hobbit;
- LEGO Marvel Super Heroes / Avengers;
- LEGO City Undercover;
- LEGO Dimensions;
- LEGO Jurassic World;
- LEGO NINJAGO titles;
- LEGO Worlds;
- LEGO Incredibles;
- LEGO Movie / Movie 2 games;
- newer LEGO Batman titles.

LEGO's 2021 NINJAGO anniversary article separately confirms playable NINJAGO appearances in LEGO Battles: NINJAGO, Nindroids, Shadow of Ronin, Dimensions, Worlds, The LEGO NINJAGO Movie Video Game, Brawls and Legacy: Heroes Unboxed.

#### Official web assets

Whenever available, acquire:
- official character icons;
- roster images;
- promotional renders;
- screenshots;
- trailers;
- downloadable profile icons.

LEGO Star Wars: The Skywalker Saga is a particularly strong reference source because the official LEGO page says the game has more than 300 playable characters and hosts a Profile Icon Encyclopedia containing hundreds of minifigure representations.

#### Local game-asset extraction

For exhaustive game coverage, web screenshots are not enough. The durable strategy is to index assets from a legally obtained local PC installation.

TT Games community tooling documents that games commonly store assets in archives and that extracted data can include:
- textures (.dds, .tex, .nxg_textures, .tsh);
- models (.ghg, .gsc, .cmo);
- configuration/text files that reveal character names and asset relationships.

Useful external research tools:
- TTGames Explorer Rebirth
- TTGames-LEGO-Documentation / TTModding docs
- QuickBMS TT Games scripts
- BrickVault for several archive formats, including Skywalker Saga with the game's own Oodle library where required
- BacTSH for texture sheets in supported DX11-era titles

These tools are external community tooling, not official LEGO/TT software. Preserve their exact version and source commit in provenance.

Do not distribute extracted copyrighted game assets through Git. Store them in local corpus storage with:
- game title/version/platform;
- executable/archive hashes;
- extraction tool/version;
- original internal path;
- asset hash;
- character mapping;
- render/texture role.

#### Game sample classification

Every game visual sample must be classified:
- exact_physical_match
- physical_release_variant
- digital_only_official_design
- game_embellished_physical_design
- non_minifigure_character

Digital-only variants are extremely useful for character translation, but shader lighting, animated mouth deformation, flexible articulation and impossible geometry do not enter physical-print statistics.

### E. Film corpus

Film references teach:
- official cinematic interpretation of minifigures;
- expression changes and mouth/eyebrow animation;
- camera-angle behavior;
- damaged/alternate states;
- costumes or characters never sold physically;
- mould and accessory decisions used in animated production.

Primary theatrical anchors:
- The LEGO Movie (2014)
- The LEGO Batman Movie (2017)
- The LEGO NINJAGO Movie (2017)
- The LEGO Movie 2: The Second Part (2019)
- Piece by Piece (2024)

The official LEGO Piece by Piece material describes the feature as a LEGO-brick-style animated biopic and the associated set introduced more than 30 new minifigure heads, making it especially valuable for face/reference diversity.

Broader film discovery should include direct-to-video LEGO films that use standard minifigure/minidoll geometry, including selected DC, Scooby-Doo and other licensed productions. A secondary filmography may seed candidates, but each production must be verified against a primary/rights-holder source before canonical promotion.

Exclude BIONICLE/Hero Factory or other non-minifigure character systems from the standard minifigure training baseline; they may be stored in separate form profiles.

#### Film acquisition strategy

Best source order:
1. official LEGO/rights-holder press stills and asset packs;
2. official trailers/character clips;
3. product/film tie-in pages;
4. locally extracted frames from a legally obtained copy for exhaustive scene coverage.

Raw film frames remain local. Git stores:
- title/version;
- frame timestamp;
- frame hash;
- source-medium provenance;
- character labels;
- crop coordinates;
- visual-state labels.

### F. Film/game frame selection

Do not train on every raw frame. That would massively overweight repeated poses and compression artifacts.

Instead:
1. scene-change sample;
2. detect minifigure-form characters;
3. crop/track characters;
4. perceptual-hash deduplicate near-identical frames;
5. cluster by costume/expression/pose;
6. preserve representative front, 3/4, profile, back, expression and action states;
7. retain rare masks/headgear and side/back views at higher priority.

This turns millions of frames into a high-information reference corpus without losing unique visual states.

## ReferenceAsset schema

Every image/asset record needs:

- reference_asset_id
- sample_id
- medium: physical_photo | physical_render | instruction | digital_game_render | game_texture | game_model | film_frame | press_still | promotional_art
- authority
- source_url or local_source_id
- source_title
- game_or_film_title
- game_version/platform or film_release
- internal_asset_path if extracted
- timestamp/frame_number if video
- view: front | rear | left | right | front_3q | rear_3q | top | bottom | unknown
- crop_bbox
- character_id
- appearance_id
- outfit_design_id
- component_ids
- expression
- mask/headgear state
- physical_correspondence
- sha256
- perceptual_hash
- width
- height
- transparency
- materialized_locally
- storage_policy
- retrieved_at
- confidence

## Coverage targets

For every physical figure record:
- >=1 catalog/reference image
- set/theme membership
- component inventory when available
- decorated component mapping
- year/release context

For each official visual design:
- front view preferred
- back view whenever decoration exists
- left/right view where arm/leg/headgear print exists
- close head crop
- close torso crop
- masks/headgear isolated where possible

For game-only/film-only designs:
- one clean neutral reference if possible
- multiple views when the model appears in 3D
- neutral/expression variants
- texture/model source if locally extractable
- explicit physical counterpart or "none known"

## Deduplication

Use multiple identities:
- cryptographic hash for exact byte duplicates;
- perceptual hash for resized/recompressed duplicates;
- visual embedding similarity for near-duplicates;
- same character/appearance/outfit but different source is not necessarily a duplicate;
- same artwork hosted at multiple URLs should resolve to one ReferenceAsset with multiple SourceOccurrence rows.

## Training-set weighting

Do not weight sources equally.

Suggested style authority:
1. official physical product/reference imagery;
2. official LEGO primary digital renders that represent physical parts accurately;
3. official/licensed game assets;
4. official film frames;
5. LDraw-derived geometry/pattern reconstructions;
6. approved custom style extensions.

Suggested identity authority:
1. exact source character reference;
2. official physical/digital LEGO version of exact appearance;
3. official related appearances;
4. approved custom gap-fill.

This prevents high-volume film/game screenshots from overwhelming the physical minifigure style baseline.

## Local storage layout

Recommended:

.agent-local/
  lego-minifigure-corpus/
    catalog/
      rebrickable/
      bricklink/
      brickset/
      ldraw/
    physical/
      raw/
      normalized/
      crops/
    games/
      <game-id>/
        provenance.json
        extracted/
        textures/
        models/
        renders/
        crops/
    films/
      <film-id>/
        provenance.json
        frames/
        crops/
    features/
    indexes/
      references.sqlite3
      embeddings/
      phash/
    manifests/

Git should contain only:
- schemas
- source registries
- importers
- normalized metadata snapshots
- derived style statistics
- validation reports
- low-volume legally safe examples where appropriate

## Definition of "trained on every official minifigure"

A claim of complete coverage requires:
- every structured physical minifigure catalog record reconciled;
- every official game title in scope enumerated;
- every playable/NPC minifigure-form character design indexed;
- every official film in scope enumerated;
- unique film/game-only visual designs identified;
- image/model/texture or frame references attached;
- duplicates and physical counterparts resolved;
- coverage metrics published;
- unresolved records explicitly listed.

Until those conditions are met, report exact coverage rather than saying "all."
