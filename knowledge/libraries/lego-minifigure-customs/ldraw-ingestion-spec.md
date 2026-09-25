# LDraw Ingestion Specification

## Purpose
Turn the LDraw Official Parts Library into a provenance-aware geometry and decoration reference layer for minifigure-custom design, AI conditioning, digital twins and fixture development.

## Authoritative distinctions
Do not collapse these concepts:
- LEGO Design ID / part number
- LEGO Element ID
- LDraw filename
- LDraw alias
- LDraw mould variant
- LDraw shortcut/assembly
- LDraw patterned part
- LDraw subpart/primitive
- BrickLink/Rebrickable identifiers

LDraw's ratified part-number specification says known LEGO Design IDs should be used when known and describes alpha suffixes for mould variants. Patterned parts use their own suffix conventions. Preserve the exact filename and classification rather than trying to infer a single universal ID.

## Ingestion record
For every relevant DAT:
- ldraw_filename
- description
- author
- LDRAW_ORG classification
- official/unofficial
- release/update metadata
- license line
- category
- keywords
- history
- aliases/moved-to relationships
- referenced files
- dependency graph
- bounding box
- geometry hash
- BFC status
- TEXMAP references
- inferred minifigure role
- external identifier candidates
- source URL/release
- ingestion timestamp

## Minifigure role classifier
Classify into:
body/head
torso
arm_left
arm_right
hand
hips
leg_left
leg_right
hair
headwear
neckwear
armor
cape/cloth
weapon
tool
shield
backpack
creature/body-extension
accessory
assembly/shortcut
patterned/decorated
other

Classification must retain confidence and evidence.

## Patterned parts
LDraw's official specification treats printed plastic and multi-colour moulded parts as patterned parts and requires patterned versions to be based on a plain part. This is useful for learning the relation:
base geometry -> decoration/multi-colour variant.

Do not copy copyrighted graphics into commercial output merely because a geometry library contains a pattern. Pattern assets are reference/provenance data.

## Mould variants
Variants sharing a nominal design identity can have different geometry. Never train a connector or print template against “the part number” without recording the exact geometry/mould revision used.

## Sticker knowledge
LDraw models stickers as thin geometry and supports formed variants for stickers intended for curved/folded surfaces. This is useful as evidence for surface/deformation workflows, but UV print templates should be independently calibrated to physical parts.

## Dependency graph
Resolve recursive type-1 references so each canonical part can be rendered reproducibly. Keep primitives/subparts shared rather than flattening provenance.

## Update strategy
LDraw publishes periodic official library updates. Record release IDs and ingest incrementally by file hash/path. A current library landing page reported update 2026-08 with 17,116 unique shapes or patterned parts, demonstrating why incremental ingestion is necessary.

## Sources
https://www.ldraw.org/part-number-spec.html
https://www.ldraw.org/article/512.html
https://www.ldraw.org/article/398.html
https://library.ldraw.org/
