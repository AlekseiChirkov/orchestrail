---
description: Reconcile atomic execution blockers on entry
load: on-demand
---

# Blocker Reconciliation Procedure

## Blocker Reconciliation

Applies whenever a leaf's `atomic-execution: blocked` is encountered on entry (orchestrator Step 0, or a standalone `/atomic-execution-implement` that reads the block). Do **not** immediately ask the user "Is it resolved?". First classify the `blocker:` text:

**1. Dependency/status blocker** — the blocker cites only prerequisite subtasks (their approval, preconditions, or completion) and no other condition. Reconcile automatically:

- Determine the prerequisites: this T-XX's declared `Depends On` entries from parent `plan.md → ## Subtasks`, unioned with any `T-YY` explicitly named in the `blocker:` text.
- A prerequisite is **satisfied** when its `plan.md` status is `done` or `reviewed` (the same readiness rule `/execution-execute` uses). A composite prerequisite is satisfied when its block shows `rollup: done` **and** `integration-validation: complete`.
- If **every** prerequisite is satisfied → auto-reconcile without asking:
  - Set `blocker: none`.
  - Set `atomic-execution: in-progress` if `last_action` shows work already began, otherwise `not-started`.
  - Append to `last_action:` — `auto-reconciled blocker: prerequisites <list> satisfied`.
  - Add a `notes:` line recording the automatic reconciliation and the observed prerequisite statuses (e.g. `auto-reconciled 2026-07-17: T-01 reviewed, T-02 done — blocker cleared, no manual confirmation`).
  - Report the reconciliation to the user and **continue** — no confirmation required.
- If **any** prerequisite is NOT satisfied → keep `blocked`, report which prerequisite is outstanding and its current status, ask "Is it resolved? (yes/no)", and **wait**.

**2. Non-status blocker** — anything else: `step N failed`, `test failures`, `lint failures`, a missing external decision, an invariant conflict, or an implementation error. Never auto-reconcile. Report the blocker and ask "Is it resolved? (yes/no)". **Wait.**

**Ambiguity rule:** if the blocker cites a prerequisite **and** any non-status condition, treat it as non-status (manual confirmation). Any doubt → manual. An extra stop is always cheaper than resuming on an unmet blocker.
