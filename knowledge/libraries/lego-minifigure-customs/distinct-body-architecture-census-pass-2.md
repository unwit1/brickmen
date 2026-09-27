# Distinct Body Architecture Census — Additional Pass

Research snapshot: 2026-09-27

## Purpose

A second-pass census focused on architectures that are mechanically distinct from the already-mapped standard/Broad/MidFig/Giant/custom-muscle families.

The criterion is not visual novelty. A body enters the architecture census when its component graph, joint graph, scale topology, or compatibility model changes materially.

## New high-value custom architectures

### Si-Dan full poseable minifigure

Minifig World currently describes Si-Dan Toys' Poseable Minifig as using **ball joints on arms, legs, feet and neck** for greater motion than a standard minifigure.

This is a major architecture difference:
- ball-jointed shoulders;
- ball-jointed hips/legs;
- articulated feet;
- ball-jointed neck;
- standard-scale compatible styling.

Brickmen implication:
create a future `poseable_standard` skeleton mode distinct from merely replacing standard arms.

### Titanic Bricks MidFig torso with ball-jointed arms

Current product description explicitly identifies:
- MidFig torso and arms;
- articulated ball joints;
- compatibility with standard minifigure components;
- resin manufacture.

This architecture is useful because it occupies the exact gap between:
- a fixed/swivel oversized torso;
- a highly articulated action-figure-like XL body.

Brickmen implication:
Broad and Mid skeletons should support multiple shoulder joint modules without changing the visual shell contract.

### Single-torso four-arm custom body

Titanic Bricks sells a standard-compatible four-arm torso.

This is mechanically/conceptually distinct from:
- Garmadon's official stacked-torso solution;
- Pong Krell/Grievous mechanical bodies.

Brickmen implication:
multi-arm support must be generalized as a shoulder-bank graph, not hard-coded as "two arms plus optional second torso."

## Newly separated official reference architectures

### Skeleton/bony figure

LEGO skeleton parts use:
- dedicated torso;
- specialized thin arms;
- specialized legs;
- standard-style head compatibility.

Why it matters:
- extreme thinness;
- non-solid torso;
- clip-like hand/arm behavior;
- useful reference for skeletal/undead/robotic custom bodies.

### Battle Droid

Dedicated mechanical family:
- 30375 torso;
- 30378 head;
- 30377/59230 arms;
- 30376 lower body.

This is a fully different body graph, not a standard minifigure with robot decoration.

### Super Battle Droid

Distinct again:
- integrated torso/head;
- specialized arms;
- dedicated lower body.

This proves that even within "droid" morphology, Brickmen should not infer one mechanical architecture.

### Faun/digitigrade lower body

Series 15 Faun introduced a digitigrade/goat-like lower-body silhouette.

This is valuable for:
- satyrs/fauns;
- bird-like humanoids;
- demon/goat characters;
- digitigrade fantasy species.

It should become a reusable lower-body skeleton topology rather than merely a visual tag.

### Legacy Homemaker/maxifigure

Historical LEGO maxifigures used an architecture radically different from both current minifigures and current custom-market "MaxiFig" usage.

Important terminology rule:
`maxifigure` is historically overloaded and must always retain source context.

## Additional patterns discovered but not promoted to architecture

### Torso/body shell add-ons

Current custom shops sell character-specific torso add-ons such as broad Shrek/Clayface-style shells.

These may preserve the standard skeleton entirely and should therefore be modeled as:
`BodyAugmentation / TorsoShellOverlay`
rather than a new FigureArchitecture unless the underlying joints/components change.

This is a valuable low-risk production strategy:
- keep standard donor mechanics;
- print one character-specific body shell;
- avoid printing wear joints.

### Muscular torso + arms replacement sets

Custom resin torso/arm sets can create a broad body while preserving standard head/lower-body compatibility.

These should feed Brickmen Broad style/mechanical research and be classified by their actual shoulder/arm interface once measured.

## Architecture concepts still worth hunting

- fully articulated custom knees/ankles at true minifigure scale;
- modular digitigrade custom legs;
- custom quadruped/taur bodies other than centaur;
- custom wing-arm or fin-arm replacement bodies;
- multi-headed/multi-neck torsos;
- expandable/mech-suit bodies built around a removable standard minifigure;
- translucent/soft-body/flexible articulated custom figures;
- magnetic or snap-fit custom joints;
- torso shells designed specifically around standard donor arm mechanics.

## Skeleton consequences

The neutral skeleton system must support:
- arbitrary number of shoulder banks;
- optional elbows/knees/ankles;
- ball, hinge, swivel and fixed joints;
- integrated torso/head bodies;
- non-humanoid lower-body graphs;
- standard donor adapters;
- overlay-only bodies that inherit another skeleton.

This is why the skeleton schema should be graph-based rather than hard-coded to humanoid two-arm/two-leg anatomy.
