# Provider Environment and Revision Preflight

Brickmen pins the upstream revisions used to verify each runnable body-provider adapter.

Environment checker:
- `tools/geometry/check_body_provider_environment.py`
- schema: `data/body-provider-environment-check.schema.json`

## Checks

Without loading model weights, it verifies:
- local provider checkout exists;
- local Git HEAD exactly matches the Brickmen-verified upstream commit;
- verified interface files exist;
- known runtime files/checkpoints exist where required;
- expected Python modules are discoverable;
- NVIDIA GPUs are visible when CUDA is required;
- documented VRAM floors are satisfied when upstream provides one.

Known documented floors currently recorded:
- PartCrafter: 8 GB;
- PartPacker: approximately 10 GB for the documented float16 inference path;
- SAM 3D Objects: 32 GB.

Brickmen intentionally records PAct and Particulate VRAM minimum as **not verified**, rather than inventing one.

## Version policy

An upstream revision mismatch is a preflight blocker.

That does not mean a newer revision is bad. It means the Brickmen adapter has not yet been re-verified against that changed code.

The expected workflow is:
1. inspect upstream changes;
2. rerun interface/output contract tests;
3. update the pinned commit;
4. only then treat the new revision as verified.

## Scope

`ready_to_attempt_inference: true` means the local environment satisfies the known verified interface prerequisites.

It does not mean:
- the model will fit every requested workload;
- generation will succeed;
- output geometry will pass Brickmen validation;
- licensing is suitable for every use;
- generated geometry is production approved.
