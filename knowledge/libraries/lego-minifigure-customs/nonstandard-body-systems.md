# Non-Standard Minifigure Body Systems: Taxonomy, Recognition, Generation, and Manufacturing

Research snapshot: 2026-09-27.

## Goal

Brickmen must understand figures whose bodies do not use the ordinary standard minifigure torso + arms + hands + hips + legs architecture.

The end-state requirement is broader than cataloging:

> Given a character, Brickmen should be able to decide that a standard minifigure, oversized-torso body, mid-figure/muscle body, classic giant/bigfig, 7 cm articulated XL body, Hagrid-like broad body, creature body, or another architecture best represents the character; generate artwork and/or new geometry in that architecture; preserve the architecture's visual grammar; and eventually manufacture the body and accessories with validated connectors.

This requires a **body architecture layer** separate from character identity, decoration style, maker labels, and manufacturing process.

---

# Terminology rule

Do not canonicalize seller/community labels as geometry.

Terms such as:

- bigfig / BigFig
- large figure
- giant
- midfig / mid-fig
- medfig
- XL
- mega fig
- muscle body
- big guy
- mini bigfig

are inconsistent across LEGO catalogs, collectors, customizers, resellers, and fan designers.

Brickmen should preserve them as:

```
source_body_label
market_body_label
community_aliases[]
```

but resolve each observed figure to a **BodyArchitecture** defined by measurable geometry and assembly.

This is already necessary in the Hulk ecosystem: HeroBloks lists Alpha Toys AF344/AF345 Hulk separately from many releases explicitly named "(BigFig)", while sellers describe the Alpha AF family as 7 cm LEGO-compatible figures. Therefore Alpha AF should not be silently merged into the classic LEGO giant/bigfig architecture.

---

# Canonical architecture model

Every body architecture must describe:

- overall scale;
- canonical standing height;
- head family;
- neck connector;
- torso/body construction;
- shoulder joints;
- arm segmentation;
- elbow joints;
- wrist/hand joints;
- hand/accessory connector;
- pelvis/hip construction;
- leg segmentation;
- foot/stud compatibility;
- articulation graph;
- compatible standard minifigure parts;
- compatible giant/bigfig parts;
- external accessory interfaces;
- printable/decoratable surfaces;
- keep-out/articulation envelopes;
- known manufacturers/examples;
- source labels/aliases;
- provenance/confidence.

A figure can share an architecture while having a completely different sculpt.

---

# Official LEGO-derived architecture families

## 1. Standard minifigure

Baseline:
- separate head;
- standard torso;
- separate arms/hands;
- hip/leg assembly;
- standard headwear/accessory ecosystem.

Subvariants such as short, medium and other modified legs remain **variants of the standard body architecture** unless their joint graph changes materially.

Use as the reference scale and coordinate system.

---

## 2. Standard minifigure with elongated limbs

Toy Story Woody is a clear official precedent.

BrickLink inventories Woody with:
- long legs;
- long arms;
- modified head;
- otherwise recognizable minifigure assembly semantics.

This should be modeled as:

`standard_minifigure + limb_length_variant`

rather than an unrelated figure system.

Why it matters:
Brickmen can create tall/slender characters without inventing a complete new torso/connector system.

Source:
https://www.bricklink.com/catalogItemInv.asp?M=toy003

---

## 3. Oversized-torso / broad-minifigure hybrid

NEXO KNIGHTS Axl is a highly useful official precedent.

BrickLink inventories Axl with:
- a standard-style minifigure head;
- normal minifigure hip/leg assemblies;
- a modified oversized torso;
- dedicated bulky armored arms;
- specialized headgear.

The torso is cataloged as "Torso, Modified Oversized with Armor..." and the figure still uses normal minifigure legs.

This is mechanically important because it creates a **middle-scale body without abandoning the minifigure lower-body system**.

Canonical architecture proposal:

`minifig_oversized_torso_hybrid`

Potential uses:
- Thing;
- Kingpin;
- Bane;
- muscular fantasy races;
- armored characters;
- broad robots;
- characters too large for standard torso but too small for giant/bigfig proportions.

Sources:
https://www.bricklink.com/catalogItemInv.asp?M=nex007
https://www.bricklink.com/v2/catalog/catalogitem.page?P=23763c01pb02

---

## 4. Hagrid-style giant/broad integrated body with standard head

Official Hagrid is mechanically distinct from Hulk-style giant figures.

BrickLink inventories Hagrid hp111 with:
- standard minifigure head 3626-family geometry;
- dedicated giant body assembly;
- attached/associated arms;
- movable hands;
- giant/broad torso/lower body.

BrickLink names part 40250cx3:
"Body Giant, HP Hagrid... with Arms and Light Nougat Movable Hands."

Canonical architecture proposal:

`giant_broad_standard_head`

This family is extremely useful for custom characters that need:
- standard face/head compatibility;
- much broader/taller body;
- minifigure visual language;
without a huge Hulk-like head.

Sources:
https://www.bricklink.com/catalogItemInv.asp?M=hp111
https://www.bricklink.com/v2/catalog/catalogitem.page?P=40250cx3

---

## 5. Classic giant/bigfig with integrated head/body shell

Early official Hulk giant figures such as SH0013 consist of:
- giant body containing the main body/head/leg form;
- separate left/right giant arms;
- separate giant hands;
- arm pins/axles.

The inventory does not contain a separate head part.

Canonical architecture proposal:

`giant_classic_integrated_head`

This is what many custom/compatible manufacturers copied or extended under the market term "BigFig."

Source:
https://www.bricklink.com/catalogItemInv.asp?M=sh0013

---

## 6. Modular-head giant/bigfig

Later official giant figures evolved.

Examples such as Thanos SH0733 and Hulk SH0967 use:
- giant body "without head" / body shell;
- separate modified giant head;
- optional separate giant hair/headgear;
- giant arms;
- giant hands;
- arm pins.

This is a distinct architecture revision because the head becomes a reusable independent component.

Canonical architecture proposal:

`giant_modular_head`

This should be the preferred reference architecture for future Brickmen-printable giant humanoids because modular head/hair/body geometry is easier to generate, customize, replace and print independently.

Sources:
https://www.bricklink.com/catalogItemInv.asp?M=sh0733
https://www.bricklink.com/catalogItemInv.asp?M=sh0967
https://www.bricklink.com/catalogItemInv.asp?M=sh1104

---

## 7. Specialized giant/creature bodies

LEGO's "Body Giant" catalog includes many bodies that are not interchangeable humanoid Hulk bodies:
- Cave Troll;
- Fantasy Era Troll;
- Bane;
- Darkseid;
- Cull Obsidian;
- gorilla bodies;
- HP Troll;
- Killer Croc variants;
- Sandy;
- other creature-specific systems.

Killer Croc SH0321 is especially instructive: its assembly uses specialized giant arms with wrist studs plus Rancor paw/claw parts rather than standard giant hands.

Therefore:
**"Body Giant" is a broad catalog family, not one connector standard.**

Canonical architecture parent:

`giant_specialized_creature`

with child architectures keyed to actual joint/connector graph.

Sources:
https://www.bricklink.com/catalogList.asp?catID=20&catLike=W&catType=P&q=giant
https://www.bricklink.com/catalogItemInv.asp?M=sh0321

---

## 8. Baby / toddler body

BrickLink catalogs bodies with fixed arms and molded hands as distinct body parts.

Canonical architecture:
`minifig_baby_toddler`

Generation use:
- children;
- very small creatures;
- stylized chibi bodies;
- source-derived small humanoids.

The fixed-arm architecture requires a different decoration/pose model than standard minifigures.

Source:
https://www.bricklink.com/catalogList.asp?catID=20&catType=P

---

## 9. Microfigure

BrickLink part 85863 is cataloged as "Body Microfigure Complete."

Canonical architecture:
`microfigure_integrated`

Treat this as a separate extreme-scale style domain, not a shrunk standard minifigure.

---

## 10. Mini-doll architecture

Mini-dolls have their own torso/body-part families and proportions.

Canonical architecture:
`minidoll_standard`

They should remain separate from minifigure architecture while being usable as:
- alternate generation target;
- proportion/style reference;
- cross-system recognition class.

Rebrickable exposes separate mini-doll torso components, confirming a distinct parts ecosystem.

---

## 11. Other official character-specific body systems

BrickLink's minifigure body-part catalog includes:
- Angry Birds bodies;
- Slimer/ghost bodies;
- pixelated/Minecraft bodies;
- small fixed-arm bodies;
- mechanical/droid bodies;
- other franchise-specific forms.

Rather than create one "weird body" bucket, use:

`specialized_character_body::<architecture_id>`

only after the joint/connector graph is characterized.

---

# Third-party/custom body architectures

## A. Compatible classic bigfig clones/extensions

HeroBloks lists many Hulk/Red Hulk/Beast releases explicitly labeled "(BigFig)" from:
- Decool;
- Sheng Yuan;
- Xinh;
- Pogo;
- Kopf;
- DLP;
- SX;
- Lele;
- others.

These should first be classified against official giant architecture, then measured for:
- exact compatibility;
- arm pins;
- hand sockets;
- head modularity;
- foot/stud compatibility;
- dimensional drift.

Do not assume every market "BigFig" is dimensionally identical.

Sources:
https://www.herobloks.com/figures/4115
https://www.herobloks.com/figures/49894

---

## B. Alpha Toys AF 7 cm articulated XL body

This is the body family the user was referring to.

Evidence:
- Alpha Toys AF345 Hulk is cataloged separately from explicit BigFig releases by HeroBloks.
- Alpha Toys AF361 Beast and AF363 Colossus are noted by HeroBloks as 7 cm tall.
- third-party sellers list AF344, AF345, AF349, AF359 and other AF Hulk-family figures as 7 cm; AF350 Abomination is sold around 7-7.5 cm.
- product imagery shows a visibly segmented upper arm/forearm construction and much more action-figure-like muscular articulation than classic giant/bigfig arms.

Canonical architecture proposal:

`custom_xl_articulated_7cm_alpha_family`

Observed visual/component features:
- approximately 7 cm class;
- separate head/hair or character-specific head shell;
- broad sculpted torso;
- upper-arm + forearm segmentation;
- elbow articulation visible in product imagery;
- enlarged custom hands;
- elongated custom legs;
- stronger anatomical musculature than classic LEGO giant bodies;
- compatible building-block feet/accessory context, according to sellers.

Unknowns requiring physical sample:
- exact shoulder pin/ball architecture;
- elbow joint geometry;
- wrist/hand connector;
- neck connector;
- hip joint;
- foot/stud geometry;
- interchangeability across AF releases;
- interchangeability with any other maker.

Brickmen must not reverse-engineer those unknowns from product images alone.

Examples:
- AF344 Hulk (Avengers);
- AF345 Hulk;
- AF346 Red Hulk;
- AF349 Maestro;
- AF350 Abomination;
- AF359 Juggernaut;
- AF361 Beast;
- AF362 Thing;
- AF363 Colossus;
- later AF36x Hulk variants.

Sources:
https://www.herobloks.com/figures/39244/alpha-toys/af344/hulk-%28avengers%29
https://www.herobloks.com/figures/39241/alpha-toys/af345/hulk
https://www.herobloks.com/figures/49858
https://www.herobloks.com/figures/49860/alpha-toys/af363/colossus-%28deadpool-2%29
https://www.01bigbricks.net/categories/minifigures-hulk
https://www.01bigbricks.net/products/minifigures-abomination-hulk-lego-af350

Important provenance note:
Do not infer that the custom-minifigure "Alpha Toys" catalog identity is necessarily the same corporate entity as unrelated companies/websites using the Alpha Toys name unless primary evidence establishes it.

---

## C. Standard-height / near-standard "muscle body" hybrid

There is a second custom approach that is much closer to standard minifigure height.

Examples:
- G/GH0304-style Hulk imagery shows a standard-size head/legs combined with a broad sculpted chest and muscular articulated arms.
- HK Mega Toys explicitly advertises custom figures using a "Muscle Body" with LEGO-compatible bricks/materials.

Canonical architecture proposal:

`custom_muscle_torso_standard_lower_body`

This is conceptually closer to Axl than to a classic bigfig:
- preserve standard head;
- often preserve minifigure-compatible lower body;
- replace torso and arms with muscular custom geometry.

This architecture may be the most useful generic "mid-sized muscular" body because it preserves far more standard accessory compatibility.

Sources:
https://www.hkmegatoys.com/en/products/g002
market imagery for GH0304 and related custom figures.

---

## D. Community 3D-printed "midfig" body systems

"Midfig" is an active community design concept rather than an official LEGO category.

Examples found:
- fan-designed Thing/Kingpin/Venom/Bane middle-figure concepts between a minifigure and bigfig;
- downloadable 3D-printable "Mid Figure (Muscle Body)" systems with custom torso, arms and hands;
- Mk2 versions explicitly include accessory-compatible hands.

One published printable design instructs users to print at 101-102% depending on printer and manually reinforce/finish joints. That is strong evidence that **joint calibration remains a central problem even for existing printable midfig projects.**

Canonical architecture:
`community_midfig_parametric`

Brickmen should not copy one designer's exact geometry. Instead, research the design space and build an original parametric mid-body architecture with:
- standard head compatibility;
- standard or selectable lower-body compatibility;
- modular torso;
- modular arms;
- configurable hand connector;
- print-calibrated joints.

Sources:
https://cults3d.com/en/3d-model/game/leg-o-mid-figure-muscle-body-for-custom-minifigures
https://cults3d.com/en/3d-model/game/leg-o-mid-figure-mk2-muscle-body-for-custom-minifigures-the_amg006-2
community discussion:
https://www.reddit.com/r/LegoMarvel/comments/1nf1w1e/lego_middle_figures_from_marvel_comics/

---

## E. Brick-built midfig / purist middle body

A different "midfig" strategy uses ordinary bricks/parts to build a body between minifig and bigfig scale.

This should be recognized as:

`brick_built_midfig`

not confused with a molded/printed custom body.

Advantages:
- native LEGO connection system;
- no new body mold;
- easy iteration.

Disadvantages:
- less character-specific surface continuity;
- more visibly constructed;
- difficult to decorate as one coherent figure.

Useful for generation as a fallback when a printable body is unnecessary.

---

## F. Premium/proprietary sculpted muscular bodies

Custom makers such as Bigguy Minifigs and Jin Custom show heavily sculpted, muscular Hulk/Red Hulk forms with body proportions different from standard minifigures and classic bigfigs.

Brickmen should initially classify these as:

`custom_proprietary_body_unknown_architecture`

until physical or high-confidence multi-view evidence resolves:
- height;
- joint segmentation;
- standard-part compatibility;
- whether they share an OEM body platform;
- whether body components are custom-printed, molded, modified donors, or combinations.

Do not infer a shared architecture from similar appearance alone.

HeroBloks is useful for identity/provenance discovery but does not always expose mechanical architecture.

---

# Architecture vs. style

This distinction is essential.

**Architecture**
describes physical structure:
- pieces;
- joints;
- dimensions;
- connectors;
- scale.

**Style**
describes visual treatment:
- anatomical exaggeration;
- LEGO-like simplification;
- chest/shoulder proportions;
- face proportions;
- surface detail;
- line/print grammar;
- sculpt language.

Therefore a "Hulk style" must not be bound to one body.

The same source character can be rendered as:
- standard minifigure;
- Axl-style oversized torso hybrid;
- community midfig;
- Alpha-style 7 cm articulated XL body;
- classic giant/bigfig;
- modular-head giant;
- brick-built midfig.

Generation should explicitly choose both:

```
body_architecture_id
body_style_profile_id
```

---

# Body Architecture entity

Recommended record:

```json
{
  "body_architecture_id": "...",
  "canonical_name": "...",
  "architecture_family": "...",
  "source_labels": [],
  "height_mm": null,
  "height_ratio_to_standard": null,
  "component_graph": [],
  "joint_graph": [],
  "connector_families": [],
  "standard_part_compatibility": {},
  "surface_map_id": "...",
  "articulation_profile_id": "...",
  "scale_profile_id": "...",
  "known_examples": [],
  "physical_validation_status": "...",
  "sources": []
}
```

---

# Component graph

Do not force all bodies into:
head / torso / arm / hand / hips / legs.

Use semantic roles:

- head;
- hair/headgear;
- neck;
- chest_shell;
- abdomen;
- pelvis;
- upper_arm_left/right;
- forearm_left/right;
- hand_left/right;
- hip_left/right;
- thigh_left/right;
- lower_leg_left/right;
- foot_left/right;
- integrated_lower_body;
- tail;
- wing;
- creature_limb;
- armor_shell;
- connector_pin;
- accessory_mount.

A standard minifigure simply leaves many roles unused.

---

# Joint graph

Each joint should specify:

```
joint_id
parent_component
child_component
joint_type
axis/axes
range
connector_family
retention_method
wear_surface
printability_class
physical_validation
```

Joint types may include:
- rotational pin;
- friction axle/pin;
- ball;
- snap;
- C-clip;
- press/friction;
- integrated/flexible;
- fixed;
- unknown.

This makes Alpha-style elbow articulation fundamentally distinguishable from classic bigfig single-piece arms.

---

# Scale profiles

Use a standard minifigure standing height as the local reference rather than relying on seller labels.

Record:
- standing height mm;
- eye height;
- shoulder height;
- head width;
- shoulder width;
- torso width;
- hand span;
- foot footprint;
- stud/grid footprint.

Then calculate normalized ratios.

For example, a ~7 cm custom body is approximately 1.7x the height of a ~4 cm minifigure-scale reference, but Brickmen should use measured samples rather than market dimensions for final geometry.

---

# Body recognition pipeline

Goal:
Given a catalog image, user photo, marketplace listing, or generated image, identify the body architecture independently of character identity.

## Stage 1 — figure segmentation

Use a person/figure segmentation model or SAM-style prompted mask.

Produce:
- figure mask;
- component masks if possible;
- confidence.

## Stage 2 — canonical pose/scale normalization

Estimate:
- feet baseline;
- head top;
- centerline;
- shoulder landmarks;
- elbow/wrist;
- hip;
- knee/leg split;
- hand tips.

If visible:
- detect studs/baseplate;
- known minifigure;
- known accessory;
to recover absolute scale.

## Stage 3 — architecture features

Visual features:
- height/width ratio;
- head width / body height;
- shoulder width / head width;
- torso width / hip width;
- arm thickness;
- upper-arm vs forearm segmentation;
- elbow presence;
- wrist/hand segmentation;
- leg length;
- integrated vs separate head;
- integrated vs separate lower body;
- standard minifigure head silhouette;
- standard leg silhouette;
- giant hand silhouette;
- foot stud/anti-stud layout where visible.

Catalog features:
- maker;
- product code;
- seller size;
- part inventory;
- source label;
- known mold family.

## Stage 4 — retrieval + classifier

Do not rely on one image classifier.

Combine:
1. exact known release lookup;
2. maker/product-code architecture map;
3. visual embedding nearest neighbors;
4. landmark/ratio classifier;
5. component/joint detector;
6. VLM explanation;
7. confidence reconciliation.

Output:
- canonical architecture ID;
- candidate alternatives;
- observed source label;
- confidence;
- evidence.

## Stage 5 — unknown architecture detection

If the figure does not fit existing geometry within confidence:
- assign `architecture_unknown_candidate`;
- save the image/source;
- create a body-architecture research candidate;
- cluster with similar unknown bodies;
- do not force it into bigfig/midfig.

This is important for continuously discovering new custom body molds.

---

# Style recognition on non-standard bodies

The generation/training system should extract style **relative to the selected architecture**, not from raw pixels alone.

Example:
A chest line on an Alpha 7 cm body occupies a different curved surface and proportion than the same design on a standard torso.

For each architecture maintain a BodySurfaceMap:

- head front/rear/side;
- chest;
- abdomen;
- upper back;
- lower back;
- upper arms;
- forearms;
- hands;
- pelvis;
- thighs;
- lower legs;
- feet;
- optional armor/accessory surfaces.

Also maintain UV or canonical render projections when possible.

Style features become normalized values such as:
- chest-detail density per surface area;
- outline thickness relative to torso width;
- face landmark positions relative to head;
- muscle-sculpt exaggeration;
- shoulder/chest ratio;
- arm taper;
- hand size;
- print-vs-sculpt semantics.

This lets Brickmen learn "Alpha-style anatomical exaggeration" or "official giant style" without confusing it with absolute dimensions.

---

# Cross-architecture style transfer

Desired operation:

```
style.translate(
  source_design,
  source_architecture,
  target_architecture,
  target_character
)
```

It should separate:

### Identity features
- hair;
- face;
- costume;
- scars;
- color blocks;
- symbols;
- characteristic musculature.

### Architecture-specific geometry
- joint boundaries;
- torso width;
- head connector;
- arm segmentation;
- foot width;
- hand connector.

### Style grammar
- degree of anatomical sculpting;
- rounding/blockiness;
- line density;
- surface relief;
- proportion exaggeration.

Then re-solve the character for the target body rather than scaling the old model.

---

# Body architecture selection for a character

Accessory/body planner should evaluate candidate architectures using:

- canonical character size relative to companions;
- body mass/bulk;
- silhouette;
- required articulation;
- outfit/armor;
- required standard accessories;
- source-era/design intent;
- closest official/custom precedents;
- user preference;
- manufacturing complexity.

Possible output:

```json
{
  "character": "Thing",
  "architecture_candidates": [
    {
      "id": "minifig_oversized_torso_hybrid",
      "rationale": "broad but still minifigure-scale"
    },
    {
      "id": "community_midfig_parametric",
      "rationale": "better comic-scale bulk"
    },
    {
      "id": "giant_modular_head",
      "rationale": "maximum size but may overstate scale"
    }
  ]
}
```

The system should not mechanically equate:
"muscular character" -> bigfig.

---

# Generation architecture

For every body architecture create a canonical digital twin.

Each twin includes:
- exact coordinate system;
- neutral pose;
- component meshes;
- joint axes;
- articulation sweeps;
- connector solids;
- surface segmentation;
- printable surfaces;
- decoration templates;
- render cameras;
- silhouette masks;
- scale metadata.

Then generation becomes:

```
Character appearance
 -> body architecture selection
 -> canonical body twin
 -> body-specific style profile
 -> custom geometry decisions
 -> surface art / sculpt generation
 -> architecture-aware DFM
 -> canonical renders
 -> evaluation
```

The body twin, not the image model, remains geometry authority.

---

# Training corpus design

For every observed figure, store:

```
FigureRelease
BodyArchitecture
BodyStyleProfile
ComponentObservations
CanonicalViewAssets
SurfaceFeatures
Character/Appearance
Maker
ProductionMethod
Confidence
```

Training pairs:

### Recognition
image(s) -> architecture ID + component graph

### Part segmentation
image -> head / torso / upper arm / forearm / hand / pelvis / legs ...

### Style representation
canonical architecture render -> style embedding/features

### Cross-architecture translation
same character/design represented in multiple architectures

Hulk is an ideal initial benchmark because the market provides:
- standard minifigure versions;
- muscle-body/mid-size variants;
- Alpha 7 cm figures;
- official and compatible classic bigfigs;
- premium custom sculpts;
- microfigure variants.

Thing, Bane, Venom, Kingpin, Colossus, Juggernaut, Abomination, Beast and Killer Croc provide additional architecture-pressure cases.

---

# 3D-printable body system strategy

Accessories are easier than complete articulated bodies. For body systems, use staged validation.

## Stage 1 — static display body

Generate:
- head;
- torso/body;
- arms;
- hands;
- lower body;
but allow fixed joints.

Purpose:
validate silhouette/style/scale cheaply.

## Stage 2 — modular non-wear body

Make components removable but do not require repeated articulation.

Purpose:
validate connectors/assembly.

## Stage 3 — articulated prototype

Parameterize:
- shoulder;
- elbow;
- wrist;
- neck;
- hip;
- leg;
- foot.

Use separate calibration coupons for every joint.

## Stage 4 — cycle-qualified body

Measure:
- insertion/removal;
- rotational torque;
- creep;
- cycle wear;
- drop;
- fracture.

Only then call the architecture reusable.

---

# Original Brickmen body families to develop

Rather than only reproducing existing custom bodies, Brickmen should eventually define its own open parametric body family.

Recommended original system:

## Brickmen Standard
canonical standard minifig compatibility.

## Brickmen Broad
Axl/Hagrid-inspired broad torso while preserving maximum standard-part compatibility.

## Brickmen Mid
between standard and giant:
- standard head option;
- standard-compatible or enlarged legs;
- custom torso/arms/hands;
- optional elbows.

## Brickmen XL
approximately 7 cm class:
- modular head;
- articulated shoulder/elbow/wrist;
- custom legs;
- enlarged hands;
- full body surface map.

## Brickmen Giant
classic bigfig-scale, modularized for 3D printing:
- separate head/hair;
- body;
- arms;
- hands;
- optionally legs if manufacturing benefits.

Each family should share connector conventions wherever mechanically sensible.

This gives the generator stable targets without depending forever on reverse-engineered third-party bodies.

---

# Physical research program

Acquire representative samples from each architecture and perform:

1. standardized photography;
2. weigh;
3. standing-height measurement;
4. bounding dimensions;
5. component disassembly;
6. joint inventory;
7. connector measurements;
8. motion range;
9. fit-force/torque;
10. 3D scan/photogrammetry where useful;
11. digital twin reconstruction;
12. repeated assembly;
13. material observation;
14. foot/stud compatibility;
15. standard-part interchangeability.

Priority samples:
- standard minifigure;
- Woody long-limb;
- Axl oversized torso;
- Hagrid broad giant;
- early integrated-head Hulk giant;
- newer modular-head Hulk/Thanos giant;
- specialized giant such as Killer Croc;
- Alpha Toys AF344/AF345;
- Alpha AF361/AF363;
- one 7.5 cm AF creature such as Abomination;
- GH0304-style muscle body;
- one community printable midfig;
- one premium proprietary muscular custom if obtainable.

---

# Research conclusion

The correct long-term abstraction is not "minifig vs bigfig."

It is a **figure-body architecture graph**.

Brickmen should understand body systems the way CAD understands machine assemblies:
- components;
- joints;
- constraints;
- connectors;
- scale;
- surfaces;
- style.

Once that layer exists, recognition, generation and 3D printing become the same problem viewed in different directions:

**Recognition:** image -> body architecture + style.

**Generation:** character + body architecture + style -> model/art.

**Manufacturing:** body architecture + validated connector/material profiles -> printable physical parts.

That is the architecture required for intelligently applying learned minifigure style to non-standard bodies instead of merely stretching standard minifigure artwork over a larger model.
