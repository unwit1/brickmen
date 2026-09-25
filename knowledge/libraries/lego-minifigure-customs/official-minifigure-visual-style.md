# Official LEGO Minifigure Visual Style

Research snapshot: 2026-09-24

## Purpose

This file defines the official-style baseline for Agent OS minifigure generation. The target is not a vague "LEGO-like" look. The target is a source-grounded visual grammar derived first from official physical LEGO minifigures and official LEGO design guidance, then augmented cautiously by official digital/game representations.

The generation objective is dual:
1. preserve the source character/reference as faithfully as the minifigure format permits;
2. translate that reference through official LEGO minifigure abstraction so the result looks plausibly official.

Neither objective may silently replace the other.

## Primary design algorithm

Official LEGO graphic designers describe a consistent translation process:

REFERENCE -> BIG PICTURE -> LEGO COLOR / PART CHOICES -> SIMPLE LARGE SHAPES -> COMPOSITION -> ICONIC FEATURES -> DETAIL REFINEMENT -> PHYSICAL-SCALE READABILITY -> SURFACE MAPPING -> FINAL CHARACTER CHECK

Marie Sertillanges described gathering all visual references, building the big picture of the character, choosing LEGO colors for torso/arms/legs/hands, sketching general shapes, and iterating between the source and minifigure. To keep a small figure detailed but readable, she starts with very simple large shapes, establishes composition with fewer elements, then cuts those shapes into finer details, choosing only the details that best capture appearance/personality.

Paul Constantin Turcanu similarly described rewatching scenes or studying official references, sketching first, then tracing digitally. His explicit design principle is that keeping it simple is key, and that detailed source material should be translated by directing attention toward the most iconic features that make the character recognizable.

These principles are the default transformation policy for all template generation.

Primary sources:
- https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6218782.pdf
- https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6143203.pdf

## Core invariants

### Readability before micro-detail
At minifigure scale, every mark consumes visual bandwidth. Prefer a few large, correctly placed identity cues over many tiny literal details.

### Composition before rendering
Block the torso/head/leg design as large regions before adding seams, wrinkles, rivets, highlights or texture. If the design is not recognizable in large flat shapes, adding detail is not the correct fix.

### Iconic-feature selection
Rank source-reference details by identity value. Preserve features that define the character, costume, era or expression. Compress or omit low-value texture.

### LEGO geometry remains authoritative
Decoration should respect the physical figure: cylindrical head, trapezoidal torso, curved arms, hip/leg segmentation, headgear interfaces and accessory constraints. Do not draw anatomical forms as if the body were human-shaped underneath.

### Printed detail does not become sculpted detail by accident
If a source garment can be communicated as print, do not imply raised seams, fabric folds or anatomy that would require a new mould unless the target explicitly calls for a custom mould.

### Underlying plastic color is part of the design
The base part color participates in the artwork. Blank/negative regions are intentional and often improve official-style readability.

### Official color language first
Prefer the official LEGO palette for base parts and major printed regions when possible. A source color can be approximated to a LEGO-compatible role while preserving relative contrast and character identity.

### Theme and era coherence
Official minifigure design evolves. Do not average all eras into one style. A Classic Space figure, 1990s Pirate, early licensed Star Wars figure, modern CMF, and modern Marvel figure have different expected detail densities.

## Official-style era profiles

These are Agent OS analytical profiles, not official LEGO product labels.

### official_physical_classic_simple — 1978–1988
Characteristics:
- extremely simple facial grammar;
- dot eyes and simple smile as dominant neutral vocabulary;
- minimal torso decoration;
- large flat color regions;
- little or no surface-wide detail;
- strong symmetry and iconic symbols.

Official LEGO states that the modern minifigure appeared in 1978. Body decoration began with stickers and the first printed body appeared in 1978.

### official_physical_expression_expansion — 1989–1998
Characteristics:
- wider emotional range;
- facial hair, scars, eyepatches and role-signifying face detail increasingly possible;
- stronger good/evil/personality encoding;
- torso graphics become more character-specific while remaining highly graphic.

LEGO historical material identifies Pirates in 1989 as an important expansion of facial expression/personality.

### official_physical_licensed_early — 1999–2009
Characteristics:
- named licensed characters become a major design problem;
- likeness is achieved by selecting iconic hair/headgear, color blocks, symbols and a few facial cues rather than portrait realism;
- character specificity increases while the minifigure silhouette remains dominant.

LEGO licensed characters began with Star Wars in 1999; realistic skin tones and more specific likeness treatment expanded in the 2000s.

### official_physical_modern — 2010–present
Characteristics:
- broader expression vocabulary;
- dual-sided heads are common where appropriate;
- more arm, leg, hip and back decoration when identity warrants it;
- dual moulding and specialist moulds can carry information previously handled only by print;
- higher detail is allowed, but official designers still begin from simple large shapes and selective detail.

Do not assume "modern" means "maximum detail." Contemporary LEGO sources explicitly describe reducing detail to preserve LEGO design DNA.

## Facial grammar

LEGO's internal Complete Minifigure Guidelines reportedly devote extensive guidance to eyebrows, facial expression and feature placement. Treat this as evidence that small feature decisions are systematic, not arbitrary.

### Eyes
Measure:
- center position;
- eye separation;
- width/height;
- pupil/highlight treatment;
- symmetry/asymmetry;
- eyewear/mask interaction.

Do not hard-code one eye proportion globally. Learn distributions by era, theme, skin-tone system and expression family.

### Eyebrows
Measure:
- vertical distance from eyes;
- angle;
- length;
- thickness class;
- curvature;
- left/right symmetry;
- expression role;
- color relationship to hair/facial hair.

LEGO's public transcript confirms eyebrow color is intended to correlate with hair color, but does not publish the exact mapping. Store the relationship as a learned corpus feature; do not invent a universal formula.

### Mouth
Measure:
- vertical position;
- width;
- curvature;
- closed/open state;
- lip/teeth/tongue presence;
- smile/frown asymmetry;
- corner marks;
- relation to facial hair.

Mouth placement should be learned from official samples by style profile rather than approximated from human facial anatomy.

### Nose and anatomical marks
Use sparingly. LEGO guidance cited publicly gives an extreme example: when a belly button is appropriate it should remain a simple circle or ellipse, not anatomical rendering. Apply the same abstraction philosophy to noses, wrinkles, cheek lines and body anatomy unless official corpus evidence for a theme shows otherwise.

### Expression ontology

Minimum normalized expression families:
neutral; happiness; confidence; smugness; determination; anger; concern; fear; surprise; sadness; disdain; mischievous; pain/battle_damage; shouting; laughter; sleep/unconscious; robotic/mask/no_readable_face.

The ontology is descriptive. Expression geometry must be learned from actual official faces.

An external historical study of LEGO faces identified six broad perceived clusters—disdain, confidence, concern, fear, happiness and anger—which is useful as a secondary validation vocabulary, not as LEGO's official taxonomy.

## Torso grammar

Analyze:
- neckline and neck opening;
- undershirt / shirt / jacket / armor layer graph;
- collars, lapels, hoods and scarves;
- emblem position and scale;
- belt/waist transition;
- buttons, zippers, straps and pockets;
- fabric fold count/direction;
- armor panel hierarchy;
- left/right symmetry;
- intentional asymmetry;
- front/back continuation;
- side print when present.

The most important question is not "how many details are visible in the reference?" but "which few shapes make this outfit immediately identifiable?"

## Arms and hands

Arm printing should be evidence-driven, not automatic. Record:
- sleeve boundary;
- shoulder insignia;
- glove/gauntlet transition;
- armor panel;
- tattoos/markings;
- left/right asymmetry;
- curvature compensation;
- whether the same information is already readable on the torso.

Do not force 360-degree coverage merely because custom printers can produce it.

## Hips and legs

Analyze:
- belt continuation;
- hip print role;
- coat tails / tunics;
- pockets;
- knee markers;
- boot/shoe transitions;
- side-leg continuation;
- front/back continuity;
- base plastic used as negative space.

Leg detail density should follow the target profile and reference importance, not a fixed requirement.

## Line work

Do not invent a single official stroke width from catalog renders. Product photos, web scaling, anti-aliasing and print processes distort apparent widths.

Instead store:
- line class: primary_outline, structural_internal, facial_primary, facial_secondary, microdetail;
- normalized thickness relative to the target print surface;
- local contrast;
- minimum surviving width observed at physical scale;
- era/theme distribution.

Generation should use line hierarchy: identity-defining boundaries strongest, secondary construction/fold marks lighter, incidental texture weakest or omitted.

## Color and shading

Official minifigure decoration is primarily graphic, not painterly. Prefer:
- flat spot-like regions;
- deliberate highlight/shadow shapes;
- limited gradients unless official corpus evidence supports them;
- clear separation of material roles;
- LEGO part color doing as much work as possible.

When a licensed reference contains complex lighting, translate material identity rather than copying the photograph's transient lighting.

## Digital/game profile

Official digital minifigures are valuable but not equal to physical print authority.

LEGO's Bits N' Bricks interview with Tara Wike says digital representations should first be as true to the toy as possible, retaining the color palette, graphic style, overall dimensions and coherent LEGO-system scale. Animation may bend or stretch rules for gameplay, but excessive liberty can make a character stop reading as a minifigure.

Classify every digital sample:
- exact_physical_match
- physical_release_variant
- digital_only_official_design
- game_embellished_physical_design
- non_minifigure_character

Digital-only decoration may expand character-translation vocabulary. Shader highlights, geometry deformation, mouth animation, impossible articulation and game-only surface effects must not enter the physical print baseline unless separately supported.

Official digital sources include LEGO Island lineage, LEGO Dimensions, LEGO Marvel games, LEGO Jurassic World, LEGO DC games and LEGO Star Wars: The Skywalker Saga. The latter advertises more than 300 playable characters and a profile-icon encyclopedia containing hundreds of minifigure representations.

## Reference fidelity vs official likeness

Every generated design receives two independent evaluations.

### Reference fidelity
How accurately does the translation preserve the source?
- defining silhouette/part choice
- major color blocks
- symbols/emblems
- garment/armor topology
- face identity and intended expression
- material/layer cues
- version/era-specific details
- front/back/side continuity

### Official LEGO likeness
How plausibly could the translation sit next to official figures?
- large-shape composition
- selective abstraction
- line hierarchy
- facial grammar
- detail density
- color language
- base-plastic use
- print-surface discipline
- mould/part plausibility
- era/theme coherence
- physical-scale readability

A design can score high on one axis and low on the other. The desired output is high on both.

## Generation rule

Never ask the model merely to "copy this image onto a minifigure."

Use:
1. identify exact source appearance;
2. extract identity-critical visual features;
3. choose plausible official parts/moulds;
4. map source colors to an official-compatible palette;
5. construct the design in large flat shapes;
6. verify recognition;
7. add only identity-supporting detail;
8. translate face through official facial grammar;
9. map artwork to physically calibrated print surfaces;
10. evaluate at actual minifigure scale;
11. score reference fidelity and official likeness separately;
12. revise the lower-scoring axis without damaging the stronger one.

## Primary sources

- LEGO Minifigure history: https://www.lego.com/uk-ua/categories/adults-welcome/article/history-of-lego-minifigures
- LEGO Bits N' Bricks minifigure guidelines transcript: https://www.lego.com/cdn/cs/set/assets/blt6b793d2604b98954/bits_n_bricks_s01e08_lego_minfigures_a_conversation_feature_and_transcript.pdf
- Star Wars graphic designer Marie Sertillanges: https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6218782.pdf
- Star Wars graphic designer Paul Constantin Turcanu: https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6143203.pdf
- Wednesday design interview: https://www.lego.com/en-pt/categories/adults-welcome/article/surprises-lego-wednesday
- Nightmare Before Christmas designer interview: https://www.lego.com/en-sk/categories/adults-welcome/article/nightmare-before-christmas-designer-interview
- Viking Village graphic-design interview: https://www.lego.com/en-za/categories/adults-welcome/article/return-of-lego-vikings-village
- BrickLink Studio decorated-minifig reference: https://studiohelp.bricklink.com/hc/en-us/articles/5877834417303-Creating-a-decorated-minifig
