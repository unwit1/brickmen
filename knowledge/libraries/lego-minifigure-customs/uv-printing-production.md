# UV Printing Production Knowledge

This is the primary production process for the library.

## Core production stack
Treat UV printing as a layered manufacturing process, not just “print CMYK on plastic.” A production-ready job may contain:
1. substrate preparation,
2. selective primer,
3. white underbase,
4. CMYK/color layer,
5. optional varnish/clear layer,
6. cure/inspection,
7. adhesion/durability testing.

Commercial UV systems explicitly support this layered model. Roland workflows use spot colors for White, Gloss and Primer and can layer primer, white and CMYK. Mimaki systems combine primer, white, CMYK and clear. Epson V-series systems support white and varnish layers, with RIP workflows able to generate separate white and varnish plates.

## White underbase
White ink is critical on dark, saturated, translucent or transparent substrates. The underbase must be treated as its own plate:
- generate it from final artwork,
- allow configurable choke/spread,
- support full-underbase, selective-underbase and no-underbase regions,
- record number of white passes,
- record print order,
- inspect for white halos caused by registration error.

For AI-generated artwork, the model should generate *separate masks* for CMYK art, white underbase and varnish rather than one flattened image.

## Primer
ABS and other plastics may need adhesion testing and, depending on printer/ink/substrate, primer. Mimaki documents selective inkjet primer as an adhesion aid on difficult substrates; Roland supports printable primer spot colors. Do not assume one primer recipe works on all LEGO colors, lots, genuine/compatible plastics, resins, paints or coatings.

For each substrate create an adhesion profile:
- part/material source,
- surface color,
- cleaning method,
- primer type,
- primer coverage,
- primer pass count,
- cure settings,
- ink set,
- print mode,
- post-cure,
- adhesion test result.

## Clear / varnish
Clear/varnish can alter gloss, tactile height and durability. Store three independent intentions:
- protective clear,
- selective gloss/matte styling,
- intentional raised texture.

Avoid unnecessary build-up on moving or mating surfaces.

## Jigs and fixturing
Jigs are first-class production assets. Each jig record should contain:
- printer model,
- bed origin,
- fixture origin,
- minifigure part/mold IDs,
- orientation,
- cavity coordinates,
- Z-height / datum,
- printable surface(s),
- keep-out areas,
- locating features,
- fixture material,
- revision,
- CAD source,
- calibration test image,
- measured repeatability.

Create separate fixtures for heads, torso shells, arms, hands, hips, legs, shields, tiles and custom resin parts. For cylindrical or compound surfaces, consider indexed multi-orientation jigs instead of trying to print around an entire shape in one pass.

## Z-height and collision safety
Direct-to-object UV printing is sensitive to object height. Maintain a machine-specific maximum-height profile and a per-jig validated Z datum. Any resin accessory or nonstandard part should be measured before loading. A raised component can risk head strikes.

## Artwork layers
Recommended production document layers:
- ART_CMYK
- ART_WHITE
- ART_PRIMER
- ART_VARNISH
- CUT/BOUNDARY
- SAFE_AREA
- KEEP_OUT
- REGISTRATION
- PART_OUTLINE
- NOTES
- JIG_ORIGIN

Where the RIP supports named spot colors, map these layers to the printer's required spot-color names.

## Calibration targets
Create a UV calibration sheet for each machine/profile:
- fine line ladder,
- microtext,
- registration crosshairs,
- white choke/spread ladder,
- solid CMYK patches,
- gradient patches,
- target LEGO color patches,
- varnish texture samples,
- primer/no-primer comparison,
- one-pass/two-pass white comparison,
- black rich-black variants,
- tiny facial-feature tests.

Use actual minifigure-scale features, not only large printer test charts.

## Color profiling
Store:
- printer,
- RIP,
- print mode,
- resolution,
- pass count,
- ink configuration,
- substrate,
- primer state,
- white-underbase state,
- varnish state,
- ICC/profile identifier,
- measured swatch results.

A single RGB/hex LEGO color is not sufficient to predict UV output. Maintain printer-specific correction tables.

## Production failure modes
- weak adhesion,
- scratching/chipping,
- white halo,
- CMYK/white misregistration,
- color shift,
- overspray,
- banding,
- grain,
- under-cured surface,
- raised edge,
- jig slippage,
- wrong Z,
- gloss mismatch,
- print on joint/connection surface,
- dust/static contamination.

## Recommended experiments
1. genuine ABS color-by-color adhesion matrix;
2. primer vs no-primer test;
3. white-pass opacity ladder;
4. underbase choke ladder;
5. varnish finish comparison;
6. abrasion/scratch test;
7. hand-oil contamination test;
8. multi-orientation jig repeatability test;
9. resin accessory adhesion matrix;
10. print-height tolerance/collision safety test.

## Sources
Roland spot-color workflow:
https://downloadcenter.rolanddg.com/contents/manuals/VW7_USE_EN/yqk1740128431226.html

Roland layered primer/white/CMYK:
https://downloadcenter.rolanddg.com/contents/manuals/VW6_USE_English/gco1696484575543.html

Mimaki selective primer, white and clear:
https://vietnam.mimaki.com/product/inkjet/i-flat/ujf-3042mkII-ex/feature.html

Epson UV white and varnish:
https://epson.com/uv-flatbed-printer

Epson V4000 multi-layer user guide:
https://files.support.epson.com/docid/other/cmp0521_ug_en.pdf
