# Figure Architecture Recognition Implementation Research

Research snapshot: 2026-09-27

## Objective

Implement architecture recognition as a **retrieval + geometry + evidence fusion** problem rather than a single image classifier.

Brickmen needs to distinguish:
- standard minifigure;
- official Giant families;
- official Half Giant/oversized torso hybrids;
- maker-specific muscle bodies;
- clone/compatible BigFig families;
- lower-body variants;
- specialized character bodies;
- unknown/new architectures.

It must also recognize detached components and scans.

## Recommended stack

### Image segmentation — SAM 2 / SAM 2.1

Meta's SAM 2 supports promptable segmentation in images and videos and was designed for strong zero-shot behavior on unfamiliar objects.

Use it to isolate:
- full figure;
- head/hair;
- torso;
- arms/hands;
- lower body;
- accessory.

Why segmentation first:
marketplace/product images often contain stands, packaging, accessories and other figures. Architecture embeddings should describe the body rather than the whole listing image.

Do not trust automatic component masks blindly; retain mask confidence and manual correction tooling.

### Image retrieval / embeddings — SigLIP 2 family

SigLIP 2 improves:
- zero-shot classification;
- image/text retrieval;
- localization;
- dense features;
- native/aspect-ratio resolution variants.

For Brickmen, use image embeddings primarily for **nearest known body/release retrieval**, not final mechanical classification.

Create embeddings for canonical:
- front;
- back;
- side;
- 3/4;
- component crops;
- silhouettes.

Query a new figure against this gallery.

### 3D retrieval — OpenShape

OpenShape provides:
- open-world/zero-shot 3D classification;
- text-to-3D retrieval;
- image-to-3D retrieval;
- point-cloud-to-3D retrieval;
- released checkpoints/training code/data.

Use it as an initial baseline for scans/generated meshes.

### 3D retrieval/parts — Uni3D

Uni3D aligns point-cloud representations with image/text features and reports:
- open-world understanding;
- cross-modal retrieval;
- one-shot part segmentation.

It is especially worth benchmarking for:
- detached arms/hands/torsos;
- scanned components;
- finding closest canonical architecture part.

### Secondary benchmark candidates

- Point-Bind: aligned 3D point clouds to image/text/audio/video embedding space; useful cross-modal baseline.
- ULIP/ULIP-2: important historical 3D multimodal baseline, but Salesforce archived the GitHub repository in June 2026. Keep as benchmark/reference rather than primary new dependency.

## Architecture-recognition fusion

Do not allow one neural embedding to decide the answer.

Suggested evidence channels:

```
maker/code prior
explicit catalog body label
known release/body-family cluster
image nearest-neighbor score
silhouette nearest-neighbor score
2D landmark/proportion distance
visible joint cue match
component topology match
3D embedding score
3D landmark distance
connector evidence
physical measurements
```

Then apply an evidence model.

Initial implementation can be rules + calibrated weighted score.

Later:
train a small classifier/ranker from reviewed observations.

## Confidence states

- exact_release_resolved
- architecture_high_confidence
- architecture_candidate
- morphology_only
- unknown

Important:
`architecture_high_confidence` still does not authorize manufacturing-critical connector reuse unless the architecture has validated physical joint profiles.

## Image normalization

Before embedding:
1. detect/crop full figure;
2. mask background;
3. estimate body vertical axis;
4. straighten/rotate;
5. normalize figure height in canvas;
6. preserve aspect ratio;
7. produce:
   - RGB normalized;
   - silhouette;
   - edge;
   - component masks.

This makes proportion cues less sensitive to seller photography.

## 2D landmark estimator

Start deterministic/semi-supervised.

Landmarks:
- top of head;
- chin/head bottom;
- neck center;
- left/right shoulder;
- elbow if visible;
- wrist;
- hand centroid;
- waist center;
- hip outer edges;
- knees/leg centers;
- foot/bottom points.

Derived ratios:
- head height / body height;
- shoulder width / body height;
- torso width / body height;
- waist / shoulder;
- hand width / head width;
- arm length / body height;
- leg length / body height.

For rigid/block figures, these ratios can be more discriminative than generic semantic embeddings.

## Joint cue classifier

Create specialized binary/multiclass detectors for:
- standard minifigure C-hand;
- Giant hand;
- standard wrist seam;
- Giant wrist seam;
- shoulder pin;
- Technic hardware;
- standard hips;
- separate rectangular legs;
- integrated Giant lower body;
- friction-pin Half Giant arm;
- specialized tail/lower body.

Use cropped component images and canonical renders.

## Component graph inference

Given segmented components, infer likely graph.

Example:
```
standard head
+ oversized torso
+ specialized large arms
+ standard hips/legs
=> Axl-like hybrid candidate
```

Example:
```
standard head
+ Half Giant torso
+ friction-pin large arms
+ normal-looking lower coat/body
=> Hagrid Half Giant candidate
```

This graph is more interpretable than a black-box label.

## Release/body-family prior

Before image recognition:
- search known maker/product code;
- retrieve known cluster;
- use as Bayesian prior, never hard rule.

This avoids errors such as:
`AF prefix -> Alpha 7cm body`
because AF336 Thing is a standard/minifigure-like Alpha release while AF362 Thing belongs to the large body cluster.

## Unknown architecture detection

This is mandatory.

Novelty signals:
- maximum image retrieval score below threshold;
- proportion vector far from all known families;
- joint cue contradiction;
- maker/release code not matching expected body family;
- 3D embedding outside cluster;
- component graph unseen.

Unknown result creates:
`FigureArchitectureCandidate`
with evidence and suggests the most useful next data:
- rear photo;
- side photo;
- detached arm;
- scale reference;
- physical sample.

## Detached-part recognition

For a loose arm/hand/torso:
1. segment;
2. orientation-normalize;
3. retrieve same semantic component only;
4. compare dimensions if scale reference exists;
5. inspect connector/joint shape;
6. retrieve architecture candidates.

This can later power:
- physical inventory;
- scan ingestion;
- automatic donor selection;
- repair/replacement generation.

## 3D scan recognition

Pipeline:
```
mesh/point cloud
 -> unit/scale resolution
 -> cleanup
 -> canonical gravity orientation candidates
 -> component segmentation
 -> point sampling
 -> OpenShape/Uni3D embeddings
 -> deterministic dimensions/landmarks
 -> connector-region descriptors
 -> ICP/alignment to known digital twins
 -> candidate distribution
```

Do not rely on embedding similarity for connector compatibility.

## Training data

### Positive examples
For each architecture:
- official/custom catalog images;
- Brickmen canonical renders;
- physical photos;
- detached components;
- scans.

### Hard negatives
Most important examples:
- Alpha standard body vs Alpha 7 cm body;
- G(2) muscle hybrid vs G(2) BigFig;
- old Hagrid Giant vs new Hagrid Half Giant;
- LEGO Giant vs compatible BigFig;
- Axl oversized torso vs G(2) muscle hybrid;
- standard minifig with armor vs true oversized torso.

### Unknowns
Deliberately include:
- unfamiliar custom bodies;
- action figures;
- minidolls;
- microfigs;
- brick-built bodies;
- malformed AI images.

## Evaluation

Measure:
- known architecture top-1/top-3;
- unknown rejection AUROC;
- release-family vs architecture confusion;
- detached part classification;
- component graph accuracy;
- calibration error;
- requested-next-evidence usefulness.

Do not optimize only top-1 classification.

A system that confidently misclassifies a new proprietary body is worse than one that says unknown.

## Runtime routing

Cheap path:
```
metadata -> normalized image -> image retrieval + ratios -> result
```

Escalated path:
```
multi-view segmentation -> joint cues -> VLM evidence -> result
```

3D path:
```
scan/mesh -> 3D retrieval + deterministic alignment
```

Human/physical escalation:
```
unknown/high-value -> acquisition/metrology queue
```

## Sources

- Meta SAM 2: https://ai.meta.com/research/sam2/
- SigLIP 2 paper: https://arxiv.org/abs/2502.14786
- OpenShape: https://github.com/Colin97/OpenShape_code
- Uni3D: https://github.com/baaivision/Uni3D
- Point-Bind: https://github.com/ZiyuGuo99/Point-Bind_Point-LLM
- ULIP/ULIP-2: https://github.com/salesforce/ULIP
