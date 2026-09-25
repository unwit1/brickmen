# AI Generation Accuracy for Minifigure Renders and Print Templates

The goal is to constrain AI with real geometry, exact source references and a learned official minifigure grammar rather than rely on free-form prompting.

## Objective function

Optimize three dimensions separately:

1. reference_fidelity — does it match the exact source character/version?
2. official_lego_likeness — does it obey the relevant official minifigure visual grammar?
3. production_feasibility — can the intended print/decal process reproduce it?

Do not collapse the first two into one score. The target is simultaneously high fidelity and high official likeness.

## Best architecture

Use deterministic 3D/reference geometry as the body authority, official physical visual statistics as the style authority, and the exact source image/work as the identity authority.

Recommended pipeline:
1. identify exact source appearance;
2. retrieve source-reference package;
3. choose exact canonical minifigure part IDs;
4. select official era/theme style profile;
5. assemble figure in Studio/LDraw/Blender;
6. render reproducible reference passes;
7. extract identity-critical source features;
8. generate flat template artwork from large shapes to detail;
9. compare against official feature distributions;
10. score reference fidelity;
11. score official likeness;
12. revise weakest axis;
13. vector-clean production art;
14. generate CMYK/spot/white/varnish/primer masks;
15. test at physical scale.

Do not ask a diffusion/image model to invent exact minifigure geometry when exact geometry already exists.

## Reference hierarchy

Identity weighting:
exact source image/work > official character reference > official adaptation evidence > high-confidence secondary reference.

Style weighting:
official physical exact/similar figure > official physical same theme/era > official physical global grammar > official digital/game > approved custom style extension > unscored custom.

Custom artwork can fill an official-data gap only after it passes custom-style-evaluation-framework.md.

## Two-stage character translation

### Stage 1 — Source decomposition
Extract without applying LEGO style:
- silhouette
- hair/headgear shape
- garment/armor layers
- major color regions
- symbols/emblems
- gloves/boots
- props/accessories
- face identity
- expression
- materials
- front/back/side-specific features

### Stage 2 — LEGO abstraction
Translate:
- human silhouette -> plausible minifigure mould choices
- complex costume -> large readable surface regions
- anatomical face -> minifigure feature grammar
- fabric/armor texture -> selected graphic cues
- real-world colors -> LEGO-compatible roles
- tiny details -> omit unless identity-critical
- lighting/shadows -> graphic material cues rather than copied illumination

This prevents the model from copying reference realism directly onto a toy-shaped body.

## Structural conditioning

Useful conditioning set:
- RGB clay render
- depth map
- world/camera normal map
- silhouette mask
- edge/canny map
- semantic part mask
- material/color ID mask
- physically calibrated print-surface mask
- source-reference segmentation

## Canonical views

Maintain:
- orthographic front
- orthographic back
- left
- right
- front 3/4
- rear 3/4
- top when headgear matters
- neutral exploded view
- production flat-art views

Store exact camera transforms and focal length.

## Geometry authority

Use LDraw or Studio/PartDesigner geometry where licensing permits.

Use geometry for:
- silhouette
- proportions
- connection positions
- camera blocking
- accessory clearance
- conditioning
- render-to-template projection

Use physical measurement for:
- final print placement
- jig surfaces
- resin fits
- tolerances

## Official style profile

Generation metadata must include:
- official style profile
- target era
- target theme/subtheme
- closest official analog samples
- allowed detail density range
- facial-expression family
- print-surface expectation
- mould-vs-print decisions
- uncertainty

Profiles:
- official_physical_classic_simple
- official_physical_expression_expansion
- official_physical_licensed_early
- official_physical_modern
- official_digital_game

## Face generation

Do not prompt "LEGO face" as a sufficient instruction.

Supply:
- target expression family
- eye/brow/mouth landmark distributions from relevant official samples
- hair/facial-hair color role
- glasses/mask region
- asymmetry requirement
- reverse expression if needed
- headgear occlusion mask

Exact unpublished LEGO internal placement rules must be learned statistically from official samples, not fabricated.

## Prompt schema

Prompts/data should include:
- source appearance ID
- source-reference features
- canonical body configuration
- exact part IDs
- color IDs
- pose
- camera
- lighting
- official style profile
- closest official analogs
- character description
- identity-critical features
- geometry constraints
- print-surface constraints
- allowed creative freedom
- forbidden alterations
- target output type

Output types:
- concept_render
- catalog_render
- print_art_front
- print_art_back
- head_wrap_concept
- arm_art
- leg_art
- accessory_concept
- full_decal_sheet
- resin_part_concept

## Negative constraints

Explicitly forbid unless target evidence requires otherwise:
- extra joints
- human fingers
- realistic anatomical hands
- human-proportioned shoulders
- elongated limbs
- incorrect head diameter
- merged arms/torso
- painted cloth texture
- photographic lighting baked into print
- random gradients
- invented studs/connectors
- excessive microdetail
- 360-degree printing merely to fill blank space
- symmetry breaking without source evidence
- perspective distortion in template images

## Official corpus

The official style corpus should eventually cover every structured official minifigure assembly record, with physical visual-feature extraction and resolved character/appearance links.

As of 2026-09-24 BrickLink exposes about 19.25k minifigure catalog items and Brickset about 19.24k. These are assembly records, not unique character counts.

Use official-character-corpus-ingestion.md for the census pipeline.

## Digital/game corpus

Digital designs are useful for official character translations unavailable physically. LEGO's public minifigure guidance discussion says digital versions should preserve the toy's palette, graphic style, dimensions and system scale, with controlled animation exceptions.

Digital-only geometry deformation, animated mouths, shaders and impossible articulation must remain tagged digital.

## Custom extension gate

After the relevant official profile is statistically established:
- score reference fidelity 0–100;
- score official likeness 0–100;
- score production quality 0–100;
- extract only novel reusable lessons from qualified customs;
- never relabel custom artwork as official.

See custom-style-evaluation-framework.md.

## Decal/template generation

AI image output is never directly print-ready.

Cleanup:
- vectorize/redraw
- remove raster noise
- correct symmetry where source requires
- enforce calibrated minimum features
- map colors to calibrated swatches
- generate white underbase
- add choke
- clip to safe area
- validate wrap continuity
- validate at actual size

## Multi-view consistency

Maintain one canonical character specification and reference bundle across every surface. Prefer one textured 3D/digital twin or one unified flat character spec over separately improvising front/back/arms/legs.

## Primary research files

- official-minifigure-visual-style.md
- official-character-corpus-ingestion.md
- minifigure-decoration-grammar.md
- artwork-and-templates.md
- custom-style-evaluation-framework.md
- data/official-style-schema.json
