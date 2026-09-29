# Brickmen Agent Instructions

Brickmen is the canonical source of truth for this project.

## Session bootstrap

Before substantial work:

1. Read `docs/agent/AUTONOMY.md`.
2. Read `AUTONOMOUS_STATE.md`.
3. Read `data/autonomous-state.json` when machine-readable state is useful.
4. Inspect the relevant canonical Brickmen documentation, datasets, registries, and schemas.
5. Inspect recent git commits when needed to determine the true latest state.
6. Resume the highest-value unfinished work rather than starting over.

Do not depend on prior conversation context when repository state can answer the question.

## Operating rule

Work autonomously and continuously.

After completing a task:
1. validate it;
2. persist useful results;
3. make a coherent commit;
4. update autonomous state;
5. select the next highest-value executable task;
6. continue.

A commit is a checkpoint, not an endpoint.

Do not stop merely because:
- one task completed;
- one research phase completed;
- a commit was made;
- one source failed;
- one task became blocked.

If blocked, record the blocker and switch to another useful independent task.

Do not ask the user what to do next unless a consequential decision genuinely requires approval.

## Persistence

GitHub is project memory.

Keep `AUTONOMOUS_STATE.md` and `data/autonomous-state.json` current enough that a fresh agent with no previous conversation can resume the project.

Before anticipated context exhaustion or interruption:
1. commit useful work;
2. update state;
3. record the exact continuation point.

## Priorities

Prefer:
- structured evidence;
- datasets;
- reference corpora;
- translation pairs;
- populated benchmarks;
- evaluations;
- tests;
- provenance;
- experimentally verified improvements.

Avoid:
- duplicate research;
- summaries of summaries;
- unnecessary architecture documents;
- prose volume without new evidence.

## Approval gates

Research, analysis, tests, datasets, documentation, and normal reversible repository development may proceed autonomously.

Require user approval before:
- spending money;
- using an unapproved paid API;
- irreversible deletion;
- force-pushing or destructive git operations;
- external publication or communication;
- other consequential external actions.

For the complete operating contract, follow `docs/agent/AUTONOMY.md`.
