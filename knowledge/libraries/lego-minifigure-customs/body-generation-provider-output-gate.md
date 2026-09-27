# Provider Output Acceptance Gate

A successful provider process is not a successful Brickmen body.

The first post-generation gate is:
- `data/body-generation-provider-output.schema.json`
- `tools/geometry/validate_body_generation_provider_output.py`

## Required component graph

Every architecture declares:
- required generated component slots;
- optional/donor-backed slots.

Provider outputs must be explicitly mapped to those slots.

The validator rejects:
- missing required slots;
- unknown slots;
- duplicate assignments;
- missing assigned files;
- files assigned that were not part of the provider run;
- failed provider execution.

It does not guess semantic part identity from arbitrary filenames.

## Example

```bash
python -m tools.geometry.validate_body_generation_provider_output \
  provider-job.json provider-run.json \
  --assign torso_shell=/tmp/result/part0.glb \
  --assign arm_l_shell=/tmp/result/part1.glb \
  ... \
  -o output-mapping.json
```

Even a complete component graph receives only:

`component_graph_complete_requires_geometry_validation`

Next gates still include:
- transform/alignment reconciliation;
- visual-envelope conformance;
- mechanical keep-out collision;
- articulation sweep;
- mesh/printability repair;
- deterministic interface insertion;
- physical validation where required.

Generated geometry remains non-production throughout this stage.
