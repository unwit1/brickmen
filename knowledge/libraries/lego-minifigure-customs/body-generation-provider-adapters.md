# Body Generation Provider Registry and Adapter Strategy

Research snapshot: 2026-09-27

Brickmen now treats 3D generation systems as **providers with different roles**, not interchangeable model names.

Machine-readable registry:
- `data/body-generation-provider-registry.json`
- schema: `data/body-generation-provider-registry.schema.json`
- job compiler: `tools/geometry/compile_body_generation_provider_job.py`

## Current provider roles

### PartCrafter
Primary structured/part-aware candidate.

Upstream:
- https://github.com/wgsxm/PartCrafter
- https://arxiv.org/abs/2506.05573

Useful Brickmen properties:
- single-image input;
- simultaneous multi-part generation;
- explicit `num_parts` input;
- optional VLM-based part-count suggestion.

Brickmen should **not** delegate part count to a VLM when the selected architecture already has a component graph. The architecture component slots are the stronger constraint.

### PartPacker
Primary part-level image-to-3D candidate.

Upstream:
- https://github.com/NVlabs/PartPacker
- https://arxiv.org/abs/2506.09980

Useful as an independent part-aware generator to compare against PartCrafter.

### PAct
Articulated-generation candidate.

Upstream:
- https://github.com/Mobiuslqm/PAct

It generates part-decomposed geometry plus articulation parameters. For Brickmen this is valuable as:
- a topology proposal;
- an articulation prior;
- a comparison source.

Its learned joints still cannot replace Brickmen validated interfaces.

### Particulate
Post-generation articulation critic.

Upstream:
- https://github.com/RuiningLi/particulate

Input is a static 3D mesh; output includes inferred parts, kinematic structure and motion constraints.

Brickmen use:
- analyze generated shells;
- compare inferred topology to selected architecture;
- flag mismatches;
- preserve Brickmen mechanical truth as authoritative.

### SAM 3D Objects
Monolithic/masked reconstruction baseline.

Upstream:
- https://github.com/facebookresearch/sam-3d-objects

Useful modes:
- reconstruct a whole figure as a visual baseline;
- reconstruct masked components separately;
- compare whole-object vs part-aware pipelines.

It is not assumed to output Brickmen manufacturing component boundaries.

### UniPart / PWM-ArtGen
Research-radar candidates until runnable upstream inference is verified in the Brickmen environment.

## Adapter rule

No external model receives authority over:
- hardware dimensions;
- socket/pin tolerances;
- joint centers that are locked by architecture;
- production component boundaries;
- validated articulation limits.

Instead:

```
BodyGenerationConditioning
 -> provider job compile
 -> provider-native image / mask / part-count inputs
 -> generated visual meshes
 -> slot mapping
 -> skeleton alignment
 -> envelope checks
 -> articulation/keep-out checks
 -> deterministic interface insertion
 -> engineering validation
```

## Component slots

Architectures now declare generated component slots.

Examples:
- Giant: 7 required visual parts;
- Broad/Mid: 6 required + optional lower-body shell;
- XL: 11 required visual parts.

The part count is architecture state, not a style-model guess.

## Provider job contract

The provider-job compiler records:
- conditioning digest;
- provider role;
- required/optional slots;
- part-count hints where supported;
- pre/post steps;
- mechanical constraints;
- acceptance rules;
- authority boundaries.

It intentionally does **not** invoke the provider yet.

Execution adapters should remain thin wrappers around this contract so providers can be swapped without changing Brickmen engineering semantics.
