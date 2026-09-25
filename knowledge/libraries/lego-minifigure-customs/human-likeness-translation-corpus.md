# Human and Live-Action Likeness Translation Corpus

Research snapshot: 2026-09-24

## Purpose

Build a dedicated source-to-LEGO supervision corpus for the question:

> Which visual cues does LEGO preserve, simplify, exaggerate, move into a mould, or omit when translating a real human face or live-action performer into a standard minifigure?

This is directly relevant to:
- user-owned photographs;
- commissioned portraits;
- historical/public-domain people;
- licensed real-person figures;
- live-action characters;
- thesis experiments on identity retention under strong stylization.

Do not merge this task into generic "licensed characters." Human likeness has different failure modes:
- facial identity must survive extreme simplification;
- hair/headgear often carries more identity than face print;
- glasses/facial hair can dominate recognition;
- actor/character wardrobe cues can carry identity when facial detail is deliberately sparse;
- a new hair/headgear mould may be necessary even when the face remains simple.

## Highest-quality primary examples

### DFB – Die Mannschaft (71014), 2016

LEGO announced 16 figures: 15 named German national players plus coach Joachim Löw. LEGO's release says the minifigures were individually modelled on the national players and wear their DFB jerseys with name and number.

Supervision value:
- same uniform across many people;
- identity differences therefore depend unusually heavily on head/hair and player number/name;
- excellent controlled corpus for separating face/hair likeness from clothing identity.

Primary:
https://www.lego.com/en-us/aboutus/news/2019/november/new-lego-dfb-minifigure-series

### Women of NASA (21312), 2017

LEGO graphic designer Marie Sertillanges stated that because the figures represented real-life women, she could not make details up and every detail needed to match reality.

Subjects:
- Nancy Grace Roman
- Margaret Hamilton
- Sally Ride
- Mae Jemison

Supervision value:
- explicitly reality-constrained design brief;
- scientific/professional clothing;
- hair silhouette;
- name/role-specific details;
- strong primary-source statement about fidelity.

Primary:
https://ideas.lego.com/blogs/a4ae09b6-0d4c-4307-9da8-3ee9f3d368d6/post/543b47ec-781a-4f32-a2f6-ca605c91f48b

### Queer Eye – The Fab 5 Loft (10291), 2021

LEGO says the design team recreated the Fab Five as minifigures and specifically reports that Tan France was difficult enough that a completely new wig element was created.

Supervision value:
- direct example of identity being moved from print into a new 3D mould;
- contemporary clothing/hair/facial-hair cues;
- multiple real people rendered under one product/style profile.

Primary:
https://www.lego.com/en-fi/aboutus/news/2021/september/lego-queer-eye

### BTS Dynamite (21339), 2023

LEGO says the seven BTS members were carefully crafted; exclusive hair pieces were made for each member and torso graphics mimic their retro outfits in the music-video disco scenes.

Subjects:
RM, Jin, SUGA, j-hope, Jimin, V, Jung Kook.

Supervision value:
- source music video gives abundant high-quality source references;
- same seven subjects can be observed from many angles;
- hair mould and torso costume cues are explicitly important;
- excellent source-video -> minifigure pair family.

Primary:
https://www.lego.com/en-za/categories/adults-welcome/article/best-features-lego-dynamite-bts-set

### Over the Moon with Pharrell Williams (10391), 2024 / Piece by Piece

Official LEGO material says the set contains Pharrell Williams and Helen Lasichanh/Williams as minifigures plus 49 interchangeable heads, with more than 30 new head designs.

Supervision value:
- two direct real-person minifigure pairs;
- unusually broad official face-design diversity in one contemporary set;
- the associated LEGO-animated biopic is a potential official digital-expression reference layer.

Primary:
https://www.lego.com/en-us/categories/adults-welcome/article/how-pharrell-williams-co-designed-his-set
https://www.lego.com/static/product/over-the-moon-with-pharrell-williams-10391

## Live-action actor/character likeness families

These are not "real-person identity" labels in the same sense as DFB/NASA/BTS. They are official LEGO translations of actors portraying licensed characters and are highly useful for photo/frame-to-minifigure experiments.

### The Big Bang Theory (21302)

Seven main characters.

LEGO's graphic designer Mathew Boyle explicitly called out expression/personality cues such as:
- Sheldon's smile;
- Howard's trademark smirk;
- Bernadette's scary side.

This is unusually direct evidence that expression/personality is selected as a likeness cue rather than attempting portrait realism.

Primary:
https://ideas.lego.com/blogs/a4ae09b6-0d4c-4307-9da8-3ee9f3d368d6/post/aa9c0c91-1771-4c37-beb4-bba22d58fc3d

### Seinfeld (21328)

Official set contains Jerry, George, Kramer, Elaine and Newman in iconic 1990s outfits.

Value:
- mostly ordinary human faces/clothes;
- recognizability cannot depend on superhero masks or fantasy armour;
- good test of hair, glasses, expression and clothing cue selection.

Primary:
https://www.lego.com/en-us/aboutus/news/2021/july/lego-ideas-seinfeld

### The Office (21336)

15 named minifigures; LEGO states 12 have dual facial expressions.

Value:
- large ensemble in a consistent workplace setting;
- excellent expression-pair supervision;
- ordinary clothing and hairstyles;
- multiple similar-looking human figures force more discriminative likeness cues.

Primary:
https://www.lego.com/en-us/product/the-office-21336

### Friends: Central Perk (21319) and The Friends Apartments (10292)

Seven minifigures in each major set, with the later set explicitly tying outfits to classic episodes.

Value:
- same characters across different official releases/outfits;
- tests identity persistence while clothing changes;
- useful for separating stable face/hair identity from changeable costume.

Primary:
https://www.lego.com/product/central-perk-21319
https://www.lego.com/en-us/product/the-friends-apartments-10292

### Home Alone (21330)

Five movie minifigures:
Kevin, Kate, Harry, Marv, Old Man Marley.

Value:
- child/adult/elder distinctions;
- facial hair and hairline;
- strong movie-frame reference availability;
- normal civilian clothing.

Primary:
https://www.lego.com/en-us/product/lego-ideas-home-alone-21330

### Jaws (21350)

Three live-action character minifigures:
Martin Brody, Matt Hooper, Sam Quint.

Value:
- moustache/facial hair/hairline/glasses/costume cues;
- extremely well-known source film;
- primary LEGO page calls the heroes faithfully represented as minifigures.

Primary:
https://www.lego.com/en-us/categories/adults-welcome/article/lego-ideas-jaws-set-fun-facts

### Jurassic Park family

Example 75936 includes:
John Hammond, Ian Malcolm, Ellie Sattler, Alan Grant, Ray Arnold, Dennis Nedry.

Value:
- high-quality source film frames;
- glasses/hats/hair/facial hair;
- costume silhouettes and recognizable accessories;
- multiple releases of the same characters across years.

Primary:
https://www.lego.com/en-us/product/jurassic-park-t-rex-rampage-75936

## Pair schema extensions for humans

For each source->LEGO pair record:

- person_or_character_id
- performer_id if live-action character
- source_reference_date/scene
- approximate age category in source
- hair silhouette
- hair color role
- facial hair type
- glasses/eyewear
- brow geometry
- eye treatment
- mouth/expression
- freckles/scars/distinctive marks
- skin/head base color system
- stable identity cues
- wardrobe-dependent cues
- accessory identity cues
- new mould used?
- closest pre-existing mould alternatives
- details omitted by LEGO
- details exaggerated by LEGO
- source expression -> LEGO expression relation

Do not encode sensitive personal attributes that are unnecessary for the visual-translation task.

## Stable vs changeable identity

Train a decomposition:

### Stable-ish likeness cues
- face geometry abstraction
- hairline/hair silhouette
- glasses
- facial hair
- signature mark
- broad age-expression cues

### Appearance-specific cues
- clothing
- uniform
- jewellery
- hat
- facial expression
- props
- temporary hairstyle

For the user's own photographs, this prevents one shirt or pose from being learned as the person's identity.

## Experimental benchmark

For a held-out photograph:
1. generate official-style minifigure;
2. ask independent reviewers to match output to source among distractors;
3. score hair/headgear selection;
4. score face identity;
5. score clothing/source fidelity;
6. score official LEGO likeness;
7. compare against generic text-only generation.

Hard benchmark:
several subjects wearing near-identical clothes.

The DFB series is a natural precedent for this experimental structure because uniform cues are shared while individual likeness still has to survive.

## Source-image rights

The official LEGO minifigure is one side of the pair.

The human/photo side must independently record rights/provenance:
- official press/licensor image;
- public-domain/archive image;
- user-owned photograph;
- licensed film frame/research-only local media;
- consented/commissioned portrait.

Never infer training rights for the source photograph merely because LEGO produced a minifigure of the subject.
