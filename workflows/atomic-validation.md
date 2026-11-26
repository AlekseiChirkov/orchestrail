---
description: Atomic Validation orchestrator — Validate a single T-XX subtask: check, propose improvements, close
phase: atomic-validation
step: "-"
---

Invocation: `/atomic-validation <path-to-atomic-description> [--batch]`
Example: `/atomic-validation .ai/tasks/todo/task_foo/T-01-slug/description.md`

If path is not provided — ask the user and do not continue.
Atomic task directory = parent directory of the provided `description.md`.
Parent task directory = one level above.

`--batch` flag: when present, pass it through to `/atomic-validation-propose` so improvement proposals are recorded without blocking for user input. Use this flag when called from `/execution-execute` (batch execution loop). When called standalone — omit the flag to preserve interactive behaviour.

To run a single step directly, call the child workflow:
`/atomic-validation-check`, `/atomic-validation-propose`, `/atomic-validation-close`.

---

## Context Bootstrap

Load the `bootstrap-atomic-validation` rule (`## Context Bootstrap`) before reading implementation files or
writing project files; run the full bootstrap when invoked standalone. The rule owns
the load order, umbrella precedence, conditional sources, and reporting.

Resolve the description and parent task paths before changing directories. Resolve
`working_dir:` from `description.md → ## Context` relative to the atomic task directory;
if absent, use the invocation directory. Set `WORK_DIR` to that absolute directory
and `AI_DIR = WORK_DIR/.ai`. The umbrella is `WORK_DIR/../.ai`.
Keep task-artifact paths absolute; run code reads, writes, and commands in `WORK_DIR`.

---

Under `/spec-run`, write only this leaf's progress block and permitted code/tests.
Return proposals sections, composite state, plan changes, new sibling descriptions, and
compression as deltas under `contract-orchestration → ## Shared-file discipline`.

## Guard

Step 0 — State Check

Read parent `state.md`. Locate the `## Subtask Progress` block for this T-XX.

**Input for validation:**
- `T-XX/description.md → ## Acceptance Criteria` — source of truth for what "done" means.
- The subtask's tests (from `target_files:`) plus `atomic-tests:` — the executable form of
  those criteria. `/atomic-validation-check` audits both that they pass and that they were not weakened.
- Parent `state.md → ## Subtask Progress → T-XX` block — context on what was done (`last_action`, `target_files:`, `notes`).
- Parent `state.md → ## Solution Design` — `### Invariants`, `### Off-limits`.

Checks:
- If `T-XX/description.md` is missing or has no `## Acceptance Criteria` → **stop**: "description.md is incomplete. Run `/discovery-decompose` + `/discovery-finalize`."
- If the `## Subtask Progress` block for this T-XX is missing → **stop**: "No execution record for T-XX. Run `/atomic-execution` first."
- If `atomic-execution` is not `complete` → **stop**: "Atomic execution not complete. Run `/atomic-execution` first."
- If `atomic-validation: complete` → **stop**: "Atomic validation already complete."
- If `atomic-validation: in-progress` → resume from the step the recorded `last_action:` marker
  names. Every resume point below is a value some workflow actually writes:

  | `last_action:` in the block | Resume at |
  |---|---|
  | `pav-check DONE` (written by `/atomic-validation-check`) | step 2 — `/atomic-validation-propose` |
  | `pav-propose done` (written by `/atomic-validation-propose` step 6, in every mode) | step 3 — `/atomic-validation-close` |
  | anything else, or absent | step 1 — `/atomic-validation-check`; it re-derives the verdict from the criteria and its own Guard handles the repeat |

  Do not infer the resume point from `## Improvement Proposals (T-XX)`: `/atomic-validation-propose` writes
  that section only when proposals are non-empty, so its absence does not mean step 2 was
  skipped.
- If `atomic-validation: not-started` (or field absent) → start from Step 1.

---

## Execution

Update parent `state.md → ## Subtask Progress` block for this T-XX: set `atomic-validation: in-progress`.

Run child workflows in order, skipping completed steps:
1. Call `/atomic-validation-check <path-to-atomic-description>` — Final check against `## Acceptance Criteria` + verdict (DONE / NEEDS WORK).
2. Call `/atomic-validation-propose <path-to-atomic-description> [--batch if --batch was passed to this workflow]` — Improvement proposals (only if DONE).
3. Call `/atomic-validation-close <path-to-atomic-description>` — Close task (only if DONE).

After each call, re-read its result. `/atomic-validation-check` owns `failed`; `/atomic-validation-close` owns `complete`.
A failed/stopped check ends this cycle immediately; do not run proposals or closure and do
not overwrite the failure with completion. Surface findings before creating fix-tasks.
A resumed `failed` record requires repaired implementation and a fresh `/atomic-validation-check`.

After completion, report final verdict and updated status.

This completion is a progress marker for the active caller, not a handoff.
