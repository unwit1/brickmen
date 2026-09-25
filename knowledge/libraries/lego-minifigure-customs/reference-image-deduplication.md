# Reference Image Materialization and Deduplication

Research snapshot: 2026-09-24

## Principle

The corpus needs as many **unique official visual states** as possible, not as many files as possible.

The same front render can appear on:
- LEGO.com;
- BrickLink;
- Rebrickable;
- Brickset;
- retailer mirrors;
- fan databases;
- press releases.

These are source occurrences, not necessarily different training images.

## Acquisition flow

metadata/reference URL
-> explicit source policy check
-> local fetch
-> SHA-256 exact dedupe
-> perceptual hash near-duplicate grouping
-> visual embedding clustering
-> canonical ReferenceAsset
-> multiple SourceOccurrence records

## Exact duplicate

Same SHA-256:
- store one content-addressed blob;
- preserve every source URL and timestamp;
- select highest-authority occurrence as preferred citation/source.

## Near duplicate

Perceptual hash catches:
- JPEG recompression;
- small resize;
- mild color change.

Do not automatically merge:
- front vs back;
- different face expression;
- accessory added/removed;
- costume recolor;
- altered helmet;
- crop exposing different information.

Near-duplicate grouping produces review candidates, not destructive merges.

## Visual embedding duplicate

Use embeddings after perceptual hashing to find:
- alternate crops of same render;
- transparent versus white-background versions;
- the same render with text/watermark;
- slightly repositioned catalog images.

Require identity/component comparison before merging.

## Preferred canonical image

Rank:
1. LEGO-hosted isolated official render;
2. LEGO-hosted clean product photo;
3. developer/rights-holder official character render;
4. high-resolution structured catalog image;
5. local model render from official game asset;
6. film frame;
7. secondary source.

For linework measurement, prefer neutral isolated renders/reconstructions over dramatic photography.

## Materialization policy

tools/knowledge/materialize_lego_reference_images.py:
- fetches exact URLs only;
- never crawls;
- requires explicit allowed hostnames;
- rate-limits requests;
- uses content-addressed SHA storage;
- preserves source occurrence metadata.

This makes source-specific legal/terms review possible without rewriting the storage pipeline.

tools/knowledge/dedupe_lego_reference_images.py adds a simple perceptual dHash after exact dedupe. Higher-level embedding clustering should be a later stage.

## Storage

Never organize raw images by filename alone.

Canonical local identity:
blobs/sha256/<prefix>/<sha256>.<ext>

Human/project organization is metadata:
ReferenceAsset
-> SourceOccurrence
-> Character
-> Appearance
-> OfficialVisualSample
-> DerivedAsset

This prevents renamed/rehosted copies from becoming duplicates.

## Training-set selection

A canonical ReferenceAsset can create multiple DerivedAssets:
- full image;
- figure crop;
- head crop;
- torso crop;
- leg crop;
- mask/headgear crop;
- segmentation mask;
- line-art extraction.

Train from DerivedAssets while retaining the canonical raw reference for audit.

## Film/game redundancy

Film:
- sample scene changes and time intervals;
- track characters;
- perceptual-dedupe;
- cluster expression/view/costume.

Game:
- prefer clean extracted texture/model renders;
- use screenshots only when model/texture data cannot represent the visible state;
- avoid repeated gameplay frames of the exact same skin.

## Metrics

Publish:
- source_occurrences
- unique_sha256_assets
- perceptual_clusters
- reviewed_visual_clusters
- unique_official_visual_samples
- samples_with_front
- samples_with_back
- samples_with_side
- samples_with_head_crop
- samples_with_component_inventory
- unresolved_identity

Raw file count is not a meaningful coverage metric.
