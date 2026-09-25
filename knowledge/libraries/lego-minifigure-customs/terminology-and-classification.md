# Minifigure Terminology and Classification

Last researched: 2026-09-24

This vocabulary exists because seller, collector, customizer, and clone-brand terminology is inconsistent. Always preserve the source's original wording, but normalize it into these fields so search and comparison remain reliable.

## Provenance classes

| Canonical class | Meaning |
|---|---|
| official_lego | LEGO-manufactured and LEGO-decorated release |
| purist_custom | New character/design assembled only from unmodified official LEGO elements and official decoration |
| altered_official | Genuine LEGO substrate changed by direct print, decal, paint, engraving, cutting, sculpting, coating, or other alteration |
| hybrid_custom | Figure combines genuine LEGO elements with third-party molded, printed, resin, cloth, metal, or other components |
| third_party_original | Fully compatible non-LEGO figure or component with an independently produced design rather than a direct copy of one known commercial figure |
| replica_ko | Third-party item whose purpose is to reproduce an existing LEGO or custom figure/component design; use only when evidence supports the relationship |
| alternate_figure_system | Building-toy figure outside standard minifigure geometry, such as minidoll-like, action-figure-like, or other proprietary systems |
| unknown | Provenance cannot yet be resolved |

Do not use custom, compatible, clone, bootleg, KO, replica, counterfeit, fake, and third-party as interchangeable database values. Store those as source terms and normalize separately. Counterfeit is a legal/product-authenticity characterization and must not be inferred merely because an item is compatible or unlicensed.

## Customization and production terms

Pad printing transfers separated ink colors from etched plates/cliches by silicone pad. It is valued for repeatability and curved-surface conformity but has setup cost per artwork/color.

UV/digital direct printing deposits digitally controlled ink and cures it with UV light. It is practical for short runs, gradients, fine detail, and variable artwork; print height/texture and curved-surface registration depend on equipment and workflow.

Waterslide decal is a thin printed transfer applied with water, usually followed by setting solution and/or protective clear coat. Record transparent versus opaque media and whether white underprinting exists.

Adhesive/vinyl film is a pressure-sensitive surface graphic. It is distinct from waterslide decal and direct printing.

Hand painted / hand finished means color or details were applied manually. Record whether the entire design or only accents/cleanup are hand-applied.

Injection molded means a component is formed in a mold under pressure. Record plastic/material when known. Third-party molded does not imply 3D printed.

Overmolded / dual-material means multiple colors/materials are molded into one component. Keep this separate from printed color.

Resin printed normally refers to SLA/DLP/MSLA or related photopolymer processes. Do not assume resin chemistry or process without evidence.

FDM printed means filament-based additive manufacture.

Cloth includes capes, pauldrons, kamas/waistcapes, coats, skirts, flags, banners and similar flexible accessories. Record material, layers, edge treatment and stiffness when known.

Chrome, metallic, pearl, transparent, glow, marbled, speckled, painted and coated are finish/material-effect observations rather than generic colors.

## Decoration coverage

Represent coverage by surface, not marketing phrase. Supported surfaces should include head_front, head_back, head_wrap, torso_front, torso_back, torso_side_left, torso_side_right, arm_left, arm_right, hand_left, hand_right, hip_front, hip_side, leg_front_left, leg_front_right, leg_side_left, leg_side_right, leg_back_left, leg_back_right, foot/toe surfaces, headgear and accessory faces.

360_print is a seller/community descriptor. Store it as a claim, then independently enumerate actual surfaces. A figure may be marketed as 360 while some surfaces remain blank.

Dual-sided head means two face/graphic treatments on opposing sides of one head. Do not confuse with wrap printing.

## Figure forms

Track form separately from character identity: standard_minifigure, short_leg, medium_leg, long/extended_leg, baby/toddler, skeleton, droid, bigfig, microfigure, microdoll, minidoll, molded_character, brick_built_character, maxi/overscale and other.

Catalogs disagree on the boundary of minifigure. Preserve the source catalog's category while giving every record an Agent OS normalized form.

## Product forms

full_figure, body_only, torso_assembly, torso_only, head_only, legs_only, arms/hands, blank, headgear, armor/bodywear, cloth, weapon, utensil/tool, prop, stand/display, accessory_pack, upgrade_kit, army_builder, duo/team/pack, decal_sheet, sticker, printed_tile/brick and packaging/collector_extra.

## Release and collecting terms

Release states: announced, preorder, in_stock, restock, sold_out, retired, discontinued, archived, cancelled, unknown.

Edition attributes: open_edition, limited_edition, numbered, convention/event exclusive, retailer exclusive, collaboration, first_edition, chase/variant, prototype/sample.

Collection states: owned, ordered, wanted, watchlist, researching, candidate_modification, design_backlog, trade/sell, sold/traded, rejected, reference_only, archived.

Army builder means a generic or troop figure intended for multiples; it is not a quality class.

Drop means a time-bounded or quantity-bounded release event. Capture announced time, opening time, sellout time when observable, restock behavior and edition size separately.

## Identity and codes

Never use a seller SKU as the canonical figure ID. One release can have a maker code, reseller SKU, HeroBloks serial, BrickLink minifigure number, Rebrickable fig number and internal ID simultaneously.

Maintain ProductCodeAlias with code_type, code, issuer, figure_release_id, source, confidence, valid_from and valid_to.

When reseller names conflict with maker names, preserve both. Prefer the maker's own product name/code as the release label when a primary source is available.

## Purist and kitbash

Purist is community terminology and generally means assembling a new character from existing unmodified official LEGO parts/prints. Edge cases differ among communities, so store purist_claim plus the actual component provenance.

Kitbash is an informal term for recombining existing pieces, sometimes across manufacturers. It does not by itself establish provenance. Normalize by the actual components used.

## Evidence rule

Every claim about print method, genuine-part use, edition size, maker identity, code, release date, compatibility or quality requires a source. Maker claims and collector observations must remain distinguishable.
