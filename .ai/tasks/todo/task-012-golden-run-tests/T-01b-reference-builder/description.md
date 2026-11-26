## Goal
Deliver `golden-eval.py build-reference` with byte-deterministic git builds, the helper home, and reference histories for all five catalog pairs, so that two builds with the same `--date-base` produce identical files, commit ids and tree ids even under a hostile user git configuration.

## Context
- Dependencies: T-01a (case loader, digests, case fixtures and suite harness)
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; strict JSON and canonical JSON as defined in the specification; every process launch stays inside `scripts/golden_*.py`; git runs with every inherited `GIT_*` variable removed, `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=/dev/null`, `-c commit.gpgsign=false -c core.hooksPath=/dev/null -c core.autocrlf=false`, `git init --object-format=sha1`; reference overlays follow the canonical artifact formats of `rules/workflow-globals.md`, `rules/tdd.md`, `workflows/pae-tests.md`, `workflows/pv-contract.md`, `workflows/pv-issues.md`, `rules/quick-flow.md` and `workflows/bugfix.md` (read only) with today's workflow and step names (`phase-pipeline`, `pe-execute`); tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-20, REQ-36, REQ-49, REQ-55, DM-1 history steps, Reference build determinism, Workspace and child environment.
- Reason: the builder plus its reference histories form one component whose done-state (deterministic, correct reference runs) is verifiable independently of capture and assertions.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation — reference task artifacts contain only the canonical pipeline fields the case's own run would write; deleting, skipping or weakening tests frozen by T-01a; writing under `tests/expected/`; any reference with `parallel` > 1.

## Scope
- **In scope:** `scripts/golden-eval.py` entry point (Python < 3.11 → exit 3, subcommand dispatch, one JSON object on stdout, diagnostics on stderr, exit-code constants); deterministic git helper; seed commit; helper home from `git ls-tree`/`git show` without `tests/`, `.ai/`, `docs/`; history steps `branch`, `switch`, `commit`, `merge`, `log`, `finalize`; `build-reference --case C --workflow W --out DIR [--date-base TIMESTAMP]`; `reference/<workflow>/overlay/` and `history.json` for the five catalog pairs.
- **Out of scope:** `check`, capture, facts, assertions, normalization (T-02); the per-composite branch-model variant built inside the suite (T-02d); attempt workspaces of `run` (T-04b reuses this helper).
- **Target files:** `scripts/golden-eval.py`, `scripts/golden_cases.py`, `tests/golden/cases/flat/reference/{spec-run,phase-pipeline}/**`, `tests/golden/cases/composite/reference/spec-run/**`, `tests/golden/cases/quick/reference/phase-pipeline/**`, `tests/golden/cases/bugfix/reference/bugfix/**`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (missing command, missing reference files).
2. Create `scripts/golden-eval.py`: interpreter version guard (exit 3 below 3.11), subcommand dispatch, machine output as one JSON object on stdout, diagnostics on stderr, the shared exit-code table.
3. Implement the deterministic git helper in `scripts/golden_cases.py`: sanitized environment and flags, fixed identities and dates, file modes 100644/100755, `git init -b main`, seed commit `seed: initial project` by `Golden Seed <seed@example.invalid>` at `2000-01-01T00:00:00Z` from the seed copied without `.git/` and `__pycache__/`, no remote.
4. Implement the helper home: every path of `git ls-tree -r --name-only <revision>` with content from `git show <revision>:<path>`, excluding the `tests/`, `.ai/` and `docs/` trees.
5. Implement history steps: `branch`, `switch`, `commit` (copy listed overlay paths, stage exactly them, subject `<type>: <subject>`, identity `Golden Reference <reference@example.invalid>`, date `date_base` + n seconds), `merge` (`--no-ff`, next number in the commit sequence), `log` (invoke the helper home's `scripts/log-step.sh` with `ORCHESTRAIL_LOG_ROOT` set to the reference log root), `finalize` (copy remaining overlay files, replace `{C<n>}` and `{c<n>}`).
6. Implement `build-reference`: load and validate the case (exit 2 with `parallel-unsupported` before creating any directory), build the workspace and run-log store under `--out`, default `--date-base` from the history.
7. Author `flat/reference/spec-run/`: three leaves in dependency order, each with a `test` commit touching only test files before its `feat` commit, per-leaf branch fields chained in plan order, `tdd: red digest` notes resolving at HEAD, Contract Check rows `PASS` for `AC-01`–`AC-03`, empty Issue List, run-log events.
8. Author `flat/reference/phase-pipeline/`: red-digest notes, `pe-execute` step events ordering the dependency chain, all phases complete, no branch fields.
9. Author `composite/reference/spec-run/`: one composite with children for parse and format, integration validation complete, `rollup: done`, per-leaf branch fields without `branch_model:`.
10. Author `quick/reference/phase-pipeline/` (`flow: quick`, `## Contract (quick)` with `### Off-limits`, `### Invariants`, `### Acceptance Criteria`, `## TDD (quick)` with `red-observed: yes` and `green-observed: yes`, no subtask directories) and `bugfix/reference/bugfix/` (`fix-<NN>-<slug>` task directory, `kind: bugfix`, `## Reproduction`, quick TDD record, pinned tests unchanged).
11. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-37 (REQ-49): given a `HOME` whose `.gitconfig` sets `commit.gpgsign=true` with a failing signing program and a `core.hooksPath` holding a failing `pre-commit` hook, `build-reference --case flat --workflow spec-run` run twice with the same `--date-base` into two directories succeeds both times, the tree digests of the two workspaces (excluding `.git/`) are equal and every ref resolves to the same commit id in both; with another `--date-base` every non-seed commit id differs while every commit's tree id is unchanged.
- REQ-49: two builds of each catalog pair with the same `--date-base` produce run-log stores whose events have identical `step`, `subtask`, `outcome`, `tests` and `gate` values in identical order.
- REQ-01: for each of the five catalog pairs `build-reference` exits 0 and, with `pytest` importable, the built workspace's open-test command exits 0 and every hidden test of the case passes against it.
- REQ-20: the helper home's file list equals `git ls-tree -r --name-only <revision>` minus the `tests/`, `.ai/` and `docs/` trees, and it contains `scripts/log-step.sh`.
- REQ-36: `git remote` in every built reference workspace prints nothing.
- REQ-55: `build-reference` on a case copy declaring `parallel` 2, 0 or `"1"` exits 2 with reason `parallel-unsupported` naming the case workflow and creates nothing under `--out`.
- CLI: the version guard maps interpreter version (3, 10) to exit 3 and (3, 11) to continue; `build-reference` prints exactly one JSON object on stdout.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (real `git` and `log-step.sh` in temporary directories), unit (version guard, placeholder substitution), smoke (guard re-pin)
- **Scenarios:**
  - AC-37 → hostile `HOME` git configuration; two builds equal; changed `--date-base` changes commit ids but not tree ids.
  - Run-log determinism → event value sequences equal across two builds per pair.
  - Reference correctness → each pair builds; open and hidden tests pass inside it.
  - Helper home → exact file list; `scripts/log-step.sh` present; no excluded tree.
  - No remote → `git remote` output empty.
  - `parallel` rejection → exit 2, `--out` untouched.
  - Version guard and JSON output → exit 3 for 3.10; single JSON object.
- **Edge cases:** happy path; boundary (date base shift, `{c<n>}` seven-character form); invalid state (signing and hooks configured by the user); missing dependencies (`pytest` absent → exit-3 path); duplicate operations (two builds into different directories).
