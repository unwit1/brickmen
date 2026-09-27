# Body Skeleton System

Created: 2026-09-27

## What is now implemented

Brickmen now has executable, graph-based neutral skeletons for:

- `brickmen_broad_v0`
- `brickmen_mid_v0`
- `brickmen_xl_v0`
- `brickmen_giant_v0`

Files live under:

`knowledge/libraries/lego-minifigure-customs/data/skeletons/`

and compile through:

`tools/geometry/generate_body_skeleton.py`

## Three layers

### 1. Generation skeleton

What is implemented now.

Contains:
- normalized landmarks;
- bones/links;
- proposed joint topology;
- articulation intent;
- body envelopes;
- parametric proportion rules;
- generation keep-outs.

Purpose:
- concept generation;
- shell alignment;
- part-aware generation;
- style transfer;
- Blender/CAD rigging;
- articulation planning.

### 2. Engineering skeleton

Future promoted form.

Adds:
- physically measured joint centers;
- validated axes/ranges;
- exact component split planes;
- articulation collision volumes;
- material/hardware selections.

### 3. Manufacturing interfaces

Never supplied by the learned/generation skeleton.

Comes from:
- JointCartridge;
- ConnectorProfile;
- process compensation;
- force/cycle validation.

This separation lets Brickmen revise proportions without invalidating proven joints.

## Coordinate system

Every skeleton is normalized by a design-height unit:

- X: left/right
- Y: back/front
- Z: ground/head
- origin: midpoint between feet on ground

The compiler converts normalized coordinates into millimeters using a requested target height.

This is not the same as globally scaling finished CAD.

Validated connector geometry is inserted **after** skeleton compilation and keeps its own dimensions.

## Default design heights

These are Brickmen design targets, not copied product measurements and not manufacturing tolerances.

- Broad: 42 mm
- Mid: 52 mm
- XL: 70 mm
- Giant: 62 mm

The distinction is intentional:

### Broad
Standard-ish stature, increased width/depth.

### Mid
Intermediate stature with flexible muscular/armored proportions.

### XL
Large, more anatomical/articulated humanoid.

### Giant
Large but blockier/broader, with simpler component language.

## Parameterization

Current skeleton compiler supports rules such as:

- shoulder width scaling;
- arm length scaling;
- torso height scaling;
- lower-body height scaling;
- stance width scaling;
- envelope depth/projection scaling.

CLI example:

```bash
python tools/geometry/generate_body_skeleton.py \
  knowledge/libraries/lego-minifigure-customs/data/skeletons/brickmen-broad-v0.json \
  --height-mm 44 \
  --param shoulder_width_scale=1.15 \
  --param arm_length_scale=1.05 \
  --format obj \
  -o broad-debug.obj
```

The OBJ is a simple line skeleton useful for inspection/import.

## Why nodes include nonfunctional anatomical landmarks

Broad/Mid bodies may have an `elbow_l` landmark even when there is no physical elbow joint.

That distinction matters:

- **landmark** guides proportions and shell generation;
- **functional joint** changes component graph and manufacturing.

AI must not infer an extra joint merely because an anatomical landmark exists.

## Skeleton topology modules

`data/skeleton-topology-modules.json` adds reusable graph patterns for:

- full ball-joint poseable standard bodies;
- single-torso four-arm figures;
- digitigrade/faun legs;
- Battle Droid-style mechanical bodies;
- integrated head+torso figures;
- donor-body torso-shell overlays.

Future modules can add:
- centaur/taur;
- tentacle;
- serpent;
- ghost;
- multi-headed;
- quadruped;
- wheel/roller lower body.

## Connection to learned 3D generation

Target flow:

```
CharacterBodyFeatureSpec
 -> FigureArchitecture / Brickmen architecture selection
 -> skeleton compile
 -> articulation/keep-out volumes
 -> BodyStyleCompiler
 -> part-aware visual shell generation
 -> shell-to-skeleton alignment
 -> deterministic JointCartridge insertion
 -> collision / DFM
 -> render critic
 -> print
```

PartCrafter/UniPart/SAM3D-Part/etc. may generate shells.

Particulate/PAct/etc. may propose articulation.

Neither may redefine locked skeleton mechanics once an architecture is selected.

## Skeleton fitting

Next implementation should solve:

```
reference landmarks
 -> optimize permitted skeleton parameters
 -> preserve architecture constraints
 -> output fitted skeleton + residual errors
```

This gives Brickmen a deterministic intermediate representation between reference imagery and 3D generation.

Example:
Venom AF-style semantics can increase:
- shoulder width;
- torso depth;
- forearm envelope;

without increasing target height.

Blob can increase:
- abdomen projection;
- waist envelope;

without inheriting Hulk's taper.

## Validation state

The four current skeletons are:
`concept_generation_skeleton_nonproduction`.

They are ready for:
- generation experiments;
- render comparisons;
- code integration;
- parameter-fitting research.

They are **not** ready for:
- direct fabrication of joint pins/sockets;
- claims of compatibility with LEGO or third-party joints;
- force/cycle assumptions.

Those require the existing physical metrology program.
