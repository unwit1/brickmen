# Game and Film Visual-Corpus Pipeline

Research snapshot: 2026-09-24

## Why local media extraction matters

Public promotional images are high quality but incomplete. A game can contain hundreds of playable/NPC designs, costume variants, masks and back/side views that never appear on an official web page. A film can show expressions, damage states and alternate costumes absent from physical products.

Therefore:
- public official assets establish provenance and provide clean anchors;
- locally owned game/film media provides exhaustive visual coverage;
- raw assets remain local;
- Git stores manifests, hashes, mappings and derived features.

## TT Games path

TT Games currently provides a broad official catalog of its LEGO titles at:
https://www.ttgames.com/games

Community reverse-engineering documentation shows a repeatable pattern across many TT LEGO games:
- archives contain game assets;
- extraction commonly uses QuickBMS scripts or format-aware tools;
- TTGames Explorer Rebirth can inspect/extract archives, textures and some 3D models;
- textures appear in formats such as DDS/TEX/NXG texture archives/TSH;
- 3D data appears in formats such as GHG/GSC/CMO depending on title.

Community sources:
- https://github.com/AcK77/TTGames-Explorer-Rebirth
- https://github.com/AcK77/TTModding-Docs
- https://github.com/AlubJ/TTGames-LEGO-Documentation
- https://github.com/linterniGamer/Tt-Games-quickbms-scripts
- https://github.com/connorh315/BrickVault

These are not official LEGO tools. Record exact versions/commits and use only with legally obtained local installations.

## Game ingestion stages

1. Verify title/version/platform.
2. Hash original archives/executable for provenance.
3. Extract to local storage with a documented tool/version.
4. Run tools/knowledge/index_ttgames_minifigure_assets.py.
5. Decode texture/model candidates with format-aware tooling.
6. Identify character definition/config files.
7. Resolve internal character names -> canonical Character / Appearance.
8. Render canonical views from models where possible:
   - front
   - back
   - left/right
   - front/rear 3/4
   - head close-up
   - helmet/mask isolated
9. Attach textures to components.
10. Crosswalk against physical releases.
11. Mark digital-only designs.
12. Deduplicate variants and publish coverage metrics.

## High-value game corpus anchors

### LEGO Star Wars: The Skywalker Saga
Official LEGO states >300 playable characters and provides a Profile Icon Encyclopedia with hundreds of minifigure icons. This should be one of the first complete game corpora.

Source:
https://www.lego.com/en-us/themes/star-wars/games/skywalker-saga

### LEGO Marvel's Avengers
Official LEGO states the game contains more than 100 new and returning playable characters and recreates key moments from Avengers and Age of Ultron.

Source:
https://www.lego.com/en-us/themes/marvel/games/avengers

### LEGO Dimensions
Especially valuable because it brings many franchises into one engine and mixes physical toy-tag figures with digital characters.

Source:
https://www.ttgames.com/games/lego-dimensions

### LEGO DC Super-Villains / Marvel Super Heroes 2
Large rosters spanning comic eras and alternate realities; valuable for designs never released physically.

Sources:
https://www.ttgames.com/games/lego-dc-super-villians
https://www.ttgames.com/games/lego-marvel-super-heroes-2

### LEGO Jurassic World
Useful physical/digital/cinematic crosswalk because the game explicitly reimagines four Jurassic films in LEGO form.

Source:
https://www.ttgames.com/games/lego-jurassic-world

## Film pipeline

Use tools/knowledge/extract_lego_film_reference_frames.py on a legally obtained local video file.

Initial extraction deliberately over-samples:
- one frame every N seconds;
- scene-change frames.

Then reduce the corpus using:
- minifigure/person detector;
- character tracking;
- crop extraction;
- perceptual hash;
- visual embeddings;
- costume/expression/view clustering.

The final training corpus should preserve visual diversity, not every duplicate animation frame.

## Frame metadata to add later

A second-stage analyzer should append:
- exact timestamp;
- character identity;
- costume/appearance;
- expression;
- mouth state;
- mask/helmet state;
- camera view;
- occlusion;
- motion blur;
- whether geometry matches a physical release;
- useful surface visibility flags.

## Film priority

Start with theatrical titles:
- The LEGO Movie
- The LEGO Batman Movie
- The LEGO NINJAGO Movie
- The LEGO Movie 2: The Second Part
- Piece by Piece

Then verify/directly ingest minifigure-form direct-to-video films.

Piece by Piece is unusually useful for face diversity: LEGO's official article says the associated Over the Moon set contains more than 30 new minifigure heads.

## Reference-image quality ranking

For style extraction:
A — direct official isolated product/character render
B — official model/texture render generated from local game assets
C — official product photo / instructions
D — clean film/game frame
E — compressed trailer/screenshot
F — secondary catalog/review image

Use lower classes for discovery when necessary, but do not let poor compression teach line thickness or color calibration.

## Failure prevention

- Never infer back/side decoration from a front-only image.
- Never treat movie lighting as print color.
- Never treat shader highlights as printed highlights.
- Never train mouth animation deformation as physical head-print geometry.
- Never assume a game model is physically released.
- Never assume a physical figure's catalog image captures every decorated component.
- Never use one reseller render to establish an official variant.
