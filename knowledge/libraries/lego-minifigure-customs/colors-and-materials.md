# Colors and Materials

## Never use one color-name field
LEGO official names, BrickLink names, Rebrickable IDs, LDraw IDs and community names can differ. BrickLink explicitly notes that its color names do not always match LEGO's. Rebrickable exposes color records with external mappings and RGB references.

Store a canonical local ID plus LEGO name/ID if known, BrickLink name/ID, Rebrickable ID, LDraw ID, RGB/hex reference, material/effect, active years, source and confidence. Examples of naming differences include BrickLink “Light Bluish Gray” versus LEGO “Medium Stone Grey.” Confirm mappings from catalog evidence.

## Physical color matching
Maintain real donor/swatches for commonly useful skin, clothing and equipment colors. Skin-tone matching is especially sensitive at head/neck/hands. Match against the actual part under consistent lighting, not a monitor.

Workflow: design in a color-managed application; print calibration patches around the target; cure/seal exactly as production; compare under neutral lighting; record the chosen correction for printer + ink + media + substrate; recalibrate when any component changes.

Transparent decals do not create opaque color. On dark parts, use white film, white ink/underbase, or substrate-aware art. Metallic/pearl/glow/speckle effects should be modeled as finishes/materials, not only RGB values.

## Paint
Record brand, line, finish, exact mix, thinner ratio, primer, coats and clear coat. Avoid friction surfaces because added thickness can interfere with joints.

## Sources
BrickLink Color Guide: https://v2.bricklink.com/en-us/catalog/color-guide
BrickLink color help: https://www.bricklink.com/help.asp?helpID=145
Rebrickable API: https://rebrickable.com/api/v3/docs/
LEGO Pick a Brick: https://www.lego.com/en-us/pick-and-build/pick-a-brick

## Additive-manufactured base color

For resin/FDM accessories, distinguish **color-through-material** from surface decoration.

Color-through-material is valuable because abrasion does not immediately expose a contrasting substrate and it can remove painting labor. It also creates a coupled materials problem: pigment/base changes can affect exposure, cure, dimensions, mechanics and surface finish.

### Resin color recipe record

Store:
- base resin/material profile;
- manufacturer/SKU/lot;
- pigment identities/lots;
- pigment quantities by mass or controlled volume;
- total batch mass/volume;
- mixing protocol/time;
- rest/degassing time if used;
- printer/exposure profile;
- wash/cure profile;
- measured CIELAB/spectral values;
- gloss;
- mechanical validation link;
- dimensional validation link;
- retained physical swatch.

Do not store only an RGB/hex target.

### Controlled color systems

Formlabs Color Kit is an example of a controlled CMYKW resin-pigment system with documented recipes. It demonstrates that repeatable color-through-resin workflows are feasible.

However, material choice still dominates function: the currently published Color Kit post-cured elongation at break is about 6%, far below the Tough 1500/2000 family. Therefore a perfect color match does not make Color Kit the correct material for a thin sword or repeated-fit connector.

AmeraLabs' 2026 TGM-7 guide states that its non-clear color variants can be mixed with one another while using common print settings. This is unusually attractive for Brickmen because TGM-7 is also designed around miniature durability. Brickmen must still validate the exact mixed color for connector dimensions and mechanics.

### LEGO-color matching workflow

1. select physical genuine/validated donor swatch;
2. measure under controlled conditions;
3. select mechanically acceptable base resin;
4. generate pigment recipe candidates;
5. print color + dimensional coupons together;
6. wash/cure exactly as production;
7. measure cured color;
8. measure critical dimensions;
9. test mechanics;
10. optimize recipe against both color error and functional constraints.

The optimizer should never minimize Delta E while ignoring fit/durability.

### Filament color

Treat filament manufacturer/color/lot as its own material profile. Multi-material/color FDM may reduce decoration for larger parts, but purge waste, nozzle size and surface texture usually make it a secondary option for fine minifigure accessories.

### Sources

- Formlabs Color Kit: https://formlabs.com/support/Using-Color-Kit/
- Formlabs Color Kit material page: https://formlabs.com/products/color-kit-form-4/
- AmeraLabs TGM-7 2026 printing guide: https://ameralabs.com/application-guide/tgm-7-resin-printing-guide/
