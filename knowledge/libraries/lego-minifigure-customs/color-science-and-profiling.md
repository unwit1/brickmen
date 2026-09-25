# Color Science and Profiling for UV Minifigure Printing

## Principle
Catalog RGB/hex values are identification/rendering references, not UV-printer recipes. Final color is a system response involving substrate, white underbase, ink, primer, varnish, RIP, screening/pass mode, curing and viewing conditions.

## Canonical color record
Store:
- local canonical color ID
- LEGO name/ID
- BrickLink name/ID
- Rebrickable ID
- LDraw code/name/value/edge/alpha/luminance/material
- measured sample identifier
- sRGB reference
- CIELAB measurement when available
- instrument/illuminant/observer
- gloss/finish
- source and date
- confidence

BrickLink explicitly notes that its names do not always match official LEGO names. LDraw's official LDConfig is valuable because it records color value, edge color, alpha/luminance and finish/material tags including chrome, pearlescent, rubber, matte metallic, metal, glitter, speckle and fabric.

## Physical master swatches
Build a physical library of genuine elements for important colors. Record mold/element, age if known, condition and measurement location. Do not assume two web RGB values prove physical equality.

## UV profiling matrix
Profile each meaningful combination:
printer × ink set × RIP mode × substrate color/material × primer × white-underbase recipe × varnish.

For each profile print:
- process-color patches,
- neutrals,
- skin/flesh targets,
- common LEGO color targets,
- saturated reds/blues/greens,
- dark near-black colors,
- light pastel colors,
- white-opacity ladder,
- overprint/underbase variants.

## Measurement
Prefer a spectrophotometer/colorimeter workflow for repeatability. Store raw measurements, not only subjective names. Calculate Delta E only when measurement conditions are comparable and preserve the formula used.

## Rendering versus manufacturing
Maintain separate values for:
- catalog/reference RGB,
- physically measured appearance,
- renderer material,
- UV printer target recipe.

Do not overwrite one with another.

## Special finishes
LDraw's finish/material metadata is useful for AI rendering, but printed metallic ink, molded pearl plastic, chrome plating and simulated metallic CMYK are physically different. Model them as separate material/process classes.

## Sources
https://www.bricklink.com/help.asp?helpID=145
https://ldraw.org/article/547.html
https://www.ldraw.org/article/299
