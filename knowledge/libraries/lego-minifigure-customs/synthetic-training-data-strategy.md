# Synthetic Training Data for Minifigure Vision and Translation

Research snapshot: 2026-09-24

## Purpose

Use structured, licensed LEGO-compatible geometry and pattern reconstructions to create large, perfectly labeled synthetic datasets for:
- figure/component detection;
- segmentation;
- view classification;
- part recognition;
- mask/headgear silhouette learning;
- geometry conditioning;
- line/coverage statistics;
- canonical-view retrieval;
- source-to-minifigure structural planning.

Synthetic data is **not** a substitute for official physical visual evidence. It is a scalable supervision layer.

## Strongest current foundation: LDraw

LDraw is unusually useful because:
- part geometry is structured;
- patterned parts are explicit files;
- minifigure heads/torsos/legs/headgear are represented independently;
- files carry machine-readable license headers;
- current contributor policy uses CC BY 4.0 or optionally CC0;
- legacy CA-approved parts can be CC BY 2.0;
- the library permits copying, derivatives and commercial use subject to attribution for the applicable CC BY files.

Important:
LDraw is a community reconstruction system, not LEGO-authored CAD or factory artwork.

Primary:
https://www.ldraw.org/docs-main/licenses/ldraw-org-contributor-agreement.html
https://library.ldraw.org/documentation/policies-and-procedures/parts-library-policies-and-faq

## Licensing must remain per file

Do not collapse the entire library to one license string.

The LDraw header can contain:
- CC BY 4.0
- CC BY 2.0 + CC BY 4.0
- CC0
- older/deprecated statements on historical material

The existing LDraw indexer already retains each file's license field. Synthetic descendants must carry the source part IDs/license attribution.

## Why synthetic + real is justified

The 2023 Brickognize research gives a strong methodology precedent:
- 1,000 synthetic scenes × 20 renders = >20,000 synthetic images;
- >1.1 million annotated brick instances;
- synthetic training dramatically outperformed training on only a handful of real images;
- few-shot fine-tuning on about 20 controlled real images further closed the synthetic-to-real gap;
- controlled and uncontrolled evaluation reached high segmentation accuracy.

This study is about bricks, not minifigure style, so its numeric performance must not be transferred directly. The relevant lesson is architectural:

**structured synthetic pretraining + small, carefully controlled real capture set can outperform scarce real-only supervision.**

Primary:
https://www.mdpi.com/1424-8220/23/4/1898

## Separate synthetic-data purposes

### Geometry/vision synthetic corpus

Safe target tasks:
- detect standard minifigure vs components;
- segment head/torso/hips/arms/legs/headgear;
- identify view angle;
- estimate pose;
- retrieve geometrically similar headgear;
- learn occlusion;
- learn camera normalization.

For these tasks, vary:
- longitude/yaw;
- latitude/elevation;
- camera distance;
- focal length / FOV;
- lighting direction/strength;
- background;
- color;
- pose;
- accessory occupancy;
- occlusion.

Ground truth is exact because it comes from the scene.

### Official-style patterned-part render corpus

Render LDraw patterned parts in canonical views to derive:
- approximate color-region masks;
- pattern edge geometry;
- symmetry;
- coverage;
- view-conditioned appearance.

Authority remains `community_structured`, not `lego_primary`.

Validate important pattern records against physical/catalog evidence before they influence official-style statistics.

### Full assembled minifigure synthetic corpus

Assemble minifigures from resolved component inventories and exact canonical transforms.

Output:
- RGB
- transparent RGB
- depth
- normal
- part-ID mask
- component-class mask
- silhouette
- camera transform
- light configuration
- source part IDs/licenses

This becomes high-volume detection/segmentation/view supervision.

### Domain-randomized corpus

For robustness:
- random neutral backgrounds;
- realistic tabletop/background textures with compatible licenses;
- different light temperature/intensity;
- blur/compression;
- partial occlusion;
- scale variation;
- image noise;
- camera tilt.

Keep a clean canonical set separate from randomized training renders.

## LDView rendering

LDView supports command-line snapshot creation with:
- `-SaveSnapshot`
- width/height
- transparent PNG
- auto-crop
- zoom-to-fit
- default latitude/longitude
- FOV/camera settings.

LDView documentation explicitly supports `DefaultLatitude`, `DefaultLongitude`, `DefaultLatLong`, view matrices, transparent snapshots and batch snapshots.

Example community AI-training usage has used:
- `-DefaultLatLong`
- `-SaveAlpha=1`
- `-SaveZoomToFit=1`
- `-LineSmoothing`
- custom light vector

Primary/technical references:
https://trevorsandy.github.io/lpub3d/assets/docs/ldview/Help.html
https://forums.ldraw.org/thread-24721-newpost.html

For a canonical multi-view dataset, **do not auto-crop independently per angle if consistent apparent scale is required**. Use a fixed camera/zoom after fitting the largest silhouette envelope.

## Canonical view grid

Recommended clean grid:
- front: lat 0, lon 0
- front-right 3/4: lat 0, lon 45
- right: lat 0, lon 90
- rear-right 3/4: lat 0, lon 135
- rear: lat 0, lon 180
- rear-left 3/4: lat 0, lon 225
- left: lat 0, lon 270
- front-left 3/4: lat 0, lon 315
- elevated variants at +20 or +30 degrees where headgear geometry matters
- top/bottom only for component geometry tasks

Coordinate conventions must be verified against the actual LDraw assembly orientation before freezing labels.

## Edge-lines caveat

For image-recognition synthetic data, LDraw community guidance recommends disabling artificial renderer edge lines when they do not exist in the physical photography, because otherwise the network can learn a synthetic-only cue.

For **LEGO visual-style research**, maintain two parallel renders:
- physical-like render with renderer edge lines disabled;
- structural line render with edge lines enabled.

Never confuse renderer outline with printed minifigure linework.

## Synthetic face corpus

Patterned LDraw heads can produce a consistent head-render dataset:
- same projection;
- same lighting;
- same yellow/flesh/base material family;
- exact orientation;
- front/reverse sides.

Useful for:
- landmark detection bootstrapping;
- expression clustering;
- dual-sided head detection;
- eyeglass/facial-hair segmentation.

The actual emotional label must come from catalog semantics, academic ratings, or human annotation, not inferred only from LDraw geometry.

## Real-capture bridge

For each synthetic target family, collect a small controlled physical set:
- same angle distribution;
- known part IDs;
- controlled lighting;
- labeled masks/components;
- a few uncontrolled backgrounds.

Use this to:
- evaluate synthetic-to-real gap;
- fine-tune detection/segmentation;
- calibrate renderer/material assumptions.

This follows the broad synthetic+few-shot-real methodology demonstrated by Brickognize.

## Do not use restricted digital assets as synthetic-training shortcuts

### Unity LEGO Microgame

The Microgame historically provided official LEGO digital elements and four example minifig prefabs (Astronaut, Adventurer, Pirate, Pizza Boy).

However, current Unity Terms explicitly prohibit using any Offering or data derived/resulting from an Offering for ML/AI training, validation or development without prior authorization.

Therefore:
- use public documentation as research context;
- do not ingest Microgame assets into the default ML training pipeline;
- only enable if a project-specific license/authorization clearly permits it.

Current Unity terms:
https://unity.com/legal/terms-of-service

### Fortnite / UEFN LEGO assets

UEFN documents hundreds of LEGO Styles and is valuable for identifying exact same-character transformation pairs.

But LEGO Brand Rules state that standalone LEGO assets cannot be sold/redistributed or made extractable, and other IP partner rules can explicitly prohibit copying/recording/extracting assets outside the permitted environment.

Therefore:
- use official web pages and metadata to identify/label pairs;
- treat UEFN as a reference/verification environment unless the applicable agreements clearly authorize ML training;
- do not design an extraction pipeline that violates brand/IP rules.

Primary:
https://dev.epicgames.com/documentation/fortnite/lego-brand-rules-in-fortnite
https://legal.epicgames.com/epicgames/uefn

## Recommended synthetic training stack

1. LDraw library with per-file licensing
2. resolved physical minifigure component inventories
3. canonical LDraw minifigure assembly transforms
4. LDView for fast deterministic canonical render generation
5. Blender/POV-Ray only where richer domain randomization or extra render passes are required
6. controlled physical photography for synthetic-to-real correction
7. grouped train/eval splits by physical design/outfit

## Evaluation

Synthetic corpus is successful only if it improves held-out real official samples.

Measure:
- minifigure detection AP
- component segmentation IoU
- view classification
- headgear family retrieval
- pose keypoint error
- synthetic->real nearest-neighbor quality
- calibration on real photographs

Do not optimize only on synthetic validation images.
