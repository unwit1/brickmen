# Canonical Reference Sets and Evidence Selection

Research snapshot: 2026-09-24

## Purpose

An OfficialVisualSample may have dozens of source occurrences:
- LEGO product render;
- LEGO press image;
- BrickLink/Rebrickable image;
- instruction art;
- LDraw patterned-part reconstruction;
- game render;
- film frame;
- duplicate crops.

Generation should not receive all of them indiscriminately.

Build one **ReferenceSet** per OfficialVisualSample containing the best available evidence for each visual role while retaining alternates and provenance.

## ReferenceSet roles

Required/desired slots:
- full_front
- full_rear
- full_left
- full_right
- full_front_3q
- head_front
- head_reverse
- torso_front
- torso_rear
- arm_left
- arm_right
- hips_legs_front
- hips_legs_rear
- mask_or_headgear_front
- mask_or_headgear_side
- accessory_primary
- structured_component_pattern
- structured_geometry
- game_texture
- game_model_render
- film_expression_states

A slot may remain missing. Do not synthesize missing official evidence and label it official.

## Evidence score

Score is for selecting among evidence records, not determining truth.

Suggested components:
- source authority
- exact sample identity confidence
- view confidence
- component visibility
- resolution
- blur/compression
- occlusion
- background cleanliness
- physical-vs-digital applicability
- whether the asset is reconstructed rather than original

Authority preference:
LEGO primary physical > rights-holder/developer primary > structured catalog > validated structured reconstruction > game frame/render > film frame > secondary discovery.

The exact use case can change weights. A local game texture is stronger than a product photo for learning the digital game's flat texture, but weaker for physical factory-print color.

## Evidence conflicts

If front and back sources disagree:
- do not pick a winner merely by score;
- check whether they are different releases/outfits;
- split OfficialVisualSample if needed;
- preserve conflict until resolved.

Common causes:
- catalog image updated after a running change;
- game outfit differs from physical release;
- mirrored secondary image;
- alternate head expression;
- replacement headgear;
- regional/promotional variant.

## Generation retrieval

For a new design, return:
1. target source-reference package;
2. closest exact-character official ReferenceSets;
3. visual analog ReferenceSets;
4. flat component evidence for relevant surfaces;
5. mask/headgear analogues;
6. optional accepted custom extensions.

Cap redundant images. A few orthogonal high-quality references are better than twenty repeated front renders.

## Corpus QA

Track ReferenceSet completeness:
- has_front
- has_rear
- has_side
- has_head
- has_torso
- has_legs
- has_headgear_if_required
- has_component_inventory
- has_structured_pattern
- has_digital_source_if_applicable
- unresolved_conflict_count

Coverage dashboards should use these measures instead of raw image totals.
