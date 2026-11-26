---
description: Validation Step 5 — Execute fix-tasks via atomic execution → validation cycles
phase: validation
step: 5
---

Invocation: `/validation-execute-fixes <task-directory>`
Called by: `/validation` as Step 5.

Task directory = provided argument (trailing slash optional).

---

## Guard

1. Read `state.md` in the task directory.
2. Check `## Phases → validation`. If `complete` → **stop**: "Validation phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Check `## Fix-Tasks → fixes-created`:
   - If the section is missing or the marker is absent → **stop**: "`/validation-create-fixes` has not been completed. Run it first."
   - If the marker is `complete` and `fixes-count: 0` is present → **stop**: "No fix-tasks were created (all issues deferred). `/validation-execute-fixes` has nothing to do. Proceed to `/validation-finalize`."
   - If the marker is `complete` with `fixes-count` greater than 0 → continue.
4. Otherwise → continue.

---

## Context Bootstrap

Load the `bootstrap-validation` rule (`## Context Bootstrap`) before code reads or writes; perform the
full bootstrap when standalone. Quick tasks execute approved fixes inline in `/validation`.

## Instructions

1. Read `## Fix-Tasks → Created:` and match every listed ID to its plan row, description,
   and canonical leaf block. Include both `T-XX-fix-<slug>` and `T-XXc-fix-<slug>`;
   do not use a top-level-only glob. A missing artifact → **stop**: "Repair incomplete fix-task creation before executing."
2. Process fixes strictly sequentially in dependency order, with the readiness and resume
   rules from `/execution-execute`. `reviewed` skips; execution complete / plan `done` resumes at
   validation. Require `## Steps` and `## Acceptance Criteria` before running a leaf.
3. For each ready fix:
   - If needed, call `/atomic-execution <fix-description>`.
   - After successful execution, call `/atomic-validation <fix-description> --batch`.
     `--batch` records proposals, prompts for nothing, applies nothing.
   - A child failure/stop propagates immediately. Follow declared caller overrides for
     ambiguities; a blocker, Guard confirmation, or test gate still stops.
   - After review, run `/compress-state --auto` on parent state, preserving protected fields.
   - Re-read the Created list and plan after every cycle; composite integration may append
     approved fix siblings. Complete these before declaring the fix cycle finished.
4. Confirm every Created entry is `reviewed` and affected composites passed integration.
   Re-run `/validation-contract` and `/validation-review` for the changed surface; preserve original issue
   decisions and record resolution evidence. New findings require another decision cycle,
   not silent approval or replacement of the existing fix list.

Report: "Step 5 (Execute Fix-Tasks) complete. N fix-tasks reviewed."
Return to the caller; this is a progress marker.
