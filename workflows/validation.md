---
description: Phase 3 — Validation orchestrator: verify contract, review code, create and execute fix-tasks
phase: validation
step: "-"
---

Invocation: `/validation <task-directory>`
Example: `/validation .ai/tasks/todo/task-01-add-oauth/`

Use `contract-phases → ## Capabilities` for the declared mechanisms and their fallback paths.

If path is not provided — ask the user and do not continue.
Task directory = provided argument (trailing slash optional).

To run a single step directly, call the child workflow:
`/validation-contract`, `/validation-review`, `/validation-issues`, `/validation-create-fixes` (which calls `/validation-classify-fixes`
as step 4a), `/validation-execute-fixes`, `/validation-finalize`.

---

## Run Logging

This pipeline writes a run log. Follow the **`contract-run-log`** rule in full — it defines the
store, the field vocabulary, and the rule that logging never blocks a run.

Apply `contract-run-log → ## Workflow coverage and routing` at each boundary. Keep internal
step logging instructions and add `--note approximate` to every ordinary prompt step.

At Step 0, preserve an inherited `RUN_ID`; otherwise open an owned run with `scripts/log-step.sh run-start` through the configured helper:

```bash
LOG_HELPER="${ORCHESTRAIL_HOME:+$ORCHESTRAIL_HOME/scripts/log-step.sh}"
PHASE_OWNS_RUN=false
if [ -z "${RUN_ID:-}" ] && [ -x "$LOG_HELPER" ]; then
  RUN_ID=$("$LOG_HELPER" run-start --pipeline validation \
  --project "$(pwd)" --task <task-directory> --flow <quick|full>) || RUN_ID=""
  [ -z "$RUN_ID" ] || PHASE_OWNS_RUN=true
fi
```

Log one `step` line after each of `validation-contract`, `validation-review`, `validation-issues`,
`validation-classify-fixes`, `validation-create-fixes`, `validation-execute-fixes`, and `validation-finalize`. Carry
`--gate pass|fail` from `validation-contract` and `validation-review`, `--fix-tasks` from
`validation-create-fixes`, `--stops 1` on the `validation-issues` approve/defer prompt when a human
answered it, and `--decisions` when `/pipeline` answered it instead.

Close with `run-end` only when `PHASE_OWNS_RUN=true`; an inherited run stays open for
its owner. Do not open a second run for `/pipeline` or `/spec-run`.

Logging is best-effort: if `$LOG_HELPER` is missing or a call fails,
continue unchanged and mention it once in the final report. Never stop, retry, or ask the
user because of a log write.

---

## Context Bootstrap

Load the `bootstrap-validation` rule (`## Context Bootstrap`) before reading implementation files or
writing project files; run the full bootstrap when invoked standalone. The rule owns
the load order, umbrella precedence, conditional sources, and reporting.

---

## Guard

Step 0 — State Check

Resolve the task directory absolutely and read `state.md → ## Phases` before writing.
Missing state or execution not `complete` → **stop**: "Complete `/execution` first."
Validation complete → ask for explicit confirmation before replacing completed artifacts.
Absent `flow:` means `full`.

On resume, use persisted outputs, not directory existence:
- `## Contract Check` → contract check ran; enforce its critical-failure decision before review.
- `## Code Review` → review ran.
- `## Issue List` with both decision subsections → issue decisions recorded.
- `## Fix-Tasks` with `fixes-created: complete`, valid Created list, and every approved
  issue assigned → fix creation finished. Newly approved unassigned issues resume step 4
  in append mode; never discard completed fixes.
- `fixes-count: 0`, or every listed fix is `reviewed` → fix execution finished.
A partial/malformed output resumes its writer. Never infer "all fixes reviewed" from an
empty directory glob. Report the selected resume step; set `validation: in-progress`.
Open an owned run only after prerequisites and flow are known.

---

## Execution

Run sequentially, skipping only completed steps whose evidence remains valid:

1. `/validation-contract <task-directory>`.
2. `/validation-review <task-directory>`.
3. `/validation-issues <task-directory>` — record approval/deferral before applying findings.
4. `/validation-create-fixes <task-directory>` — full tier only; it calls `/validation-classify-fixes`.
5. `/validation-execute-fixes <task-directory>` — full tier only, skipped when `fixes-count: 0`.
6. `/validation-finalize <task-directory>` — after approved work and final checks succeed.

For `flow: quick`, steps 1–3 remain mandatory against `## Contract (quick)`.
Skip separate fix-task steps 4–5. Apply only approved findings inline, run the TDD gate
before changed behaviour, keep frozen tests, and rerun both `/validation-contract` and `/validation-review`.
Preserve the original issue decisions and record which approved items are resolved.
New findings return to the decision step. If a quick gate fails, promote per `contract-quick-flow`;
do not silently expand inline scope. The ADR trigger remains unchanged.

Any child stop/failure propagates; do not advance using an incomplete result. On a full
fix cycle, recheck the affected contract and review findings before finalization without
recreating already-recorded fix directories. Persist unresolved/deferred results.

Close only the run this invocation owns. Report verification, fixes, deferrals, and final
status. Child completion is a progress marker, not an extra user handoff.
