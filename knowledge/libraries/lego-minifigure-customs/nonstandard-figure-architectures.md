# Non-Standard Minifigure and Custom Figure Architectures

Research snapshot: 2026-09-27

## Executive conclusion

"BigFig", "midfig", "muscle body", "mega fig", "7CM", and similar market terms are not reliable mechanical standards.

Brickmen must model **figure architecture** separately from:
- character identity;
- maker;
- source label;
- body size;
- style;
- release.

The same character may legitimately exist in multiple architectures. Hulk is an ideal example: official LEGO has used Giant/BigFig bodies, standard minifigure bodies, and short-leg Mighty Micros bodies, while third-party makers use multiple unrelated large or muscular systems.

Therefore the canonical relationship is:

```
Character / SourceAppearance
  -> FigureRelease
  -> FigureArchitectureObservation
  -> FigureArchitecture
  -> ComponentGraph
  -> JointGraph
  -> ConnectorProfiles
  -> Surface/Style Profile
```

A seller label such as "BigFig" is preserved as evidence, but it must not silently determine the normalized architecture.

## Why this matters

A generation system that only knows "make Hulk" may choose the wrong physical language.

Different architectures change:
- head/body ratio;
- torso width;
- arm length and bulk;
- hand size;
- leg architecture;
- articulation;
- compatible accessories;
- connector dimensions;
- printable surfaces;
- how much detail should be sculpted versus printed;
- acceptable silhouette exaggeration.

For future 3D printing, these systems also require different joint engineering and material strategies.

## Official and custom architecture families found in the scan

### Standard minifigure family

Baseline modular minifigure architecture:
- head;
- torso;
- arms;
- hands;
- hips;
- legs;
- headwear/accessories.

Variants include:
- short legs;
- medium articulated legs;
- long/extended legs and long-arm special bodies;
- specialized heads/hair;
- dual-moulded or specialized limbs.

These should remain variants within the standard minifigure architecture unless the component/joint graph changes substantially.

### LEGO Giant / BigFig / Giant figure family

BrickLink catalogs the large modular Hulk/Thanos-style architecture as **Giant** parts.

Representative Hulk/Thanos inventories establish a reusable mechanical family:
- body/torso giant components;
- left Giant arm 10154;
- right Giant arm 10124;
- left Giant hand 10127;
- right Giant hand 10126;
- Technic axle/pin 43093 used at the shoulders;
- character-specific body/head/arm variants.

This is important for manufacturing automation: the shoulder connection does not need to be reinvented from a picture. It can be represented as a validated reusable connector/joint family.

Later Giant figures may have modified heads, armor and arms while retaining major joint families.

### Legacy Giant / Troll family

Fantasy Era trolls and similar older large bodies are not assumed to be the same architecture as modern Hulk/Thanos Giant figures.

BrickLink lists Fantasy Era Troll giant body variants around part 60671. The architecture should remain a separate family until component/joint measurements prove compatibility.

### Hagrid giant-body hybrid

Hagrid demonstrates another official architecture:
- giant/oversized body component 40250 family;
- standard minifigure-style head/hair compatibility in at least some releases;
- body proportions and joints distinct from the Hulk Giant family.

This shows why "large figure" should not map to one universal BigFig template.

### Axl / oversized-torso minifigure hybrid

Nexo Knights Axl is especially important as an official precedent for an intermediate architecture.

Representative inventory evidence shows:
- standard minifigure head;
- standard minifigure hips/legs;
- oversized torso assembly 23763c01;
- specialized large arms 24101/24104.

Mechanically and visually this is closer to "oversized torso on standard lower body" than a classic Hulk Giant.

This architecture is an excellent reference for future custom muscular/mid-scale figures because it preserves many standard minifigure relationships.

### Alpha Toys AF 7 cm articulated muscle family

The "AF" Hulk line is **Alpha Toys**.

Representative catalog/listing evidence:
- AF344–AF347 Hulk variants are marketed around 7 cm;
- AF345 is cataloged as Alpha Toys Hulk;
- AF361 Beast is documented as 7 cm tall;
- AF363 Colossus is documented as 7 cm tall;
- the broader AF family includes Hulk, Red Hulk, Maestro, Abomination, Weapon H, A-Bomb, Thing/Colossus/Beast and other muscular characters.

The visual architecture is clearly distinct from both standard minifigures and LEGO's traditional Hulk Giant:
- more humanized/muscular torso;
- large articulated arms;
- separate hands;
- long muscular legs;
- standard-system compatibility claims in retailer listings.

**Do not yet treat all AF 7 cm releases as mechanically identical.** Physical samples are required to verify whether shoulder, wrist, hip, head and accessory connections are shared across the family.

Normalized status:
`custom_alpha_7cm_muscle / physical_metrology_pending`.

### G (2) muscular hybrid family

G (2) releases such as GH0303 Red Hulk and GH0304 Hulk show another custom muscular morphology.

Visual evidence suggests:
- oversized muscular torso/arms;
- separate hands;
- minifigure-derived head/lower-body proportions;
- architecture distinct from Alpha Toys 7 cm.

Exact joint dimensions and cross-release compatibility are not established from public catalog evidence.

Normalized status:
`custom_g2_muscle_hybrid / physical_metrology_pending`.

### Bigguy Minifigs muscular family

Bigguy's Hulk/Red Hulk customs use a proprietary muscular large-body treatment distinct from classic Giant and Alpha Toys.

Public product/catalog images show:
- broad sculpted torso;
- very large muscular arms/hands;
- separate two-leg lower body;
- custom head/neck treatment.

The exact joint graph, height and compatibility dimensions require a physical sample.

Normalized status:
`custom_bigguy_muscle / physical_metrology_pending`.

### Mr.J Brick x Heart muscular family

Mr.J Brick x Heart Hulk customs show another proprietary large muscular architecture:
- sculpted chest/back musculature;
- specialized arms/hands;
- separate legs;
- distinct proportions from Bigguy and Alpha.

Do not merge this with Bigguy merely because the silhouette category is similar.

Normalized status:
`custom_mrj_heart_muscle / physical_metrology_pending`.

### Maker-specific custom BigFig families

Premium/custom makers including Calypso Customs, Shadow Studio, STUDIOGENESIS and others release products explicitly described as BigFig.

The label alone does not prove use of the official LEGO Giant joint graph. Each maker/body family must be measured or supported by strong component evidence before being mapped to `lego_giant_modular`.

Until resolved:
`custom_bigfig_maker_specific`.

### Compatible clone Giant / BigFig families

HeroBloks catalogs many figures explicitly labeled BigFig from brands such as:
- Decool;
- Xinh;
- Sheng Yuan;
- Lele;
- Pogo;
- Kopf;
- Koruit;
- Bela;
- Eagle;
- other compatible brands.

Many likely reproduce or adapt the LEGO Giant architecture, but **release-level compatibility must not be inferred solely from the BigFig label**.

Track each release as:
- `source_body_label = BigFig`;
- architecture candidate;
- evidence;
- physical validation state.

### KDL ~6.5 cm large figures

KDL Thing K2302 is publicly listed around 6.5 cm.

This is evidence of another intermediate/large custom scale. It is not enough to establish its joint compatibility with Alpha Toys, LEGO Giant or other 6–7 cm bodies.

Normalize as a candidate family until measured.

### Community "midfig" printable bodies

"Midfig" is a community/design label rather than a standardized mechanical architecture.

Examples include:
- printable "mid figure/muscle body" projects with separate torso/arms and standard-compatible hands;
- community designs intended to sit visually between minifig and BigFig;
- purist brick-built mid-scale bodies.

Some printable authors explicitly discuss sanding/scaling/gluing joints, which confirms that mechanical compatibility varies by printer/model rather than defining one universal MidFig standard.

Brickmen should retain:
`source_body_label = midfig`
while assigning a specific architecture only after geometry/joints are identified.

### Microfigure / baby / minidoll / adjacent systems

Official LEGO also contains body architectures far outside the standard minifigure, including microfigures, baby/toddler bodies, minidolls and theme-specific character systems.

These should eventually enter the same `FigureArchitecture` framework if Brickmen wants generation across all LEGO-compatible character formats.

They are adjacent to the current custom-large-body priority rather than being forced into the minifigure subtype table.

## Terminology policy

Store three separate concepts:

1. **source label** — exact wording from maker/catalog: BigFig, Midfig, Mega fig, 7CM, muscle body, Giant.
2. **normalized scale/morphology class** — standard, intermediate, large, micro, oversized-torso hybrid, muscular humanoid, etc.
3. **mechanical architecture** — exact component/joint/connector graph.

Never promote source terminology into mechanical truth.

Example:

```json
{
  "source_body_label": "BigFig",
  "normalized_morphology": "large_humanoid",
  "architecture_candidate_id": "lego_giant_modular",
  "architecture_confidence": "catalog_inferred",
  "physical_validation": "pending"
}
```

## FigureArchitecture data model

Required fields:

- architecture_id
- canonical_name
- source_aliases
- maker_scope
- architecture_status
- scale_class
- nominal_height_mm and evidence
- component_graph
- joint_graph
- connector_profile_ids
- standard_system_connections
- canonical_coordinate_frames
- component_landmarks
- articulation_axes/ranges
- articulation_keepouts
- mating/accessory zones
- printable/decoratable surfaces
- canonical body proportions
- style_profile_id
- digital_twin_id
- measurement_profile_id
- manufacturing_profile_ids
- recognition_features
- representative_release_ids
- source/evidence
- confidence

## Component graph

Do not assume every figure contains the normal seven-part minifigure breakdown.

Example LEGO Giant conceptual graph:

```
body
 |- head or integrated/special head
 |- left shoulder pin -> left arm -> left hand
 |- right shoulder pin -> right arm -> right hand
 |- lower-body/legs
 |- optional armor/headwear
```

Example Axl hybrid:

```
standard head
 -> oversized torso
    |- specialized left arm/hand
    |- specialized right arm/hand
 -> standard hips
    |- standard left leg
    |- standard right leg
```

Example custom Alpha body must remain provisional until teardown/metrology establishes the real graph.

## Joint graph

Each joint should store:

- joint_id
- parent component
- child component
- joint type
- degrees of freedom
- rotation/translation axis
- nominal range
- connector geometry IDs
- friction/retention target
- materials
- wear surface
- disassembly method
- physical validation

This is the bridge from catalog knowledge to printable engineering.

## Compatibility graph

Track compatibility at the **interface**, not the whole figure.

Examples:
- accepts standard minifigure headgear;
- accepts standard head;
- accepts 3.18-family bar;
- uses Technic 43093 shoulder pin;
- accepts standard minifigure hand;
- accepts standard legs;
- standard stud/anti-stud mounting;
- custom proprietary wrist;
- unknown.

A body can therefore be partly compatible.

## 3D-printing strategy

### Modular first

Do not print a complex articulated body as one monolithic piece.

Generate each articulation component independently:
- torso;
- arms;
- hands;
- head/hair where needed;
- hip/lower-body;
- legs;
- armor.

### Reuse commodity hardware

Where an architecture already uses common LEGO-system hardware, prefer validated genuine/compatible components when practical.

The LEGO Giant shoulder use of Technic 43093 is an important precedent: printing the visual torso/arm around a proven pin may be mechanically superior to resin-printing a tiny wear-critical axle/pin.

A community printable Iron Golem BigFig similarly uses 43093 hardware to connect modular printed components.

### Parametric joints

All printable joints should come from validated architecture-specific connector libraries, not generative meshes.

```
alpha_shoulder_joint_v1
lego_giant_shoulder_43093_socket_v1
axl_standard_hip_interface_v1
custom_midfig_wrist_v3
```

### Hybrid materials

A large custom body may use:
- resin for visual shells;
- commodity ABS/Technic pins for joints;
- FDM/nylon/POM-like inserts where appropriate;
- metal rods/fasteners only for architectures explicitly designed for them.

Material selection follows measured force/cycle data.

## Physical acquisition/metrology queue

Priority physical samples:

1. official LEGO Giant Hulk/Thanos components or inexpensive known-compatible equivalents;
2. official Axl oversized-torso body;
3. official Hagrid giant body;
4. Alpha Toys AF345 Hulk and/or AF361 Beast;
5. G (2) GH0304 Hulk;
6. Bigguy Hulk/Red Hulk;
7. Mr.J Brick x Heart Hulk;
8. KDL K2302 Thing;
9. one community printable MidFig;
10. standard/short/medium/long-leg baselines.

For each:
- photograph disassembly;
- weigh;
- measure overall proportions;
- measure every joint;
- classify polymer where feasible;
- record connector cross-compatibility;
- scan components;
- create canonical digital twin;
- run joint force/cycle tests where sacrificial samples permit.

## High-value cross-architecture character corpus

Characters appearing in many body treatments are ideal translation supervision.

Priority:
- Hulk;
- Red Hulk;
- Thing;
- Colossus;
- Beast;
- Juggernaut;
- Abomination;
- Venom/large symbiotes where available;
- Thanos;
- large fantasy trolls/ogres.

Hulk alone supplies examples across:
- standard minifigure;
- short-leg/Mighty Micro;
- official Giant;
- compatible Giant;
- Alpha Toys 7 cm;
- G (2);
- Bigguy;
- Mr.J/Heart;
- premium custom BigFig.

This is far more valuable for style research than treating each product only as a collector listing.

## Sources / discovery references

Primary/structured discovery sources should include:
- LEGO official catalogs/instructions where available
- BrickLink inventories and part catalogs
- Rebrickable part/inventory data
- HeroBloks custom/compatible release catalog
- maker/storefront primary pages
- retained physical measurements

Representative current evidence:
- HeroBloks Alpha Toys Hulk/Beast/Colossus records
- 01BigBricks Alpha Toys 7 cm listings
- BrickLink Giant Hulk/Thanos inventories with Giant arms/hands and Technic 43093
- BrickLink Axl inventory with oversized torso/arms and standard head/lower body
- BrickLink Hagrid giant body and standard head compatibility
- printable community Giant/MidFig models as secondary engineering evidence

Catalog evidence establishes identity and candidate relationships. Only physical metrology should establish manufacturing-critical dimensions.

## Topology extension: non-humanoid and multi-segment bodies

The architecture registry must cover more than humanoid scale classes.

Official catalog evidence establishes useful topology precedents:

- **stacked-torso multi-arm**: Lord Garmadon figures can combine a standard torso with an additional modified short torso/armor assembly, creating a second shoulder/arm level rather than using one four-arm torso;
- **specialized mechanical/droid**: General Grievous has dedicated mechanical torso, arm and leg families;
- **ghost lower body**: 19859 family;
- **serpent lower body**: 98140 family with molded flexible tail;
- **merfolk lower body**: 65755 family;
- **tentacle lower bodies**: 24793 / 87749 families;
- **robot roller lower body**: 5470;
- **centaur hybrid**: 67638 lower body;
- **Jabba-style specialized tail body**: 98111c01 family;
- **integrated character-specific bodies**: Angry Birds, Gollum-like integrated body/head forms, Lumpy Space Princess and other franchise-specific molds.

These are not merely cosmetic tags. They change:
- component graph;
- locomotion/footprint;
- articulation;
- surface map;
- accessory clearance;
- pose generation;
- support/printing strategy.

### Generation rule

The generator should preserve standard-minifigure grammar only on components that remain standard.

For example:
- centaur: standard head/torso/arms may use minifigure art grammar, while the quadruped lower body gets its own surface/style map;
- serpent: do not invent two legs because the character was trained mostly on standard figures;
- multi-arm: shoulder levels and arm count come from FigureArchitecture before character styling;
- mechanical droid: do not force flesh/minifigure-arm assumptions onto mechanical limbs.

### Release-level architecture evidence

Maker and serial prefixes are priors, not architecture IDs.

Current custom-market evidence reinforces this:
- Alpha Toys AF345 Hulk is sold around 7 cm and HeroBloks groups Alpha releases separately from explicit BigFig entries;
- Alpha AF361 Beast and AF363 Colossus are cataloged at 7 cm;
- G (2) GH0304 Hulk is a distinct muscular minifigure-like form in product imagery, while G (2) GH0318 Kingpin is separately cataloged as a BigFig.

Therefore all custom ingestion writes a `FigureArchitectureObservation` per release/body family before any maker-level propagation.

See:
- `nonstandard-body-census-and-ingestion.md`
- `data/figure-architecture-observation-schema.json`
- `data/body-style-profile-registry.json`.

## Mega-scale and enhanced-articulation custom systems

### OA 16 cm MegaFig candidate family

HeroBloks currently documents OA2201-OA2204 as a four-release MegaFig group, each at 16 cm:
- Dr Manhattan;
- Sentinel;
- Atom Smasher;
- Giant Man.

This is enough to create a *family candidate* and scale profile, but not enough to claim identical joints.

Canonical provisional ID:
`custom_oa_160mm_megafig_candidate`.

Research questions:
- molded vs printed vs multi-part construction;
- head/neck modularity;
- shoulder/elbow/wrist joints;
- hips/knees;
- foot/stud compatibility;
- whether OA2201-OA2204 share a blank body platform.

### DY very-large figures

DY_Minifigs current records include at least:
- DY1806 Galactus at 28.5 cm;
- DY1817 Ant-Man Quantum Realm at 22.5 cm tall and 8 cm wide.

The difference is large enough that Brickmen keeps:
`custom_dy_mega_scale_unresolved`
as an umbrella observation only.

### Buildable characters

Buildable Giant Man/Sentinel/Galactus entries are cataloged separately from MegaFig and BigFig versions.

Canonical umbrella:
`buildable_character_figure_unresolved`.

This is an *assembly architecture* rather than a body mold:
- graph nodes = parts/subassemblies;
- graph edges = studs/pins/hinges/ball joints/etc.;
- surface/style may be distributed across many elements.

Future generation should be able to choose between:
- minifigure/custom body;
- Giant/BigFig;
- Mega-scale custom body;
- brick-built character.

### Standard-scale custom ball-joint arms

Current custom makers have begun replacing the normal minifigure shoulder connection with ball-jointed/adapted arm systems while retaining roughly 1:1 minifigure scale.

Canonical provisional family:
`custom_standard_ball_joint_arm_adapter`.

This architecture is strategically important for Brickmen because it demonstrates that **articulation can be upgraded independently from the rest of the body**.

A future Brickmen Standard-Articulated option could preserve:
- standard head;
- torso dimensions;
- hips/legs;
- hand/accessory system;
while replacing only the shoulder interface.

Research must establish:
- adapter/pin dimensions;
- ball diameter;
- socket material;
- insertion force;
- rotation range;
- torso-hole stress;
- cycle wear.

### Scale class remains descriptive

Suggested descriptive scale metadata may include:
- micro;
- standard;
- intermediate;
- large/Giant;
- extra-large;
- mega.

These are useful for retrieval and character-relative scale selection, but **never identify architecture by themselves**.

