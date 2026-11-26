## Goal
Deliver recorded imports and usage attachment, launch limits and variant halts, cancellation and attempt timeout, and resume without automatic restart, so that every attempt — imported, refused, cancelled, timed out or orphaned — is counted, recorded with exactly one outcome and reflected in the run's exit code without any unapproved relaunch.

## Context
- type: composite
- children: T-05a, T-05b, T-05c, T-05d
- Dependencies: T-04 (experiment directory, ledger, launch, test double)
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; strict and canonical JSON as defined in the specification; attempts run sequentially; every process launch and signal stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py` and the double; timing-based tests use generous margins and assert ordering, not durations; every child re-pins the source guard; contract: `.ai/specs/012-golden-run-tests.md` (delivery part 5 — limits, cancellation, resume, import; Recorded imports; Limits; Resume).
- Reason: four independently testable components with their own criteria clusters — recorded evidence intake, launch limits and halts, signal handling and timeout, resume (S2 = 4, S5 = 4).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by an earlier subtask; writing under `tests/expected/`; any automatic relaunch; releasing a halted variant without a new approved manifest; defining usage telemetry or prices.

## Scope
- **In scope:** `import-recorded`, `attach-usage`, count/time/spend limits with refusal reasons, critical-missed-defect halts, SIGINT/SIGTERM handling, per-attempt timeout, `run --resume [--retry-incomplete]`, orphan recovery.
- **Out of scope:** evaluation records and the full outcome table (T-06a); reports (T-07).
- **Target files:** `scripts/golden_runner.py`, `scripts/golden_capture.py`, `scripts/golden-eval.py`, the test double under `tests/golden/`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
See children: T-05a (recorded imports and usage attachment), T-05b (launch limits and variant halts), T-05c (cancellation and attempt timeout), T-05d (resume without automatic restart).

## Acceptance Criteria
- Integration: one experiment that receives a recorded import, then a `run` whose second launch is refused by `max_attempts` (exit 6), then `run --resume` with the stored manifest and approval (which launches nothing further) and `run --resume` with changed manifest bytes (exit 4), yields a ledger with consecutive `seq` values, one `finished` event per attempt, and a unit outcome for every planned unit consistent with each attempt record.
- Integration: across a run that produces a policy refusal (exit 6), and a separate run cancelled by SIGTERM (exit 7) that is then resumed, the reported exit codes are the highest of the codes their attempts and refusals produced, and the double's ledger never shows a launch for a unit whose last outcome forbids one.

## Test Plan
- **Level:** integration (executed by `/phase-composite-validation`)
- **Scenarios:**
  - Import → limit refusal → resume with changed bytes → consistent ledger, records and outcomes.
  - Refusal and cancellation runs → highest exit code; no forbidden launch.
- **Edge cases:** happy path; invalid state (resume with changed manifest); concurrent operations (signal during launch).
