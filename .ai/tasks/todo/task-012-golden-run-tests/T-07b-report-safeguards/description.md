## Goal
Add the report safeguards — sealed holdout with an explicit `--reveal-holdout` journal event, contamination tracking across a manifest family, exclusion of private text, retention without deletion, and validation of records read by `report` — and complete the negative catalog, so that holdout metrics stay `sealed` until revealed, reused holdout tasks are excluded, and no report leaks prompts, outputs or environment values.

## Context
- Dependencies: T-07a (report builder)
- Constraints: Python 3.11+ standard library only, run as `python3 -I`; strict and canonical JSON as defined in the specification; the family journal `<artifact-root>/families/<experiment_family>.jsonl` is append-only; reports never contain prompts, model output text, conversation transcripts or environment variable values; no artifact is deleted automatically; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py` and the double; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-19 (N-07 and the ledger part of N-08), REQ-32, REQ-34, REQ-42, REQ-43, REQ-46, DM-9 family journal, DM-12.
- Reason: the safeguards form one component that constrains what a report may contain and reveal, with one criteria cluster; completing the negative catalog belongs here because its last corruption (N-07) is detected when `report` reads an invalid record.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; deleting any artifact; verdict logic (T-07c).

## Scope
- **In scope:** holdout metrics `sealed` by default; `--reveal-holdout` appending `holdout-revealed` with the configuration hash and holdout task ids and setting `holdout_revealed: true`; `contamination` for tasks revealed under another configuration hash in the same family, excluded from holdout metrics and decisions; privacy filtering of every report field and `report.md`; `retain_until` in every report; no deletion; `report` exiting 2 on an invalid attempt or evaluation record (for example `cost_usd: "0"` with `cost_source: absent`); the remaining negative-catalog rows and a completeness check over N-01–N-12.
- **Out of scope:** verdicts and decision-task selection (T-07c consumes the contamination list).
- **Target files:** `scripts/golden_report.py`, `scripts/golden-eval.py`, the test double under `tests/golden/`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` (experiments E1 and E2 in one family, a double whose result text and environment contain `SECRET-MARKER-7`, the negative-catalog completeness check) and observe them fail for the right reason.
2. Implement holdout sealing and `--reveal-holdout` with the family-journal event.
3. Implement contamination detection from the family journal and exclusion from holdout metrics.
4. Implement privacy filtering so that no prompt, model output, transcript or environment value reaches `report.json` or `report.md`.
5. Implement `retain_until` in every report and confirm that no code path deletes an artifact.
6. Implement record validation on read (exit 2) and add the N-07 and ledger-write N-08 rows to the negative-catalog table with a completeness check over N-01–N-12.
7. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-13 (REQ-19): for the references mutated as N-01–N-12 (record validation for N-07, the update and accept path for N-09), each yields exactly the check and reason named in the Edge Cases table and no outcome `independently-accepted`; the suite's negative-catalog table has exactly one row for each of N-01–N-12; N-07 makes the record writer exit 8 and `report` reading it exit 2.
- AC-23 (REQ-32, REQ-46): for experiment E1 with a holdout task, `report` without `--reveal-holdout` shows its holdout metrics `sealed`; after `--reveal-holdout` the family journal holds the event; E2 in the same family with a different configuration hash lists that task under `contamination` and excludes it from holdout metrics.
- AC-31 (REQ-42, REQ-43): for a double whose result text and environment contain the marker `SECRET-MARKER-7`, neither `report.json` nor `report.md` contains the marker, both contain `retain_until` equal to the start date plus `retention_days`, and every attempt directory still exists after `report`.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (experiments with the scripted double, family journals, report subprocesses), contract (report field filtering), smoke (guard re-pin)
- **Scenarios:**
  - AC-13 → twelve rows with exact results; completeness; N-07 writer exit 8 and reader exit 2.
  - AC-23 → sealed, revealed event, contamination in E2.
  - AC-31 → marker absent; `retain_until` value; attempt directories retained.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; duplicate (revealing twice appends two events, same task ids); invalid state (invalid record read by `report`); permission boundaries (private text never reported); missing dependencies (absent family journal → no contamination).
