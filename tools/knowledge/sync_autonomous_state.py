#!/usr/bin/env python3
"""Refresh the canonical continuation from validated review progress, without new history summaries."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.knowledge.build_fortnite_semantic_review_progress import build_progress, DEFAULT_PLAN, DEFAULT_BATCH_DIR
from tools.knowledge.build_fortnite_semantic_critic_evidence import build as build_critic_evidence
from tools.knowledge.build_fortnite_semantic_critic_hardcase_queue import build as build_hardcase_queue

DATA = ROOT / "knowledge/libraries/lego-minifigure-customs/data"


def synchronize(state, progress, hardcase_queue=None):
    """Preserve historical checkpoints while updating every active continuation field."""
    if progress.get("invalid_review_records") != 0:
        raise ValueError("Cannot synchronize from invalid semantic reviews")
    total = progress["eligible_pairs"]
    submitted = progress["submitted_first_review_pairs"]
    remaining = progress["remaining_first_review_pairs"]
    if any(type(v) is not int or v < 0 for v in (total, submitted, remaining)) or submitted + remaining != total:
        raise ValueError("Inconsistent semantic progress counts")
    result = copy.deepcopy(state)
    next_batch = progress["next_materialized_incomplete_batch"] or progress["next_planned_batch"]
    next_index = next_batch["batch_index"] if next_batch else None
    first_step = f"Review first-review batch {next_index:04d}" if next_index else "First-review coverage is complete"
    instruction = (
        f"Do not restart completed architecture gates. {submitted}/{total} high-priority pairs have submitted "
        f"first reviews with {progress['submitted_semantic_annotations']} annotations; {remaining} remain. "
        f"{first_step}. Obtain genuinely independent second reviews and explicit adjudication before canonical "
        "promotion. Preserve exact hashes, source appearance, uncertainty, and no-hidden-view rules. "
        "Continue exact-release multiview evidence and generation evaluation with the existing tools."
    )
    result["current_workstream"] = (
        f"fortnite_semantic_first_review_batch_{next_index:04d}_plus_exact_release_multiview"
        if next_index else "semantic_independent_second_review_and_exact_release_multiview"
    )
    result["semantic_review_frontier"] = {
        key: progress[key] for key in (
            "eligible_pairs", "complete_first_review_batch_count", "submitted_first_review_pairs",
            "remaining_first_review_pairs", "submitted_semantic_annotations", "independently_double_reviewed_pairs",
            "adjudicated_pairs", "next_materialized_incomplete_batch", "next_planned_batch",
        )
    }
    result["semantic_review_frontier"]["evidence_sha256"] = hashlib.sha256(
        json.dumps(progress, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    for gap in result.get("known_gaps", []):
        if gap.get("id") == "fortnite_semantic_review_labels":
            gap["description"] = instruction
            gap["status"] = "pending_independent_second_review_and_remaining_first_review"
    for task in result.get("highest_value_tasks", []):
        text = task.get("task", "").casefold()
        if (task.get("id") == "fortnite_semantic_first_review"
                or "fortnite first-review" in text
                or text.startswith("review first-review batch ")
                or text.startswith("first-review coverage is complete")):
            task["id"] = "fortnite_semantic_first_review"
            task["task"] = first_step + "; obtain independent second reviews and adjudicate before canonical promotion."
    result["continuation"] = {"instruction": instruction}
    result["completed_batches_are_historical_snapshots"] = True
    if hardcase_queue is not None:
        gate = result.setdefault("semantic_evidence_gate", {})
        previous = gate.get("hardcase_priority", {})
        gate["hardcase_priority"] = {
            "processor_version": hardcase_queue["processor_version"],
            "unique_critic_items": hardcase_queue["unique_critic_items"],
            "unpaired_uncertainty_items": hardcase_queue["unpaired_uncertainty_items"],
            "duplicates_ignored": hardcase_queue["duplicate_critic_items_ignored"],
            "queue_sha256": hashlib.sha256(
                (json.dumps(hardcase_queue, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            ).hexdigest(),
            "policy": previous.get("policy", "Unpaired uncertainty retained without translation-priority score; identical critic IDs count once, conflicts fail; no eligibility promotion."),
        }
    return result


def render_markdown(state, summaries):
    frontier = state["semantic_review_frontier"]
    rows = []
    for title, filename, summary in summaries:
        rows.append(f"| [{title}](knowledge/libraries/lego-minifigure-customs/data/{filename}) | "
                    f"{summary['model_input_allowed_cases']}/{summary['total_cases']} | {summary['blocked_cases']} |")
    priorities = "\n".join(f"- {task['task']}" for task in state["highest_value_tasks"])
    return f"""# Brickmen Autonomous State

Updated: {state['updated_date']}. Status: {state['status']}.
Latest validated checkpoint: `{state['latest_validated_test_commit']}`.

This is the current continuation, generated by `tools/knowledge/sync_autonomous_state.py`.
Historical checkpoints remain in [machine state](data/autonomous-state.json), per-batch source records, and Git history.

## Mission

Improve accurate minifigure and part generation through source appearance, official style, canonical geometry,
measured evaluation, and manufacturing evidence. Reuse existing tools and preserve unknowns.

## Architecture input gates

| Evaluation corpus | Model-input allowed | Blocked |
| --- | --- | --- |
{chr(10).join(rows)}

These are evidence input gates; they do not establish generated-image accuracy or physical fit.

## Semantic review frontier

- First reviews: {frontier['submitted_first_review_pairs']}/{frontier['eligible_pairs']} pairs;
  {frontier['remaining_first_review_pairs']} remain, with {frontier['submitted_semantic_annotations']} submitted annotations.
- Independent double reviews: {frontier['independently_double_reviewed_pairs']}.
- Adjudicated pairs: {frontier['adjudicated_pairs']}; promotion must still pass the dedicated eligibility gate.
- [Derived progress](knowledge/libraries/lego-minifigure-customs/data/semantic-review-batches/fortnite-semantic-review-progress.json)
  is recomputed from checked-in batch membership and validated review records.
- First-review labels remain provisional until independent review and explicit adjudication.

## Next work

{priorities}

{state['continuation']['instruction']}

## Constraints and reusable paths

- Missing rear/side evidence remains missing. Geometry and game imagery cannot substitute for physical appearance.
- Digital connector validity does not prove physical fit. Lower/upper torso reference fitting still needs additional landmarks.
- [Generation workflow](knowledge/libraries/lego-minifigure-customs/generation-workflow.md) covers briefs,
  part namespaces, appearance/geometry evidence, rendering dependency pins, output contracts, and evaluation.
- [Existing geometry validation](knowledge/libraries/lego-minifigure-customs/body-generation-validation-bundle.md)
  and provider continuation should be extended rather than duplicated.
- [Exact-release flat-art evidence](knowledge/libraries/lego-minifigure-customs/data/exact-release-flat-art-reference-sets-v1-summary.json)
  records reviewed surface coverage; additional photographs need exact release identity and visual review.
- Paid services, irreversible deletion, force push, external publication and communication require authorization.

## Refresh and verify

```powershell
python tools/knowledge/sync_autonomous_state.py --check
python tools/validate_repo.py
python -m pytest tests -q
```

After changing reviewed evidence, run the sync tool without `--check`; pass `--updated-date YYYY-MM-DD`
when updating the checkpoint date. Continue work under [the autonomous contract](docs/agent/AUTONOMY.md).
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--updated-date")
    args = parser.parse_args()
    state_path = ROOT / "data/autonomous-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    progress = build_progress(DEFAULT_PLAN, DEFAULT_BATCH_DIR)
    critics, critic_summary = build_critic_evidence(DEFAULT_BATCH_DIR)
    hardcase_queue = build_hardcase_queue(critics)
    updated = synchronize(state, progress, hardcase_queue)
    if args.updated_date:
        from datetime import date
        date.fromisoformat(args.updated_date)
        updated["updated_date"] = args.updated_date
    summaries = []
    for title, filename in (
        ("Original benchmark", "body-architecture-benchmark-model-input-manifest.json"),
        ("Challenge v4", "body-architecture-recognition-challenge-model-input-manifest-v4.json"),
        ("Custom architectures", "body-architecture-custom-model-input-manifest-v1.json"),
    ):
        document = json.loads((DATA / filename).read_text(encoding="utf-8"))
        summaries.append((title, filename, document["summary"]))
    outputs = {
        state_path: json.dumps(updated, indent=2, ensure_ascii=False) + "\n",
        ROOT / "AUTONOMOUS_STATE.md": render_markdown(updated, summaries),
        DEFAULT_BATCH_DIR / "fortnite-semantic-review-progress.json": json.dumps(progress, indent=2, ensure_ascii=False) + "\n",
        DATA / "fortnite-semantic-critic-evidence-v1.jsonl": "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in critics),
        DATA / "fortnite-semantic-critic-evidence-v1-summary.json": json.dumps(critic_summary, indent=2, ensure_ascii=False) + "\n",
        DATA / "fortnite-semantic-critic-hardcase-queue-v1.json": json.dumps(hardcase_queue, indent=2, ensure_ascii=False) + "\n",
    }
    stale = [path for path, content in outputs.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
    if not args.check:
        for path in stale:
            path.write_text(outputs[path], encoding="utf-8", newline="\n")
    print(json.dumps({"status": "stale" if args.check and stale else "current", "changed_paths": [p.relative_to(ROOT).as_posix() for p in stale]}))
    return 2 if args.check and stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
