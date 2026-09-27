# Continue an Executed Body Generator Run

Brickmen now has an orchestration command for the post-inference half of a generator workflow:

- `tools/geometry/continue_body_generator_run.py`

It does not launch the external GPU provider.

## First pass: stop at review

Given:
- conditioning;
- provider job;
- executed provider-run report;
- workspace;

the command:
1. discovers/classifies provider component meshes;
2. builds the global geometry-based semantic mapping proposal;
3. writes `mapping-proposal.json`;
4. writes `mapping-review.html`;
5. writes a continuation manifest;
6. exits at the explicit mapping-review boundary.

## Second pass: selection supplied

After the reviewer exports a mapping-selection JSON, rerun with:

```bash
--mapping-selection mapping-selection.json
```

Brickmen then:
1. validates the selection belongs to this architecture/job/provider;
2. explicitly promotes the selected mapping candidate;
3. writes `output-mapping.json`;
4. runs the complete generated-body validation bundle;
5. refreshes pipeline state.

## Separation from critics

This workflow rejects post-generation critics such as Particulate. Critic analysis is an auxiliary evidence workflow and cannot substitute for primary component generation.
