# Body Generation Pipeline State

Brickmen now exposes body-generation work as an explicit resumable gate model:

- `data/body-generation-pipeline-state.schema.json`
- `tools/geometry/summarize_body_generation_pipeline_state.py`

This is designed for future agents and interrupted workflows.

## Gates

The current state model tracks:
1. conditioning;
2. articulation sweeps;
3. structural guides;
4. provider job;
5. provider run;
6. component-slot mapping;
7. provider→Brickmen frame alignment;
8. coarse bbox geometry validation;
9. exact collision/boolean validation;
10. mechanical interface validation.

## Why this matters

A future session should not need to infer status from commit history.

The state file can say:

```
conditioning                    complete
articulation_sweeps             complete
structural_guides               complete
provider_job                    complete
provider_run                    pending
component_mapping               not_started
frame_alignment                 not_started
bbox_geometry_validation        not_started
exact_collision_boolean         not_started
mechanical_interface_validation blocked
```

and then emit concrete next actions.

## Production boundary

The pipeline-state artifact itself is non-production.

Even when all visual generation gates pass, any reference-only mechanical profile remains a blocker until its own engineering/physical validation is promoted separately.
