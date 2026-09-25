# Sourcing, Catalogs, and Market Evidence

## Source hierarchy

A — Primary manufacturer/maker/process documentation: LEGO and a custom/accessory maker's own product/process pages. Best evidence for maker-issued name/code, claimed materials/process, release details and original/current retail price.

B — Ratified technical/community standards: LDraw specifications and similar standards.

C — Established structured catalogs and market datasets: BrickLink, Rebrickable, Brickset, HeroBloks, BrickEconomy and similar. Best for identifier crosswalks, discovery and historical structure; preserve catalog-specific naming.

D — Reseller catalogs and specialist review/archive sites: useful for availability, seller aliases, current asking price, discontinued listings and release history. Do not silently elevate reseller naming to maker identity.

E — Experienced community findings with reproducible evidence: compatibility tests, side-by-side photos, print/QC comparisons.

F — Anecdotal community claims: sightings, rumored maker aliases, factory relationships, QC reports. Useful discovery signals only until corroborated.

G — AI-generated inference/hypothesis: never promote directly to manufacturing or identity truth.

## Core official/catalog sources

LEGO Pick a Brick: current genuine elements; search by piece/set and category/color.
https://www.lego.com/en-us/pick-and-build/pick-a-brick

BrickLink: official-oriented collector marketplace/catalog for parts, minifigures, inventories, colors and price history.
https://www.bricklink.com/

Rebrickable: structured catalog/API and downloadable datasets for official sets, parts, minifigs and colors, including external IDs. Use bulk downloads for complete ingestion.
https://rebrickable.com/api/v3/docs/
https://rebrickable.com/downloads/

Brickset: useful secondary browsing across minifigure categories, years, character names and tags.
https://brickset.com/minifigs

Brickognize: photo-based candidate identification for parts, minifigs, sets and sticker sheets. Confirm before canonicalizing.
https://brickognize.com/

LDraw: open geometry ecosystem useful for part references/rendering/color mapping.
https://www.ldraw.org/

BrickLink Studio: digital assembly/decorated-minifigure preview.
https://www.bricklink.com/v3/studio/download.page

## Custom and compatible discovery

HeroBloks is a major discovery/historical catalog covering LEGO, compatible brands and commercially printed customs. Its inclusion rules do not cover every collector category, so treat it as a source, not the master ontology.
https://www.herobloks.com/

The long-tail maker/source list belongs in data/customizer-source-registry.json. Programmatically expand it from HeroBloks brand facets, maker sites, resellers and release archives while retaining source provenance.

## Price evidence

Do not store one current_price field as truth. Append PriceObservation records.

For official/catalogued LEGO items, BrickLink Past 6 Months Sales represents recorded order sales and is stronger evidence of transactions than current asking prices. Keep new/used, currency, quantity and observation time.

Current Items for Sale is asking-market evidence, not sale evidence.

BrickEconomy and similar services are model/aggregate observations. Store their methodology/source class distinctly.

Maker storefront price is original/current retail evidence for that maker at the observed time.

Reseller and marketplace listings are asking prices unless a completed-sale result is explicitly available.

## Supplier records

Record category, URL, region, genuine-vs-compatible policy per component, MOQ, unit cost, shipping, lead time, consistency, return policy and last verification.

## Cost model

donor parts + decoration + accessories + cloth + packaging + consumables + spoilage + labor + setup amortization + marketplace/payment fees + shipping materials.

## Provenance

Record genuine/compatible/unknown status per component. A hybrid figure can contain genuine body parts, third-party helmet, custom cloth and custom weapon simultaneously.

Cache catalog IDs, listing IDs and acquisition/observation date. Price, availability, maker status and release status are time-sensitive observations, not permanent facts.

Agent OS should normalize identifiers, preserve source/timestamp and keep historical observations so sourcing recommendations can explain changes.
