# LEGO Pick a Brick and Official Customization Ingestion

Research snapshot: 2026-09-24

## Current official systems

### Pick a Brick

The US Minifigure Parts filter currently exposes 778 results, of which 751 are standard
LEGO-system items. The Minifigure Accessories category exposes 565 results; parts plus
accessories show 1,343 results overall.

This is a **current availability catalog**, not the all-time minifigure corpus.

It is useful for:
- current official element/design IDs;
- official product images;
- existing mould/headgear/accessory vocabulary;
- current colors;
- purist design candidates;
- validation that a proposed custom part can be replaced by an existing official element.

### Create a Minifigure

LEGO describes this as a pre-printed-part combinatorial experience built from hundreds of
Pick a Brick elements. It is the correct official control for:

"How closely can this person/character be represented without custom printing or new geometry?"

Store that result separately from a printed/custom result.

### Minifigure Factory

LEGO distinguishes Minifigure Factory from Create a Minifigure: Factory permits custom torso
graphics/text/symbols while the rest of the figure is assembled from offered official components.

Useful supervision:
- official customization region = torso;
- screen-to-print color is not guaranteed exact;
- LEGO explicitly advises contrast for text readability;
- user-defined graphics can be combined with official heads/hair/legs/accessories.

## Programmatic snapshot

Current community tooling documents LEGO's Pick a Brick web application as:

POST https://www.lego.com/api/graphql/PickABrickQuery

As of 2026-06-24, working requests require:
- Origin: https://www.lego.com
- x-locale: en-US (or target locale)
- Referer: the matching Pick a Brick page
- User-Agent

The GraphQL operation no longer accepts the old unused $sku declaration; quantityInSet should
use sku:null when no set is being queried.

Adapter:
tools/knowledge/snapshot_lego_pick_a_brick.py

The adapter intentionally snapshots the full PAB element space, then relies on canonical
element/design ID crosswalks for minifigure classification. This is more robust than guessing
from English names alone.

## Multi-region value

A maintained June-2026 implementation reports successful PAB queries for numerous locales
including US, GB, AU, CA, DE, FR, NL, KR, PL, SE, NZ, CZ, DK, FI, NO, ES, IT and PT.

A future multi-region run should store:
- element availability by locale;
- price by locale/currency;
- stock/channel changes;
- identical design IDs in different element colors;
- regional differences.

Those market fields are useful collection/business metadata but should not change official
visual-style supervision.
