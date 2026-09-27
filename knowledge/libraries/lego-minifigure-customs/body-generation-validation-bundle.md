# Generated Body Validation Bundle

Brickmen now has one orchestration command for already-generated component meshes:

- `tools/geometry/run_body_generation_validation_bundle.py`

It runs the validation layers in a consistent order and writes a resumable artifact bundle.

## Inputs

Required:
- BodyGenerationConditioning JSON;
- provider-output component mapping JSON;
- output directory.

Optional:
- articulation sweeps;
- structural-guide manifest;
- provider job;
- provider run;
- joint-contact regions.

## Outputs

- `geometry-validation.json`
- `mesh-quality.json`
- `exact-keepout-validation.json`
- `pose-collision-validation.json`
- `continuous-collision-validation.json`
- `pipeline-state.json`
- `bundle-manifest.json`

## Two different success concepts

`generated_geometry_validation_passed`

means the current generated mesh bundle passed:
- coarse visual-envelope geometry;
- topology preflight;
- exact fixed keep-outs;
- sampled pose collisions;
- conservative continuous rotation collision proof.

It does **not** mean production ready.

`pipeline_production_ready`

also considers the broader state machine, including physical/mechanical interface validation.

For the current Giant shoulder work, a visually and collision-valid generated shell can still remain blocked because the 43093 interface is reference-only pending physical validation.

## Example

```bash
python -m tools.geometry.run_body_generation_validation_bundle \
  data/generation-conditioning/brickmen-giant-official-cad-v0.json \
  /tmp/output-mapping.json \
  /tmp/giant-validation \
  --sweeps data/articulation-sweeps/brickmen-giant-official-cad-v0.json \
  --contact-regions data/joint-contact-regions/brickmen-giant-v0.json
```

A nonzero exit code means one or more generated-geometry validation gates did not pass. The artifact bundle remains available for diagnosis.
