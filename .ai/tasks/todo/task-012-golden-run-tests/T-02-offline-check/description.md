## Goal
Deliver the offline `check` pipeline (capture → extract → assert → evaluate → normalize → compare) with reviewed expected results for all five catalog pairs, so that every reference passes with outcome `independently-accepted` and compare `passed` while each corruption yields its named failure.

## Context
- type: composite
- children: T-02a, T-02b, T-02c, T-02d, T-02e
- Dependencies: T-01 (cases, references, builder, suite harness)
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; strict and canonical JSON as defined in the specification; every process launch stays inside `scripts/golden_*.py`; pipeline artifact formats are read from `rules/` and `workflows/` and never changed; tests extend `tests/golden-runs.py`; every child re-pins the source guard; contract: `.ai/specs/012-golden-run-tests.md` (delivery parts 2 and 3, DM-2–DM-5).
- Reason: five independently testable components with their own criteria clusters — capture and facts, projection normalization, hidden checks, semantic assertions with the check outcome, and golden comparison with reviewed expectations (S2 = 5, S5 = 5). Parts 2 and 3 together form the regression suite that is useful on its own.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by an earlier subtask; writing under `tests/expected/` other than through `accept-expected`.

## Scope
- **In scope:** `check`, capture (DM-2), facts (DM-3), hidden checks HC-1–HC-3, semantic assertions SA-01–SA-15, the check outcome, projection and NR-1–NR-4 (DM-4), compare, `--update` candidates and `accept-expected` (DM-5), expected results for the five pairs, the recording test double.
- **Out of scope:** manifests, `run`, ledger, experiment directories (T-03 onward); isolation prefixes for hidden checks (T-04c); evaluation records (T-06a).
- **Target files:** `scripts/golden-eval.py`, `scripts/golden_capture.py`, `scripts/golden_semantics.py`, `scripts/golden_normalize.py`, `tests/expected/{flat/spec-run,flat/phase-pipeline,composite/spec-run,quick/phase-pipeline,bugfix/bugfix}/{projection.json,review.json}`, the test double under `tests/golden/` (path set by design), `tests/golden/cases/*/reference/**` (corrections only, see Execution Strategy), `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
See children: T-02a (capture and fact extraction), T-02b (semantic projection normalization), T-02c (hidden checks and missed defects), T-02d (semantic assertions and check outcome), T-02e (golden comparison, candidates and reviewed expectations).

## Acceptance Criteria
- Integration: `check` on the reference of each of the five catalog pairs records the steps capture, extract, assert, evaluate, normalize and compare in that order, each `passed`, yields outcome `independently-accepted` and exits 0, and two runs produce byte-identical `facts.json` and `projection.json`.
- Integration: every corruption of the suite's negative catalog delivered by the children (N-01–N-06, N-08 normalization and capture parts, N-09–N-12) yields its named check and reason and no outcome `independently-accepted`; for N-03 compare stays `passed`.
- Integration: the full `python3 -I tests/golden-runs.py` passes with `pytest` importable, and `tests/expected/` changes only through `accept-expected` (no other code path writes there).

## Test Plan
- **Level:** integration (executed by `/phase-composite-validation`)
- **Scenarios:**
  - Five references through `check` → ordered `passed` steps, accepted outcome, exit 0, deterministic facts and projection bytes.
  - Negative catalog run → each named result; no accepted outcome; N-03 compare `passed`.
  - Write-path audit → a run of the whole suite leaves the SHA-256 of every file under `tests/expected/` unchanged.
- **Edge cases:** happy path; invalid state (corrupted references); missing dependencies (`pytest` absent → exit-3 path).
