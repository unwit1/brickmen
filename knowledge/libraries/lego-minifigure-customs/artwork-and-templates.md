# Artwork and Templates

## Master-file rule

Use vector masters where practical (SVG/AI/Affinity/Inkscape). Keep separate layers for:
- physical boundary
- safe area
- bleed/wrap
- substrate/base color reference
- major color regions
- keyline/outline
- secondary line work
- white underbase
- primer if required
- varnish/clear if required
- registration
- cut line where applicable
- labels/notes
- source-reference overlay used only for design checking

Export process-specific PNG/PDF from the master.

## Template-first generation

The model should generate into a known physical surface template, not create a pretty rendered minifigure and hope it can later be flattened.

Required surface templates:
- head front
- head reverse
- head wrap
- torso front
- torso back
- torso left/right side where process supports it
- left/right arms
- hip front
- left/right leg front
- left/right leg side
- left/right leg rear where applicable
- headgear/helmet printable surfaces
- shields/tiles/accessories
- cape/cloth cuts

## Official-style translation inside templates

Generation order:
1. lock physical template and base-part color;
2. place large source-reference color blocks;
3. place identity-critical motifs;
4. test recognition with all micro-detail hidden;
5. add structural lines and secondary details;
6. add facial expression using official feature grammar;
7. remove anything that does not improve identity/readability;
8. check wraps and neighboring surfaces;
9. inspect at actual physical scale;
10. produce print layers.

The goal is not maximum template coverage. The goal is the smallest set of marks that reproduces the character convincingly while looking officially designed.

## BrickLink Studio reference

BrickLink Studio's decorated-minifig guide specifies PNG input and gives a head canvas reference of 416 × 320 px with face features around 193 × 142 px. The guide explicitly states that this is a reference rather than a definitive LEGO design guideline.

Use it for:
- preview normalization;
- rough face-feature bounding context;
- decorated-part visualization.

Do not treat the pixel dimensions as a physical manufacturing specification.

Source:
https://studiohelp.bricklink.com/hc/en-us/articles/5877834417303-Creating-a-decorated-minifig

## Physical templates

Build production templates in millimeters and derive pixels from DPI. Lock printer scaling to 100% / Actual Size; never Fit to Page.

Each physical template needs:
- centerline
- measured dimensions
- printable boundary
- safe area
- bleed/wrap overlap
- seam zones
- keep-out regions
- registration marks
- calibration ruler
- target part/design ID
- mold variant
- template version
- measurement source and confidence

Community/image templates can bootstrap alignment, but physical measurement and process tests remain authoritative for production.

## Source-reference package

Every generated template should point to a structured reference package containing:
- exact character/version
- source work
- issue/episode/scene/game skin/official art identifier
- primary images
- front/back/side evidence where available
- color roles
- material/layer notes
- identity-critical features
- known uncertainty

Do not allow a generic character name to substitute for a specific costume/version.

## Flat-art rule

Print templates must not contain:
- photographic lighting baked into colors
- fake fabric texture
- 3D bevel/shadow effects unless the official style/profile intentionally represents the feature graphically
- raster noise
- AI painterly artifacts
- perspective distortion
- arbitrary gradients unsupported by the target profile

Highlights and shadows should be deliberate graphic shapes.

## Face templates

Keep the head substrate color separate from features.

Store:
- eye/brow/mouth landmarks
- reverse expression
- hair/headwear occlusion mask
- wrap seam
- glasses/mask region
- facial hair region
- expression label

Do not include skin/base color in a face-only graphics layer unless the design intentionally prints a different skin region.

## White underbase and registration

For transparent media/direct printing, create a white-underbase layer beneath colors needing opacity. Slightly choke underbase to prevent white halos if registration shifts. Exact choke is process-specific and must be calibrated, not copied from another printer.

Save:
- jig coordinate system
- origin
- printer profile
- jig version
- underbase/choke test revision

## Decal-sheet organization

Later custom/decal research can teach sheet ergonomics, but not official style.

Useful sheet conventions to retain as production knowledge:
- clearly separated component groups;
- obvious left/right labeling;
- front/back orientation;
- wrap order;
- substrate color note;
- alternate-expression or alternate-costume variants;
- spare/backup small decals where appropriate;
- application instructions/provenance.

Bob's Customs, AV Figures and other decal makers can contribute to this layer after their artwork is evaluated against the official visual grammar. Their finished artwork must not be promoted into the official baseline.

## Validation

For every template:
1. print a known ruler/grid at 100%;
2. measure with calipers;
3. correct workflow scale;
4. test outline on sacrificial part;
5. inspect at naked-eye distance;
6. inspect under magnification for process defects;
7. photograph and log result;
8. version the template.

A design that looks impressive at 1000% zoom but fails at physical size is not production-ready.

Naming:
project_character-version_part_surface_art-v###_style-process-profile.ext
