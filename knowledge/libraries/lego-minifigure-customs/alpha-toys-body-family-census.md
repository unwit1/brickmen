# Alpha Toys Body-Family Census

Research snapshot: 2026-09-27

## Why this census exists

Alpha Toys is now a direct demonstration that **maker + AF serial prefix does not identify one body architecture**.

At minimum, current evidence supports:

1. standard/minifigure-like Alpha releases;
2. a ~4–4.5 cm muscular/symbiote hybrid body;
3. a ~7 cm muscular large-body family.

There may be further revisions/families. Brickmen therefore resolves body architecture at release/body-family level.

## Family A — AF321–AF326 symbiote muscle hybrid

Observed releases:
- AF321 Venom (movie);
- AF322 Carnage;
- AF323 Riot;
- AF324 Anti-Venom;
- AF325 Venom;
- AF326 Anti-Venom.

Retail series evidence:
- AF321–AF326 sold together;
- product dimension approximately 4–4.5 cm;
- ABS;
- LEGO-compatible marketing.

Visual architecture:
- standard-ish total stature;
- highly widened/sculpted torso and shoulders;
- large muscular arms;
- standard-like two-leg lower silhouette;
- large organic/symbiote accessory package.

Normalized candidate:
`custom_alpha_45mm_muscle_hybrid`.

## Family B — AF327–AF332 symbiote hybrid revision candidate

Observed:
- AF327 Toxin;
- AF328 Ancient Venom;
- AF329 Lasher;
- AF330 Absolute Carnage;
- AF331 Sleeper;
- AF332 Phage.

Retail examples remain approximately 4–4.5 cm.

Some HeroBloks records use the source tag `MaxiFig`, notably AF328/AF330.

That tag must not imply a larger mechanical scale because:
- retailer size remains around standard-minifigure height;
- imagery shows oversized upper-body mass rather than a 7 cm stature jump.

Current treatment:
same architecture candidate as Family A, but mechanical equivalence is unverified.

## Family C — standard/minifigure-like Alpha releases

AF336 Thing (First Steps) is a clear counterexample to "all Alpha customs are oversized."

Current treatment:
`minifig_standard_or_custom_standard`.

The AF333–AF341 series requires release-level classification rather than one family assumption.

## Family D — ~7 cm muscular large body

Strong current evidence includes:
- AF344 Hulk;
- AF345 Hulk;
- AF349 Maestro;
- AF351 Weapon H;
- AF358 A-Bomb;
- AF362 Thing;
- AF365 Juggernaut;
- AF367 Infinity Hulk;
- AF369 Green Scar;
plus documented 7 cm Beast/Colossus releases and other Hulk-family figures.

Retail/catalog sources explicitly market multiple examples as 7 cm.

Normalized candidate:
`custom_alpha_7cm_muscle`.

Visual language:
- significantly taller than standard minifigure;
- longer legs;
- more anatomical humanoid proportions;
- large articulated-looking arms;
- high sculptural anatomy density.

This is **not** the AF321–AF332 Venom architecture.

## Important code-range warning

Do not create rules such as:
- AF3xx = 7 cm;
- AF32x = hybrid;
- AF36x = 7 cm.

Serial locality can support a cluster prior, but actual architecture resolution must use:
- release record;
- catalog image;
- stated size;
- known body-family cluster;
- eventually physical components.

## Architecture features worth comparing physically

### AF325 vs AF345

This pair is especially valuable because both are exaggerated muscular characters from Alpha but use very different scale strategies.

Measure:
- overall height;
- shoulder width / height;
- chest depth / height;
- hip/lower-body width;
- leg length;
- hand width;
- head/neck connection;
- shoulder joint type;
- wrist joint;
- standard accessory grip;
- leg/hip compatibility.

This establishes whether Alpha's design language is shared across architectures or mostly body-family-specific.

### AF325 vs AF328

This pair resolves whether AF327–AF332 is:
- mechanically identical to AF321–AF326;
- a revised mold family;
- a closely related but separate architecture.

## Training value

Alpha offers unusually strong within-maker supervision.

### Same maker / different architecture
- AF336 standard-like Thing;
- AF325 45 mm hybrid Venom;
- AF345 7 cm Hulk;
- AF362 7 cm Thing.

This helps learn:
**maker style != body architecture**.

### Same broad morphology / different architecture
- AF325 Venom hybrid;
- AF345 Hulk 7 cm;
- AF365 Juggernaut 7 cm.

This helps separate:
- upper-body exaggeration;
- overall stature;
- anatomy detail.

### Same architecture / different characters
AF321–AF326 and AF327–AF332 provide many symbiotes on one/few related body families.

This is ideal for learning:
- reusable skeleton;
- character-specific surface shell;
- shared accessories/anchors.

## Brickmen-original design implications

The AF325 pattern supports a useful original Brickmen body mode:

**standard-height broad/muscular hybrid**

This should be distinct from Brickmen MidFig if the latter is taller.

Possible future architecture target:
`brickmen_broad_v0`.

Design goals:
- standard minifigure head ecosystem where viable;
- standard or adapted lower body;
- widened torso;
- replaceable large arms/hands;
- standard 3.18-family accessory grip;
- deterministic shoulders/wrists;
- character shells for symbiotes, Bane-like bodies, heavy armor, etc.

## Research sources

- AF321: https://www.herobloks.com/figures/31376/alpha-toys/af321/venom-%28movie%29
- AF325: https://www.herobloks.com/figures/31518/alpha-toys/af325/venom
- AF321–AF326 dimensions: https://brixtoy.com/product/marvel-venom-movie-af321-minifigures/
- AF328: https://www.herobloks.com/figures/33823/alpha-toys/af328/ancient-venom
- AF327–AF332 dimension example: https://brixtoy.com/product/marvel-ancient-venom-af328-minifigures-2/
- 7 cm catalog examples: https://www.01bigbricks.net/categories/minifigures-bigfigs
- AF369 7 cm example: retailer listing observed 2026-09-27
