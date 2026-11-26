## Goal
Enforce count, time and spend limits before every launch and halt a variant after a critical missed defect, so that a refused unit is recorded `stopped-by-policy` with the exact reason, the remaining schedule is still processed, and `run` exits 6.

## Context
- Dependencies: T-04b (reservation, launch, usage), T-02c (missed defects and claimed success), T-05a (imports count toward limits)
- Constraints: Python 3.11+ standard library and `git` only, run as `python3 -I`; decimals compared exactly (`decimal` or `fractions`, never floats); refusal reasons checked in the specified order (`cap-unenforceable`, `spend-unknown`, `spend-limit`); a cost is known when `cost_usd` is not null whatever its coverage; elapsed run time is summed over resumed runs from ledger timestamps; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-24, REQ-25, REQ-28, REQ-44, Limits, Run sequence step 4.
- Reason: launch admission (limits and halts) is one decision component with one criteria cluster (which launch is refused, with which reason and exit).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; releasing a halted variant; production budgets.

## Scope
- **In scope:** `attempt-limit`, `unit-attempt-limit`, `total-wall-limit`; spend bound (known costs + unknown-cost attempts × cap under `count-at-cap` + cap for the next attempt) with `cap-unenforceable`, `spend-unknown`, `spend-limit`; `refused` events and unit outcomes; continuing the remaining schedule; exit 6; `critical-missed-defect` halt of every not-yet-launched unit of the variant.
- **Out of scope:** timeout (T-05c); resume and `--retry-incomplete` scheduling (T-05d uses these checks).
- **Target files:** `scripts/golden_runner.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (no refusals).
2. Implement count limits from reserved attempts (`attempt-limit`, `unit-attempt-limit`).
3. Implement `total-wall-limit` from ledger timestamps summed over runs plus `max_wall_seconds_per_attempt`.
4. Implement the spend bound and the ordered refusal reasons, including the declaration's `per_attempt_cost_cap` and `accept_unverified_cost_cap`.
5. Implement refusal recording: `refused` event, unit outcome `stopped-by-policy` with the reason, continue the remaining schedule, exit 6.
6. Implement the critical-missed-defect halt: after an attempt with a `critical` missed defect, record every not-yet-launched unit of that variant `stopped-by-policy` `critical-missed-defect` and launch none of them, while other variants continue.
7. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-16 (REQ-24, REQ-25): with a double that exits 1 with no output, the ledger shows `reserved` before `launched`, the attempt is `technically-incomplete` and counts toward `max_attempts`; with attempts of known costs `0.2` and `0.2`, cap `0.5` and `max_cost_usd` `0.8`, the third launch is refused with `spend-limit`; with an earlier unknown cost and policy `refuse`, the next launch is refused with `spend-unknown`; with policy `count-at-cap` and the same costs it launches when the bound is within `max_cost_usd`; with a declaration `per_attempt_cost_cap: "unverified"` and no acceptance, the first launch is refused with `cap-unenforceable`; each refusal makes `run` exit 6.
- AC-19 (REQ-28): when variant B's first attempt has workflow-claimed success and fails a `critical` hidden test, B's remaining units are `stopped-by-policy` with `critical-missed-defect`, no further B launch occurs, and other variants continue.
- AC-34 (REQ-44): with `max_attempts` 1 and two planned units, the second unit is `stopped-by-policy` `attempt-limit` and `run` exits 6; with `max_attempts_per_unit` 1 and `--retry-incomplete` on an incomplete unit, it is refused with `unit-attempt-limit`; with `max_total_wall_seconds` smaller than `max_wall_seconds_per_attempt`, the first unit is refused with `total-wall-limit`.
- Ordering: when several spend reasons apply at once, the refusal names the first in the order `cap-unenforceable`, `spend-unknown`, `spend-limit`, and each refusal appends one `refused` event.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (runs with the scripted double), unit (spend bound arithmetic, reason order), smoke (guard re-pin)
- **Scenarios:**
  - AC-16 → event order; counted failure; `spend-limit`, `spend-unknown`, `count-at-cap` launch, `cap-unenforceable`; exit 6 each.
  - AC-19 → B halted, others continue.
  - AC-34 → `attempt-limit`, `unit-attempt-limit`, `total-wall-limit`.
  - Reason precedence and one `refused` event per refusal.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; boundary (bound exactly equal to `max_cost_usd`, attempts equal to the limit); empty/null (unknown cost); invalid state (unverified cap without acceptance); duplicate (retry of a unit at its limit).
