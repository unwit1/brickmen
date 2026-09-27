# Additive Manufacturing Product Safety Gate

Research status: U.S.-focused compliance research, 2026-09-27.

## Purpose

Keep R&D/custom-display production separate from any future claim that printed minifigure components are children's toys.

This is not legal advice. It is an automation gate so the system does not silently turn a research prototype into a consumer children's product without the appropriate compliance review/testing.

## Core rule

**A fully cured part that seems safe to an adult is not automatically a compliant children's toy.**

If a product is designed or intended primarily for children 12 or younger in the United States, CPSC children's-product requirements can apply.

CPSC states that children's products subject to safety rules generally require third-party testing by a CPSC-accepted laboratory and a Children's Product Certificate (CPC), subject to specific exemptions/relief.

## Small-parts issue

Minifigure accessories are inherently small.

CPSC states that products intended for children under three must not contain small parts, or release small parts after use-and-abuse testing, when those parts fit the regulatory small-parts cylinder.

Therefore Brickmen should not infer age suitability from compatibility with an existing building-toy system.

Store:
- intended_age;
- product_class;
- small_parts_review;
- labeling_review;
- test_report_ids;
- certificate status.

## Paint/coating/material issues

CPSC currently states, among other requirements:
- lead in paint/similar surface coating limit for children's products: 90 ppm;
- total lead in accessible components: 100 ppm;
- ASTM F963/16 CFR Part 1250 can impose additional toy requirements;
- phthalate rules may apply to specified plasticized components.

A paint, primer, clear coat, resin, pigment, decal or adhesive change can therefore be a product-safety-relevant material change.

Never treat "non-toxic," "skin safe," a resin SDS, or a vendor biocompatibility statement as a substitute for the applicable children's-product testing/certification.

## Small-batch status is not a universal exemption

CPSC has a Small Batch Manufacturer program, but its guidance explicitly says:
- qualifying firms must register to use potential testing relief;
- underlying product rules still apply;
- a CPC is still required for covered children's products;
- some Group A requirements, including small parts and lead in paint, do not receive the small-batch third-party-testing relief described by CPSC.

Therefore the business system must never implement:
```
small batch == no testing
```

## Manufacturing traceability helps compliance

The additive-manufacturing batch system should preserve:
- date/place of manufacture;
- material/resin/filament lot;
- pigments/coatings/adhesives;
- production batch;
- QC test records;
- supplier documents;
- lab test/certificate linkage.

This overlaps strongly with the production traceability Brickmen needs anyway.

## Automation state

Suggested safety state:

```
research_only
display_collectible
general_use_review
childrens_product_review
testing_required
testing_complete
certificate_ready
approved_for_marketed_use
blocked
```

No AI/model may promote a product into a child-directed marketing state based solely on appearance or user demand.

## Trigger a safety re-review when

- base resin/filament changes;
- pigment formulation changes;
- paint/ink/clearcoat changes;
- adhesive changes;
- accessible metal is added;
- breakaway geometry changes;
- age grading changes;
- supplier changes;
- a lab/certificate scope no longer matches the manufactured configuration.

## Sources

- CPSC Toy Safety guidance: https://www.cpsc.gov/Business--Manufacturing/Business-Education/Toy-Safety
- CPSC Small Parts guidance: https://www.cpsc.gov/Business--Manufacturing/Business-Education/Business-Guidance/Small-Parts-for-Toys-and-Childrens-Products
- CPSC Children's Product Certificate: https://www.cpsc.gov/Business--Manufacturing/Testing-Certification/Childrens-Product-Certificate
- CPSC Small Batch Manufacturers: https://www.cpsc.gov/Business--Manufacturing/Small-Business-Resources/Small-Batch-Manufacturers-and-Third-Party-
- CPSC Toy Safety FAQ: https://www.cpsc.gov/FAQ/Toy-Safety
