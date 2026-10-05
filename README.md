# Brickmen

Brickmen is the canonical repository for the user's LEGO customs and custom minifigure research, knowledge, schemas, datasets/metadata, prompts, evaluation protocols, ingestion tooling, and related automation.

## Repository role

- **Canonical home:** LEGO customs / custom minifigure knowledge and tooling.
- **Agent OS relationship:** Personal Agent OS may index, route to, and reference Brickmen, but should not retain duplicate canonical copies of Brickmen-owned knowledge after migration and audit.
- **Migration policy:** Source material is copied and verified here before source copies are removed or replaced with thin pointers.
- **Provenance:** Existing source paths and source-repository history are preserved in migration records where practical.

## Generate accurate minifigs and parts

Start with the [generation workflow](knowledge/libraries/lego-minifigure-customs/generation-workflow.md). It provides one reusable brief for source appearance, evidence, exact part/color choices, geometry revisions, view coverage, critical features and output requirements. The compiler produces a prompt and an unreviewed feature checklist for either ChatGPT or a local workflow. It does not run a model or certify physical accuracy.

```powershell
python tools/knowledge/compile_generation_brief.py --init minifigure --output-dir work/my-design
# Complete work/my-design/brief.json and attach the referenced files.
python tools/knowledge/compile_generation_brief.py --input work/my-design/brief.json --output-dir work/my-design/compiled
```

Use `--init part` for helmets, accessories, bricks and other standalone parts. Incomplete briefs produce a report and no prompt. Keep reference media and generated output outside Git.

Validation:

```powershell
python tools/validate_repo.py
python -m pytest tests -q
```

See the [development state](knowledge/libraries/lego-minifigure-customs/development-state.md) for tested capabilities, remaining gaps and the next development step.

## Initial migration source

The initial corpus is being migrated from `unwit1/personal-agent-os`, primarily:

- `knowledge/libraries/lego-minifigure-customs/`
- LEGO/minifigure-specific utilities under `tools/knowledge/`
- LEGO-specific tests
- LEGO-specific GitHub Actions workflows and triggers

The first pass intentionally preserves source-relative paths to minimize breakage. A later refactor may simplify the dedicated-repository layout after all references and workflows have been audited.
