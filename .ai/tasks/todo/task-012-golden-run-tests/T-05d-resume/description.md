## Goal
Deliver `run --resume DIR [--retry-incomplete]`, so that a resumed experiment records orphaned reservations as `technically-incomplete` `orphaned`, never relaunches a unit with a finished attempt unless its last outcome is `technically-incomplete`, `--retry-incomplete` is given and the per-unit limit allows it, and refuses changed manifest bytes with exit 4.

## Context
- Dependencies: T-04a (opening rules, ledger), T-04b (launch and capture), T-05a (imports-only directories), T-05b (limit checks), T-05c (cancelled and timed-out outcomes)
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; resume requires `stop.resume_allowed`; preflight is re-run; orphans count toward limits; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-27, Resume, Opening an experiment directory, Edge cases (runner killed between `reserved` and `finished`; resume with changed bytes).
- Reason: resume is one scheduling component with one criteria cluster (what an interrupted experiment does next).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; any automatic restart.

## Scope
- **In scope:** `--resume` opening (lock, stored-copy comparison exit 4, `resume_allowed` else exit 4, `resumed` event, preflight re-run); orphan recovery (capture when the temporary workspace still exists, outcome `technically-incomplete` `orphaned`, `finished`); schedule continuation (skip finished units; `--retry-incomplete` for units whose last outcome is `technically-incomplete` within `max_attempts_per_unit`; `attempt_no` increments); `experiment-exists` for `run` without `--resume`.
- **Out of scope:** reports over resumed experiments (T-07a).
- **Target files:** `scripts/golden_runner.py`, `scripts/golden-eval.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` (an experiment with one accepted unit, one `technically-incomplete` unit and one orphaned reservation) and observe them fail for the right reason (no resume).
2. Implement `--resume` opening: stored-copy comparison, `resume_allowed`, `resumed` event, preflight re-run.
3. Implement orphan recovery for every `reserved` attempt without `finished`.
4. Implement schedule continuation with finished-unit skipping, `--retry-incomplete` and attempt numbering.
5. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-18 (REQ-27): for an experiment with one accepted unit, one `technically-incomplete` unit and one orphaned reservation, `run --resume` without `--retry-incomplete` records the orphan `technically-incomplete` `orphaned` and makes no adapter call; with `--retry-incomplete` exactly two calls occur, each with `attempt_no` 2; with changed manifest bytes `--resume` exits 4; `run` without `--resume` on that directory (which holds a `launched` event) exits 2, while `run` after only an `import-recorded` into a fresh directory proceeds without `--resume`.
- Resume gate: a manifest with `stop.resume_allowed: false` makes `run --resume` exit 4; a successful resume appends one `resumed` event and re-runs preflight (a dirty tracked tree at resume exits 5).
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (prepared experiment directories, scripted double, real `git`), smoke (guard re-pin)
- **Scenarios:**
  - AC-18 → orphan recorded with no call; two retries with `attempt_no` 2; changed bytes exit 4; `experiment-exists` exit 2; imports-only directory proceeds.
  - `resume_allowed: false` → exit 4; `resumed` event; dirty tree at resume → exit 5.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; invalid state (orphaned reservation, changed manifest bytes); duplicate (resume twice); boundary (retry at the per-unit limit); missing dependencies (orphan whose temporary workspace is gone).
