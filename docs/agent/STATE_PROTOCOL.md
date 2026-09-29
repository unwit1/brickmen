# Autonomous State Protocol

Brickmen uses repository state as the handoff mechanism between agents and sessions.

## Canonical state files

- `AUTONOMOUS_STATE.md` — concise human-readable operational checkpoint.
- `data/autonomous-state.json` — machine-readable equivalent for orchestrators and agents.

These are operational state, not substitutes for canonical datasets, research documents, or git history.

## When to update

Update state after:
- a meaningful research/development batch;
- a change in highest-value priority;
- discovering a blocker that may affect future agents;
- completing a major validation;
- before anticipated context/runtime termination.

Do not update it after every trivial edit.

## What to record

Keep:
- current objective;
- current workstream/frontier;
- last meaningful commit when practical;
- completed batch summary;
- blocked tasks and reasons;
- pending validation;
- highest-value next tasks;
- exact continuation instruction.

Do not paste:
- long reasoning traces;
- full research notes;
- duplicated canonical data;
- transient tool logs.

## Continuation semantics

A new agent should be able to:
1. read `AGENTS.md`;
2. read autonomous state;
3. inspect the referenced canonical files/recent commits;
4. resume without prior conversation history.

## Blocker semantics

Use bounded retries.

If a task cannot progress:
1. record the blocker;
2. try a materially different method if justified;
3. mark it blocked if still unresolved;
4. continue another independent task.

Do not let one blocked source or tool halt the run.

## Commit semantics

A commit is a durable checkpoint, not a completion signal.

Prefer coherent, understandable commits using prefixes such as:
- `research:`
- `data:`
- `schema:`
- `benchmark:`
- `docs:`
- `code:`
- `test:`
- `fix:`
- `audit:`
- `agent:`

Before committing structured-data changes, run relevant validation/tests where available.

## Conflict handling

Never overwrite newer repository state blindly.

When state or target files changed since they were read:
- fetch current content;
- reconcile;
- preserve valid newer work;
- then write.

Never force-push as part of normal autonomous operation.
