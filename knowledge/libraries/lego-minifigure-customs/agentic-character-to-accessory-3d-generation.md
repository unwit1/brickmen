# Agentic Character-to-Printable-Accessory Generation

Research snapshot: 2026-09-27.

## Goal

Enable a user to ask:

> "Make LEGO-compatible accessories for Character X."

and have Brickmen autonomously:

1. resolve the exact character/incarnation/source appearance;
2. determine which features should become custom 3D geometry;
3. retrieve visual references and analogous minifigure/custom-part geometry;
4. create consistent concept views;
5. generate one or more candidate 3D shells;
6. convert/repair those shells into deterministic manufacturing geometry;
7. insert validated LEGO-compatible functional interfaces;
8. validate scale, articulation, wall thickness, topology and printability;
9. render the finished part back into the canonical minifigure scene;
10. compare it to the source references and LEGO-style grammar;
11. iterate automatically;
12. output a traceable 3MF/STEP/STL package for the selected production profile.

The main architectural rule is:

**Generative models may propose the visual shell. Deterministic CAD and Brickmen's validated connector library remain the authority for dimensions, interfaces and manufacturing constraints.**

This prevents progress in visual AI from being coupled to connector reliability.

---

## Why a monolithic text-to-3D model is the wrong target

A general 3D model must simultaneously infer:

- which character version is intended;
- what visual details matter;
- what should be represented as 3D geometry instead of printed decoration;
- minifigure-scale abstraction;
- accessory scale;
- exact connection geometry;
- arm/head/body clearance;
- minimum printable feature size;
- support/orientation implications;
- manufacturable topology.

Current text/image-to-3D systems are good enough to generate useful visual shells but they do not provide evidence that they can guarantee tiny functional interfaces or LEGO-compatible tolerances.

The correct architecture is therefore modular and closed-loop.

---

# End-state pipeline

```
User request
  -> Character / appearance resolver
  -> Accessory opportunity planner
  -> Reference bundle builder
  -> LEGO abstraction planner
  -> Multiview concept generator
  -> 3D candidate generator ensemble
  -> Candidate normalization
  -> Semantic part decomposition
  -> Parametric connector insertion
  -> Articulation / keep-out enforcement
  -> Mesh / CAD repair
  -> DFM + printability checks
  -> Canonical renders
  -> Visual fidelity + LEGO-style critic
  -> Geometry / manufacturing critic
  -> Automatic repair / regeneration loop
  -> Process-specific compensation
  -> 3MF / STEP / STL build package
  -> Slice preflight
  -> physical prototype
  -> measurement feedback
  -> generator/profile learning
```

Every stage creates provenance and an explicit confidence score.

---

# 1. Character and appearance resolution

Brickmen already has much of the required foundation:

Character -> Incarnation -> SourceAppearance -> OutfitDesign

The generation agent should never begin from a raw character name if a more specific appearance can be resolved.

Example request:

> make accessories for Aragorn

Possible unresolved questions:
- Fellowship / Two Towers / Return of the King;
- Strider versus Gondor armor;
- film versus book-inspired;
- sword Andúril versus Ranger sword;
- cloak, crown, armor and scabbard state.

The resolver should build:

```json
{
  "character_id": "...",
  "appearance_id": "...",
  "outfit_design_id": "...",
  "source_confidence": "...",
  "identity_critical_features": [],
  "available_reference_views": [],
  "uncertainties": []
}
```

The system may generate several design branches if more than one appearance is plausible rather than silently choosing.

---

# 2. Accessory opportunity planning

Before generating geometry, determine **what should actually be a new mould/printed part**.

Classify source features into:

- existing canonical LEGO-compatible part;
- donor part with decoration only;
- 2D printed/decal feature;
- cloth/soft-goods feature;
- custom rigid 3D accessory;
- custom flexible component;
- omit/simplify;
- uncertain.

Examples:

A character's chest straps are usually decoration.

A large shoulder pauldron may require custom geometry.

A helmet crest may be:
- incorporated into the helmet shell;
- a separate removable attachment;
- represented graphically,
depending on source evidence and manufacturability.

The planner should score each proposed custom part on:

- identity importance;
- availability of existing parts;
- source visibility;
- expected printability;
- articulation impact;
- complexity;
- mechanical risk;
- reuse potential across characters;
- expected demand.

This stage avoids generating unnecessary custom geometry.

---

# 3. Reference bundle generation

The agent should construct an **AccessoryReferenceSet**, not dump every character image into a model.

Desired roles:

- object/front;
- object/back;
- object/left;
- object/right;
- object/top/bottom when relevant;
- full-character context;
- detail close-up;
- silhouette reference;
- material reference;
- alternate-state reference;
- closest official LEGO analogue;
- closest existing accessory analogue;
- canonical mating-part geometry.

Separate:
- source-appearance authority;
- geometry analogue;
- LEGO-style analogue.

A real-world sword may provide identity geometry, while official minifigure swords provide abstraction/style/scale precedent.

---

# 4. Source segmentation and accessory isolation

Research target: automatic extraction of the relevant object from character references.

Useful technologies:

- SAM 2 for image/video segmentation;
- open-vocabulary object localization;
- VLM-guided masks;
- game-model/component extraction when permitted by the source pipeline;
- optical-flow/video tracking for objects across frames.

The result should not simply be a raster crop.

Store:
- mask;
- confidence;
- source image;
- occlusion;
- inferred hidden regions;
- orientation;
- semantic label;
- material clues.

For a sword partially hidden behind a character, the agent should explicitly mark the missing geometry as inferred rather than source-observed.

Meta's SAM 2 is suitable as a segmentation primitive because it supports promptable object segmentation across images and video.

---

# 5. LEGO/minifigure abstraction before 3D generation

This is a critical Brickmen-specific advantage.

Do not ask a 3D generator to recreate the real object literally and only scale it down afterward.

Generate an **AccessoryDesignSpec** first:

```json
{
  "part_type": "helmet",
  "visual_role": "source_fidelity",
  "source_features": [],
  "features_to_preserve": [],
  "features_to_simplify": [],
  "features_to_omit": [],
  "target_dimensions_mm": {},
  "target_style_profile": "...",
  "mating_interfaces": ["headwear_socket"],
  "articulation_keepouts": [],
  "minimum_feature_profile": "...",
  "symmetry": "...",
  "separate_components": []
}
```

Translation rules should be learned from:
- official accessory geometry;
- LDraw/other allowed digital twins;
- Brickmen physical measurements;
- source-to-official LEGO translation pairs;
- accepted custom extensions.

Research should specifically study:
- real sword -> LEGO sword simplification;
- human helmet -> minifigure helmet;
- realistic hair -> minifigure hair;
- fabric armor -> rigid minifigure armor;
- firearm/tool proportions;
- fantasy horns/wings;
- capes/skirts/robes.

This creates a reusable **3D accessory grammar**, analogous to the existing 2D decoration grammar.

---

# 6. Multiview concept generation

Current 3D systems generally benefit from image conditioning, and multiple consistent views reduce ambiguity.

TRELLIS explicitly recommends image-conditioned generation over direct text-to-3D for detail/creativity. Tripo and Meshy expose multiview-to-3D APIs.

Brickmen should therefore use:

```
character/source references
 -> AccessoryDesignSpec
 -> controlled front view
 -> controlled side view
 -> controlled rear view
 -> optional top view
 -> multiview consistency check
 -> 3D generator
```

The views should use:
- orthographic or near-orthographic cameras;
- neutral lighting;
- no perspective exaggeration;
- constant scale;
- consistent shape;
- plain background;
- no minifigure hand/head unless intentionally needed for scale.

The image-generation system should receive a canonical silhouette/feature spec so it does not redesign the object independently from each angle.

---

# 7. 3D generator ensemble

Do not hard-code one provider.

Create a provider-neutral interface:

```
geometry.generate(
    design_spec,
    reference_images,
    multiview_images,
    provider,
    model_version,
    seed,
    settings
)
```

Generate multiple candidates from multiple systems and score them.

## Tripo

Current v3 API supports:
- text to model;
- image to model;
- multiview to model;
- image-to-multiview;
- mesh segmentation;
- mesh completion;
- decimation;
- texturing;
- model conversion.

Tripo H3.1 (v3.1-20260211) currently supports text, image and multiview inputs, detailed geometry, up to approximately 2M faces and PBR output.

Particularly relevant Brickmen capabilities:
- multiview generation;
- repeatable seed behavior;
- semantic mesh segmentation;
- "generate in parts";
- low-poly/smart topology options.

## Meshy

Current API supports:
- text-to-3D;
- image-to-3D;
- multi-image-to-3D;
- smart topology;
- remeshing;
- STL/3MF export;
- printability repair;
- MCP integration for agents.

Meshy currently exposes 3MF generation and a dedicated print-repair endpoint that repairs non-manifold edges, holes and degenerate topology.

This makes Meshy useful both as:
- a generator;
- a post-generation repair service.

## Hunyuan3D 2.1

Strong open-source research candidate:
- image-to-shape;
- PBR texture generation;
- released weights;
- released training code;
- local deployment;
- fine-tuning research potential.

Current published VRAM requirements are roughly:
- 10 GB shape generation;
- 21 GB texture;
- 29 GB combined.

For Brickmen, geometry-only operation is often enough because the manufacturing shell and decoration pipeline are separate.

## TRELLIS

Important open research platform:
- text and image conditioning;
- multi-image conditioning;
- mesh output;
- variants/local editing;
- training code;
- 500K curated 3D dataset.

TRELLIS documentation itself recommends text -> image -> image-conditioned 3D rather than relying only on text-conditioned 3D.

## SPAR3D / Stable Fast 3D

Useful low-latency candidate-generation systems.

SPAR3D reconstructs a 3D mesh from one image and explicitly improves hidden/backside inference through point-cloud conditioning.

These models are valuable for:
- large candidate ensembles;
- fast prototyping;
- comparing generated backside hypotheses.

## Commercial provider policy

Store for every generation:
- provider;
- exact model snapshot;
- API version;
- license/terms snapshot;
- cost;
- seed;
- inputs;
- generated asset hash.

Models will change frequently. Benchmark exact snapshots, not brand names.

---

# 8. Direct CAD generation research

Some accessories should bypass free-form mesh generation.

Examples:
- simple sci-fi blaster;
- rectangular backpack;
- shield;
- mechanical tool;
- scabbard;
- boxy armor;
- studs/connectors;
- repeated geometric motifs.

Research three paths:

## LLM -> CadQuery/build123d code

CadQuery and build123d are Python/OpenCascade parametric CAD systems suitable for headless deterministic execution.

A coding agent can:
1. write CAD code;
2. execute it;
3. render the result;
4. inspect the render;
5. modify parameters/code;
6. export STEP/3MF.

Existing Cadmium demonstrates this pattern using an LLM that writes CadQuery, renders multiple viewpoints, and iteratively improves the model.

## Text-to-CAD APIs

Zoo exposes text-to-CAD through its API/KCL ecosystem.

This should be benchmarked for:
- simple weapons;
- shields;
- backpacks;
- mechanical props.

## Mesh/point cloud -> parametric CAD

CAD-Recode is particularly interesting:
- input: point cloud;
- output: executable CadQuery Python;
- based on a language model;
- trained on a procedurally generated 1M-CAD-program dataset.

Research route:

```
AI-generated shell
 -> sample/regularize point cloud
 -> CAD-Recode
 -> editable CadQuery approximation
 -> Brickmen connector insertion
 -> deterministic manufacturing model
```

This will likely work best on mechanical/hard-surface accessories rather than sculpted hair or organic helmets.

---

# 9. Hybrid mesh + CAD construction

This should be the default for complex parts.

Example helmet:

```
AI mesh exterior shell
 + deterministic head socket
 + deterministic wall-thickness operation
 + deterministic inner clearance
 + deterministic brim/neck keep-out
 = manufacturing model
```

Example sword:

```
AI/generated blade + guard + pommel
 + validated parametric hand bar
 + controlled root fillet
 + blade-thickness DFM
 = manufacturing model
```

The visual shell can change without changing the connector.

---

# 10. Semantic decomposition

Generated assets should be segmented into meaningful regions:

- decorative shell;
- grip;
- socket;
- support-sensitive detail;
- removable attachment;
- left/right symmetric elements;
- separate physical pieces.

Tripo's current mesh segmentation endpoint can automatically split geometry and its v2 beta supports semantic labeling plus reference-image guidance.

This suggests a useful pipeline:

```
generated mesh
 -> semantic segmentation
 -> identify unwanted/generated connector
 -> remove it
 -> preserve visual shell
 -> insert Brickmen connector
```

For providers without semantic mesh segmentation, use:
- connected-component analysis;
- curvature/feature analysis;
- VLM-assisted rendered masks;
- spatial rules.

---

# 11. Mesh normalization and repair

Every generative mesh should pass through deterministic geometry QA.

Check:
- correct units;
- correct scale;
- watertightness;
- manifoldness;
- self-intersections;
- duplicate vertices/faces;
- inverted normals;
- disconnected debris;
- degenerate triangles;
- tiny floating components;
- minimum thickness;
- internal surfaces;
- trapped volumes;
- excessive triangle count;
- bounding box.

Useful libraries:
- Trimesh: Python mesh loading, watertight analysis and repair helpers;
- CGAL Polygon Mesh Processing: robust intersection detection, repair, remeshing and Boolean operations;
- Open3D: mesh processing, simplification and point-cloud operations;
- Blender Python API: scripted geometry/modifier operations.

Use automated repairs only where the transformation is bounded and auditable.

A repair that changes the silhouette or identity-critical feature should trigger regeneration or review.

---

# 12. Canonical LEGO-compatible scale

Generative models should never decide final size.

The AccessoryDesignSpec declares:
- target connector frame;
- total allowed envelope;
- expected min/max dimensions;
- canonical minifigure mating part;
- articulation envelope.

The generated shell is aligned to a canonical digital twin.

Use optimization to fit:
- reference silhouette;
- intended LEGO-scale aesthetic;
- connector location;
- keep-out envelope.

Scale should be explicit in millimeters before DFM.

---

# 13. Articulation and collision solver

For helmets/armor/backpacks/accessories, automatically simulate movement.

Examples:

Helmet:
- head rotation;
- torso collision;
- shoulder collision;
- back accessory conflict.

Neck armor:
- head rotation;
- arm sweep;
- shoulder height;
- torso top.

Weapon:
- hand grip;
- arm movement;
- torso/leg collision;
- secondary grip where applicable.

Backpack:
- neck/helmet clearance;
- arm sweep;
- stud/back-interface clearance.

Store swept keep-out volumes in the digital-twin library.

Reject candidate geometry that intersects forbidden volumes beyond tolerance.

---

# 14. Minimum-feature and wall-thickness enforcement

The manufacturing profile already knows printer/material limits.

Apply an automatic thickness transform:

- detect too-thin regions;
- locally thicken from the hidden/internal side where possible;
- preserve external silhouette;
- protect detail;
- re-render and re-score.

For a sword:
- grip remains connector-controlled;
- blade root may need thickening;
- free blade can preserve visual taper within minimum feature rules.

For hair:
- isolated strands may merge into stylized clumps.

This is where "LEGO abstraction" and manufacturability reinforce each other.

---

# 15. Render-critic-repair loop

This is one of the most important research directions.

Existing agentic CAD projects already demonstrate the pattern:

```
generate code/model
 -> execute
 -> render multiple views
 -> vision model critiques
 -> revise
```

Brickmen can make this much stronger because the critic has structured targets.

For every candidate, render:

- front;
- rear;
- left;
- right;
- 3/4;
- top if relevant;
- attached to canonical minifigure;
- exploded connector view;
- clay;
- silhouette;
- normal/depth.

Critics:

### Source fidelity critic
Compare:
- silhouette;
- proportions;
- identity-critical features;
- curvature/ornament;
- source-specific asymmetry.

### LEGO abstraction critic
Compare against:
- official accessory analogues;
- theme/era grammar;
- detail density;
- thickness;
- proportions.

### Geometry critic
Check:
- connector placement;
- symmetry requirements;
- keep-outs;
- topology;
- wall thickness.

### Production critic
Check:
- printable orientation;
- supports;
- trapped resin;
- thin features;
- expected postprocess damage.

The orchestrator decides whether to:
- edit;
- regenerate;
- choose a different provider;
- switch to CAD;
- simplify;
- split into multiple components.

---

# 16. Automated visual scoring

Do not rely on one VLM score.

Build a metric bundle:

- silhouette IoU against approved concept/reference;
- landmark distance;
- multi-view silhouette consistency;
- bounding-box/proportion error;
- render-reference embedding similarity;
- surface-normal consistency where a 3D reference exists;
- symmetry error;
- closest-official-accessory embedding similarity;
- identity-critical-feature presence classifier.

Human preference labels can later train a ranking model.

The score should select candidates, not redefine source truth.

---

# 17. Candidate ensemble / best-of-N research

For each AccessoryDesignSpec:

1. generate N multiview concept bundles;
2. generate M 3D candidates per concept/provider;
3. normalize;
4. automatically eliminate invalid topology/scale;
5. render;
6. score;
7. keep top K;
8. repair/refine;
9. select final.

This is likely much more reliable than expecting one generation to be perfect.

Track:
- success rate;
- cost;
- latency;
- number of repair iterations;
- final acceptance;
per provider and part class.

The router then learns:

- Tripo works best for helmets;
- Hunyuan is strongest for ornamental weapons;
- direct CadQuery is strongest for shields;
- SPAR3D is cheap for candidate variation;

or whatever the empirical results actually show.

---

# 18. Provider benchmark program

Benchmark every model on the same accessory suite.

Part families:

- straight sword;
- curved sword;
- axe;
- spear;
- shield;
- handgun/blaster;
- rifle;
- backpack;
- simple helmet;
- ornate helmet;
- hair;
- shoulder armor;
- chest/neck armor;
- horns;
- creature appendage;
- staff;
- scabbard;
- mechanical tool.

Difficulty axes:
- symmetry;
- thinness;
- fine relief;
- occlusion;
- organic curvature;
- hard-surface detail;
- multiple components;
- source fidelity.

Metrics:
- valid generation rate;
- watertight rate;
- self-intersection rate;
- automatic repair success;
- multi-view consistency;
- fidelity;
- LEGO abstraction;
- minimum-feature violations;
- connector-integration success;
- final print acceptance;
- generation cost;
- GPU/time;
- human intervention minutes.

Store exact model versions.

---

# 19. Dataset construction

The most valuable Brickmen-specific research may be building a supervised accessory corpus.

Create:

```
SourceObject
 -> AccessoryDesignSpec
 -> Official/validated LEGO-like analogue
 -> 3D geometry
 -> canonical multiview renders
 -> dimensions
 -> connector
 -> manufacturing profile
 -> print outcome
```

Dataset categories:
- official physical accessories;
- allowed third-party/custom references;
- Brickmen original/validated parts;
- synthetic procedural accessories;
- negative/failure examples.

For every 3D accessory derive:
- clay renders;
- silhouettes;
- depth;
- normals;
- curvature;
- part masks;
- voxel/SDF/point-cloud representations;
- feature descriptors.

High-value translation pairs:
- source weapon -> official LEGO adaptation;
- source helmet -> official adaptation;
- source hair -> official hair;
- realistic armor -> minifigure armor.

These pairs can train a future "minifigure geometry abstraction" model rather than a generic 3D model.

---

# 20. Synthetic training data

Brickmen can generate large amounts of legally controlled synthetic data from parametric primitives.

Generate random but plausible:
- swords;
- axes;
- shields;
- helmets;
- backpacks;
- horns;
- sci-fi weapons;
- armor.

For each:
- save exact CAD program;
- render multiview images;
- generate point cloud;
- generate mesh;
- store dimensions and semantic parameters.

This can train:
- image -> CAD;
- point cloud -> CAD;
- visual parameter extraction;
- DFM classifier;
- geometry critic.

CAD-Recode itself demonstrates the usefulness of procedurally generated CAD-program data at large scale.

---

# 21. Fine-tuning versus retrieval

Do not fine-tune immediately.

Phase order:

### Phase 1 — retrieval/prompting
Use Brickmen RAG:
- source appearance;
- accessory analogues;
- style grammar;
- target dimensions.

### Phase 2 — provider routing
Learn which generator/settings work by part class.

### Phase 3 — critic/ranker training
Train on accepted/rejected outputs.

### Phase 4 — adapter/fine-tune open 3D model
Hunyuan3D 2.1 and TRELLIS are research candidates because weights/training code are available.

Potential training target:
- input: consistent accessory reference views;
- output: better minifigure-scale shell geometry.

### Phase 5 — dedicated geometry abstraction model
Train specifically on source-object -> Brickmen-accessory pairs.

Keep connector geometry outside the learned model even after fine-tuning.

---

# 22. Learning from physical prints

The ultimate data advantage is physical feedback.

For every generated part:
- generation provider/version;
- seed/settings;
- concept version;
- mesh repair operations;
- final CAD operations;
- printer/material/profile;
- measurements;
- force test;
- defects;
- photographs;
- acceptance;
- user preference.

The system can learn:

```
visual generation features
 -> predicted manufacturability
 -> predicted print defect risk
 -> predicted human acceptance
```

Eventually it can reject fragile-looking geometry before slicing.

---

# 23. Self-improving geometry agent

Create separate agents/services rather than one huge prompt:

### AppearanceAgent
Resolves exact character/version/reference.

### AccessoryPlanner
Decides which geometry should exist.

### ConceptAgent
Creates the AccessoryDesignSpec and multiview concept.

### GeometryRouter
Chooses Tripo/Meshy/Hunyuan/TRELLIS/CAD.

### CADAgent
Creates or refines parametric hard-surface geometry.

### MeshAgent
Repairs/normalizes generative geometry.

### ConnectorAgent
Applies approved parametric interfaces.

### DFMEngine
Deterministic checks and compensations.

### VisualCritic
Checks reference/style fidelity.

### GeometryCritic
Checks dimensions/collision/topology.

### ManufacturingCritic
Checks printability and selected material.

### ExperimentAgent
Creates validation coupons when confidence is insufficient.

### ReleaseAgent
Packages approved geometry and provenance.

None of these agents may override deterministic safety/manufacturing gates.

---

# 24. Suggested API surface

```
accessory.resolve_character()
accessory.plan_components()
accessory.build_reference_set()
accessory.generate_design_spec()
accessory.generate_multiview()
geometry.providers()
geometry.generate()
geometry.segment()
geometry.normalize()
geometry.repair()
geometry.render_bundle()
geometry.score()
geometry.iterate()
cad.generate()
cad.reconstruct()
connector.attach()
articulation.check()
dfm.check()
dfm.repair()
manufacturing.package()
generation.benchmark()
generation.feedback()
```

---

# 25. Research implementation phases

## Phase G0 — schemas and benchmark harness

Implement:
- AccessoryDesignSpec;
- AccessoryReferenceSet;
- GeometryCandidate;
- GeometryEvaluation;
- provider registry;
- exact-version provenance;
- canonical render harness;
- benchmark part suite.

No new ML training.

## Phase G1 — commercial API ensemble

Adapters:
- Tripo;
- Meshy.

Test:
- text;
- image;
- multiview;
- topology settings;
- segmentation;
- remesh/print repair.

Objective:
establish a strong baseline quickly.

## Phase G2 — local open-model lab

Deploy:
- Hunyuan3D 2.1;
- TRELLIS;
- SPAR3D / Stable Fast 3D.

Run the identical benchmark.

Objective:
cost/privacy/control and future fine-tuning.

## Phase G3 — parametric CAD agent

Implement:
- CadQuery/build123d agent;
- rendering feedback loop;
- deterministic executor sandbox;
- simple accessory tasks.

Evaluate against mesh generators.

## Phase G4 — hybrid geometry compiler

Implement:
- semantic segmentation;
- shell extraction;
- connector deletion;
- parametric connector insertion;
- automatic wall thickness;
- keep-outs;
- mesh/CAD Boolean pipeline.

This is the most important engineering milestone.

## Phase G5 — visual critic loop

Implement automatic:
- canonical renders;
- silhouette/landmark metrics;
- VLM critique;
- source fidelity;
- LEGO-style fidelity;
- regeneration/edit selection.

## Phase G6 — physical-feedback integration

Connect to the additive validation system.

Every printed generation becomes training/evaluation evidence.

## Phase G7 — learned router/ranker

Train:
- provider selection model;
- candidate ranking model;
- failure-risk model.

## Phase G8 — Brickmen-specific fine tuning

Only after enough accepted geometry exists:
- fine-tune open model or adapters;
- build source->minifigure accessory translation pairs;
- evaluate against frozen benchmark.

---

# 26. What can be automated today

A credible prototype can already automate:

1. character lookup/reference retrieval;
2. object/reference segmentation;
3. multiview concept creation;
4. Tripo/Meshy generation via API;
5. local Hunyuan/TRELLIS generation;
6. automatic mesh repair/normalization;
7. generated connector removal;
8. validated connector insertion;
9. collision checks against the canonical figure;
10. minimum-feature checks;
11. render-based scoring;
12. iterative generation;
13. 3MF/STL export;
14. slicing/preflight.

The main unsolved part is not "can software generate a printable mesh?" It is achieving **consistently excellent source fidelity and minifigure design judgment without manual art direction**.

That is primarily a dataset + critic + routing problem.

---

# 27. Highest-priority research questions

1. Does multiview conditioning materially outperform a single carefully generated concept image for each accessory class?
2. Which current 3D generator wins per part class after deterministic connector replacement?
3. How much candidate quality improves by using a LEGO-abstracted concept image rather than a literal source image?
4. Can CAD-Recode turn hard-surface generated meshes into useful editable CadQuery code?
5. Can a VLM reliably identify and remove invented connector geometry?
6. What automatic visual metrics correlate with human judgment of "looks like an official minifigure accessory"?
7. What is the best representation for custom training: mesh, point cloud, SDF, latent, CadQuery code, or multimodal bundle?
8. How many accepted source->accessory pairs are needed before Brickmen-specific fine tuning improves over retrieval/ensemble generation?
9. Can the manufacturing critic predict thin-feature/warp failures from geometry before slicing?
10. Can print-result photographs and measurements train a useful defect-risk model?
11. Which accessory classes should always route to parametric CAD rather than neural 3D generation?
12. Can a learned simplification agent reliably convert realistic geometry into readable minifigure-scale geometry?
13. How should the agent split one design into multiple printable/movable components?
14. How should color/decoration decisions co-design with geometry instead of being treated independently?
15. At what confidence can the system autonomously print a prototype versus requiring a design-review render first?

---

# Current external research targets

- Tripo API / H3.1: https://developers.tripo3d.ai/
- Meshy API: https://docs.meshy.ai/
- Hunyuan3D 2.1: https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
- Microsoft TRELLIS: https://github.com/microsoft/TRELLIS
- SPAR3D: https://github.com/Stability-AI/stable-point-aware-3d
- Stable Fast 3D: https://stability.ai/news-updates/introducing-stable-fast-3d
- CAD-Recode: https://github.com/filaPro/cad-recode
- CadQuery: https://cadquery.readthedocs.io/
- build123d: https://build123d.readthedocs.io/
- Zoo/KCL: https://docs.zoo.dev/
- SAM 2: https://ai.meta.com/research/sam2/
- Trimesh: https://trimesh.org/
- CGAL Polygon Mesh Processing: https://doc.cgal.org/latest/Polygon_mesh_processing/
- Open3D: https://www.open3d.org/docs/latest/
- Objaverse/Objaverse-XL: https://objaverse.allenai.org/
- SketchGraphs: https://github.com/PrincetonLIPS/SketchGraphs

## Canonical conclusion

Brickmen should not attempt to invent the entire geometry with one model.

The highest-confidence route to full automation is:

**resolve exact source -> generate a structured LEGO-scale design spec -> produce consistent multiview concepts -> use an ensemble of 3D/CAD generators for the visual shell -> deterministically insert validated interfaces and manufacturing constraints -> render and automatically critique -> iterate -> physically validate -> feed the outcome back into the router/critic.**

That architecture can improve continuously as 3D generation models change while preserving compatibility and manufacturability.
