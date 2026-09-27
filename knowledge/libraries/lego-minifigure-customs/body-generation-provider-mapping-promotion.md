# Promoting a Provider Part Mapping Proposal

Geometry-based provider mappings are proposals, not silent truth.

Promotion tool:
- `tools/geometry/promote_body_provider_output_mapping.py`

## Explicit review boundary

The caller must select a candidate index:

```bash
python -m tools.geometry.promote_body_provider_output_mapping \
  mapping-proposal.json provider-job.json provider-run.json 0 \
  --reviewer "name-or-agent-id" \
  --review-note "checked against front/side structural guides" \
  -o output-mapping.json
```

Promotion:
- copies the selected shared provider→Brickmen-mm transform;
- maps the selected anonymous provider files to slots;
- reruns the normal structural mapping validator;
- refuses incomplete candidates;
- refuses critic-only provider jobs;
- records proposal score and ambiguity;
- records reviewer/note;
- remains non-production.

## Important distinction

A proposal can have:

`automatic_promotion_allowed: false`

and still be explicitly promoted after review.

That is expected for symmetric bodies where geometry alone cannot distinguish every left/right or front/back orientation.

The promoted mapping is then eligible for the generated-body validation bundle.
