# Visual Normalization and Automatic Minifigure Cropping

Research snapshot: 2026-09-24

## Purpose

Reference acquisition only scales if raw product images, game screenshots and film frames can be converted into consistent character/component crops automatically.

The system should preserve raw evidence but train/retrieve primarily from **DerivedAssets**:
- isolated figure crop;
- transparent figure mask;
- head crop;
- torso crop;
- hips/legs crop;
- left/right arm crop;
- hair/headgear/mask crop;
- accessory crop;
- canonical-view label;
- quality metrics.

## Source-specific strategy

### Isolated physical catalog render
Usually skip detector if the figure is already isolated. Use background/alpha analysis plus geometry-aware component partitioning.

### Product/set photography
Use open-vocabulary detector -> instance segmentation -> minifigure crop. Multiple figures become separate DerivedAssets linked to the same SourceAsset.

### Film/game screenshots
Use detector + segmenter + video/object tracking. Track identity across frames and retain only high-information state changes.

### Extracted game models/textures
Do not run a 2D detector first. Render deterministic canonical views from the source model and preserve original texture sheets separately.

### LDraw / structured geometry
Render exact views directly; use as component/surface masks and geometry supervision rather than as visual-authenticity authority.

## Recommended open vision stack

### Grounding DINO / Grounded SAM
Grounding DINO provides open-set text-conditioned object detection and its project advertises Grounded SAM 2 integration. Candidate prompts:
- LEGO minifigure
- minifigure
- LEGO character
- minifigure head
- minifigure helmet
- minifigure torso

Use this for broad detection where the image may contain scenery, vehicles and multiple figures.

Source:
https://github.com/IDEA-Research/GroundingDINO

### SAM 2.1
SAM 2 supports promptable image/video segmentation and multi-object video tracking. This makes it especially useful for film and gameplay footage after the initial minifigure detection.

Source:
https://github.com/facebookresearch/sam2

License/model terms must be checked and pinned in the implementation manifest before deployment.

### YOLOE candidate
YOLOE supports open-vocabulary detection/segmentation from text or visual prompts and may provide a faster production path after benchmarking.

Source:
https://github.com/ultralytics/ultralytics

Do not adopt based on speed claims alone. Benchmark accuracy on a dedicated LEGO corpus and review package/license implications.

## LEGO-specific detector training

Foundation detection should bootstrap labels, not remain the only detector forever.

Build a reviewed dataset with classes:
- standard_minifigure
- minidoll
- bigfig
- microfigure
- skeleton
- droid_or_robot_minifigure_form
- molded_character
- non_minifigure_character
- head
- torso
- hips
- leg_left
- leg_right
- arm_left
- arm_right
- hand_left
- hand_right
- hair
- helmet_or_mask
- neck_bodywear
- cape_or_cloth
- accessory

Fine-tune or train a compact detector only after the corpus contains enough reviewed labels. Measure false positives on LEGO bricks that resemble body shapes.

## Figure segmentation

Segmentation output:
- alpha mask
- bounding box
- visible-component mask
- occlusion mask
- confidence
- detector prompt/class
- model/version

Never destructively remove the original background from the canonical raw image.

## Component splitting

Prefer structural knowledge over pure visual guessing.

If component geometry is known:
1. fit/align a standard minifigure skeleton or rendered silhouette;
2. infer head/torso/hips/limb regions;
3. refine boundaries with segmentation;
4. use occlusion relationships to handle crossed arms/accessories.

If geometry is unknown/unique:
- segment figure first;
- use dedicated component detector;
- mark uncertain component boundaries instead of hallucinating a clean split.

## View classification

Required classes:
- front
- rear
- left
- right
- front_3q_left
- front_3q_right
- rear_3q_left
- rear_3q_right
- top
- bottom
- unknown

Best approach:
1. render reference geometry across known camera angles;
2. train/fit a view classifier using silhouettes/keypoints;
3. use head/torso orientation and visible arm/leg asymmetry;
4. store probability distribution rather than only winner.

Near-front/rear images receive higher weight for print-pattern analysis than extreme perspective views.

## Video tracking and frame reduction

For film/game footage:
1. detect candidate minifigures on scene-change/key frames;
2. seed SAM 2 tracking through adjacent frames;
3. compute crop quality each frame;
4. compute expression/costume/view embeddings;
5. keep best representative frame per state cluster;
6. retain rare side/back/headgear states even if lower visual quality.

Do not retain thousands of nearly identical animation frames.

## Image quality metrics

Store:
- pixel dimensions
- crop size
- blur
- compression/blockiness
- occlusion percentage
- segmentation confidence
- perspective severity
- lighting neutrality
- background cleanliness
- visible surfaces
- alpha availability
- watermark/text overlay
- source authority

### Use restrictions by measurement

Color calibration:
only neutral/high-quality physical/official renders.

Line-width/style measurement:
isolated official physical references, structured pattern reconstructions validated against physical figures, or clean flat game textures.

Identity/reference:
can use lower-quality film/game frames if they expose unique official designs.

## Component reference assembly

For every OfficialVisualSample aim to build a ReferenceSet:
- best full front
- best full rear
- best left/right
- best head
- best torso
- best hips/legs
- best mask/headgear
- component catalog images
- structured pattern/geometry references
- game texture/model references when applicable
- film expression states when applicable

Missing views stay explicitly missing. Never synthesize missing evidence and store it as official reference.

## Automatic corpus QA

Reject/quarantine candidates with:
- non-LEGO custom figure mistakenly detected as official
- fan render without official provenance
- AI-generated image
- retailer composite that edits the official product
- severe watermark obscuring design
- wrong character/version mapping
- screenshot shader/light treated as print
- minidoll/bigfig mixed into standard-minifigure baseline
- mirrored image that reverses asymmetrical print
- catalog thumbnail too small for intended measurement

## Human-review priority

Review first:
- digital-only characters
- game/film-only masks
- ambiguous physical variants
- figures with multiple similarly named releases
- rare side/back evidence
- new/custom moulds
- samples that would materially change style-profile distributions

Routine duplicate front renders can be auto-resolved with higher confidence.

## Output schema

Every DerivedAsset should include:
- derived_asset_id
- source_reference_asset_id
- transform_type
- model/tool/version
- bbox
- segmentation mask path/hash
- component label
- view label + confidence
- character/appearance mapping
- visible surfaces
- quality metrics
- transformation parameters
- reviewer status
- created_at

Derived assets remain auditable back to the original source.
