# Minifigure Decoration Grammar

## Purpose

Teach Agent OS the visual language of official minifigure-scale decoration while preserving the exact source character as closely as the minifigure format allows.

The style authority is:
1. official LEGO physical minifigures;
2. LEGO primary design guidance/interviews;
3. official LEGO/licensed digital minifigures, with digital-only effects isolated;
4. structured catalogs and LDraw for identity/geometry;
5. accepted custom style extensions only after scoring against the official baseline.

A custom design must never redefine what counts as official.

See:
- official-minifigure-visual-style.md
- official-character-corpus-ingestion.md
- custom-style-evaluation-framework.md

## Core translation sequence

REFERENCE
-> identify exact character/version/appearance
-> rank identity-critical cues
-> choose plausible minifigure parts/moulds
-> map major colors
-> block large simple shapes
-> check composition/recognition
-> refine only useful detail
-> map to real print surfaces
-> check actual-size readability
-> score source fidelity
-> score official LEGO likeness
-> revise

This sequence follows public descriptions by LEGO graphic designers: establish the big picture and simple large shapes first; only then cut those shapes into selected details.

## Official style is profiled, not averaged

Supported top-level profiles:
- official_physical_classic_simple
- official_physical_expression_expansion
- official_physical_licensed_early
- official_physical_modern
- official_digital_game

Theme-specific subprofiles are learned beneath these when enough samples exist.

Do not use a modern Marvel detail density to generate a 1980s Town figure unless explicitly requested. Do not force Classic Space simplicity onto a modern CMF or licensed collector figure.

## Learnable feature classes

### Head

Record:
- feature bounding box normalized to head template
- eye centers and separation
- eye width/height
- pupil/highlight convention
- eyebrow position, angle, length, thickness, curvature
- eyebrow color role and relation to hair
- mouth center, width, curvature, open/closed state
- teeth/tongue/lip treatment where present
- nose mark presence/type
- cheek/dimple/wrinkle primitives
- scar/freckle/tattoo/marking primitives
- facial-hair regions
- eyewear/mask landmarks
- front/back secondary expression
- hair/headwear occlusion of reverse print
- wrap seam behavior
- intentional asymmetry

LEGO's public discussion of The Complete Minifigure Guidelines confirms extensive eyebrow guidance, expression use and eyebrow/hair-color relationships. Exact unpublished numeric rules must be learned from official samples rather than invented.

### Expression families

Normalize at least:
neutral
happiness
confidence
smugness
determination
anger
concern
fear
surprise
sadness
disdain
mischievous
pain_or_battle_damage
shouting
laughter
sleep_or_unconscious
robotic_masked_or_no_readable_face

Expressions are not stored as a single label only. Store the feature geometry that produces the expression.

### Torso

Record:
- neck opening relationship
- neckline/collar/lapel/hood/scarf
- garment/armor layer graph
- shirt/jacket/armor boundaries
- major flat-color regions
- belt and waist transitions
- pockets/fasteners
- fabric folds
- emblems/badges and bounding boxes
- armor panel hierarchy
- printed-vs-sculpted boundary
- symmetry/asymmetry
- front/back continuation
- side-print continuation

The primary metric is information value: which shapes make the outfit recognizable at a glance?

### Arms

Record:
- whether arms are printed
- sleeve boundaries
- gauntlets/gloves
- tattoos/markings
- shoulder insignia
- armor transitions
- left/right asymmetry
- curvature compensation
- continuity with torso

Arm printing is optional evidence, not a default requirement.

### Hips / legs

Record:
- hip print role
- belt continuation
- coat/tunic tails
- pockets
- knee details
- boots/shoes
- left/right continuity
- side-leg continuation
- rear-leg continuation where present
- base plastic used as negative space

### Hair, headgear, bodywear and accessories

For source fidelity, record which visual information is carried by mould rather than print:
- silhouette-defining hair
- helmets/masks
- capes/coats/skirts/kamas
- neckwear/shoulder armor
- weapons/tools/props
- tails/wings/creature elements

A generation should not try to paint a silhouette-defining object onto the torso when an appropriate mould should carry it.

## Line hierarchy

Do not learn one fixed pixel width from web images.

Measure normalized line classes:
- primary_outline
- structural_internal
- facial_primary
- facial_secondary
- microdetail

For each class record:
- normalized thickness relative to surface dimensions
- local contrast
- curvature
- continuity
- minimum surviving feature at physical scale

Desired behavior:
- identity boundaries strongest;
- garment/panel construction secondary;
- folds/wrinkles/scars lighter;
- texture omitted unless it materially improves recognition.

## Shape hierarchy

Every decoration should have:
1. silhouette / mould layer
2. major color blocks
3. identity-critical symbols
4. structural garment/armor details
5. facial/expression detail
6. restrained microdetail

If levels 1–3 fail, adding level 6 is not a valid repair.

## Color grammar

Track colors by role:
- base_plastic
- primary_garment
- secondary_garment
- outline/keyline
- skin
- hair/facial_hair
- metallic
- highlight
- shadow
- emblem/accent
- transparent/effect

Prefer official LEGO colors for base elements and LEGO-compatible flat graphic relationships. Do not copy photographic lighting into print art.

## Negative space

Measure how much substrate color is intentionally unprinted. Official-looking artwork often benefits from leaving the base plastic visible instead of filling every surface.

High coverage is not automatically high quality.

## Detail-density measures

For each surface derive:
- marks per normalized area
- number of color regions
- number of line segments/curves
- smallest feature size
- filled-area ratio
- edge density
- symmetry
- dominant motif share
- count of identity-critical motifs

Use distributions by era/theme. Avoid universal maxima until corpus analysis provides evidence.

## Reference fidelity representation

For every design, keep two separate structures:
- source_reference_features: what the original character actually looks like;
- minifigure_translation_features: how those cues were compressed into LEGO grammar.

This permits a model to copy the reference faithfully without copying human anatomy or rendering style literally.

## Dataset representation

Do not store only finished raster examples. Extract:
- normalized landmark coordinates
- line-width classes
- shape primitives
- fill regions
- symmetry relationships
- semantic labels
- color-role labels
- overlap/layer ordering
- edge-distance/safe-zone statistics
- wrap relationships
- mould-vs-print responsibility
- reference-fidelity links

## Official digital/game data

Digital samples are tagged separately.

Allow digital sources to teach:
- character/outfit interpretation
- alternative official designs
- face/expression ideas
- color blocking
- digital-only characters

Exclude from physical decoration grammar unless corroborated:
- shader/specular effects
- animated mouth deformation
- flexible limbs/knees
- stretched/squashed geometry
- impossible articulation
- non-printable surface lighting

## Accuracy tests

Score independently:
- source-reference fidelity
- official LEGO likeness
- physical-size readability
- landmark placement
- line hierarchy
- symmetry
- continuity across part boundaries
- safe-zone compliance
- process printability
- color/opacity feasibility

Do not average source fidelity and official likeness into one number during optimization. A high-fidelity but un-LEGO-like design and an official-looking but inaccurate design are different failure modes.

## Production handoff

Generated art remains a candidate until:
- converted/redrawn as clean vector paths where practical;
- checked at actual size;
- colors mapped to calibrated targets;
- white/primer/varnish behavior assigned;
- safe zones and wraps validated;
- component surfaces labeled;
- source and style profile stored.

## Primary sources

LEGO minifigure design/history:
https://www.lego.com/uk-ua/categories/adults-welcome/article/history-of-lego-minifigures

Complete Minifigure Guidelines public discussion:
https://www.lego.com/cdn/cs/set/assets/blt6b793d2604b98954/bits_n_bricks_s01e08_lego_minfigures_a_conversation_feature_and_transcript.pdf

Official graphic-design workflow examples:
https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6218782.pdf
https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6143203.pdf
