# Non-Standard Figure Digital Twin Ingestion

Research snapshot: 2026-09-27

## Goal

Convert geometry/catalog/physical evidence into canonical **ArchitectureDigitalTwin** records that can support:
- recognition;
- generation;
- style analysis;
- articulation;
- connector engineering;
- printing;
- inspection.

## Source hierarchy

For geometry:
1. Brickmen physical metrology + scan;
2. official/manufacturer geometry where legitimately available;
3. official LDraw parts;
4. well-established structured community CAD;
5. physical photogrammetry/scan;
6. inferred geometry from images.

Manufacturing-critical dimensions always prefer physical validation.

## Ingest each component separately

Never flatten an architecture into one body mesh during ingestion.

For every component:
- source ID;
- part/mold ID;
- source status/license;
- file hash;
- coordinate system;
- units;
- mesh/BREP quality;
- bounding box;
- semantic component type;
- connection surfaces;
- printable surfaces;
- decoration surfaces.

## LDraw value

LDraw provides a particularly useful starting corpus because many non-standard official parts are already componentized.

Current confirmed examples:

### Modern BigFig
- 10154 Bigfig Arm Left — official.
- 10124 Bigfig Arm Right — official.
- 10126/10127 Giant hand family — official.

The 10124 file header explicitly gives the hand socket location in LDraw coordinates, making it useful for extracting a canonical wrist frame.

### Hagrid Half Giant
Current official LDraw list includes:
- 37777 torso;
- 37779 left arm with friction pin;
- 37783 right arm with friction pin;
- 38628/38630 arm+hand forms.

This provides direct component semantics and joint naming.

### Fantasy Era Troll
60671 is an official LDraw shortcut composed from multiple subparts, meaning Brickmen can explode it into an initial component graph before physical teardown.

### Axl
23763 currently exists in the Parts Tracker as an unofficial shortcut/body reference and is explicitly keyworded Axl/Giant/Midfig. It should remain marked unofficial and physically/catalog validated before it becomes geometry authority.

## Ingestion stages

### D0 — acquire
- download;
- preserve exact source URL;
- license;
- date;
- SHA-256;
- source status.

### D1 — parse
For LDraw:
- resolve references recursively;
- retain original LDU coordinate system;
- preserve color/material IDs;
- distinguish shortcut/subpart/primitive.

### D2 — normalize
Create Brickmen coordinate frame without destroying source coordinates.

Store:
- source transform;
- mm transform;
- canonical architecture frame.

### D3 — semantic component classification
Map part to:
- torso;
- arm;
- hand;
- lower body;
- head;
- hardware;
- armor;
- accessory.

### D4 — connector extraction
Automatically identify candidate:
- pin;
- axle;
- bar;
- stud;
- socket;
- bore;
- friction surfaces.

Use catalog/LDraw help metadata when available.

Every automatically extracted connector remains `candidate` until measured/validated.

### D5 — assembly graph
Resolve:
- parent/child component;
- joint center;
- joint axis;
- insertion direction;
- degrees of freedom.

### D6 — articulation
Generate swept volumes through the expected movement range.

### D7 — surfaces
Tag:
- visual shell;
- decoration;
- contact;
- joint;
- hidden;
- support-protected.

### D8 — canonical render bundle
Produce identical cameras/backgrounds for recognition and style learning.

### D9 — physical reconciliation
When a sample is available:
- align scan/measurements;
- calculate deviation;
- distinguish CAD approximation from mold reality;
- generate manufacturing connector profiles.

## LDraw units

Brickmen already records the LDraw convention:
- 20 LDU = one stud width;
- approximately 0.4 mm/LDU.

Do not use that conversion alone to declare precision fit dimensions. It is suitable for global geometry and initial frame locations, while final fit remains empirical.

## Digital-twin record

```json
{
  "digital_twin_id": "...",
  "architecture_id": "...",
  "revision": "...",
  "source_components": [],
  "source_hashes": [],
  "coordinate_systems": {},
  "component_graph": {},
  "joint_graph": {},
  "connector_candidates": [],
  "validated_connector_profile_ids": [],
  "landmarks": {},
  "articulation": {},
  "surface_schema_id": "...",
  "canonical_renders": [],
  "physical_reconciliation": {},
  "confidence": "..."
}
```

## Important separation

### Reference digital twin
Enough for:
- renders;
- recognition;
- style analysis;
- rough collision.

### Engineering digital twin
Requires:
- physical dimensions;
- joint metrology;
- force/cycle profiles;
- manufacturing compensation.

A reference twin must not silently become a printable mechanical master.

## Geometry reuse

When two releases use the same validated architecture component:
- link the same component master;
- store only release-specific decoration/shell differences.

This supports large custom catalogs without duplicating geometry.

## Model training outputs

From every digital twin derive:
- normalized multiview RGB;
- silhouette;
- depth;
- normals;
- part masks;
- joint masks;
- connector masks;
- point clouds;
- occupancy/SDF if useful;
- proportion vectors;
- component graph.

These become supervised inputs for architecture recognition and generation.

## Initial ingestion order

1. 10154/10124/10126/10127/43093 Giant component family.
2. 37777/37779/37783/38628/38630 Hagrid Half Giant.
3. 60671 Troll assembly/subparts.
4. Axl 23763 + arm components after source resolution.
5. legacy Hagrid 40250 from physical/catalog reconstruction.
6. measured Alpha/G(2)/other custom bodies only after sample acquisition.

## Sources

- LDraw Bigfig Arm Left list: https://library.ldraw.org/parts/list?tableSearch=10154.dat
- LDraw Bigfig Arm Right detail: https://library.ldraw.org/parts/213
- LDraw Half Giant list: https://library.ldraw.org/parts/list?tableSearch=3777.dat
- LDraw 2023-07 Half Giant update: https://library.ldraw.org/updates/view2307
- LDraw Troll 60671: https://library.ldraw.org/parts/30633
- LDraw Axl 23763 tracker record: https://library.ldraw.org/parts/51698
