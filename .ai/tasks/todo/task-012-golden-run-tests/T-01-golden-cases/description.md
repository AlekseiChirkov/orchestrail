## Goal
Ship the four self-contained golden cases and a deterministic `build-reference` command so that every one of the five catalog pairs can be rebuilt offline into a reference workspace and run-log store whose open and hidden tests pass.

## Context
- type: composite
- children: T-01a, T-01b
- Dependencies: none
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; strict JSON (duplicate keys, `NaN`, `Infinity` and non-integer numbers rejected; decimals as strings; UTC millisecond timestamps; canonical JSON as defined in the specification); every process launch stays inside `scripts/golden_*.py`; tests extend the shared offline suite `tests/golden-runs.py` (`unittest`, behaviour-named); every child re-pins the source guard; contract: `.ai/specs/012-golden-run-tests.md` (delivery part 1, DM-1, Reference build determinism).
- Reason: delivery part 1 holds two independently testable components — the case catalog (fixtures, loader and suite harness) and the reference builder with its histories — each with its own criteria cluster (S2 = 2, S5 = 2).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by an earlier subtask; writing under `tests/expected/`.

## Scope
- **In scope:** the four cases `flat`, `composite`, `quick`, `bugfix` (seed projects, `case.json`, hidden tests, defect maps, reference overlays and histories for five catalog pairs); case loading, validation and tree digests; the suite harness with its `pytest` gate; the `golden-eval.py` entry point and `build-reference`; the helper home.
- **Out of scope:** capture, facts, assertions, comparison (T-02); manifests and running (T-03 onward).
- **Target files:** `tests/golden/cases/{flat,composite,quick,bugfix}/**`, `scripts/golden_cases.py`, `scripts/golden-eval.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
See children: T-01a (golden case fixtures and catalog loader), T-01b (deterministic reference builder and reference histories).

## Acceptance Criteria
- Integration: for each of the five catalog pairs (`flat`/`spec-run`, `flat`/`phase-pipeline`, `composite`/`spec-run`, `quick`/`phase-pipeline`, `bugfix`/`bugfix`), `build-reference` from the shipped case exits 0, and with `pytest` importable the built workspace's open-test command exits 0 and every hidden test of the case passes against it.
- Integration: the case digest of every shipped case computed by the loader is identical before and after building all five references (the builder never writes into a case directory), and each built workspace's seed commit tracked files equal the case's seed project files outside `.ai/`.
- Integration: `python3 -I tests/golden-runs.py` passes with `pytest` importable and exits 3 with exactly one `pytest` diagnostic without it.

## Test Plan
- **Level:** integration (executed by `/phase-composite-validation`)
- **Scenarios:**
  - Build all five references → each exits 0; open and hidden tests pass inside each workspace.
  - Case digests before and after the builds → equal; seed commit tree equals seed files outside `.ai/`.
  - Suite with and without `pytest` → exit 0 / exit 3 with one diagnostic.
- **Edge cases:** happy path; missing dependencies (`pytest` absent).
