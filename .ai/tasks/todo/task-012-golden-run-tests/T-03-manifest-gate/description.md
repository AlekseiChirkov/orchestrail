## Goal
Deliver the experiment manifest contract and the `run` gate up to preflight — validation, configuration hashing, the instructions digest, interactive approval, authorization, preflight and `--dry-run` — so that no workspace is created and no adapter is invoked unless a valid, runnable, approved and pinned manifest passes every check in the order 2 → 4 → 5.

## Context
- type: composite
- children: T-03a, T-03b, T-03c
- Dependencies: T-01 (case loader, digests, `golden-eval.py`), T-02 (test double)
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; strict and canonical JSON as defined in the specification; every process launch stays inside `scripts/golden_*.py`; no real `claude` invocation (the test double only); tests extend `tests/golden-runs.py`; every child re-pins the source guard; contract: `.ai/specs/012-golden-run-tests.md` (delivery part 4, DM-6–DM-8, Command-line interfaces, Run sequence steps 1 and 3).
- Reason: three independently testable components with their own criteria clusters — manifest validation with hashing and digests, interactive approval with run authorization, and preflight with the dry-run plan (S2 = 3, S5 = 3).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by an earlier subtask; writing under `tests/expected/`; launching any adapter (T-04b).

## Scope
- **In scope:** DM-6 validation (valid/runnable), configuration hash, instructions digest with owner policy entries, the shipped `claude` declaration, `validate-manifest [--print-current]`, `approve`, `run` stages 1–2, `tests/run-golden.sh`, preflight (pinning, aliases, workspace location, adapter version, `pytest` with the child `PATH`), plan ordering, attempt keys, argv expansion, `--dry-run`.
- **Out of scope:** experiment directory, lock, ledger and launches (T-04); isolation probes (T-04c); switch semantics (T-04d); the safe template (T-08b).
- **Target files:** `scripts/golden_manifest.py`, `scripts/golden_runner.py`, `scripts/golden-eval.py`, `tests/golden/adapters/claude.json`, `tests/run-golden.sh`, the test double under `tests/golden/`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
See children: T-03a (manifest validation, hashing and instructions digest), T-03b (interactive approval and run authorization), T-03c (preflight and dry-run plan).

## Acceptance Criteria
- Integration: a regression manifest for `flat`/`spec-run` pinned with the values of `validate-manifest --print-current` validates as `valid: true, runnable: true`, is approved through a pseudo-terminal with the printed 12-character prefix, and `run --dry-run` with it exits 0, prints the plan, the preflight results and the planned argv, creates no file and leaves the test double's ledger empty.
- Integration: with that approved manifest, an invalid manifest document makes `run` exit 2, a limit edited after approval makes it exit 4, and a dirty tracked tree makes it exit 5 — each before any workspace, experiment directory or adapter invocation, and in that precedence when several apply at once.

## Test Plan
- **Level:** integration and contract (executed by `/phase-composite-validation`)
- **Scenarios:**
  - Validate → approve → dry-run end to end → exit 0, plan printed, no files, empty ledger.
  - Combined faults → exit 2 before 4 before 5; nothing created.
- **Edge cases:** happy path; invalid state (manifest edited after approval); permission boundaries (approval only from a terminal).
