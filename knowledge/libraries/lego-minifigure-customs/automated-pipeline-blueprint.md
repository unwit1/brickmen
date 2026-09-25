# Automated Custom Minifigure Pipeline Blueprint

## Input
Character description and/or user-authorized reference images, desired fidelity, budget/run size, target production process, existing donor constraints.

## Stage 1: resolve physical architecture
Choose canonical torso/head/arm/hand/hip/leg/headgear/accessory IDs. Decide which shapes can use existing elements and which require custom resin geometry.

## Stage 2: assemble digital twin
Load exact geometry and colors. Apply deterministic pose/camera. Produce diagnostic render bundle.

## Stage 3: concept generation
Retrieve only relevant style grammar and character context. Condition generation on depth/normals/silhouette/part masks plus reference-image guidance where authorized.

## Stage 4: decoration extraction
Separate graphics from geometry. Reproject/trace into calibrated 2D print surfaces. Vector-clean and semantic-label artwork.

## Stage 5: manufacturing separation
Generate CMYK/color art, white underbase, primer mask where needed, varnish mask where needed, keep-out mask and proof render.

## Stage 6: custom geometry
For new resin pieces, create/clean sculpt, replace functional connectors with validated parametric connectors, check clearances, orient/support using the selected resin profile, print prototype and measure.

## Stage 7: proof
Render the exact final digital assembly with production artwork and resin parts. Generate front/back/side/3-4 views and an exploded BOM.

## Stage 8: physical prototype
Use named jig and UV profile. Record batch. Inspect registration, opacity, adhesion, color and articulation.

## Stage 9: feedback learning
Attach photos, measurements and defects to the batch. Update only empirical correction profiles supported by evidence.

## Stage 10: release
Freeze artwork revision, geometry revisions, BOM, manufacturing profile, QC standard, rights record and product photography.

## Safety gates
No automatic commercial release when rights status is unclear.
No unvalidated AI connector geometry.
No UV job outside machine/jig height constraints.
No silent substitution of part/mould/color.
No production promotion from a single unverified render.
