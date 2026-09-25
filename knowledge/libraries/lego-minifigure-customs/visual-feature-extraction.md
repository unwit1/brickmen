# Official Minifigure Visual Feature Extraction

Research snapshot: 2026-09-24

## Purpose

Convert the official reference corpus into measurable visual grammar rather than treating images as opaque examples.

The feature system has two complementary layers:

1. deterministic features that are auditable and interpretable;
2. learned visual embeddings used for similarity, retrieval, clustering and anomaly detection.

Neither layer replaces exact character/appearance metadata.

## Deterministic features

### Global crop
Measure:
- width / height / aspect ratio;
- alpha or segmentation coverage;
- dominant palette;
- color entropy;
- luminance distribution;
- saturation distribution;
- edge density;
- horizontal/vertical edge balance;
- approximate bilateral symmetry;
- negative-space/background ratio;
- component visibility;
- crop/view quality.

### Head
Measure after head-region normalization:
- printed-feature bounding box;
- face-feature occupancy;
- left/right symmetry;
- edge density;
- number of connected dark/colored regions;
- dominant print colors;
- negative substrate area;
- eye/brow/mouth landmark features when a dedicated landmark model is available;
- reverse-face relationship.

### Torso
Measure:
- decoration coverage;
- largest color-region share;
- palette size;
- bilateral symmetry;
- emblem location/scale;
- edge density by vertical bands;
- approximate line orientation distribution;
- negative substrate area;
- front/back continuation.

### Hips / legs / arms
Measure:
- decoration present/absent;
- print coverage;
- left/right symmetry;
- boot/glove transition position;
- side-print presence;
- edge density;
- dominant color roles.

## Why deterministic features matter

A learned embedding can say two images are similar without telling us why.

For style learning we need interpretable statements such as:
- modern Star Wars torsos use more edge density than Classic Space;
- classic faces use far less printed area than modern licensed faces;
- accepted official Batman cowls carry silhouette identity while the visible head print remains sparse;
- a custom design exceeds the normal detail-density distribution for its official comparison profile.

Every derived rule should be reproducible from stored features.

## Learned image embeddings

Use embeddings for:
- exact/near duplicate discovery beyond perceptual hashes;
- retrieval of visually analogous official minifigures;
- clustering by costume topology;
- finding mask/headgear analogues;
- identifying outliers for human review;
- matching crops to source-character references.

### DINOv3

Meta's current DINOv3 repository exposes pretrained visual backbones through Hugging Face Transformers and explicitly documents image-feature extraction. DINO-style self-supervised visual features are strong candidates for visual-similarity retrieval where text labels are incomplete.

Primary source:
https://github.com/facebookresearch/dinov3

Recommended use:
- visual nearest neighbors;
- clustering physical minifigure crops;
- finding repeated artwork under different backgrounds/crops;
- retrieving analogous silhouette/garment/armor structures.

Do not assume a DINO embedding understands LEGO semantic identity by itself.

### SigLIP 2

Google's SigLIP 2 models are available through Transformers; the public model card exposes zero-shot image/text classification and an Apache-2.0 license for the referenced checkpoint.

Primary model reference:
https://huggingface.co/google/siglip2-base-patch16-224

Recommended use:
- text-to-image retrieval from descriptive queries;
- zero-shot labels such as "masked superhero", "clone helmet", "double-breasted jacket";
- cross-modal retrieval when character metadata is incomplete;
- secondary duplicate/semantic clustering.

### Two-index strategy

Maintain both:
- DINOv3 visual index;
- SigLIP2 multimodal index.

For a generation request:
1. exact metadata lookup first;
2. exact character/appearance official examples;
3. DINO nearest visual analogues;
4. SigLIP semantic analogues;
5. profile-wide samples.

This keeps retrieval grounded in identity before visual similarity.

## Embedding provenance

Every embedding record needs:
- reference/derived asset ID;
- model repository/name;
- exact model revision if pinned;
- library/runtime version;
- preprocessing configuration;
- source crop hash;
- embedding dimension;
- normalization rule;
- output shard/file;
- generated_at.

Recompute embeddings when:
- model revision changes;
- preprocessing changes;
- the source crop changes.

Never silently mix incompatible embedding spaces.

## Style distributions

Aggregate deterministic features by:
- official style profile;
- year;
- theme/subtheme;
- physical/digital;
- component type;
- masked/unmasked;
- skin-tone system;
- expression family;
- source quality class.

Store robust statistics:
- count;
- median;
- mean;
- standard deviation;
- p05/p10/p25/p50/p75/p90/p95;
- missing-data rate.

Prefer percentile ranges over rigid hand-written thresholds.

## Custom comparison

A custom candidate should be compared to the nearest appropriate official distribution, not to the whole corpus.

Example:
modern masked Star Wars trooper custom
-> modern physical Star Wars
-> helmeted/masked subset
-> analogous armor topology
-> compare line density, coverage, symmetry, palette and feature hierarchy.

A custom can intentionally exceed an official percentile if the source appearance requires it, but the deviation must be explicit.

## Color handling

Do not treat web image RGB as factory print color truth.

For style features, image colors can measure:
- number of regions;
- relative contrast;
- hue family;
- color-role relationships.

Physical production color calibration remains a separate measured workflow.

## Line-work proxy

True factory vector lines are rarely available.

For raster references derive:
- edge-map density;
- skeletonized-edge length where appropriate;
- multi-scale edge density;
- distribution of dark-to-light transitions;
- smallest stable feature under downsample tests.

For LDraw/community vector reconstructions validated against the physical figure, derive more exact path/region metrics but keep authority tagged secondary_structured.

## Downsample survivability test

Every crop should be evaluated at:
- high analysis resolution;
- representative catalog resolution;
- approximate real-world minifigure angular/physical viewing scale.

A detail that disappears immediately under realistic downsampling should not have the same style importance as a chest emblem, eye, brow, belt, or boot boundary.

## Anomaly detection

Flag:
- physical figure whose measured features look unlike its era/theme;
- wrong crop/view;
- custom mistakenly ingested as official;
- digital screenshot with shader-heavy edge/contrast statistics;
- mirrored or altered retailer image;
- incorrectly segmented head/torso;
- mislabeled minidoll/bigfig.

Use anomaly flags to prioritize human review rather than auto-delete.

## Output

For each DerivedAsset:
- deterministic_feature_record
- embedding_record_ids
- style_profile
- nearest official neighbors
- quality/confidence
- anomaly flags

The original ReferenceAsset remains immutable evidence.
