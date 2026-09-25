# Migration from Personal Agent OS

Brickmen is the canonical home for the user's LEGO customs and custom-minifigure research, knowledge, schemas, datasets/metadata, prompts, evaluation protocols, ingestion tooling, and related automation.

Source repository: `unwit1/personal-agent-os`

## Policy

1. Copy or otherwise materialize Brickmen-owned content in this repository.
2. Verify the destination against the source before source cleanup. For text files, matching Git blob SHAs are treated as byte-for-byte verification.
3. Audit source-side references before deleting a source path.
4. Keep Personal Agent OS integration pointers and routing metadata, but do not keep duplicate canonical LEGO/custom-minifigure knowledge there.
5. Future LEGO/custom-minifigure ingestion should target Brickmen first.
6. Preserve provenance back to the original source repository/path and relevant upstream sources.

## Verified migration state — 2026-09-25

The following sampled files have matching Git blob SHAs between `unwit1/personal-agent-os` and `unwit1/brickmen`:

### Knowledge
- `knowledge/libraries/lego-minifigure-customs/README.md`
- `knowledge/libraries/lego-minifigure-customs/ai-generation-accuracy.md`
- `knowledge/libraries/lego-minifigure-customs/chatgpt-image-control-group.md`
- `knowledge/libraries/lego-minifigure-customs/knowledge-ontology.md`
- `knowledge/libraries/lego-minifigure-customs/master-training-data-taxonomy.md`
- `knowledge/libraries/lego-minifigure-customs/research-backlog.md`
- `knowledge/libraries/lego-minifigure-customs/data/customizer-source-registry.json`
- `knowledge/libraries/lego-minifigure-customs/data/training-data-source-registry.json`

### Tooling
- `tools/knowledge/ingest_lego_minifigure_references.py`
- `tools/knowledge/materialize_lego_reference_images.py`
- `tools/knowledge/build_fortnite_lego_translation_pairs.py`
- `tools/knowledge/build_minifigure_reference_sets.py`
- `tools/knowledge/discover_flashpoint_lego_webgames.py`
- `tools/knowledge/discover_lego_instruction_references.py`
- `tools/knowledge/discover_lego_page_media.py`
- `tools/knowledge/enrich_bricklink_minifigure_references.py`
- `tools/knowledge/extract_lego_film_reference_frames.py`
- `tools/knowledge/index_ldraw_minifig_patterns.py`

The Brickmen commit history also contains the dedicated knowledge-corpus migration and subsequent LEGO tool migrations. This file records verification performed after those copies.

## Cleanup status

Personal Agent OS already documents that LEGO/custom-minifigure tooling is canonical in Brickmen and should route such jobs here. Source deletion remains staged until reference audits show that deleting a path will not leave broken Agent OS-local references.

During cleanup, prefer replacing Agent OS's old LEGO library with a thin integration pointer rather than preserving a second canonical copy.

## Remaining audit

- Verify the rest of `knowledge/libraries/lego-minifigure-customs/` against Brickmen.
- Verify remaining LEGO/minifigure-specific scripts, tests, workflows, schemas, and trigger files.
- Find and migrate any LEGO-custom-specific material outside the obvious library/tool paths.
- Audit internal references in Personal Agent OS and retarget them to Brickmen or remove obsolete references.
- Remove verified duplicate source files in logical batches.
- Leave a stable Agent OS routing/integration document after cleanup.


## Source cleanup completed — 2026-09-25

The following verified duplicates were removed from `unwit1/personal-agent-os` after reference checks:

- `tools/knowledge/index_rioforce_lego_textures.py`
- `tools/knowledge/render_ldraw_pattern_training_views.py`
- `tools/knowledge/ingest_rebrickable_minifig_corpus.py`
- `tests/test_ingest_rebrickable_minifig_corpus.py`

The paired Rebrickable test and implementation were removed together so Agent OS would not retain a failing test that referenced a migrated script.


Additional completed migration/cleanup:
- `tools/knowledge/build_fortnite_lego_translation_pairs.py` removed from Agent OS after verification.
- `tools/knowledge/profile_training_source_webpage.py` migrated into Brickmen, then removed from Agent OS.
- `tools/knowledge/snapshot_huggingface_dataset.py` migrated into Brickmen, then removed from Agent OS.
- `.github/lego-census-trigger` removed from Agent OS after verifying the identical Brickmen copy.

The two generically named training-source tools were classified as Brickmen-owned because their implementation is explicitly LEGO-research scoped and no non-LEGO Agent OS references were found.
