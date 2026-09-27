# LDraw Geometry Ingestion for Brickmen Digital Twins

Research/implementation snapshot: 2026-09-27

Brickmen now has a deterministic path from a local LDraw library to flattened reference geometry, provenance manifests, bounding boxes, and OBJ meshes.

Implementation:
- `tools/geometry/ingest_ldraw_geometry.py`
- `tests/test_ldraw_geometry_ingestion.py`
- `data/ldraw-geometry-manifest.schema.json`
- `data/ldraw-geometry-ingestion-targets.json`

## Why this is the next Giant step

The earlier Giant pass resolved assembly frames from `10128p01c01.dat`, but frame origins alone cannot produce:

- front/back/side silhouette ground truth;
- shell depth;
- component bounding volumes;
- approximate collision envelopes;
- surface region correspondence;
- mesh-to-image render controls.

Full recursive geometry can.

## LDraw transform model

LDraw line type 1 is a subfile reference:

```
1 colour x y z a b c d e f g h i file
```

The `x y z` values are translation and the nine `a..i` values are the 3x3 transform applied to the child file. Brickmen recursively composes those transforms and flattens line-type 3 triangles and line-type 4 quads.

The resolver follows normal LDraw locations including:

- current file directory;
- `parts/`;
- `parts/s/` via normal relative references;
- `p/`;
- `p/48/` via normal primitive references;
- `models/`.

## Provenance and licensing

Do **not** attach one blanket license label to an ingested geometry tree.

The LDraw library contains legacy Contributor Agreement material identified by CC BY 2.0-era headers, while current contributor agreements allow CC BY 4.0 or CC0. Every source file therefore keeps:

- relative source path;
- SHA-256;
- author;
- `!LDRAW_ORG` classification;
- exact `!LICENSE` string;
- `!HELP`;
- history lines;
- occurrence count.

Attribution/export policy can then be calculated from the actual dependency graph.

## Geometry behavior

Current ingester:

1. resolves the root file from a local LDraw tree;
2. recursively follows type-1 references;
3. composes affine transforms;
4. tracks BFC `CERTIFY CW/CCW`, `INVERTNEXT`, and mirror parity for triangle winding;
5. emits type-3 triangles;
6. triangulates type-4 quads;
7. records type-2/type-5 counts without treating edge/conditional lines as surface triangles;
8. computes LDU and nominal-mm bounding boxes;
9. generates an optional deduplicated OBJ;
10. refuses unresolved dependencies by default.

## Authority boundary

The common 0.4 mm/LDU conversion is useful for reference geometry, but it does not convert LDraw into physical metrology.

LDraw-derived geometry may drive:

- reference rendering;
- digital-twin registration;
- visual envelope measurement;
- collision hypotheses;
- component segmentation;
- training/evaluation controls.

It may **not** by itself establish:

- pin/socket tolerance;
- interference;
- insertion/removal force;
- friction;
- wear;
- resin/FDM dimensional compensation;
- production articulation limits.

Those remain physical-validation outputs.

## Giant ingestion queue

Highest priority:
- complete Hulk shortcut `10128p01c01`;
- body `10128`;
- arms `10154` and `10124`;
- hands `10127` and `10126`;
- shoulder hardware reference `43093`.

After flattening, generate orthographic reference renders and derive front/back/side envelope observations directly from the known component assembly.

## Axl policy

The current `23763` work remains unofficial, so it can be ingested into a quarantined research tier for topology and registration experiments, but not promoted into printable connector authority.

This is especially useful because the current draft explicitly registers a standard `973` torso core with the oversized shell. Brickmen should preserve which geometry came from official donor components versus provisional shell work.

## Sources

- LDraw file format specification: https://ldraw.org/article/218.html
- LDraw current documentation index: https://library.ldraw.org/documentation
- LDraw contributor agreement: https://www.ldraw.org/docs-main/licenses/ldraw-org-contributor-agreement.html
- LDraw legal/library agreement information: https://www.ldraw.org/legal-info
- LDraw header/directory rules: https://library.ldraw.org/documentation/ldraworg-official-parts-library-standards/header-meta-commands
- LDraw primitive reference: https://wiki.ldraw.org/wiki/Primitives_Reference
