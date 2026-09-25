# Part Identification and Crosswalk

## Goal
Given a physical part, photo, catalog ID, LDraw file, BrickLink entry or Rebrickable entry, resolve it to the same canonical Agent OS part record without destroying source-specific distinctions.

## Identifier classes
- canonical local part ID
- LEGO Design ID
- LEGO Element ID
- LDraw filename
- LDraw alias/moved-to
- BrickLink item number
- Rebrickable part number
- Studio/PartDesigner identity
- supplier SKU
- user inventory ID

## Resolution rules
1. Exact authoritative identifier match outranks visual similarity.
2. A Design ID is not interchangeable with an Element ID.
3. Mould variants remain separate geometry records even if marketplaces group them.
4. Decorated/patterned versions link to, but do not replace, base geometry.
5. Aliases are explicit graph edges, not duplicate canonical records.
6. Photo recognition returns candidates, never unquestioned identity.
7. Physical measurements can disambiguate visually similar variants.

## Photo intake
For unknown parts:
- photograph front/back/sides and moulded-number areas;
- run recognition/catalog lookup;
- capture candidate IDs;
- compare silhouette and connection geometry;
- inspect mould marks/design numbers;
- verify against at least one catalog/geometry source;
- record confidence.

## Crosswalk conflicts
When sources disagree, store both assertions with provenance. Create a reconciliation record rather than overwriting a value.

## AI consequence
Generation prompts should use canonical local IDs plus the exact source geometry revision. Human-readable names are descriptive only.
