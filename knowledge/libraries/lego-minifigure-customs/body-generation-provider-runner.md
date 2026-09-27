# Running Body Generation Providers

Brickmen now has a **dry-run-first** local provider wrapper:

- `tools/geometry/run_body_generation_provider.py`
- schema: `data/body-generation-provider-run.schema.json`

It does not install providers or dependencies and does not accept third-party licenses.

## Supported verified CLI adapters

- PartCrafter
- PartPacker
- PAct
- Particulate

SAM 3D Objects is intentionally plan-only until a Brickmen image+mask Python-API runner is implemented. The wrapper does not invent unsupported CLI flags.

## Dry-run example

```bash
python -m tools.geometry.run_body_generation_provider \
  data/provider-jobs/brickmen-giant-official-cad-v0/partcrafter.json \
  data/body-generation-provider-registry.json \
  --provider-repo /path/to/PartCrafter \
  --source-image /path/to/reference.png \
  --output-dir /tmp/brickmen-partcrafter \
  --report /tmp/brickmen-partcrafter-plan.json
```

Dry-run validates:
- provider ID;
- verified adapter status;
- upstream entrypoint path;
- source input existence;
- architecture part-count mapping;
- staging strategy.

It does **not** launch model inference.

## Explicit execution

Add `--execute` only after the upstream provider environment is installed and its license/weights are acceptable to the operator.

```bash
... --execute --timeout-seconds 3600
```

Execution writes:
- stdout log;
- stderr log;
- discovered mesh/data output paths;
- return code;
- execution-success state.

The wrapper does not interpret a process exit code of zero as a Brickmen-valid body. Output still requires:
- component-slot resolution;
- alignment;
- envelope checks;
- keep-out/sweep checks;
- deterministic interface insertion;
- DFM;
- physical validation where mechanics matter.
