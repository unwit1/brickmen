# Anonymous Provider Part Mapping Proposals

PartCrafter and PartPacker can return useful part-separated geometry without Brickmen semantic names.

Brickmen now proposes mappings without trusting provider output order:

- `data/body-provider-output-mapping-proposal.schema.json`
- `tools/geometry/propose_body_provider_output_mapping.py`

## Global registration first

The mapper does not independently scale every part.

It:
1. inspects all provider component AABBs;
2. builds one provider-union AABB;
3. builds the union of expected Brickmen component-slot visual targets;
4. searches orientation-preserving axis permutations/signs;
5. solves one uniform scale + translation for the entire part bundle;
6. transforms every provider part with that shared transform.

This preserves the provider's assembly proportions and relative placement.

## Semantic assignment second

For each global registration, Brickmen computes a cost for every part/slot pair using:
- size/shape log error;
- normalized center distance;
- AABB overlap.

A bitmask dynamic-programming assignment then finds the minimum-cost one-to-one mapping.

This supports:
- more provider parts than required slots: extras remain unassigned;
- fewer provider parts than slots: missing slots remain explicit;
- anonymous names such as `part_00.glb`;
- provider order unrelated to Brickmen semantics.

## Ambiguity stays visible

Symmetric figures often allow multiple equally plausible registrations:
- left/right exchange;
- 180° front/back rotations;
- similarly shaped hands or arms.

The tool ranks candidates and records:
- near-best count;
- distinct near-best semantic mappings;
- best/second score margin;
- sign/orientation ambiguity.

Automatic promotion is deliberately strict.

The normal workflow is:
1. generate mapping proposal;
2. compare best candidates with structural guides/source evidence;
3. explicitly promote one reviewed mapping;
4. run the full validation bundle.

## Critic boundary

Post-generation critics such as Particulate are rejected by this mapper. Their outputs are auxiliary articulation evidence, not anonymous primary body parts.
