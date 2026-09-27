# Venom Cross-Architecture Control Study

Research snapshot: 2026-09-27

## Why Venom matters

Venom is Brickmen's first control character where **height and upper-body mass are deliberately decoupled**.

Venom appears across:
- ordinary standard minifigure interpretations;
- Alpha Toys' ~4–4.5 cm muscular/symbiote hybrid;
- many compatible/custom BigFig interpretations;
- Alpha "MaxiFig"-tagged releases that remain around standard-minifigure total height;
- larger custom bodies.

This makes Venom an important correction to any naive rule such as:

> bulky character -> taller figure architecture

Alpha's AF321–AF332 families show that a figure can remain approximately standard minifigure height while radically changing:
- torso width/depth;
- shoulder mass;
- arm volume;
- hand/forearm silhouette;
- surface spikes/tendrils.

## Standard minifigure baseline

LEGO Venom releases such as SH0542 remain within the standard minifigure architecture.

Translation:
- Venom's mass is mostly suggested through decoration, head/face expression and accessories;
- shoulder/arm silhouette stays standard;
- white chest spider and facial markings carry disproportionate identity weight;
- symbiote tendrils become separate accessories/constructs when represented in 3D.

BrickLink lists SH0542 as a normal minifigure appearing in multiple Spider-Man sets.

## Alpha Toys AF321–AF326 — ~4–4.5 cm symbiote muscle hybrid

Retail/catalog evidence:
- Alpha Toys;
- AF321–AF326 sold as one series;
- product dimension listed as ~4–4.5 cm;
- AF321 Venom (movie);
- AF322 Carnage;
- AF323 Riot;
- AF324 Anti-Venom;
- AF325 Venom;
- AF326 Anti-Venom.

Product imagery shows recurring:
- oversized sculpted shoulder/torso shell;
- large muscular arms;
- strong deltoid/forearm mass;
- standard-like two-leg lower silhouette;
- total height still near standard minifigure scale;
- large symbiote accessories.

Architecture candidate:
`custom_alpha_45mm_muscle_hybrid`.

### Design lesson

This family communicates "large monster body" through **width/depth and limb bulk rather than overall height**.

The body-style compiler therefore needs independent dimensions for:
- stature;
- shoulder width;
- chest depth;
- arm bulk;
- hand scale.

A single `large_body=true` flag is inadequate.

## Alpha Toys AF327–AF332 — related symbiote revision candidate

Examples:
- AF327 Toxin;
- AF328 Ancient Venom;
- AF329 Lasher;
- AF330 Absolute Carnage;
- AF331 Sleeper;
- AF332 Phage.

Retail evidence still lists examples at ~4–4.5 cm.

HeroBloks tags AF328/AF330 as "MaxiFig", but their catalog/product imagery and retailer dimensions do not establish giant height.

Brickmen therefore stores:
- source_body_label = MaxiFig;
- architecture candidate = Alpha 45 mm muscle hybrid;
- mechanical equivalence to AF321–AF326 = pending.

### Important ontology lesson

"MaxiFig" can describe **bulky visual treatment** rather than a mechanically standardized height class.

Preserve the label; do not use it as architecture truth.

## Compatible/custom BigFig Venom ecosystem

HeroBloks catalogs Venom BigFig releases from makers including:
- Decool;
- Kopf;
- Pogo;
- Sheng Yuan;
- STUDIOGENESIS;
- SX;
- Xinh;
- others.

Movie Venom BigFigs also exist from:
- Eagle;
- World Minifigures;
- Xinh.

These provide a large-body comparison set but remain mechanically unresolved until mold-family clustering/metrology is done.

Representative:
- Xinh XH1911 Venom BigFig;
- Xinh XH1829 movie Venom BigFig;
- Sheng Yuan 1183-8 / 1184C;
- STUDIOGENESIS 61616.

## Architecture-neutral Venom semantics

Candidate CharacterBodyFeatureSpec:

```json
{
  "morphology_archetype": "symbiote_massive_humanoid",
  "stature_intent": "source_dependent",
  "mass_distribution": {
    "shoulders": "very_large",
    "chest": "very_large",
    "waist": "medium_to_large",
    "upper_arms": "large",
    "forearms": "very_large",
    "hands": "large"
  },
  "surface_materials": ["symbiote_organic"],
  "identity_features": [
    "large_white_eye_shapes",
    "white_spider_emblem_or_source_specific_chest_mark",
    "large_teeth",
    "tongue_source_dependent",
    "black_primary_body",
    "organic_tendrils_source_dependent"
  ]
}
```

The exact source appearance overrides generic defaults.

## New morphology dimension: stature vs mass

Brickmen should represent at least:

```
stature_class
upper_body_mass
lower_body_mass
shoulder_width
chest_depth
limb_bulk
hand_scale
head_scale
```

separately.

Examples:

### Standard Venom
- stature: standard
- upper-body mass: standard geometry
- perceived mass: print/accessories

### Alpha AF325
- stature: roughly standard
- upper-body mass: very large
- lower body: standard-like
- arms: very large

### BigFig Venom
- stature: large
- upper-body mass: very large
- lower body: large
- hands: large

This distinction should improve architecture selection for characters such as:
- Venom;
- Bane;
- Kingpin;
- Blob;
- armor-heavy characters.

## Symbiote surface-material grammar

Add `symbiote_organic` as a surface semantic.

Possible style treatments:
- smooth base mass;
- sparse raised veins;
- tendril/spike silhouette;
- glossy finish;
- emblem as print/paint or shallow relief;
- teeth/tongue as separate geometry when identity-critical.

### Manufacturing constraints

Avoid:
- dense micro-veins that become brittle/noisy;
- thin free-standing tendrils without tough material support;
- deep grooves crossing joints;
- spikes inside articulation sweeps.

Prefer:
- large silhouette tendrils;
- broad surface relief;
- printed vein networks;
- removable accessory tendrils.

## Venom-specific component reuse

A reusable architecture should allow:
- base muscle torso shell;
- character-specific chest surface;
- interchangeable head;
- optional shoulder/back tendril anchors;
- shared arm/hand mechanics.

This is ideal for:
- Venom;
- Carnage;
- Riot;
- Anti-Venom;
- Toxin;
- Lasher;
- Phage.

It also offers a strong training set where many characters share body family but differ in surface/color/silhouette details.

## Same-architecture symbiote corpus

AF321–AF326 is valuable for **same architecture, different character** learning.

Use it to separate:
- architecture invariants: shoulder/arm/lower-body grammar;
- symbiote species style: organic mass/tendrils;
- character identity: colors/emblems/head/tongue/spikes.

This complements the cross-architecture Hulk/Thing datasets.

## Cross-architecture Venom benchmark

Recommended comparison set:
1. LEGO standard Venom;
2. Alpha AF321/AF325 45 mm hybrid;
3. one validated custom/compatible BigFig Venom;
4. Brickmen MidFig generated Venom;
5. Brickmen Giant-compatible generated Venom.

Questions:
- can Brickmen preserve identity while moving body mass between print and geometry?
- can it preserve approximate height while widening only upper body?
- does the surface compiler assign veins/tendrils intelligently?
- do accessories/tendrils scale with architecture without altering grip mechanics?

## Physical acquisition priority

Add one AF321–AF326 representative, preferably AF325 or AF321, to the physical metrology queue.

Measure:
- assembled height;
- torso width/depth;
- standard leg/hip compatibility;
- head/neck interface;
- shoulder joint;
- elbow/arm segmentation if any;
- wrist/hand connection;
- accessory grip;
- compatibility with Alpha AF327–AF332 if a second sample is acquired.

This should occur separately from acquiring a 7 cm Alpha Hulk/Beast body.

## Sources

- Alpha AF325 HeroBloks: https://www.herobloks.com/figures/31518/alpha-toys/af325/venom
- Alpha AF321 HeroBloks: https://www.herobloks.com/figures/31376/alpha-toys/af321/venom-%28movie%29
- AF321–AF326 series dimension: https://brixtoy.com/product/marvel-venom-movie-af321-minifigures/
- AF325 dimension: https://www.minifigtoys.com/products/venom-af325-minifigures-marvel-minifigure
- Alpha AF328: https://www.herobloks.com/figures/33823/alpha-toys/af328/ancient-venom
- AF327–AF332 dimension example: https://brixtoy.com/product/marvel-ancient-venom-af328-minifigures-2/
- Xinh XH1911 BigFig: https://www.herobloks.com/figures/28107/xinh/xh1911/venom-%28bigfig%29
- Xinh XH1829 movie BigFig: https://www.herobloks.com/figures/27853/xinh/xh1829/venom-%28movie%29-%28bigfig%29
- LEGO standard Venom SH0542 sets: https://www.bricklink.com/catalogItemIn.asp?M=sh0542&in=S
