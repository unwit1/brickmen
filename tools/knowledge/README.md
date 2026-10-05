# Brickmen Knowledge Tools

This directory contains Brickmen's canonical LEGO-customs and custom-minifigure ingestion, extraction, indexing, reference-building, dataset-preparation, and evaluation utilities.

## Repository boundary

These tools were historically developed inside `unwit1/personal-agent-os`. Brickmen now owns them. Personal Agent OS may orchestrate or invoke Brickmen workflows, but new LEGO/custom-minifigure tooling should be implemented here rather than duplicated in Agent OS.

## Data flow

source -> Brickmen extractor/indexer -> provenance-aware candidate data -> deduplication / validation -> reviewed Brickmen knowledge or local high-volume corpus

Generated high-volume image/media corpora should normally remain outside Git unless the committed artifact is a compact reviewed manifest, schema, statistic, or provenance record.

## Accuracy workflow entry points

Use [generation-workflow.md](../../knowledge/libraries/lego-minifigure-customs/generation-workflow.md) for complete commands and input expectations.

| Tool | Responsibility |
| --- | --- |
| `compile_generation_brief.py` | Scaffold and validate one shared generation packet; create a deterministic prompt, contract requirements and feature checklist. |
| `build_minifigure_reference_sets.py` | Rank evidence, preserve source occurrences/conflicts, deduplicate within roles, and report missing minifigure or part views. |
| `build_minifigure_training_splits.py` | Join identity groups and confirmed duplicate relationships before assigning train/validation/test splits. |
| `render_ldraw_pattern_training_views.py` | Produce local LDView part views pinned to source hash, declared library revision and renderer configuration. |
| `inventory_training_source_tree.py` | Inventory a reviewed local source tree for the bulk-ingestion workflow, preserving paths/hashes without copying assets. |
| `../validate_repo.py` | Check syntax, JSON, backlog references and workflow tool availability without loading models. |

The generation compiler reuses `data/chatgpt-control-generation-schema.json` and `data/ai-output-contracts.json`; do not introduce a separate provider prompt schema. Run metadata such as seed/model revision belongs to the actual generation record. Unexposed values remain unavailable.

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
