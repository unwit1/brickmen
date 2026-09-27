# Body Provider Readiness

Brickmen can compile a current provider/readiness manifest:

- schema: `data/body-generation-provider-readiness.schema.json`
- compiler: `tools/geometry/compile_body_provider_readiness.py`

The report answers a different question from a provider ranking.

It records:
- which providers are primary generators, baselines, or post-generation critics;
- whether Brickmen has a verified runnable adapter;
- special inputs required by each path;
- output contracts and component-mapping requirements;
- helper tools available for execution/review;
- the canonical pipeline-state status;
- shared downstream validation coverage;
- physical/mechanical blockers that remain outside software-only authority.

## Important distinction

A provider can be `brickmen_execution_runnable: true` while the canonical experiment still says no GPU execution has been performed.

Likewise, every generated-geometry validation layer can be implemented while a real Giant shoulder remains blocked from production by physical 43093 interface validation.

The readiness report makes those distinctions explicit rather than treating “code exists,” “model ran,” “geometry passed,” and “production ready” as the same state.
