# Parts, Anatomy, Identification, and Donors

Treat the figure as an assembly: hair/headwear; head; neck accessory; torso shell; left/right arms; left/right hands; hips; left/right legs; cloth/capes/armor; handheld/accessory parts. Printed and dual-molded variants can have separate catalog identities.

## Surfaces
Track head front/back/wrap, torso front/back/sides, arms, hip front, leg fronts/sides and accessory faces separately. Curvature and joints make them different decoration problems.

## Identification
Record both design/part identity and color identity. Element IDs often identify a design/color/decorated combination. Rebrickable can cross-reference element IDs to part/color and external IDs. Brickognize can propose IDs from photos for parts, minifigs, sets and sticker sheets; confirm candidates before canonicalizing.

## Donor taxonomy
Maintain inventories for blank/minimally printed torsos; heads by base/skin color; arms/hands; hips/legs including dual molding; hair/headgear by silhouette; armor/neckwear/back accessories; capes/skirts/cloth; weapons/tools/props; display/packaging parts.

Choose donors by silhouette, then color, then print coverage/removability, then availability/cost. For production prefer parts with reliable supply rather than rare retired donors.

## Inventory fields
local_item_id, system, design_id, element_id, BrickLink item number, Rebrickable part number, description, color mappings, decoration, mold variant, quantity, condition, source, unit cost, storage bin, reserved project, photo, notes.

## Sources
https://www.lego.com/en-us/pick-and-build/pick-a-brick
https://rebrickable.com/api/v3/docs/
https://brickognize.com/
https://www.bricklink.com/


## Architecture-aware anatomy

The standard head/torso/arm/hand/hips/legs decomposition is only the baseline. Before applying anatomy assumptions, resolve `FigureArchitecture`.

Non-standard examples include:
- LEGO Giant bodies with Giant arms/hands and dedicated shoulder hardware;
- Hagrid-style giant-body hybrids using a standard-style head;
- Axl-style oversized torso/arms with standard head and lower body;
- Alpha Toys AF ~7 cm muscular bodies;
- maker-specific Bigguy, Mr.J/Heart, G (2), KDL and compatible BigFig systems;
- community MidFig constructions.

For every architecture store an explicit component graph and joint graph. Compatibility is per interface, not an all-or-nothing property. A body may accept a standard head but use proprietary arms, or use a standard-system bar while retaining proprietary wrist joints.

See `data/figure-architecture-registry.json` and `nonstandard-figure-architectures.md`.
