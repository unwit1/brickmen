# Resin Custom Minifigure Parts

Primary targets: hair, helmets, hats, armor, shoulder pieces, backpacks, weapons, props, creature features, heads and other nonstandard accessories.

## Design rule
Treat connection geometry as an engineering fit problem, not a visual approximation.

Separate a part into:
- visual shell,
- connection interface,
- clearance zones,
- articulation zones,
- stress zones,
- print supports/contact zones.

The connection interface should be independently parameterized so fit can be tuned without redesigning the sculpt.

## Geometry sources
Use LDraw/Studio/PartDesigner geometry as reference for existing part placement and connectivity. PartDesigner accepts OBJ, DAT and LDR objects and supports adding connectivity information for Studio use.

Do not assume LDraw’s approximate 0.4 mm/LDU is sufficient for press fits. Verify critical dimensions physically.

## Fit types
Use engineering categories:
- clearance/sliding fit,
- transition/push fit,
- interference/press fit.

For resin accessories intended to be repeatedly removed, avoid aggressive interference fits because brittle materials can crack or damage genuine parts.

## Calibration system
For every printer + resin + layer height create test coupons for:
- hole diameter,
- pin diameter,
- slot width,
- clip opening,
- wall thickness,
- peg/stud clearance,
- neck/head interface,
- hand-grip accessory diameter,
- headgear fit,
- armor neck-hole fit.

Print a ladder of dimensional offsets around nominal geometry and record measured outcomes.

Formlabs explicitly recommends fit tuning by printer/material and documents typical Form 4 dimensional tolerances in the hundredths-to-tenths of a millimeter range depending on feature size. Treat manufacturer numbers as a starting point only.

## Shrinkage and post-cure
Record:
- resin,
- printer,
- exposure profile,
- layer height,
- orientation,
- wash method/time,
- pre-cure measurement,
- post-cure method/time/temp,
- final measurement.

A fit that works before post-cure may tighten or loosen after cure.

## Orientation
Orient to protect visible surfaces and connection geometry:
- keep support scars away from display faces,
- avoid supports inside critical sockets where possible,
- orient long thin weapons to minimize warp,
- add drain paths to hollow parts,
- avoid unsupported suction-cup geometry.

## Minimum features
Maintain printer/resin-specific minimum wall, pin, hole, engraved line and raised detail tables. For reference, Formlabs' Form 4 guide recommends a 0.5 mm minimum hole and 0.75 mm minimum drain hole, but the actual hobby printer/resin combination must be calibrated separately.

## Surface finishing
Workflow options:
- wash/cure,
- support removal,
- micro-sanding,
- filler/primer,
- paint,
- UV print on resin,
- clear coat.

If UV-printing resin pieces, they need a separate substrate profile from ABS LEGO elements.

## Safety
Uncured photopolymer resin requires appropriate gloves, eye protection, ventilation/work practices and manufacturer-directed washing/curing. Keep contaminated tools segregated. Fully cure waste before disposal where local rules require; follow resin/SDS and local regulations.

## Part record
part_id, concept, CAD source, revision, units, canonical dimensions, connector family, nominal fit, printer, resin, layer height, exposure profile, orientation, support preset, dimensional compensation, wash, cure, measured dimensions, fit test results, UV print profile, paint profile, photos, failure notes.

## AI-assisted sculpting
AI can generate concept art, turnarounds and surface motifs, but functional geometry should be reconstructed in CAD/sculpting software with explicit dimensions. If a 3D generative model produces a mesh, retopologize/repair it and replace its connectors with validated parametric connection geometry.

## Studio integration
Import final OBJ into PartDesigner, set scale from known dimensions, add connectivity, and test in Studio before physical production.

Sources:
https://formlabs.com/global/blog/3D-printing-tolerances-for-engineering-fit/
https://formlabs.com/white-papers/form-4-design-guide/
https://studiohelp.bricklink.com/hc/en-us/articles/5872512112663-What-is-PartDesigner
https://studiohelp.bricklink.com/hc/en-us/articles/5877891573911-Importing-a-3D-object
