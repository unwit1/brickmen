# Brickmen

Brickmen is the canonical repository for the user's LEGO customs and custom minifigure research, knowledge, schemas, datasets/metadata, prompts, evaluation protocols, ingestion tooling, and related automation.

## Repository role

- **Canonical home:** LEGO customs / custom minifigure knowledge and tooling.
- **Agent OS relationship:** Personal Agent OS may index, route to, and reference Brickmen, but should not retain duplicate canonical copies of Brickmen-owned knowledge after migration and audit.
- **Migration policy:** Source material is copied and verified here before source copies are removed or replaced with thin pointers.
- **Provenance:** Existing source paths and source-repository history are preserved in migration records where practical.

## Initial migration source

The initial corpus is being migrated from `unwit1/personal-agent-os`, primarily:

- `knowledge/libraries/lego-minifigure-customs/`
- LEGO/minifigure-specific utilities under `tools/knowledge/`
- LEGO-specific tests
- LEGO-specific GitHub Actions workflows and triggers

The first pass intentionally preserves source-relative paths to minimize breakage. A later refactor may simplify the dedicated-repository layout after all references and workflows have been audited.
