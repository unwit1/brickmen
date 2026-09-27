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

## Additive manufacturing extension — 2026-09-27

The custom-geometry stage now routes through the additive-manufacturing controller rather than assuming resin is always the final process.

### Process-routing extension

Before physical production:
1. classify part geometry and functional interfaces;
2. insert only validated parametric connector features;
3. determine feasible processes: MSLA/SLA, FDM, casting, printed injection tooling, traditional molding, outsource;
4. estimate cost/capacity/labor/risk using observed data;
5. select a validated machine/material/build/postprocess profile;
6. create the build artifact and immutable job manifest;
7. run slicer/slice-level preflight;
8. dispatch only if safety, traceability and qualification gates pass.

### Closed-loop physical feedback

After printing:
1. wash/cure/finish using the exact recorded profile;
2. retain sample identity through post-processing;
3. inspect critical dimensions;
4. collect fit/force/cycle evidence where required;
5. record visible defects and yield;
6. update cost/labor observations;
7. create a **candidate** compensation/profile revision;
8. require validation before production promotion.

### Automation rule

The pipeline may automatically generate, slice, queue, inspect and analyze known experiment/process classes. It must not silently promote an unvalidated connector, material blend, cure recipe or process change.

See:
- `additive-manufacturing-first-cell-plan.md`
- `automated-additive-manufacturing-cell.md`
- `parametric-cad-and-connector-automation.md`
- `additive-manufacturing-validation-program.md`
- `additive-manufacturing-economics-and-process-crossover.md`
- `data/additive-manufacturing-automation-contracts.json`
- `data/additive-process-selection-rules.json`
- `data/additive-first-experiments.json`

## Character-to-accessory geometry generation extension — 2026-09-27

Stage 6 custom geometry is expanded into a provider-neutral generation compiler.

### 6A. Accessory planning
- resolve exact Character/Incarnation/SourceAppearance;
- classify source features as existing part, decoration, cloth, new rigid geometry, new flexible geometry, or omit;
- create AccessoryDesignSpec for each required custom part.

### 6B. Reference preparation
- build AccessoryReferenceSet with orthogonal source views, context, official-style analogues and canonical mating-part geometry;
- segment/isolate the target object;
- mark hidden/inferred geometry explicitly.

### 6C. Controlled concept
- generate/reconstruct consistent front/back/left/right views at canonical scale;
- validate cross-view consistency before 3D generation.

### 6D. Geometry ensemble
Route by part class among:
- Tripo/Meshy commercial APIs;
- Hunyuan3D/TRELLIS/SPAR3D local models;
- direct CadQuery/build123d;
- CAD reconstruction such as CAD-Recode.

Generate multiple candidates rather than trusting first output.

### 6E. Geometry compiler
For each candidate:
- normalize units/scale;
- repair bounded topology problems;
- semantically isolate the visual shell;
- delete/untrust generated functional interfaces;
- attach validated parametric Brickmen connector geometry;
- apply articulation/keep-out volumes;
- enforce manufacturing minimum features;
- create deterministic manufacturing geometry.

### 6F. Critic loop
Render canonical views and score separately:
- source/reference fidelity;
- LEGO/minifigure abstraction;
- topology/geometry validity;
- connector and articulation correctness;
- selected-process DFM.

The orchestrator may edit/regenerate/switch provider/switch to CAD/split the part based on the failing dimension.

### 6G. Physical feedback
After a prototype, attach measurements, failure codes and photos to the GeometryCandidate lineage. Use accepted/rejected history to improve provider routing and candidate ranking.

See:
- `agentic-character-to-accessory-3d-generation.md`
- `data/3d-generation-provider-registry.json`
- `data/accessory-generation-benchmark.json`
- `parametric-cad-and-connector-automation.md`
- `additive-manufacturing-validation-program.md`
