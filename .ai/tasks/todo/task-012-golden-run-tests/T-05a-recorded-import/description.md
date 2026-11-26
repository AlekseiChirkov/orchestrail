## Goal
Deliver `golden-eval.py import-recorded` and `golden-eval.py attach-usage`, so that a workspace produced outside the runner is captured and evaluated exactly like a live attempt and labelled `execution_source: recorded`, incomparable seeds and mismatched role models are refused with exit 2, parallel cases are rejected by every command that reads them, and attached usage sets `cost_source: attached`.

## Context
- Dependencies: T-04a (experiment directory, ledger), T-04b (attempt record, capture → compare on an attempt), T-03a (manifest validation), T-01a (`parallel` rejection in the case loader)
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; strict JSON and decimal strings as defined in the specification; imports perform `run` step 1 and the directory opening except that `execution_enabled` may be false and cost limits may be null when no variant is `executable`; an import applies no spend limit but counts toward `max_attempts` and `max_attempts_per_unit`; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-07, REQ-34, REQ-38, REQ-55, Recorded imports, DM-2 (`seed_context`), Command-line interfaces (`import-recorded`, `attach-usage`).
- Reason: recorded evidence intake — workspaces and usage produced outside the runner — is one component with one criteria cluster (faithful, labelled intake with refusals).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; computing prices or token valuations; launching an adapter for a recorded unit.

## Scope
- **In scope:** `import-recorded --manifest FILE --unit U --workspace DIR --metadata FILE [--run-log DIR] [--artifact-root DIR]` (unit of a `recorded` variant else exit 2; metadata validation; `models_by_role` non-empty, not an alias and equal to the variant's role models else exit 2 `model-mismatch`; seed commit tracked files versus seed project outside `.ai/` else exit 2 `incomparable`; `reserved` with `{source: "recorded"}` and `finished`; limit counting with exit 6; capture copy of workspace and run log; extract → compare; `execution_source: recorded`; `seed_context: "unverified"`; usage from metadata with `null` when absent); `attach-usage --experiment DIR --attempt KEY --usage FILE` (usage document validation, `cost_source: attached`, coverage and category, `usage-attached` event); `parallel-unsupported` rejection for a manifest-named case in `import-recorded` and the cross-command check.
- **Out of scope:** reports using attached usage (T-07a); evaluation queue entries for imports (T-06b).
- **Target files:** `scripts/golden_runner.py`, `scripts/golden_capture.py`, `scripts/golden-eval.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (missing commands).
2. Implement `import-recorded` validation: manifest stage 1 with the relaxed rules, directory opening, recorded-variant membership, metadata shape, `models_by_role` checks, `parallel-unsupported` before any directory is created.
3. Implement the comparability check (`incomparable`) and `seed_context: "unverified"`.
4. Implement the import record: `reserved` (`source: recorded`) and `finished` events, limit counting (exit 6), capture of the given workspace and run log, extract → compare, `attempt.json` with `execution_source: recorded` and usage from metadata.
5. Implement `attach-usage`: validate `{category, cost_usd, coverage, tokens, source, source_sha256}`, update the attempt's usage with `cost_source: attached`, append `usage-attached`.
6. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-28 (REQ-38): the `flat`/`spec-run` reference imported for a `recorded` variant yields an attempt record with `execution_source: recorded`, an outcome equal to the `check` outcome of the same workspace, and an empty test-double ledger.
- AC-46 (REQ-55): for copies of the `composite` case whose `spec-run` workflow declares `parallel: 2`, `parallel: 0` and `parallel: "1"`, `check`, `build-reference`, `validate-manifest` (manifest task naming that case), `run` (approved runnable regression manifest naming it, with the test double) and `import-recorded` (into a `recorded` variant of a manifest naming it) each exit 2 with reason `parallel-unsupported` naming the case workflow, no workspace or experiment directory is created, and the double's ledger is empty; the shipped cases all declare `parallel: 1` or omit it.
- REQ-07: an import whose seed commit files differ from the case seed exits 2 with `incomparable`; an import whose `models_by_role` differ from the variant's role models exits 2 with `model-mismatch`; an import for a unit of a non-`recorded` variant exits 2.
- Recorded imports: the import appends exactly `reserved` (details `{source: "recorded"}`) and `finished`, records `seed_context: "unverified"`, and an import beyond `max_attempts_per_unit` exits 6.
- REQ-34: metadata with `cost_usd: null` stores `null` with `cost_source: absent`; after `attach-usage` with category `experimental_evaluation` the attempt usage has `cost_source: attached` and the ledger holds `usage-attached`.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (built references imported into temporary experiment directories; every command run as a subprocess), contract (exit codes and record fields), smoke (guard re-pin)
- **Scenarios:**
  - AC-28 → recorded attempt; outcome equals `check`; empty ledger.
  - AC-46 → five commands × three `parallel` values → exit 2 naming the workflow; nothing created; empty ledger; shipped cases compliant.
  - Refusals → `incomparable`, `model-mismatch`, non-recorded unit.
  - Import events, `seed_context`, per-unit limit → exit 6.
  - Usage → `null`/`absent`; attached usage and event.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; empty/null (null cost, null tokens); boundary (import at exactly the per-unit limit); duplicate (second import of the same unit); invalid state (seed from another project); missing dependencies (no experiment directory for `attach-usage` → exit 2).
