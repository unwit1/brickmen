# Joint Engineering for Printable Figure Architectures

Research snapshot: 2026-09-27

## Purpose

Define a reusable engineering layer for articulated Brickmen bodies.

A FigureArchitecture describes **where** joints exist and how components are connected. A JointProfile describes **how one physical joint is manufactured, assembled, retained, moved, worn and validated**.

The visual body shell is never allowed to invent its own production joint.

## Core principle

Separate:

```
visual shell
joint housing
wear element / joint primitive
connector interface
```

where practical.

This permits:
- reprinting a shell without changing the joint;
- replacing a worn insert;
- using a tough/FDM/thermoplastic joint inside a fine resin shell;
- using commodity LEGO/Technic hardware when it is superior;
- moving from resin prototyping to molded production without redesigning the character sculpt.

## Why no universal joint clearance exists

Ball/socket and snap joints depend on:
- ball/pin size;
- socket wall thickness;
- socket opening/undercut;
- material modulus/elongation/creep;
- surface finish/friction;
- printer/process;
- print orientation;
- cure;
- temperature;
- load arm and expected torque.

Stratasys' PolyJet DfAM guidance explicitly treats ball size, socket wall, material and orientation as variables and recommends a compliant C-shaped socket for snap-fit ball joints.

Protolabs Network likewise treats snap fits as process/material-specific.

Therefore Brickmen stores empirically validated JointProfiles rather than values copied from an online tutorial.

## Joint primitive library

### J1 — rotational friction pin

One cylindrical pin rotates in a bore.

Uses:
- simple shoulder;
- hip;
- giant arm;
- accessory hinge.

Parameters:
- pin diameter/length;
- bore;
- lead-in;
- axial retention;
- bearing length;
- surface finish;
- process compensation.

Measure:
- insertion/removal;
- breakaway torque;
- running torque;
- radial play;
- axial play;
- torque after cycles.

### J2 — captured/shouldered pin

Rotational pin with geometry that prevents axial withdrawal.

Useful when:
- component should rotate but not detach during ordinary posing.

Variants:
- molded head;
- snap barb;
- separate cap;
- commodity axle/pin.

### J3 — snap-fit ball and C-socket

Ball gives multiple rotational degrees of freedom.

Engineering requirements:
- socket opening narrower than ball retention envelope;
- compliant/open/C-shaped socket or relief segments;
- adequate root fillets;
- material with sufficient elastic recovery;
- orientation chosen so socket spreading does not split weak print layers.

Do not print a brittle closed resin socket and force a ball into it.

Candidate uses:
- shoulder;
- neck;
- hip on larger Brickmen XL/Mega bodies.

### J4 — ball plus replaceable socket insert

Preferred Brickmen option where scale permits.

```
resin sculpt shell
 -> insert pocket
 -> tough/FDM/molded socket insert
 -> ball/stem on mating component
```

Benefits:
- wear part is replaceable;
- resin shell can prioritize visual detail;
- joint can use nylon/PETG/POM-like or molded material;
- insert dimensions can be calibrated separately.

### J5 — ball-stud / adapter pin shoulder

Relevant to standard-scale custom ball-jointed arms.

Concept:
- adapter/pin fits standard torso shoulder opening;
- ball or articulated interface sits outside/partially within torso;
- custom arm socket attaches to the adapter.

Current custom products demonstrate the feasibility of a pin-in-torso ball-joint concept, but their exact geometry must be measured rather than copied.

Potential Brickmen use:
`brickmen_standard_articulated_shoulder_v1`.

### J6 — hinge/pin elbow

Single-axis elbow:
- fork + pin;
- captured pin;
- hidden pin;
- snap pin.

Better than tiny ball/socket where the limb is too narrow.

### J7 — wrist friction peg

For small hands, a simple rotational peg may be more robust than a tiny ball.

Use:
- standard-like hands;
- XL hands where rotation is required but wrist tilt is optional.

### J8 — C-clip / bar articulation

Useful only where size/material makes repeated clip flex safe.

Connect to the existing 3.18-family connector validation rather than inventing another bar standard.

### J9 — detented rotational joint

Add discrete stable poses to prevent creep/sag.

Potential uses:
- large hips;
- heavy shoulders;
- knees on Mega-scale bodies.

Parameters:
- detent count;
- tooth/lobe geometry;
- preload;
- torque peaks;
- wear.

### J10 — commodity-hardware hybrid

Use existing standardized hardware inside a custom shell.

Candidates:
- LEGO/compatible Technic pin/axle where architecture permits;
- polymer pin;
- metal pin/rod for display-oriented systems where explicitly designed;
- molded joint insert.

Official LEGO Giant use of reusable shoulder hardware is a valuable architectural precedent.

## Joint choice by scale

Do not scale one joint uniformly.

### Standard (~minifigure)
Prefer:
- standard LEGO interfaces;
- small friction pin/peg;
- tested ball-pin shoulder adapter;
- existing hand/bar system.

Very small printed ball sockets may be mechanically marginal.

### Mid
Possible:
- pin shoulder;
- small ball shoulder if material permits;
- pin elbow;
- peg wrist.

### XL ~65-75 mm
Strong candidate for:
- ball shoulder;
- pin/ball elbow depending silhouette;
- rotational wrist;
- articulated hips.

### Mega >100 mm
Joint loads increase because limbs are longer/heavier.

Need:
- higher torque capacity;
- replaceable inserts;
- detents or stronger friction strategy;
- possibly commodity/mechanical hardware.

Large scale does not make the problem easier automatically.

## Joint style versus joint engineering

A figure can visually imitate the *poseability language* of another system while using a different internal joint.

Example:
"Alpha-like articulated muscular silhouette" may imply visible elbow separation and greater shoulder range.

Brickmen can achieve that with an original:
- replaceable ball shoulder;
- pin elbow;
- rotating wrist;
without copying Alpha's actual connector geometry.

## Parametric JointProfile

Every validated joint includes:

- joint_profile_id;
- primitive_type;
- revision;
- parent/child component roles;
- degrees of freedom;
- axes;
- motion range;
- male/female geometry;
- nominal dimensions;
- process compensation;
- material pair;
- shell interface;
- insertion/removal force targets;
- breakaway/running torque targets;
- axial/radial play limits;
- cycle target;
- creep/load test;
- approved orientations;
- failure modes;
- physical evidence;
- manufacturing status.

## Torque matters as much as fit

For articulated bodies, "fits" is insufficient.

Measure:
- peak assembly force;
- separation force;
- initial breakaway torque;
- running torque;
- torque after 10/100/500/etc. cycles;
- static sag under known moment;
- permanent deformation;
- play/backlash.

For a limb:
```
required_joint_torque >
limb_mass * gravity * center_of_mass_distance * safety_factor
```

The real torque target should be learned from the physical body and desired poseability.

## Instrumented joint test fixture

Extend the existing force-test station.

Modules:
- linear insertion axis;
- rotary motor/encoder;
- torque sensor or force gauge at known lever arm;
- component fixture;
- camera;
- cycle controller.

Tests:
1. assemble;
2. measure insertion;
3. zero;
4. sweep joint through permitted range;
5. record torque-angle curve;
6. dwell at loaded pose;
7. repeat cycles;
8. remeasure;
9. inspect cracks/whitening/wear;
10. classify.

Store raw force/torque curves.

## Ball/socket calibration matrix

For each selected material/process:

Sweep:
- ball diameter;
- socket sphere diameter;
- socket throat/opening;
- wall thickness;
- relief slit number/width;
- root fillet;
- socket depth;
- orientation.

Responses:
- assembly force;
- cracking;
- retention;
- breakaway torque;
- range;
- play;
- cycles;
- creep/sag.

No selected production value until a physical matrix is run.

## Resin-specific policy

Resin is excellent for shells but not automatically ideal for wear surfaces.

Evaluate:
- tough miniature resin;
- engineering tough resin;
- flexible/tough blend;
- replaceable non-resin insert.

Failure modes:
- socket cracking on insertion;
- stem fracture;
- brittle wear debris;
- creep/loosening;
- cure-dependent fit;
- surface polishing changing torque.

Joint qualification must use the same cure/process as production.

## FDM/thermoplastic insert policy

FDM can be strategically useful inside resin bodies even where it is visually inferior.

Candidate insert materials:
- PETG;
- nylon;
- other validated engineering thermoplastics.

Advantages:
- tougher snap behavior;
- replaceable inexpensive wear part;
- geometry can be printed independently of cosmetic shell.

Small-nozzle precision still requires calibration.

## Injection-molding migration

Design joint housings with future molding in mind:
- draft/parting feasibility;
- avoid impossible undercuts or make insert separable;
- allow replaceable molded joint cartridges;
- preserve visual shell interface.

Ball/socket snaps rely on material elastic recovery; the production thermoplastic may permit a different socket design than resin.

Store:
`prototype_joint_profile -> production_joint_profile`
as a relationship rather than assuming identical CAD.

## Recognition implications

When recognizing a custom body, joint cues are first-class features:
- visible shoulder ball;
- adapter pin;
- elbow seam;
- wrist seam;
- pinned shoulder;
- ball hip;
- detented hinge;
- fixed arm.

The recognizer can classify architecture even when surface styling is misleading.

## Roadmap

1. establish standard minifigure torque/rotation baselines;
2. measure official LEGO Giant shoulder/hand joints;
3. measure one commercial custom ball-joint arm figure;
4. measure Alpha AF shoulder/elbow/wrist;
5. build Brickmen joint coupon generator;
6. qualify pin and ball/socket primitive families;
7. prototype Brickmen Mid;
8. prototype replaceable-joint Brickmen XL;
9. use physical results to train joint-risk/selection model.

## Sources

- Stratasys PolyJet DfAM guide: https://support.stratasys.com/SupportCenter/HTML5UserGuides/Design_DFAM_Guide_July_2020/Responsive%20HTML5/DOC-01103_x_Design-PJ-AM-Guide-HTML/DfAM_Guide-Chapter/DfAM_Guide-Chapter.htm
- Protolabs Network snap-fit guide: https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/
- Shapeways historical ball-joint guide (process-specific historical reference): https://www.shapeways.com/blog/how-to-design-snap-fit-ball-joints-for-3d-printing-with-shapeways
- AmericanBricks Wookiee ball-joint arms: https://americanbrickstore.com/wookiee-warrior-kashyyyk-minifigures-assorted-colors/
- Republic Customs Helldivers ball-joint arms: https://americanbrickstore.com/helldivers-b-01-tactical-minifigures-ball-joint-arms/
- AmericanBricks TCS assembly note: https://hpbrickedup.com/products/tcs-anakin-skywalker-and-obi-wan-kenobi
