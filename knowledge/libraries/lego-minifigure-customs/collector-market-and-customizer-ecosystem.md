# Collector Market and Customizer Ecosystem

Research snapshot: 2026-09-24

This layer extends the manufacturing library into collection intelligence: who made a figure, which exact character appearance it represents, how it differs from other releases, what components it contains, what it cost at a point in time, where it was sold, and how reliable each identification is.

## Canonical hierarchy

Character -> Incarnation/Continuity -> SourceAppearance -> Outfit/Design -> FigureRelease -> ComponentRelease -> MarketObservation

This prevents common failures such as treating every Batman as one design, conflating a movie costume with a comic costume, or merging two releases because resellers reused the same character name.

A SourceAppearance can point to an exact comic issue/panel, film/TV episode or frame, game skin/model, animation episode, concept art, promotional image, toy/statue, trading card, packaging art, official merchandise or other documented reference. Fan art may be recorded only as fan-art provenance and must never be silently promoted to canonical source material.

## Market layers

| Layer | Examples | Main use |
|---|---|---|
| Official LEGO/catalog | LEGO, BrickLink, Rebrickable, Brickset | official IDs, inventories, colors, variants, donor parts |
| Premium custom printers | Citizen Brick, FireStar, Brickmania, United Bricks, Minifigs4u, Orbital, ChipChipCustom, Grandpa Clone Customs and similar makers | direct-print releases, small runs, edition behavior, genuine-part claims |
| Hybrid custom/accessory makers | BrickTactical, Clone Army Customs, AV Figures, BigKidBrix, EclipseGRAFX, Jonak Toys, Calypso Customs and similar | figures plus helmets, weapons, cloth, decals, molded/resin upgrade parts |
| Compatible mass-market brands | WM, XINH, Koruit, KDL, Kopf, POGO, G-family codes, Decool, Bela, SY and many others | low-cost releases, brand/product codes, alternate molds and broad character coverage |
| Accessory specialists | BrickArms, BrickWarriors, BrickForge, CapeMadness and maker-specific accessory lines | weapons, armor, gear, cloth and modular body parts |
| Aggregators/catalogs | HeroBloks, BrickEconomy, BrickPicker/BrickScan, BrickFigures, Brick4 | discovery, alias resolution, historical records, values/market estimates or image identification |
| Resellers | Brixtoy and many regional custom/compatible sellers | current availability, aliases, reseller SKUs, price observations |
| Community/review | CustomMinifig.co.uk, Eurobricks, Reddit, collector groups and maker social feeds | release discovery, historical context, QC/compatibility observations |

HeroBloks should be ingested as an important discovery and historical catalog, not treated as the canonical naming authority. Its own scope includes LEGO, compatible brands and commercially printed customs, while excluding some categories such as decals and many generic figures. Agent OS therefore needs broader inputs.

## Representative current observations

Current market examples show why price and production class must be separate fields. Citizen Brick listings commonly show individual figures around the mid-$20 to mid-$30 range, with larger/special products higher. FireStar currently lists custom designs around the high teens to upper £20s and explicitly states its custom-printed figures use genuine LEGO. Jonak currently lists many UV printed clone figures around the mid-teens to low $20s. Grandpa Clone Customs currently distinguishes official-helmet and replica-helmet configurations in its product names and prices. These are observations, not permanent price tiers.

Mass-market compatible releases can be dramatically cheaper than premium customs and may be resold under different names or codes. Do not infer manufacturer from price, seller title or packaging photo alone.

## Release identity

FigureRelease should capture maker, brand, collaboration partners, maker product code, title, normalized character, source appearance, year/wave, announced/released dates, edition size, numbered status, exclusive/collaboration status, preorder/restock status, substrate provenance and included components.

Collaboration is many-to-many. Examples such as maker x printer x retailer should not be flattened into one fake manufacturer.

Maker records need aliases, country/region when documented, direct storefront/social channels, first/last observed dates, active/inactive/unknown status, production-method claims and product-code patterns.

## Component-level collection

The smallest useful collector record is often a component rather than a complete figure. Track heads, torsos, arms, hands, hips, legs, headgear, hair, helmets, armor, neck/bodywear, cloth, weapons, tools, props, stands and packaging extras separately.

This allows Agent OS to answer which release has the best helmet but weakest body, whether a premium custom can be upgraded with a third-party cloth set, whether an accessory is available independently, whether two figures share the same custom mold, whether a compatible body can accept official hands/headgear, and which donor/accessory combination is cheapest without losing the desired look.

## Quality observations

Quality is multidimensional and source-specific. Store observations for print registration, opacity, line/detail resolution, surface texture/raised ink, color match, rub/scratch resistance, clutch, joint tension, mold seams, flash, brittleness, fit, accessory grip, cloth fraying, completeness, packaging and defect/replacement response.

Do not convert one review into a permanent maker score. Quality can change by factory, mold generation, production batch and release year. Keep observation date, product/batch and source.

## Price intelligence

PriceObservation fields should include amount, currency, observation_type, source/listing, seller, region, timestamp, condition, completeness, quantity/lot size, included accessories, edition size, stock status and whether shipping/tax are included.

Observation types: MSRP/original retail; current retail; sale price; current asking price; completed sale; auction result; marketplace aggregate; model/estimate.

BrickLink past-six-month sales are transaction-grounded for catalogued LEGO items and should be kept distinct from current listings. Market-model sites such as BrickEconomy are useful secondary estimates but must be tagged model/aggregate rather than sold comp.

Never overwrite price history. Append observations so Agent OS can produce time series, detect restocks and distinguish scarcity from reseller markup.

## Accessory ecosystem

Normalize accessories by function and attachment: weapon/firearm, melee, shield, tool, musical, food/household, sci-fi/fantasy prop, backpack, pouch, belt/holster, armor, helmet/headgear, hair, neckwear, shoulder gear, cape/coat/kama/skirt, wings, tail/creature part, limb/body replacement, display/base and packaging extra.

Record attachment interface such as hand bar, head stud, neck post, torso/waist sandwich, clip, peg or custom modular interface and store compatibility observations rather than assuming universal fit.

## Collection intelligence

Connect Bootlego MASTER and franchise trackers to canonical Character and SourceAppearance records. A collection gap is then calculable, not manually inferred:

canonical roster -> known releases -> owned releases -> wanted releases -> missing appearance/variant -> available accessory/customization path -> design backlog.

The same system can flag duplicate purchases, near-duplicate costumes, superior later releases, figures worth harvesting for components, and variants that do not exist commercially and should move to custom design.

## Monitoring cadence

High-change sources such as maker storefronts, social release announcements and reseller catalogs can be observed daily/weekly. Structured official catalogs can update on a slower schedule. Historical archives and community posts should be ingested opportunistically with source date and confidence.

A source disappearing is itself evidence: retain cached metadata, source URL, first/last seen and archive references so discontinued makers and figures remain searchable.
