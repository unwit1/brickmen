# Controlled Physical Minifigure Reference Capture

Research snapshot: 2026-09-24

## Why this matters

The official web corpus is biased toward front three-quarter catalog renders. Template generation needs information that those images often omit:
- exact back print;
- left/right arm print;
- side-leg print;
- reverse face;
- helmet/mask sides and rear;
- print alignment around curved surfaces;
- real-world scale and edge survivability.

A controlled local photography program can fill these gaps with user-authored photographs of physical official figures.

## Capture tiers

### Tier A — whole-figure canonical views

Capture:
- front
- rear
- left
- right
- front-left 3/4
- front-right 3/4
- rear-left 3/4
- rear-right 3/4
- top when hair/headgear geometry matters

Keep:
- pose neutral;
- arms at standardized angle;
- hands standardized;
- head square to torso unless a dedicated head rotation sequence is being captured;
- same focal length and camera distance.

### Tier B — component macro

Capture separately:
- head front
- head reverse
- head left/right when wrap exists
- torso front/back
- each printed arm
- hips/legs front/back/sides
- helmet/headgear front/side/rear
- cloth/bodywear laid flat where safe
- primary accessory

This is higher-value for template learning than another full-figure beauty shot.

### Tier C — rotational geometry

For masks/headgear/new mould study:
- 12 or 24 evenly spaced yaw angles;
- optional elevation rings;
- silhouette mask;
- scale reference.

This can support photogrammetry or silhouette-based geometry fitting.

## Imaging setup

Prefer:
- fixed camera/tripod;
- fixed focal length;
- low-distortion macro or telephoto-equivalent framing;
- diffused light tent;
- neutral matte background;
- manual exposure;
- manual/fixed white balance;
- RAW capture when available;
- color/gray reference card at start of each session;
- ruler/scale target in calibration frame;
- remote shutter/timer.

Optional for glossy ABS:
- cross-polarized lighting/camera filter pair to suppress specular glare;
- separate non-polarized capture to preserve material/gloss information.

Do not mix glare-suppressed and normal images without labeling them.

## Perpendicular print capture

For flat-print reconstruction, align the visible printed surface as perpendicular to the optical axis as geometry permits.

This matches Mecabricks' own reference-submission guidance: its decoration workflow asks for scanned images or perpendicular photos of printed pieces, sharp/high resolution, and recommends combining multiple views such as torso front/back for reconstruction.

## Focus

At minifigure macro distances depth of field is shallow.

Use:
- smaller aperture within diffraction limits;
- focus stacking for masks/headgear where necessary;
- one non-stacked original retained alongside any merged stack.

Never let focus-stacking artifacts become training linework without source linkage.

## Session calibration

At the start/end of a session record:
- camera/device
- lens
- focal length
- aperture
- ISO
- shutter
- white balance
- light source
- polarizer state
- turntable revision
- background
- calibration target image
- capture date

## Naming

figure:
<official_sample_id>__full__front__raw.<ext>

component:
<official_sample_id>__head__front__raw.<ext>
<official_sample_id>__torso__rear__raw.<ext>
<official_sample_id>__helmet__right__raw.<ext>

derived:
<same-prefix>__normalized.png
<same-prefix>__mask.png

## Metadata

Every capture links to:
- BrickLink/Rebrickable/LEGO IDs;
- exact figure release;
- component IDs;
- whether part is known replacement/running change;
- condition/wear;
- scratches/yellowing/print loss;
- accessories included;
- source collection location.

Wear matters: a damaged old print must not teach the model that scratches are part of the official artwork.

## Capture priority queue

Prioritize figures that:
1. have no rear/side public evidence;
2. have arm/side-leg printing;
3. have dual-sided heads;
4. use complex masks/helmets;
5. have metallic/pearlescent printing;
6. are important theme/era calibration anchors;
7. have disputed catalog variants;
8. are needed for source->LEGO TranslationPairs.

## Derived assets

From user-authored captures create:
- background-removed crop;
- perspective-normalized component crop;
- edge/line map;
- color-region map;
- silhouette;
- head/torso landmarks;
- multi-view geometry fit;
- photogrammetry model if capture quality supports it.

Derived assets must retain links to every raw frame used.

## Rights

The photograph itself is user-authored. The depicted LEGO design and any licensed character artwork remain separate underlying rights. Keep raw/high-volume captures local by default and use rights/provenance policy to determine research, redistribution, and business use.
