## Goal
Execute hidden checks HC-1–HC-3 on a throwaway copy of the final workspace with an empty `HOME` and the child environment allowlist, so that failed hidden tests map to defect ids and severities, missed defects are recorded under workflow-claimed success, and a missing `pytest` yields exit 3 after every other check.

## Context
- Dependencies: T-02a (capture, facts including leaf tests and phases)
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; hidden checks never run inside the executor workspace; `HOME` is an empty temporary directory and the environment is built from the allowlist of Workspace and child environment; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-08, REQ-28 (missed defect definition), REQ-35, DM-3 hidden checks, Terminology (workflow-claimed success, missed defect).
- Reason: hidden checks are the evaluator-side component with their own done-state (correct defect mapping and seed replay), testable without semantic assertions.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; the isolation prefix (T-04c adds it).

## Scope
- **In scope:** throwaway copies; HC-1 (`pytest` on `hidden/tests/` copied next to the final project, failures mapped through `hidden/defects.json`); HC-2 seed replay (seed copy plus final versions of the files holding leaf tests or quick `tests:` names, run by node id, pass/fail per function); HC-3 defect summary; `workflow_claimed_success` from the three phase markers (finalization ignored); missed defects with severity; the evaluate step status and `hidden/` results in the check output; REQ-35 for `check`.
- **Out of scope:** SA-05's use of HC-2 results and the outcome (T-02d); late defects (T-06a); isolation prefix (T-04c).
- **Target files:** `scripts/golden_semantics.py` (or a hidden-check module chosen by design), `scripts/golden-eval.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (missing hidden results).
2. Implement throwaway copies of the final workspace and seed project with an empty temporary `HOME` and the allowlisted child environment.
3. Implement HC-1: copy `hidden/tests/` next to the final project, run `pytest`, map each failed test to its defect id and severity.
4. Implement HC-2: overlay the final versions of the test files containing leaf tests (or quick `tests:` names) onto a seed copy, run those functions by node id, record pass/fail per function.
5. Implement HC-3 and missed defects: defect ids whose `detected_by` tests failed; with `workflow_claimed_success` true each becomes a missed defect with its severity and `source: hidden`.
6. Implement REQ-35 for `check`: when `pytest` is not importable by the interpreter, mark pytest-dependent checks, run every other step, print one diagnostic naming `pytest` and the provisioning command, install nothing, exit 3.
7. Record HC statuses, per-test results and the evaluate step status in the check output under `hidden/`.
8. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- REQ-08 (HC-1): `check` on each of the five references records HC-1, HC-2 and HC-3 `passed`, no missed defect, and evaluate `passed`.
- REQ-19 (N-03): a `flat`/`spec-run` reference with all phases complete and one hidden test made to fail records HC-1 `failed`, `workflow_claimed_success` true and a missed defect with the defect's id and severity.
- REQ-19, REQ-28 (N-06): a `composite` reference whose `parse_amount` returns `Decimal` while the children's open tests pass records HC-1 failure of D-1 and a `critical` missed defect.
- HC-2: replay records one pass/fail result per leaf test function, and the SHA-256 of every file of the checked workspace is unchanged after the hidden checks.
- Hidden-check environment: the hidden-check process sees a `HOME` that is an empty temporary directory and only environment names from the allowlist.
- REQ-35: `check` with an interpreter where `import pytest` fails runs every other step, prints exactly one diagnostic naming `pytest`, starts no installer and exits 3.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (real `pytest` subprocesses on copies), unit (defect mapping, claimed-success rule), smoke (guard re-pin)
- **Scenarios:**
  - Five references → all HC `passed`, no missed defect.
  - N-03 → HC-1 `failed`, claimed success, missed defect recorded.
  - N-06 → critical missed defect D-1.
  - Replay → per-function results; workspace hashes unchanged.
  - Environment → empty `HOME`, allowlisted names only.
  - No `pytest` → exit 3, one diagnostic, no installer.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; missing dependencies (`pytest` absent); invalid state (claimed success with failing hidden test); permission boundaries (hidden checks never write to the executor workspace).
