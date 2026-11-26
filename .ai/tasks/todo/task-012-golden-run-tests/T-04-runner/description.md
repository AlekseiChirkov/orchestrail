## Goal
Deliver live execution through the adapter — the exclusive experiment directory and fsynced ledger, attempt workspaces with the helper home and child environment, adapter launch and result handling, isolation probes and variant switches — so that an approved run with the test double launches each planned unit exactly once with the declared argv and environment, captures and evaluates it like `check`, and never exposes evaluator-only material.

## Context
- type: composite
- children: T-04a, T-04b, T-04c, T-04d
- Dependencies: T-02 (capture → compare pipeline, test double), T-03 (manifest, authorization, preflight, plan, argv)
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; strict and canonical JSON as defined in the specification; attempts run sequentially; every process launch stays inside `scripts/golden_*.py`; only the test double is ever executed as `claude`; tests extend `tests/golden-runs.py` and the double; every child re-pins the source guard; contract: `.ai/specs/012-golden-run-tests.md` (delivery part 5 — runner, ledger, adapters; DM-8–DM-10; Run sequence; Opening an experiment directory; Workspace and child environment; Isolation; Variant switches).
- Reason: four independently testable components with their own criteria clusters — experiment directory and ledger, attempt launch, isolation probes, variant switches (S2 = 4, S5 = 4).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by an earlier subtask; writing under `tests/expected/`; process-level sandboxing of the harness itself; any case prompt or switch passing `--allow-pr`, `--repo` or `--parallel`.

## Scope
- **In scope:** experiment directory layout, lock, ledger, `experiment.json`, `plan.json`, `blinding.json`; workspaces, helper home, attempt log root, child environment; reservation and launch; result parsing, model identity, usage storage, attempt records; isolation probes and weaker designs; variant switches.
- **Out of scope:** limits, cancellation, timeout, resume, recorded imports (T-05); evaluation records and queue (T-06); reports (T-07).
- **Target files:** `scripts/golden_runner.py`, `scripts/golden_probe.py`, `scripts/golden_manifest.py`, `scripts/golden_capture.py`, `scripts/golden-eval.py`, the test double under `tests/golden/`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
See children: T-04a (experiment directory and ledger), T-04b (attempt launch through the adapter), T-04c (isolation probes and evaluator-only material), T-04d (variant switches).

## Acceptance Criteria
- Integration: an approved regression `run` of each of the five catalog pairs, with the test double replaying that pair's reference, creates one experiment directory with the DM-9 layout, records `reserved`, `launched` and `finished` for one attempt, yields outcome `independently-accepted` with compare `passed`, and exits 0.
- Integration: an approved comparison `run` with two variants (one with `switches`) under a `command-prefix` test prefix that denies probe reads and connections launches one attempt per unit, records `enforced` isolation in every attempt record, and the double's ledger holds exactly one entry per unit with the argv and environment names that unit's variant declares.

## Test Plan
- **Level:** integration (executed by `/phase-composite-validation`)
- **Scenarios:**
  - Regression run per catalog pair with replaying double → DM-9 layout, three ledger events, accepted, exit 0.
  - Comparison run with switches under the test prefix → one ledger entry per unit, `enforced` isolation, per-variant argv and environment.
- **Edge cases:** happy path; permission boundaries (evaluator-only material unreadable to the executor).
