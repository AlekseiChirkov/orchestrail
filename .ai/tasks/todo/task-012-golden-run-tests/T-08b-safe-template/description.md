## Goal
Ship `tests/golden/manifest-template.json` that validates as `valid: true, runnable: false`, and prove the paid boundary end to end, so that no command other than an approved runnable `run` ever invokes the adapter, neither `scripts/validate-contracts.sh` nor `scripts/sync.sh` references the golden tooling, and the offline suite needs no network.

## Context
- Dependencies: T-08a (`calculate`), T-07a (`report`), T-03b (`run` authorization), T-03a (`validate-manifest`), T-02e (`check`, test double)
- Constraints: Python 3.11+ standard library only, run as `python3 -I`; strict JSON as defined in the specification; the template has `approval: null`, `execution_enabled: false` and every model, price and limit field `null`; the offline-namespace test uses `unshare --user --net true` only when it succeeds on the host and is reported skipped otherwise; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-05, REQ-10, REQ-37, NFR offline operation, Out of Scope (no registration in the validator or deploy script).
- Reason: the safe default and its boundary proof are one component — "nothing paid runs by default" — with one criteria cluster.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh` (read by the test, never changed), every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; any non-null model, price or limit in the template.

## Scope
- **In scope:** `tests/golden/manifest-template.json`; a suite test of the paid boundary across `run` (no manifest, template, disabled, missing approval), `check`, `validate-manifest`, `report` and `calculate` with the double on `PATH`; a text check that `scripts/validate-contracts.sh` and `scripts/sync.sh` contain neither `golden-eval.py` nor `run-golden.sh`; the offline-namespace re-run of the five `check` calls.
- **Out of scope:** CI files; documentation (T-08c).
- **Target files:** `tests/golden/manifest-template.json`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (template absent).
2. Author `tests/golden/manifest-template.json` with every DM-6 field present, owner-chosen values `null`, `approval: null` and `execution_enabled: false`.
3. Implement the paid-boundary suite test over the listed commands with the double's ledger and the text check of the two scripts.
4. Implement the offline-namespace test that re-runs the five reference `check` calls inside `unshare --user --net` when available and reports a skip otherwise.
5. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-02 (REQ-05, REQ-10): with the test double on `PATH`, `run` without `--manifest`, with the template, with `execution_enabled: false` and with a missing approval file each exit 4; `check`, `validate-manifest`, `report` and `calculate` run as well; afterwards the double's ledger is empty, and neither `scripts/validate-contracts.sh` nor `scripts/sync.sh` contains `golden-eval.py` or `run-golden.sh`.
- AC-27 (REQ-37): `validate-manifest` on `tests/golden/manifest-template.json` reports `valid: true, runnable: false`, and `run` with it exits 4.
- REQ-37: every model, price and limit field of the template is `null`, `approval` is `null` and `execution_enabled` is `false`.
- Offline operation: when `unshare --user --net true` succeeds on the host, the five reference `check` calls pass inside that namespace; otherwise that test is reported skipped and nothing else changes.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (command subprocesses with the double, network namespace when available), smoke (template validation, script text check, guard re-pin)
- **Scenarios:**
  - AC-02 → four `run` refusals with exit 4; four other commands; empty ledger; no references in the two scripts.
  - AC-27 → `valid: true, runnable: false`; `run` exit 4.
  - Template field scan → all owner values null.
  - Network namespace → pass or reported skip.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; empty/null (template nulls); missing dependencies (`unshare` unavailable); permission boundaries (no adapter call without approval).
