## Goal
Deliver `golden-eval.py check` through the capture and extract steps, so that a finished workspace and run-log store become a DM-2 capture and a deterministic, versioned `facts.json`, with every missing, unparsable or ambiguous source reported as an extract `error` naming the source and reason.

## Context
- Dependencies: T-01b (reference workspaces, `golden-eval.py`, deterministic git helper)
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; strict and canonical JSON as defined in the specification; every process launch stays inside `scripts/golden_*.py`; artifact formats read from `rules/workflow-globals.md`, `workflows/pae-tests.md`, `workflows/pv-contract.md`, `workflows/pv-issues.md`, `rules/quick-flow.md`, `workflows/bugfix.md`, `rules/run-log.md` (never changed); the leaf `repo:` field and `## Repositories` are not read; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-03, REQ-15, REQ-55, DM-2, DM-3 facts table.
- Reason: capture and fact extraction is the single source every later step reads; its done-state is a complete capture and correct facts, verifiable without assertions or normalization.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by T-01; writing under `tests/expected/`; semantic assertions, hidden checks, normalization and comparison (later children).

## Scope
- **In scope:** `check --case C --workflow W --workspace DIR [--run-log DIR] [--out DIR] [--update]` argument handling (default `--out` is a new temporary directory printed in the output; `--update` accepted and ignored until T-02e), the per-step status record with later steps `not-run`; capture (`workspace/` with `.git`, `git.json`, `run-log/`, `commands.json`, `capture.json` with tree digest, `seed_digest`, capture errors); open-test execution recorded in `commands.json`; every DM-3 fact; `facts.json`.
- **Out of scope:** SA/HC evaluation, outcome, projection, compare and candidates (T-02b–T-02e); attempt records and recorded-import `seed_context` (T-04b, T-05a).
- **Target files:** `scripts/golden-eval.py`, `scripts/golden_capture.py`, `scripts/golden_semantics.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (missing `check` command, missing facts).
2. Add `check` to `scripts/golden-eval.py`: arguments, case validation (exit 2 `parallel-unsupported` before any directory is written), output directory, step record with statuses from `passed`, `failed`, `error`, `skipped`, `not-run`.
3. Implement capture in `scripts/golden_capture.py`: workspace copy with `.git`, `git.json` (every commit reachable from any ref with full sha, parents, subject, changed paths; refs with targets; the single root commit reachable from HEAD as seed commit), run-log copy, `capture.json`; the comparison of the seed commit's tracked files with the seed project outside `.ai/`; capture `error` when anything cannot be written or a comparison fails.
4. Run the case `test_command` on a copy of the captured workspace and record argv, exit code, duration and output file names in `commands.json`.
5. Extract task-state facts in `scripts/golden_semantics.py`: task directory (exactly one new or changed `state.md` under `.ai/tasks/todo/` or `.ai/tasks/completed/`), `flow:`, `kind:`, `## Phases` (including an ignored `finalization` marker), leaf and composite blocks by field name, `plan.md` statuses for `full` flow.
6. Extract leaf mode and leaf tests from `notes:` entries: split at line breaks and `; `, join digest continuation pieces matching `^.+ → test_\w+(, test_\w+)*$`, read only `tdd: characterize —`, `tdd: none —` and `tdd: red digest —` entries, resolve names in `test_globs` files at HEAD (error when a name matches functions in two files).
7. Extract validation facts: Contract Check rows with criterion id from the first `AC-\d+` token, Issue List entries under `### Approved` and `### Deferred` (error on other non-empty content), `## Contract (quick)` and `## TDD (quick)`.
8. Extract git and log facts: commits and refs, branch model by the reader rule (value; absent with any `branch:` → `per-leaf`; else none; any other value → error), changed paths against the baseline by per-file content hash excluding `.git/`, run-log events ordered by run and `seq` (absent store → empty list), open-test result.
9. Write `facts.json` deterministically with a facts version; on any required source failure set extract `error` with source and reason.
10. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- REQ-03 (DM-2): `check` on each of the five references writes `capture/` with `workspace/` (including `.git`), `git.json`, `run-log/`, `commands.json` and `capture.json`, records capture and extract `passed`, and records every later step with a status from the step vocabulary.
- DM-2: a workspace whose seed commit's tracked files differ from the seed project outside `.ai/` yields capture `error` naming the comparison.
- REQ-15: mutated references with two task directories, no task directory, an unparsable leaf block header, and unrecognized text under `### Approved` each yield extract `error` whose record names the source and the reason.
- REQ-18 (fact extraction): the notes entry `tdd: red digest — AC-1 → test_a; AC-2 → test_b; context-receipt: implementer bootstrap — no-packet epoch 1` yields leaf tests `test_a` and `test_b` only; a `tdd: red output` entry is ignored; a test name defined in two `test_globs` files yields extract `error`.
- DM-3 branch model: `branch_model: per-composite` yields `per-composite`; absent with a block recording `branch:` yields `per-leaf`; absent without one yields none; `branch_model: other` yields extract `error`.
- Determinism: two `check` runs of the same reference produce byte-identical `facts.json`.
- REQ-55: `check` on a case copy declaring `parallel` 2 exits 2 with `parallel-unsupported` naming the case workflow and writes no capture.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (real `git`, file copies, subprocess open tests), unit (notes parsing, branch-model rule), smoke (guard re-pin)
- **Scenarios:**
  - Capture layout per reference → required files exist; capture and extract `passed`.
  - Seed mismatch → capture `error`.
  - Four extraction corruptions → extract `error` with source and reason.
  - Digest parsing → `test_a`, `test_b`; ignored entries ignored; duplicate definition → `error`.
  - Branch model variants → expected values or `error`.
  - Double `check` → identical `facts.json` bytes.
  - `parallel` 2 → exit 2, no capture.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; empty/null (absent run-log store, absent `branch_model:`); duplicate (two task directories, name in two files); invalid state (unparsable header, unknown branch model); missing dependencies (no task directory).
