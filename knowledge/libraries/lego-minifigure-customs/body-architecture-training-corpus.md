# Body Architecture and Style Learning Corpus

Research snapshot: 2026-09-27

## Objective

Train/retrieve systems that can independently answer:

1. **What physical figure architecture is this?**
2. **What visual body style does it use?**
3. **Which character/source design is applied to it?**
4. **How should that design transfer to another architecture without copying its mechanics?**

The corpus must prevent architecture, style, maker and character from collapsing into one shortcut.

## Canonical factorization

Every training sample should factor:

```
CharacterIdentity
SourceAppearance
FigureArchitecture
BodyStyleProfile
CharacterBodyDesign
ManufacturingProcess
ObservationEvidence
```

### Example

A catalog photo of Alpha AF345 Hulk becomes:

```
CharacterIdentity = Hulk
SourceAppearance = specific Hulk appearance hypothesis
FigureArchitecture = custom_alpha_7cm_muscle
BodyStyleProfile = alpha_af_7cm_muscular_visual
CharacterBodyDesign = AF345-specific visual design observation
ManufacturingProcess = unknown / observed only
```

It does **not** mean:
`Hulk => custom_alpha_7cm_muscle`.

## Four corpus axes

### Axis A — architecture diversity

Include:
- standard;
- short/medium/long;
- Axl broad hybrid;
- Hagrid broad giant;
- early/later Giant;
- specialized Giant creature;
- Alpha 7 cm;
- G (2) muscle;
- KDL large;
- ball-joint standard;
- Mega-scale;
- buildable;
- multi-arm;
- mechanical/droid;
- centaur;
- serpent;
- ghost;
- tentacle;
- mini-doll;
- unknown/proprietary.

### Axis B — character diversity

Do not train body architecture primarily on Hulk-like characters.

Include:
- normal humans;
- muscular humans;
- robots;
- monsters;
- quadruped hybrids;
- multi-arm characters;
- giants;
- children;
- stylized creatures.

### Axis C — same-character cross architecture

These are especially valuable.

Hulk:
- standard;
- short/Mighty Micro;
- official Giant;
- compatible BigFig;
- Alpha 7 cm;
- G (2) muscle;
- premium custom;
- bighead source label.

Other strong candidates:
- Thing;
- Bane;
- Kingpin;
- Colossus;
- Beast;
- Juggernaut;
- Abomination;
- Sentinel;
- Giant Man / Ant-Man;
- Galactus;
- Luffy variants.

The same character represented at multiple scales teaches the model that **character is not architecture**.

### Axis D — same-architecture cross character

Examples:
- Alpha AF family across Hulk, Red Hulk, Maestro, Thing, Beast, Colossus, Juggernaut, Abomination;
- OA2201-2204 16 cm Mega family candidate;
- official Giant across Hulk/Thanos/etc.;
- standard minifigure across thousands of characters.

This teaches:
**architecture is not character.**

## Sample modalities

Per sample where available:

### Source/captured
- catalog images;
- front/rear/side;
- disassembly photos;
- product dimensions;
- part inventory;
- maker/release metadata.

### Derived 2D
- full figure mask;
- semantic component masks;
- landmarks;
- silhouette;
- edge map;
- normalized crop;
- scale annotations.

### Canonical 3D
- mesh/digital twin;
- component meshes;
- joint axes;
- connector geometry class;
- UV/surface labels;
- neutral-pose renders;
- articulated-pose renders;
- depth;
- normals;
- part-ID masks.

### Physical
- measured dimensions;
- mass;
- material observations;
- force/torque;
- range of motion;
- cycle wear;
- scan/photogrammetry;
- fit compatibility.

The model should know the evidence class so a catalog photo is never treated like a measured joint.

## Architecture recognition task

Input:
- one or more images and optional metadata.

Target:
- FigureArchitecture distribution;
- component graph;
- joint cues;
- morphology facets;
- unknown probability.

Training strategy:
- exact release metadata may assist training/labeling;
- evaluation should include a **visual-only** split so the model cannot win by reading maker/product code.

### Leakage tests

Run:
- character-held-out;
- maker-held-out;
- release-code-held-out;
- body-family-held-out;
- theme/franchise-held-out.

If performance collapses on maker-held-out data, the architecture model is memorizing brands rather than geometry.

## Component segmentation task

Semantic classes should be architecture-aware but share universal roles:

- head;
- headgear/hair;
- chest/torso;
- abdomen;
- pelvis;
- upper arm;
- forearm;
- hand;
- thigh;
- lower leg;
- foot;
- tail;
- tentacle;
- quadruped body;
- joint adapter;
- armor shell.

Part-aware 3D models such as PartCrafter and UniPart demonstrate the utility of explicit part-level generation/segmentation. PAct/ArtLLM/Particulate provide useful research directions for inferring articulated structure.

## Body style representation

Do not train one opaque style label if structured measurements can be extracted.

BodyStyleProfile features include:
- proportions;
- anatomical exaggeration;
- blockiness/roundness;
- sculpt relief density;
- surface-break density;
- print-vs-sculpt ratio;
- joint visibility;
- accessory scale;
- head/facial proportion grammar;
- edge/chamfer/fillet language;
- symmetry/asymmetry.

Separate:
- **global architecture proportions**;
- **style deviations from architecture baseline**.

Example:
A shoulder width of 25 mm is architecture/scale-specific.
A shoulder/head ratio or normalized deltoid exaggeration can be style-comparable.

## Style embedding research

Train/retrieve a style embedding from canonicalized views after removing character-specific decoration where possible.

Potential inputs:
- clay renders;
- geometry-only normals;
- depth;
- silhouettes;
- semantic part masks;
- decimated geometry descriptors.

Avoid allowing:
- logos;
- face identity;
- costume colors;
to dominate "body style."

Research on geometry/appearance disentanglement and structure-aware part generation supports this separation.

## Cross-architecture style transfer dataset

A training pair should not mean "scale mesh A to body B."

Record:

```
source_architecture
source_style
target_architecture
identity_features
style_features_to_transfer
architecture_features_to_preserve
result
evaluation
```

Transfer categories:

### geometry-style transfer
Examples:
- blocky -> anatomical;
- low-relief -> sculptural;
- official Giant simplification -> Brickmen XL.

### surface-art transfer
Map costume/printing to the target BodySurfaceMap.

### proportion transfer
Apply normalized style ratios within target architecture constraints.

### sculpt-vs-print transfer
A chest strap may remain print on standard minifigure but become shallow sculpt on a 70 mm XL body.

The decision itself is a learned/rule-based style feature.

## Negative examples

Keep failure data.

Examples:
- standard legs hallucinated onto serpent;
- fused elbow on an articulated architecture;
- Alpha-style sculpt copied with a standard minifigure shoulder socket;
- Giant body uniformly scaled to 7 cm;
- human anatomy applied to a mechanical droid;
- character logo used as a style classifier shortcut;
- seller "BigFig" label overriding visible joint mismatch.

Negative examples are useful for critics/rankers.

## Synthetic data

Brickmen can generate controlled training data from original parametric body architectures.

For each Brickmen blank:
1. vary body proportions within approved bounds;
2. vary joint visibility;
3. vary relief/muscle stylization;
4. render canonical views;
5. keep exact component/joint labels;
6. produce known style factors.

This provides unlimited, fully labeled architecture/style examples without inheriting third-party proprietary geometry.

## Procedural cross-architecture training

Generate the same synthetic character costume onto:
- Brickmen Standard;
- Broad;
- Mid;
- XL;
- Giant;
- centaur/serpent test bodies where meaningful.

Targets:
- correct semantic placement;
- correct topology;
- style consistency;
- no invalid connector changes.

## Physical feedback labels

Printed Brickmen bodies add:

- joint success/failure;
- torque;
- crack location;
- wall-thickness issue;
- support scar;
- warp;
- acceptable detail;
- human aesthetic acceptance.

This allows future models to predict not only visual quality but manufacturing risk.

## Data split policy

### Architecture recognition
Group split by:
- physical body family;
- maker;
- character.

### Style retrieval
Hold out:
- characters;
- colorways;
- franchises.

### Style transfer
Hold out complete:
`source architecture -> target architecture`
pairs.

This tests whether the model can recombine factors rather than replay known pairings.

## Evaluation axes

Never use one aggregate score.

### Architecture
- architecture accuracy;
- unknown detection;
- component graph edit distance;
- joint graph accuracy;
- scale error.

### Style
- style-feature error;
- style retrieval accuracy;
- architecture leakage;
- character leakage.

### Character
- source identity fidelity;
- costume feature presence.

### Generation
- topology correctness;
- component separability;
- joint placement;
- canonical-view consistency;
- manufacturing DFM;
- print outcome.

## Training progression

### C0 — retrieval baseline
No training.
- embeddings;
- nearest neighbors;
- rules;
- VLM labels.

### C1 — architecture classifier
Train on normalized images + masks.

### C2 — component segmentation
Train/adapter using canonical component roles.

### C3 — style feature predictor
Predict interpretable BodyStyleProfile attributes.

### C4 — style embedding / ranker
Use accepted/rejected and similarity pairs.

### C5 — part-aware body generation
Fine-tune or condition PartCrafter/UniPart/open generator on Brickmen-original structured bodies.

### C6 — articulation proposal
Use PAct/ArtLLM/Particulate-style systems as proposal/critic layers.

### C7 — architecture-conditioned body compiler
Generated components are snapped/rebuilt onto deterministic FigureArchitecture joints.

### C8 — physical-feedback model
Predict print/joint risks.

## Do not fine-tune proprietary geometry as the foundation

Third-party custom body examples can teach:
- category;
- descriptive style;
- proportion statistics;
- architecture recognition.

Brickmen's manufacturing geometry should be generated from:
- its original parametric architecture;
- validated official-compatible interfaces where appropriate;
- physical calibration.

This cleanly separates learning *what a style looks like* from reproducing somebody else's exact body mold.

## Relevant research

- PartCrafter: https://github.com/wgsxm/PartCrafter
- PAct: https://github.com/Mobiuslqm/PAct
- ArtLLM: https://openaccess.thecvf.com/content/CVPR2026/html/Wang_ArtLLM_Generating_Articulated_Assets_via_3D_LLM_CVPR_2026_paper.html
- Particulate: https://openaccess.thecvf.com/content/CVPR2026/html/Li_Particulate_Feed-Forward_3D_Object_Articulation_CVPR_2026_paper.html
- UniPart: https://openaccess.thecvf.com/content/CVPR2026/html/He_UniPart_Part-Level_3D_Generation_with_Unified_3D_Geom-Seg_Latents_CVPR_2026_paper.html
- Disentangle-and-Diffuse: DOI 10.1109/MCG.2026.3721727
- StyleSculptor: https://doi.org/10.1145/3757377.3763929
