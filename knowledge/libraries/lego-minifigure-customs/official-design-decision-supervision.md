# Primary-Source LEGO Design Decision Supervision

Research snapshot: 2026-09-24

The corpus should not learn official style only from pixels. LEGO designers have publicly described parts of their decision process, and those statements can become explicit supervision.

## Recurrent algorithm recovered from primary sources

Across Star Wars, The Nightmare Before Christmas, Wednesday, KPop Demon Hunters, Vikings and ONE PIECE, a consistent process emerges:

1. gather authoritative source references;
2. identify the few appearance/personality cues that define the subject;
3. choose base LEGO colors and existing component vocabulary;
4. establish large, simple, readable shapes before micro-detail;
5. selectively subdivide those shapes only where detail improves recognition/material/story;
6. decide which cues belong in existing geometry, new geometry, printing, cloth or accessories;
7. iterate high-sensitivity cues such as eyes, expression and silhouette heavily;
8. omit literal realism that does not survive the LEGO filter;
9. reserve unusual decoration regions or new moulds for cases where they materially improve identity;
10. validate the whole character as a coherent LEGO object rather than maximizing copied detail.

## Model implication

A source-to-minifigure model should first predict a DesignDecisionPlan, then generate artwork/geometry.

Suggested plan fields:
- authoritative_reference_ids
- P0_identity_cues
- P1_supporting_cues
- base_part_colors
- existing_part_candidates
- new_mould_candidates
- print_regions
- accessory/cloth assignments
- expression target
- audience/style filters
- deliberately_omitted_details
- material/fold cues
- detail_budget
- iteration_hotspots

The generated image is downstream of this plan.

## Training labels from designer commentary

Designer statements can label TranslationPairs with causal explanations such as:
- kept_existing_iconic_design
- added_arm_printing_as_special_upgrade
- new_element_needed_for_likeness
- existing_elements_plus_print_sufficient
- source_scariness_reduced
- expression_selected_from_multiple_characteristic_states
- graphics_restore_accuracy_after_geometric_simplification
- historical_reference_informed_material_and_color
- small_eye_angle_changes_high_sensitivity
- new_accessory_element_for_signature_prop

These labels are more informative than a generic similarity score.
