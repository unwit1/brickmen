# Color and Material Reference Sources for Visual Training

Research snapshot: 2026-09-24

## Why color needs multiple representations

A single RGB hex value is not "the LEGO color."

Separate:
- official/base color identity;
- catalog/display RGB approximation;
- physically measured plastic color;
- print ink target;
- rendered material;
- transparent/pearlescent/chrome/metal/rubber behavior.

Image generation should learn color *roles and relationships* from catalog images while manufacturing uses calibrated physical targets.

## LDraw LDConfig

LDraw's `LDConfig.ldr` is the canonical color definition file for the LDraw ecosystem.

It includes:
- LDraw color code;
- display RGB value;
- edge color;
- optional alpha;
- material tags such as CHROME, PEARLESCENT, RUBBER and SPECKLE;
- comments that map many colors to LEGO color IDs/names.

Source:
https://ldraw.org/article/547.html

Use for:
- renderer consistency;
- LDraw/BrickLink/Rebrickable crosswalk;
- coarse color role;
- material category.

Do not treat its display RGB as a calibrated measurement of physical ABS.

## BrickLink colors

BrickLink explicitly notes that its color names do not always match official LEGO names and it does not recognize every LEGO-released color.

Store:
- BrickLink ID/name;
- LEGO official name/ID when known;
- LDraw code/name;
- Rebrickable ID/name;
- active years;
- mapping confidence.

Source:
https://www.bricklink.com/help.asp?helpID=145

## Studio color/material representation

BrickLink Studio includes:
- Solid
- Transparent
- Chrome
- Pearl
- Metallic
- Milky
- Glitter
- Speckle
- Satin
- plus rendering-specific material types such as Rubber and luminous/glowing variants.

Source:
https://studiohelp.bricklink.com/hc/en-us/articles/5459441964695-Color-palette

These categories are useful supervision for material rendering, but Studio's display appearance is not a print calibration target.

## Mecabricks material maps

Mecabricks' decoration specification is particularly useful for separating:
- transparent print color texture;
- base material;
- metallic print;
- chrome/sticker behavior;
- sticker shape.

Its newer color texture specification says the printed/sticker areas are in the color texture while the background remains transparent; a separate data texture encodes metal/chrome/sticker information.

This is a strong conceptual template for Agent OS production masks even if Mecabricks source assets remain subject to separate rights review.

## Physical swatches

For production, create a local measured swatch table:
- official element ID / color;
- spectrophotometer or colorimeter reading where available;
- camera-session color-chart corrected RGB;
- printer/profile/substrate combination;
- measured ΔE against target;
- white-underbase state;
- clear/varnish state.

Keep physical measurement separate from web/catalog RGB.

## Training rule

The generative model should learn:
- which colors belong together;
- relative contrast;
- official palette tendencies;
- material category;
- where substrate color is intentionally left exposed.

A later production stage maps those semantic/color roles to calibrated device values.
