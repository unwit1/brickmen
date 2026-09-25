# Master Training-Data Taxonomy for Official-Style Minifigure Generation

Research snapshot: 2026-09-24

## Objective

Maintain one exhaustive, provenance-aware corpus that can teach:

SOURCE APPEARANCE
-> IDENTITY / VISUAL CUES
-> LEGO ABSTRACTION DECISIONS
-> COMPONENT / MOULD CHOICE
-> FLAT DECORATION
-> PHYSICAL MINIFIGURE
-> EVALUATION / PRODUCTION OUTPUT

The taxonomy deliberately separates evidence types. A product photograph, a flat torso texture,
a game-only minifigure, a source movie still, a custom decal, and a failed AI generation are all
useful, but they supervise different tasks and must not be collapsed into one undifferentiated
"training image" pool.

## A. Canonical identity layer

### Character
Who or what the subject is independent of version.

Fields:
- character_id
- canonical_name
- aliases
- franchise
- creator/rightsholder
- species/entity type
- person/fictional/object classification

### Incarnation
Continuity or adaptation.

Examples:
- Earth-616
- MCU
- Arkham game universe
- Fortnite cosmetic identity
- original user character

### SourceWork
Film, issue, episode, game, illustration set, costume design, concept art, etc.

### SourceAppearance
The exact visual state to reproduce.

Fields include:
- appearance_id
- incarnation_id
- source_work_id
- issue/episode/scene/timestamp/skin/outfit identifiers
- costume state
- expression
- damage/transformation state
- mask/headgear state
- date/version

### OutfitDesign
A normalized design that may appear in multiple source frames or media assets.

## B. Source-character reference layer

These are identity ground truth, not LEGO style ground truth.

Types:
- licensor press still
- production still
- film frame
- comic panel/page
- animation frame/model sheet
- game render
- game texture/model
- concept art
- costume sheet
- turnaround/model sheet
- promotional illustration
- toy/statue/packaging art
- trading card
- user-owned original art
- commissioned/rights-cleared art
- user photograph
- portrait / reference photography

Required labels:
- exact appearance ID
- view
- resolution
- crop
- provenance
- authority
- whether color is trustworthy
- whether geometry is trustworthy
- whether expression is canonical

## C. Official physical LEGO layer

### FigureRelease
Official minifigure release record.

### ComponentRelease
Each head, torso, arm, hand, hips, leg, hair, helmet, cowl, neckwear, bodywear, cloth,
weapon, tool, prop, accessory, stand or display component.

### Physical evidence
- LEGO product render
- LEGO product photograph
- BrickLink image
- Rebrickable image
- Pick a Brick element image
- instruction art
- catalog/book image
- controlled user photography
- macro component photography
- reverse/side/turntable capture
- scan
- calibrated color measurement

### Structured physical metadata
- set
- year
- theme
- element ID
- design ID
- color ID
- BrickLink ID
- Rebrickable ID
- part inventory
- parent/print-of relationships
- alternate/replacement/running change

## D. Official structured geometry / decoration layer

Types:
- LDraw part geometry
- LDraw patterned parts
- Studio decoration templates
- Mecabricks UV layouts
- Mecabricks official-decoration textures
- official game meshes/textures
- UEFN/LEGO digital meshes/materials
- extracted TT/legacy game textures/models
- reconstructed UV maps
- calibrated production templates

Labels:
- source authority
- component ID
- geometry vs decoration
- UV space
- front/back/side surface semantics
- vector/raster
- reconstruction status

## E. Official digital LEGO layer

Types:
- playable game minifigure
- NPC
- digital-only costume
- profile icon
- official character render
- game texture
- game model
- film/TV LEGO-form character
- LEGO Style / cosmetic conversion
- official virtual product/configurator

Required relation:
- physical exact match
- physical near match
- digital-only
- game-embellished physical release
- non-standard figure system

## F. Source -> LEGO TranslationPair layer

Highest-value supervision.

Each TranslationPair includes:
- exact source appearance
- official LEGO target
- target medium
- exactness/confidence
- preserved features
- simplified features
- omitted features
- exaggerated features
- moved-to-mould features
- moved-to-accessory features
- moved-to-cloth features
- base plastic/color decisions
- print-region allocation
- expression translation
- mask/headgear route
- new-mould decision
- accessory substitutions
- identity-critical features
- source/LEGO side-by-side references

Pair families:
- Fortnite Outfit -> LEGO Style
- film costume -> physical LEGO
- comic costume -> physical/game LEGO
- animation model -> physical LEGO
- game skin -> LEGO Style / physical LEGO
- real person -> official minifigure
- historical clothing -> official minifigure
- creature/nonhuman source -> LEGO minifigure/mould solution

## G. Face / expression supervision

Record:
- head ID
- face side
- eye landmarks
- pupil/iris representation
- eyebrow landmarks
- mouth path/shape
- wrinkles/cheek lines
- beard/moustache
- scars/freckles/marks
- glasses/visor
- expression label
- valence/arousal where available
- six-basic-emotion labels
- intensity
- era/theme
- head substrate color
- printed coverage
- feature bounding box
- symmetry/asymmetry

Sources:
- official head components
- reverse heads
- Bartneck/Obaid emotion studies
- game/film expression states
- user-calibrated head macros
- vector/reconstructed head patterns

## H. Line-work / graphical-style supervision

Measure:
- stroke/edge density
- line hierarchy
- black/dark line proportion
- curvature
- corner frequency
- parallel lines
- hatching/fold grammar
- outline vs interior-detail ratio
- negative space
- connected regions
- smallest stable feature
- downsample survivability
- bilateral symmetry
- emblem scale
- feature placement by normalized surface coordinates

Aggregate by:
- era
- theme
- subtheme
- component
- medium
- age target
- licensed/unlicensed
- realistic/cartoon source

## I. Color / material supervision

Separate:
1. source-character color role
2. official LEGO base plastic color
3. official print color
4. digital render RGB
5. photography RGB
6. calibrated physical measurement

Track:
- LEGO color ID
- LDraw color
- BrickLink color
- material
- metallic/pearlescent/translucent
- fluorescent
- chrome
- dual-mould
- overmould
- opacity / underbase
- relative contrast

Never treat arbitrary web RGB as factory color ground truth.

## J. Mask / headgear / hair decision supervision

For every masked/head-covered appearance label:
- identity carried by silhouette
- identity carried by graphics
- face visibility
- required depth
- existing official mould candidate
- head print candidate
- helmet/cowl print candidate
- new-mould requirement
- hybrid route
- attachment interface
- collision envelope
- hair/headgear substitution
- side/rear dependence

Routes:
- head_print
- existing_headgear_unprinted
- existing_headgear_plus_print
- new_3d_part
- new_3d_part_plus_print
- accessory_plus_head_print
- hybrid

## K. Accessories / props / cloth supervision

Types:
- weapon
- tool
- musical instrument
- handheld prop
- shield
- cape
- kama
- skirt
- coat tails
- pauldrons
- backpack
- wings
- neckwear
- body armor
- stand/display item

Track source cue -> official abstraction and compatibility interface.

## L. Flat-template / decal supervision

Asset types:
- head wrap
- face-only
- torso front
- torso rear
- arm left/right
- hips
- leg front/back/side
- helmet/cowl
- shield/accessory
- full decal sheet
- UV map
- vector master
- print-ready raster

Metadata:
- component surface
- pixel dimensions
- physical dimensions
- coordinate system
- bleed
- safe area
- base color excluded/included
- white underbase
- spot colors
- vector path count
- source/reconstruction/custom status
- template version

## M. 3D geometry supervision

Types:
- official part geometry
- community reconstruction
- game model
- photogrammetry
- user scan
- custom printable geometry
- AI-generated concept mesh
- production mesh

Measurements:
- attachment geometry
- tolerances
- wall thickness
- silhouette
- overhang
- print surfaces
- collision
- head/neck/stud/bar/clip compatibility

## N. Custom-style extension corpus

Classes:
- purist custom
- altered official
- custom printed genuine LEGO
- hybrid
- third-party original
- high-end pad print
- high-end UV
- decal
- hand-painted
- injection-moulded compatible
- resin/printed part

Use cases:
- novel graphic grammar
- characters never made officially
- flat templates
- mask/headgear alternatives
- production technique
- negative examples

Every custom sample stores:
- maker
- product
- date
- method
- component provenance
- official-style score
- reference fidelity score
- what novel supervision it adds
- admit/reject reason

## O. Negative / control corpus

Required negatives:
- over-detailed customs
- too-realistic anatomy
- over-shaded/airbrushed art
- generic toy-like output
- wrong costume version
- incorrect emblem
- wrong mask route
- wrong mould
- invented details
- excessive gradients
- texture noise
- human hands/limbs
- poor AI generations
- mirrored asymmetrical prints
- blurry/compressed references
- incorrect character labels
- custom accidentally classified official

Also include positive controls:
- purist solutions using only existing official parts
- extremely simple classic figures
- official minimal faces
- official high-detail figures

## P. Generation-run corpus

Every ChatGPT/local generation becomes research data.

Store:
- Control Generation Packet
- model/provider
- model revision if exposed
- workflow/prompt version
- references
- seed/sampler if exposed
- output
- evaluation scores
- failure labels
- human preference comparisons
- next-revision hypothesis

This supports prompt optimization and preference/critic training.

## Q. Human evaluation corpus

Collect:
- pairwise official-likeness preference
- pairwise source-fidelity preference
- manufacturability preference
- first visible failure
- P0/P1 failures
- reviewer confidence
- expertise level
- optional LEGO-designer review when available

Do not collapse human judgment into one scalar.

## R. Production / manufacturing corpus

Records:
- print process
- printer
- ink
- substrate
- pretreatment
- white underbase
- curing
- jig
- registration
- vector/raster source
- production resolution
- defects
- abrasion
- adhesion
- opacity
- color delta
- reprint decision

Links generated art to real physical outcomes.

## S. Dataset and source metadata

Every dataset/source gets:
- source_id
- title
- provider
- source class
- source URL/location
- snapshot date
- dataset version
- row/item count
- data modalities
- authority
- permission/provenance record
- ingestion adapter
- raw storage location
- hash
- parser version
- dedupe status
- validation status
- promotion status
- known biases
- known missingness

## T. Permission / provenance

For this research project, rights clearance may be recorded as already obtained.

Still preserve:
- permission basis
- contact/representative
- date
- scope
- research/personal/LEGO-review use
- raw redistribution permission if separate
- commercial deployment permission if separate
- source hash / terms snapshot

This is audit metadata, not a reason to discard otherwise useful research data.

## U. Corpus tiering

Tier 0 — immutable raw evidence
Tier 1 — normalized assets
Tier 2 — resolved identities/components
Tier 3 — derived crops/masks/views
Tier 4 — deterministic features / embeddings
Tier 5 — TranslationPairs and semantic labels
Tier 6 — accepted training samples
Tier 7 — evaluation-only holdouts
Tier 8 — negative/control samples
Tier 9 — generated outputs / feedback / production results

Never train directly from Tier 0 without the normalization/resolution layer when a structured route exists.

## V. Completeness metrics

Report separately:
- physical figure records discovered/resolved
- physical components discovered/resolved
- samples with front/rear/side
- head coverage
- torso coverage
- mask/headgear coverage
- LDraw pattern coverage
- flat-template coverage
- digital-game designs
- film designs
- Fortnite LEGO Style pairs
- other TranslationPairs
- expression-labelled heads
- custom samples reviewed/admitted
- negative samples
- generation runs
- human evaluations
- manufacturing validations
- unresolved identity count
- unresolved rights/provenance count

"Image count" alone is never a completeness metric.
