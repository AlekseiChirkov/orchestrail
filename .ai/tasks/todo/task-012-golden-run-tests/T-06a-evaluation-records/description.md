## Goal
Deliver `golden-eval.py evaluate` with append-only DM-11 records and the full DM-10 outcome table, so that every attempt receives the outcome of its first matching row, a contradicting human verdict opens a dispute that only the named resolver closes, and an attempt with compare `failed` and everything else `passed` is still `independently-accepted`.

## Context
- Dependencies: T-05b (policy refusals), T-05c (cancelled and timed-out attempts), T-05d (orphaned attempts), T-04a (ledger and directory opening), T-02d (check-level outcome rows)
- Constraints: Python 3.11+ standard library only, run as `python3 -I`; strict JSON as defined in the specification; records `evaluations/<attempt_key>/<revision>.json` with revision from 2, never rewritten; `review` and `dispute-resolution` take `accepted`/`rejected`, `late-defect` takes `defect` with `defect_id` and `severity`, `exclusion` takes `null` with a manifest `rule_id`; normalize and compare statuses never change the outcome; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-03, REQ-08, REQ-29, REQ-31, DM-10 outcome rules, DM-11 records, Command-line interfaces (`evaluate`).
- Reason: the outcome engine with its record intake is one component with one criteria cluster (which outcome each attempt and unit has).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; rewriting or deleting any record.

## Scope
- **In scope:** `evaluate --experiment DIR --attempt KEY --evaluator NAME` with exactly one of `--verdict accepted|rejected`, `--late-defect ID --severity S`, `--resolve-dispute accepted|rejected`, `--exclude RULE_ID`, and `--reason TEXT`; record writing and `evaluation-recorded`, `exclusion-recorded`, `dispute-opened`, `dispute-resolved` events; dispute opening when a `review` status contradicts the automated outcome; `--resolve-dispute` only by `evaluation.dispute_resolver` with an open dispute (else exit 2); late-defect window from `followup_window_days` and `ended_at` (outside → `source: "late"`, `outside-window`, no change); exclusion only with a manifest `rule_id`; outcome recomputation by rows 1–9 and unit outcome derivation, written back to the attempt and unit records.
- **Out of scope:** the evaluation queue (T-06b); report labels (T-07a).
- **Target files:** `scripts/golden_evaluation.py`, `scripts/golden-eval.py`, `scripts/golden_runner.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` (one prepared attempt per outcome row) and observe them fail for the right reason (no `evaluate`, no full outcome table).
2. Implement the outcome table rows 1–9 and unit-outcome derivation in `scripts/golden_evaluation.py`, used by the runner, imports and `evaluate`.
3. Implement `evaluate` argument validation, the experiment-directory opening for an existing directory, and DM-11 record writing with the next revision and the matching ledger event.
4. Implement disputes: open on a contradicting `review`; resolve only by the resolver with an open dispute, else exit 2.
5. Implement late defects (window, `outside-window`) and exclusions (`rule_id` must exist in `exclusion_rules`).
6. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-20 (REQ-03, REQ-29): attempts matching each row of the DM-10 outcome table, including one with both a capture error and a failed assertion and one with an SA `error`, each receive the outcome of their first matching row, and an attempt with compare `failed` and everything else `passed` is `independently-accepted`.
- AC-22 (REQ-31): for an automatically accepted attempt, recording `evaluate --verdict rejected` opens a dispute and makes the unit `rejected-by-criteria`; `--resolve-dispute` by a person other than the resolver exits 2; `--resolve-dispute accepted` by the resolver makes the unit `independently-accepted` and every record remains.
- REQ-29 (late defects): a `late-defect` record within `followup_window_days` of `ended_at` makes the outcome `rejected-by-criteria` with reason `late-defect`; one outside the window is recorded with `source: "late"` and `outside-window` and changes no outcome.
- DM-11: record revisions start at 2 and increase by one per record; an `--exclude` naming no manifest `rule_id` exits 2; `--resolve-dispute` without an open dispute exits 2; no record file is ever modified after it is written.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** unit (outcome table over synthetic attempt and record sets), integration (`evaluate` subprocesses on prepared experiment directories), smoke (guard re-pin)
- **Scenarios:**
  - AC-20 → nine rows plus the two combined cases → first-matching outcomes; compare-only failure → accepted.
  - AC-22 → dispute opened; wrong resolver exit 2; resolver acceptance; records intact.
  - Late defect inside/outside the window.
  - Revisions, unknown rule, resolve without dispute, immutability.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; boundary (late defect exactly at the window edge, `followup_window_days` 0); duplicate (second verdict appends a new revision); invalid state (resolve without dispute); permission boundaries (only the named resolver closes a dispute); missing dependencies (unknown attempt key → exit 2).
