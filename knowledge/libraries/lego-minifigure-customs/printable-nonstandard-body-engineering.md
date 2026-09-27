# Printable Non-Standard Body Engineering Patterns

Research snapshot: 2026-09-27

## Purpose

Translate the non-standard body catalog research into **reusable engineering patterns** for printable articulated figures.

The goal is not to reproduce any one third-party proprietary body verbatim. The goal is to learn which mechanical strategies work, preserve interoperability where appropriate, and design Brickmen-original architecture families whose functional interfaces are deterministic, measurable and replaceable.

## Pattern 1 — printed visual shells around commodity LEGO-system joint hardware

### Evidence

A current community Iron Golem BigFig design by BenTri:
- prints the visual body/limbs;
- uses three Technic 43093 axle/pin pieces;
- provides rotating arms, hands, legs and head;
- exposes bar and stud connections;
- warns that fit depends on printer tolerances.

This is closely aligned with the official modern Giant pattern, where representative LEGO Giant inventories use 43093 shoulder hardware with reusable Giant arm/hand families.

### Brickmen lesson

For high-load/wear joints, **do not insist that every component be resin printed**.

A better architecture can be:

```
printed torso shell
 + molded Technic/commodity axle-pin
 + printed arm shell
 + validated hand connector
```

Advantages:
- mature thermoplastic wear surfaces;
- inexpensive replacement;
- less sensitivity to brittle resin;
- simpler force/cycle qualification;
- easier repair.

Automation consequence:
the BOM generator can automatically select commodity joint hardware when the FigureArchitecture allows it.

## Pattern 2 — printable MidFig with manually tuned friction joints

### Evidence

The_amg006's printable "Mid Figure (Muscle Body)" provides:
- separate torso;
- arm;
- normal hand;
- accessory-compatible hand.

The author recommends:
- printing at 101% or 102% depending on printer;
- using a regular LEGO stick/rod;
- cutting/sanding;
- superglue to reinforce joints and reduce wear.

The Mk2 preserves similar manual tuning guidance.

### Brickmen lesson

This is useful evidence of demand and feasibility, but it also demonstrates the exact failure mode Brickmen's calibration system should eliminate.

Replace:
`print whole model at 101-102% + sand until fit`

with:
`keep visual shell at canonical scale + independently compensate each validated joint profile`.

Global scale adjustment is especially undesirable because it changes:
- head/torso proportions;
- accessory compatibility;
- wall thickness;
- art/decal geometry;
- all connectors at once.

Brickmen should solve the joint, not scale the figure.

## Pattern 3 — oversized figure preserving LEGO-system connector vocabulary

### Evidence

BenTri's 2× compatible Giant Minifigure is designed to remain compatible with the standard system and mixes:
- stud/anti-stud connections;
- Technic pins/axles;
- standard minifigure-style neck connection;
- bar grips;
- separate torso, waist, arms, hands, legs and head.

### Brickmen lesson

A non-standard body does not have to invent proprietary connector standards.

A Brickmen-original architecture can deliberately reuse:
- 3.18-family bars;
- studs/anti-studs;
- Technic pins/axles;
- standard minifigure neck/head interfaces;
- existing accessory anchors.

This creates a much larger compatible ecosystem and reduces calibration work.

## Pattern 4 — reusable component families across characters

BenTri's Redstone Golem explicitly reuses the arms, legs and hands from the earlier Iron Golem body while changing torso/head geometry.

This is the exact component strategy Brickmen should prefer:

```
FigureArchitecture
  -> shared skeleton / limbs / joints
CharacterBodyVariant
  -> torso shell
  -> head shell
  -> optional armor/accessories
```

Benefits:
- fewer validated joint families;
- more reusable training examples;
- fewer manufacturing experiments;
- easier spare parts;
- more consistent style.

## Pattern 5 — official Half Giant / oversized torso architectures

LDraw now exposes an official "Half Giant" Hagrid family:
- torso 37777;
- left arm 37779 / assembled arm-hand 38628;
- right arm 37783 / assembled arm-hand 38630;
- matching specialized hair 37784.

The arms are explicitly described as using friction pins.

This is different from:
- old Hagrid Body Giant 40250 family;
- modern Hulk/Thanos Giant;
- Axl oversized-armour torso.

### Brickmen lesson

There is no reason to collapse "large torso + normal head" into one generic hybrid.

Architecture registry should preserve:
- old Hagrid Giant;
- modern Hagrid Half Giant;
- Axl oversized-torso hybrid;
- Brickmen-original MidFig.

They can still share connector primitives where measurements prove compatibility.

## Pattern 6 — digital twin from component geometry, not assembled photographs

Official/community CAD sources are especially valuable when they expose **separate mechanical components**.

For each architecture, ingest:
- body/torso;
- arm L/R;
- hands;
- lower body;
- head interface;
- joint hardware;
- armor/hair.

Derive:
- component coordinate systems;
- joint center;
- insertion axis;
- swept articulation envelope;
- collision volumes;
- support-exclusion surfaces.

The canonical FigureArchitecture digital twin should be an assembly graph, not one merged mesh.

## Design rule: shell and skeleton are separate

Every printable custom articulated body should have:

### Skeleton/interface layer
Deterministic:
- joint centers;
- pins/sockets;
- mating faces;
- hardware;
- ranges of motion;
- keep-outs;
- accessory anchors.

### Visual shell layer
Variable:
- muscles;
- clothing;
- armor;
- character silhouette;
- surface relief;
- decorative geometry.

Generation may freely modify the shell within the skeleton's keep-outs.

This mirrors character rigging in animation and makes automated regeneration safer.

## Recommended joint hierarchy

Prefer in order:

1. **existing commodity LEGO-system hardware**
   - Technic axle/pin;
   - standard bars;
   - studs;
   - standard heads/hands when appropriate.

2. **replaceable thermoplastic insert**
   - FDM nylon/PETG/POM-like outsourced/molded insert;
   - snap-in sleeve/bushing.

3. **validated resin joint**
   - only where loads/cycles are low enough.

4. **integrated resin flexure**
   - only after material/fatigue validation.

Visual fidelity should not force a poor wear material into a joint.

## Architecture-specific modularity

### Giant-like
Suggested:
- torso;
- arms;
- hands;
- lower body/legs;
- optional independent head;
- commodity shoulder hardware.

### MidFig/muscle hybrid
Suggested:
- standard or architecture-specific head;
- torso;
- upper arms;
- hands;
- standard or custom hips/legs;
- optional shoulder armor.

### Highly anatomical 7 cm body
Potential:
- torso;
- upper/lower arms only if source architecture actually articulates there;
- hands;
- pelvis;
- legs;
- head.

Do not add elbow/knee joints merely because an action-figure body could support them. Preserve target architecture style.

## Joint cartridge concept

Brickmen should research a replaceable **JointCartridge** abstraction.

A cartridge is a small deterministic part or hardware set inserted into a visual component.

Examples:
- shoulder_43093_axle_socket;
- wrist_bar_socket;
- neck_standard_minifig;
- hip_pin_pair;
- friction_bushing.

Schema:
```
JointCartridge
  id
  architecture scope
  parent interface
  child interface
  hardware BOM
  material
  nominal geometry
  process compensation
  insertion force window
  rotation torque window
  cycle life
  replacement procedure
```

This allows the same Hulk torso shell to be regenerated without changing its proven shoulder mechanics.

## Automation-friendly component boundaries

Choose seams that are:
- hidden or stylistically plausible;
- reachable for assembly;
- favorable for printing orientation;
- favorable for UV/paint decoration;
- favorable for replacement.

Examples:
- wrist cuff;
- shoulder seam;
- belt/waist line;
- helmet boundary;
- boot boundary.

The agent should be allowed to move a split line within an approved region to improve printability.

## Parametric skeleton generator

Target interface:

```
body_skeleton.generate(
  architecture_id,
  stature_parameters,
  joint_profile_ids,
  accessory_anchor_profile,
  manufacturing_profile
)
```

Output:
- neutral skeleton;
- joint frames;
- keep-out volumes;
- articulation sweeps;
- attachment anchors;
- component split planes;
- character-shell envelopes.

Then:

```
character_shell.fit(
  source_body_features,
  body_style_profile,
  skeleton
)
```

## Original architecture over proprietary cloning

Third-party bodies such as Alpha Toys, G(2), Bigguy and Mr.J/Heart are valuable **style and market evidence**.

For Brickmen-original printable bodies:
- learn proportion grammar;
- learn where sculptural information is placed;
- preserve generic interoperability requirements;
- design independent joint geometry or use standard-system hardware;
- do not assume permission to copy a proprietary sculpt or exact proprietary joint geometry.

This also makes the architecture more adaptable to different printers/materials.

## First recommended printable body

The highest-confidence first complete articulated body is not Alpha.

It is a **Brickmen Giant-compatible research body** built from:
- an original neutral visual shell;
- standard-system head/accessory interfaces where appropriate;
- 43093-class shoulder hardware or an independently validated equivalent interface;
- bar/stud accessory anchors;
- modular hands/arms;
- architecture-specific dimensional calibration.

Why first:
- strongest public component evidence;
- official LDraw arm/hand geometry exists;
- community printed precedent exists;
- commodity joint hardware is available;
- large geometry is easier to print/measure than tiny standard hands/arms.

Second:
**Brickmen original MidFig**, designed around standard/minifigure interfaces and replaceable joints.

Third:
architecture-specific shells inspired by the style grammars learned from Alpha/G(2)/Bigguy/etc., without copying their proprietary geometry.

## Sources

- LDraw Bigfig Arm Left 10154: https://library.ldraw.org/parts/list?tableSearch=10154.dat
- LDraw Bigfig Arm Right 10124: https://library.ldraw.org/parts/213
- LDraw Half Giant parts: https://library.ldraw.org/parts/list?tableSearch=3777.dat
- LDraw Fantasy Troll 60671: https://library.ldraw.org/parts/30633
- BenTri Iron/Swift Golem BigFig: https://cults3d.com/en/3d-model/game/lego-compatible-iron-golem-and-swift-golem-bigfig
- BenTri Giant Minifigure: https://cults3d.com/en/3d-model/game/lego-compatible-giant-minifigure-bentri
- BenTri Redstone Golem reuse example: https://cults3d.com/en/3d-model/game/lego-compatible-redstone-golem-bigfig-minecraft-bentri
- The_amg006 Mid Figure: https://cults3d.com/en/3d-model/game/leg-o-mid-figure-muscle-body-for-custom-minifigures
- The_amg006 Mid Figure Mk2: https://cults3d.com/en/3d-model/game/leg-o-mid-figure-mk2-muscle-body-for-custom-minifigures-the_amg006-2
