## Goal
Write a blinded evaluation-queue entry for every finished live or recorded attempt, so that `queue.json` holds only attempt key, blinded label, task id, case, workflow and split, and no queue file contains a variant id, the requested model id or a `unit_id` even when the run wrote the model into `plan.md`, `state.md` or a commit.

## Context
- Dependencies: T-04b (attempt finish), T-05a (recorded imports), T-04a (blinded labels)
- Constraints: Python 3.11+ standard library and `git` only, run as `python3 -I`; canonical JSON as defined in the specification; the queue's workspace copy omits `.git/`; in `plan.md` every table cell under a header starting with `Model` becomes `<redacted>`; in the task `state.md` every line of `## Model Selection` after its heading becomes `<redacted>`; the queue omits the attempt record, adapter output and commit bodies; free text elsewhere may still reveal a model (a stated limit); every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-30, DM-9 evaluation queue.
- Reason: the queue is the blinding component with its own done-state (what a human evaluator can see), testable separately from outcome rules.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; the report's label mapping (T-07a).

## Scope
- **In scope:** `evaluation-queue/<attempt_key>/` with `queue.json`, the redacted workspace copy without `.git/`, `facts.json`, `assertions.json` and hidden results; the two redaction rules; omission of attempt record, adapter output and commit bodies; writing the entry at attempt finish for `run` and `import-recorded`.
- **Out of scope:** reports mapping labels to variants (T-07a).
- **Target files:** `scripts/golden_evaluation.py`, `scripts/golden_runner.py`, the test double under `tests/golden/`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` (a double that writes the requested model id into a `plan.md` `Model (Claude)` column, a `## Model Selection` line of the task `state.md` and a commit trailer) and observe them fail for the right reason (no queue).
2. Implement the queue writer: `queue.json` with exactly the six keys, the workspace copy without `.git/`, facts, assertions and hidden results.
3. Implement the redactions of `plan.md` model cells and the `## Model Selection` section, and the omission of the attempt record, adapter output and commit bodies.
4. Write the queue entry at attempt finish in `run` and `import-recorded`.
5. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- REQ-30: for a comparison run whose double writes the requested model id into a `plan.md` `Model (Claude)` column, a `## Model Selection` line of the task `state.md` and a commit trailer, no file under `evaluation-queue/` contains a variant id, that model id or a `unit_id`.
- DM-9: every `queue.json` has exactly the keys `attempt_key`, `blinded_label`, `task_id`, `case`, `workflow`, `split`; no queue entry contains a `.git` directory, an `attempt.json` or adapter output; the redacted `plan.md` cells read `<redacted>`.
- REQ-30, REQ-38: a recorded import also produces a queue entry meeting the two criteria above.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (runs and imports with the scripted double; byte scans of the queue), smoke (guard re-pin)
- **Scenarios:**
  - Model id in three places → absent from every queue file, as are variant ids and unit ids.
  - Queue shape → six keys; no `.git`, attempt record or adapter output; redacted cells.
  - Recorded import → compliant queue entry.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; empty/null (no `## Model Selection` section, `plan.md` without model columns); boundary (header `Model` alone and `Model (Codex)`); permission boundaries (evaluator sees only blinded material).
