# Brickmen Knowledge Tools

This directory contains Brickmen's canonical LEGO-customs and custom-minifigure ingestion, extraction, indexing, reference-building, dataset-preparation, and evaluation utilities.

## Repository boundary

These tools were historically developed inside `unwit1/personal-agent-os`. Brickmen now owns them. Personal Agent OS may orchestrate or invoke Brickmen workflows, but new LEGO/custom-minifigure tooling should be implemented here rather than duplicated in Agent OS.

## Data flow

source -> Brickmen extractor/indexer -> provenance-aware candidate data -> deduplication / validation -> reviewed Brickmen knowledge or local high-volume corpus

Generated high-volume image/media corpora should normally remain outside Git unless the committed artifact is a compact reviewed manifest, schema, statistic, or provenance record.

## Provenance expectations

Runs should retain, where applicable:
- upstream source and URL;
- source version/tag/commit;
- retrieval date;
- exact Brickmen tool commit;
- content hashes;
- rights/storage policy;
- processing version;
- target theme/media/product context;
- relationships to derived manifests and datasets.

See `/MIGRATION_FROM_PERSONAL_AGENT_OS.md` for migration verification and cleanup status.
