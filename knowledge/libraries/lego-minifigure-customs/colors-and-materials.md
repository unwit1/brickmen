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
