## Goal
Close the delivery with the deterministic scenario calculator, the safe manifest template with an end-to-end paid-boundary check, and the operating manual with its index rows, so that the shipped tool runs no model by default, every hypothetical figure is labelled `kind: hypothetical`, and an owner can operate every command from `docs/GOLDEN-RUNS.md`.

## Context
- type: composite
- children: T-08a, T-08b, T-08c
- Dependencies: T-07 (reports and verdicts), T-03 (manifest validation and run gate)
- Constraints: Python 3.11+ standard library only, run as `python3 -I`; strict and canonical JSON; exact `Fraction` arithmetic; documentation follows `.ai/principles/coding.md → Documentation` and document placement; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; every child re-pins the source guard; contract: `.ai/specs/012-golden-run-tests.md` (delivery part 8; DM-13, Calculator, Documentation, REQ-37, REQ-40, NFR offline operation).
- Reason: three independently testable components with their own criteria clusters — calculator, safe template with the paid boundary, documentation (S2 = 3, S5 = 3).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by an earlier subtask; writing under `tests/expected/`; documents in the repository root.

## Scope
- **In scope:** `calculate`, `tests/golden/calculator-example.json`, `tests/golden/manifest-template.json`, the paid-boundary and offline-namespace suite tests, `docs/GOLDEN-RUNS.md`, one row in `docs/README.md`, one inventory row in `scripts/README.md`.
- **Out of scope:** CI registration (owned elsewhere), adopting a promoted variant.
- **Target files:** `scripts/golden_calculator.py`, `scripts/golden-eval.py`, `tests/golden/calculator-example.json`, `tests/golden/manifest-template.json`, `docs/GOLDEN-RUNS.md`, `docs/README.md`, `scripts/README.md`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
See children: T-08a (scenario calculator), T-08b (safe manifest template and paid boundary), T-08c (operating manual).

## Acceptance Criteria
- Integration: with `pytest` importable, `python3 -I tests/golden-runs.py` exits 0 and `bash scripts/validate-contracts.sh` passes with the final re-pinned source guard; without `pytest` the suite exits 3 with one diagnostic.
- Integration: every `golden-eval.py` command named in `docs/GOLDEN-RUNS.md` is accepted by the command-line parser, and the documented template and calculator example are the shipped files (`validate-manifest` on the template reports `valid: true, runnable: false`; `calculate` on the example exits 0).

## Test Plan
- **Level:** integration and smoke (executed by `/phase-composite-validation`)
- **Scenarios:**
  - Full suite and validator → pass; exit-3 path without `pytest`.
  - Documentation cross-check → commands parse; template and example behave as documented.
- **Edge cases:** happy path; missing dependencies (`pytest` absent).
