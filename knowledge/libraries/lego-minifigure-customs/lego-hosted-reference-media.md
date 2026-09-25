# LEGO-Hosted Reference Media Acquisition

Research snapshot: 2026-09-24

## Why LEGO-hosted media gets highest preference

Catalog aggregators are excellent for census and crosswalks, but when the same visual is available from LEGO itself, the LEGO-hosted occurrence is preferred for provenance.

Useful LEGO-hosted surfaces include:
- product pages and galleries;
- press/news asset packs;
- theme/character/game pages;
- designer interviews;
- building instructions;
- LEGO Kids media;
- downloadable profile icons and promotional renders.

## Building instructions

LEGO states that almost all instructions in its online archive are downloadable PDFs and that the archive covers thousands of sets, including older sets, though not every set ever made.

Known URL pattern:
https://www.lego.com/en-us/service/building-instructions/<set-number>

The set page exposes one or more direct LEGO CDN PDF links. Do not guess CDN asset IDs; discover them from the official set page and store the relationship.

Tool:
`tools/knowledge/discover_lego_instruction_references.py`

The tool:
- derives unique set numbers from physical minifigure occurrences;
- visits explicit instruction pages;
- records direct PDF URLs;
- caches pages for resumability;
- does not download PDFs.

### Why instructions are secondary visual evidence

Instruction art can show:
- minifigure assembly;
- component choice;
- occasionally cleaner simplified views of the figure;
- set-specific variant context.

But instruction illustrations are not guaranteed to expose all print surfaces and may be stylized or too small for line-width/color measurement.

Use them mainly for:
- identity verification;
- part/mould confirmation;
- missing catalog context;
- candidate image discovery.

## Press/news/game/film pages

Many LEGO news pages expose downloadable media packs or clean official images. Rather than crawl LEGO.com, maintain a curated list of source pages in the source registry and run:

`tools/knowledge/discover_lego_page_media.py`

It visits only explicit LEGO.com URLs and extracts:
- image src/srcset;
- poster images;
- OpenGraph/Twitter media;
- direct linked PNG/JPG/WebP/SVG/video/ZIP/PDF assets;
- LEGO CDN/assets links.

It never follows links recursively and never downloads bytes.

The output flows into the source-policy review and controlled image materializer.

## Source precedence

When duplicates resolve to the same image:
1. LEGO-hosted source occurrence;
2. rights-holder/developer official occurrence;
3. BrickLink/Rebrickable structured catalog occurrence;
4. other reviewed structured sources.

Keep every occurrence but choose the highest-authority source as canonical provenance.

## Asset packs

Press releases sometimes offer "Download all assets" ZIP packages.

Treat a ZIP as a SourceBundle:
- source page URL;
- bundle URL;
- retrieval timestamp;
- SHA-256;
- bundle filename;
- extracted-file manifest;
- per-file hashes;
- derived ReferenceAssets.

Do not commit large ZIPs to Git. Keep them local.

## Future instruction-PDF processing

After PDF discovery:
1. download selected PDF locally;
2. hash it;
3. render pages at fixed DPI;
4. find likely minifigure pages using visual detection rather than OCR-only heuristics;
5. crop figure/component imagery;
6. perceptual-deduplicate;
7. label source page number and set number;
8. link crops as DerivedAssets.

This should be a gap-filler; isolated product/component renders remain better training references.
