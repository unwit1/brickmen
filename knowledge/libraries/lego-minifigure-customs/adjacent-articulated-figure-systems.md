# Adjacent Articulated Figure Systems as Brickmen Engineering References

Research snapshot: 2026-09-27

## Purpose

Brickmen's target remains LEGO-compatible/custom minifigure ecosystems.

However, adjacent brick/action-figure systems solve useful problems:
- high articulation at tiny scales;
- replaceable armor;
- pose-holding joints;
- modular limb construction;
- standard connection points;
- style transfer onto articulated anatomy.

Treat these as **engineering/style references**, not automatically compatible FigureArchitectures.

## MEGA / Mega Construx micro action figures

Mattel currently describes Halo Mega Construx figures as:
- micro action figures;
- 12 points of articulation;
- detachable/swappable armor;
- building pieces compatible with other name brands.

Independent figure reviews place many of the modern figures at about **2 inches / ~51 mm** and describe a highly articulated graph including:
- ball-jointed head;
- shoulder articulation;
- elbow articulation;
- rotating wrists;
- waist;
- ball-jointed hips;
- hinged knees.

Older/newer line revisions differ, so do not infer one universal joint implementation across every Mega release.

### Brickmen lessons

1. **High articulation is possible near minifigure-adjacent scale.**
2. Anatomy and articulation can be layered:
   ```
   joint skeleton
    -> body component
    -> removable armor / visual shell
   ```
3. A figure can use many articulation points without abandoning building-system accessories.
4. Removable armor is an excellent precedent for Brickmen shell overlays.
5. 2-inch scale is a strong design reference for `Brickmen Mid` even though its exact connectors should remain original.

### Research targets

Acquire one modern Mega micro action figure and document:
- shoulder joint;
- elbow link;
- wrist;
- waist;
- hip;
- knee;
- armor mount;
- hand/accessory grip;
- foot/building-system interface.

Use it as a mechanical reference only.

Sources:
- Mattel Hyperius product, 12 points: https://service.mattel.com/us/productPopup.aspx?prodno=GYG46&siteid=27
- Mattel TMNT collector figure, hyper-poseable: https://m.service.mattel.com/us/Technical/productDetail?prodno=DMW23&siteid=27
- Mega Construx MOTU articulation review: https://www.actionfigurebarbecue.com/2019/02/minifigure-review-man-at-arms-from.html

## Kre-O / Kreon articulation

Historical Kre-O Micro-Changer figures used limited ball-joint-like shoulder and hip articulation beyond standard LEGO minifigure motion.

Brickmen lesson:
a building-block-compatible humanoid can improve the standard shoulder/hip range without moving to a much larger action-figure scale.

Treat as historical design-space evidence, not a candidate compatible connector standard.

Source:
https://thefwoosh.com/2013/04/hasbro-kre-o-transformers-micro-changers-combiners-constructicon-devastator-set/

## Minimates

Minimates are not a LEGO-compatible building figure architecture, but small figures demonstrate a different way to distribute articulation.

TMNT Minimates reviews report:
- ball neck;
- ball shoulders;
- hinged elbows;
- rotating wrists;
- rotating waist;
- ball hips;
- hinged knees;
- rotating ankles.

Brickmen lesson:
joint primitive choice can vary by body region. A good figure does **not** require the same joint type everywhere.

Source:
https://tmnttoys.com/15figures/minimatesmirage/review.html

## Official/custom skeleton ball-joint precedent

LEGO skeleton variants historically used ball-jointed arm configurations, and current custom makers are now adapting ball-joint arms to ordinary humanoid minifigure-scale torsos.

This is especially relevant to Brickmen Standard-Articulated:
- articulation can be upgraded on one subassembly;
- the rest of the body can retain standard geometry.

## What to learn versus what not to copy

Learn:
- articulation graph;
- body/armor layering;
- range-of-motion strategy;
- joint scale selection;
- use of hinge vs ball vs swivel;
- removable wear components;
- silhouette preservation around joints.

Do not automatically copy:
- proprietary exact connector geometry;
- dimensions;
- surface sculpt;
- protected character-specific assets.

Brickmen's output should use original parametric joints validated against its own requirements.

## Architecture research relationship

AdjacentReferenceSystem is not FigureArchitecture.

Store:
```
AdjacentReferenceSystem
  -> MECHANICAL_PRECEDENT_FOR -> JointPrimitive
  -> STYLE_PRECEDENT_FOR -> BodyStyleProfile
  -> SCALE_REFERENCE_FOR -> BrickmenBodyFamily
```

This prevents recognition from classifying a Mega Construx figure as a LEGO-compatible Brickmen body while still letting the generator learn useful articulation design.
