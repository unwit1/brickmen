# Geometry and Digital Twins

The repository should maintain a digital twin for every frequently used base part.

## Canonical representation
For each part:
- local canonical ID,
- LEGO design/element IDs if known,
- BrickLink ID,
- Rebrickable ID,
- LDraw file ID,
- Studio/PartDesigner ID,
- mesh source/license,
- physical measurements,
- print surfaces,
- connector definitions,
- coordinate frame,
- bounding box,
- UV/texture map,
- render presets,
- fixture/jig references.

## LDraw reference system
LDraw defines:
- right-handed coordinates,
- -Y as up,
- 20 LDU = one brick width/depth,
- 24 LDU = one brick height,
- 8 LDU = one plate height,
- approximately 0.4 mm per LDU.

The official library contains thousands of shapes and patterned parts and is useful for geometry/reference. The standard torso assembly references base torso 973 plus arm and hand parts in its assembly definitions.

## Example torso assembly references
LDraw's official torso shortcut records torso shell 973, arms 3818 and 3819, and hands 3820 in the standard assembly. This is valuable for exact digital assembly and AI conditioning.

## Digital-twin render bundle
Generate automatically for each part:
- perspective beauty render,
- orthographic front/back/left/right/top/bottom,
- depth maps,
- camera normals,
- world normals,
- silhouette,
- edge map,
- material ID,
- part ID,
- UV map reference,
- dimensions overlay.

## Print-surface annotation
Tag mesh polygons as:
- printable_primary,
- printable_secondary,
- curved_print,
- non_printable_joint,
- fixture_contact,
- hidden,
- high_risk_collision.

This lets Agent OS reason about whether artwork should be printed in one orientation, multiple indexed passes, or avoided.

## Physical validation
For every critical part, compare digital geometry to measured physical samples. Store:
- measurement tool,
- sample quantity,
- mean,
- min/max,
- part age/source,
- mold variation if observed.

Geometry imported from community CAD is a reference model, not guaranteed manufacturing metrology.

Sources:
https://www.ldraw.org/article/218.html
https://ldraw.org/article/512
https://library.ldraw.org/
https://library.ldraw.org/parts/37776
