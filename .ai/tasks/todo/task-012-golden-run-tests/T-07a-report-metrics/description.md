## Goal
Deliver `golden-eval.py report` writing DM-12 `report.json` and `report.md` with every METRICS value per variant and split, cost per accepted result through `summarize_outcomes` with the DM-11 mapping, the blinding map and a deterministic bootstrap acceptance interval, so that the same experiment always yields byte-identical reports apart from `generated_at` and unknown usage is reported as incomplete, never as zero.

## Context
- Dependencies: T-06a (outcomes and records), T-06b (queue and blinded labels), T-05a (recorded attempts, attached usage), T-03c (dry-run plan for the measured-variant scenario)
- Constraints: Python 3.11+ standard library only, run as `python3 -I`; strict and canonical JSON as defined in the specification; numbers as exact decimal or reduced `n/d` strings; `summarize_outcomes` is called once per variant and split with `combined_cost` requested, imported read-only from `scripts/usage_telemetry_outcomes.py`; the bootstrap draws indices `int.from_bytes(sha256(f"{seed}:{b}:{i}".encode()).digest()[:8], "big") % n`; median, nearest-rank p90 and the `n < 5` marker follow the completed spec 006 export composition; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-06, REQ-09, REQ-30 (report mapping), REQ-33, REQ-34, DM-11 mapping, DM-12, Promotion rule (bootstrap).
- Reason: the report builder (metrics, cost and interval) is one component with one criteria cluster (correct, complete, deterministic numbers).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; `scripts/usage_telemetry_outcomes.py` (read only); any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; float arithmetic in reported values; holdout sealing, contamination and privacy filtering (T-07b); verdicts (T-07c).

## Scope
- **In scope:** `report --experiment DIR` (stored copies, attempts, records; output under `reports/<YYYYMMDDTHHMMSSZ>/`); METRICS (`planned`, `started`, `completed`, `pending`, `unit_outcomes`, `accepted` with denominator per `analysis.denominator` or `planned` for regression, `censored`, `first_attempt_success`, `missed_defects`, `calls`, `tokens`, `attempts_per_unit`, `fix_tasks`, `elapsed_ms` statistics, `worker_time_ms: null` with `not-observed`, `cost`, `acceptance_interval`); the DM-11 mapping (opportunities, attempts, one label per unit with a finished attempt, `as_of`, `verify_acceptance`); `measured`, `availability`, `blinding`, `isolation`, `weaker_designs`, `diagnostics`, `cost_basis`; `report.md` rendering of the same values.
- **Out of scope:** `--reveal-holdout`, contamination, privacy and retention checks, record validation on read (T-07b); `comparisons` verdicts (T-07c).
- **Target files:** `scripts/golden_report.py`, `scripts/golden-eval.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` (synthetic attempt sets plus run/import experiments with the scripted double) and observe them fail for the right reason (no `report`).
2. Implement `report` input loading through the experiment-directory opening for an existing directory and the output directory naming.
3. Implement METRICS per variant and split from unit and attempt records, including denominators, censoring, first-attempt success, missed-defect counts, `null` sums with `known_attempts`, attempts per unit, elapsed statistics and `worker_time_ms`.
4. Implement the DM-11 mapping and one `summarize_outcomes` call per variant and split with `combined_cost`.
5. Implement report-level fields: `measured` (a unit with a finished attempt), `availability`, `blinding` label → variant map, `isolation`, `weaker_designs`, `cost_basis`, `diagnostics`.
6. Implement the seeded bootstrap acceptance interval on per-task acceptance means (null with `no-analysis` when `analysis` is null).
7. Render `report.md` from the same values with exact decimals or reduced fractions.
8. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-04 (REQ-06, REQ-07): for an approved comparison manifest with variants A–F where D is `unavailable` and C is `recorded`, `run --dry-run` prints a plan listing the same task ids, case digests and source revision for every variant, C's units with `source: recorded`, no unit for D, and creates no experiment directory; after `import-recorded` of the `flat`/`spec-run` reference for one C unit and `report`, C has `measured: true` and D `measured: false`, and the ledger holds `reserved` and `finished` for that import; an import whose seed commit files differ from the case seed exits 2 with `incomparable`; an import whose `models_by_role` differ from C's role models exits 2 with `model-mismatch`.
- AC-05 (REQ-08, REQ-09): for an experiment with one unit each whose attempt has workflow-claimed success and a failed hidden test, is cancelled, is technically incomplete, and is accepted with unknown cost, `report` shows the first unit `rejected-by-criteria`, all four outcomes in `unit_outcomes`, `accepted` equal to `{count: 1, denominator: 4}` under `planned`, and `cost.coverage` `incomplete`.
- AC-21 (REQ-30): for a comparison experiment whose double writes the requested model id into a `plan.md` `Model (Claude)` column, a `## Model Selection` line of the task `state.md` and a commit trailer, no file under `evaluation-queue/` contains a variant id, that model id or a `unit_id`, `blinding.json` has mode 0600, experiment directories have mode 0700, and the report maps every blinded label to its variant.
- AC-24 (REQ-33, REQ-34): for one unit with attempts costing `0.4` and `0.6` whose last attempt is accepted, `cost_per_accepted` is `1` with coverage `complete` when both costs are complete; with no accepted unit it is `null` with `accepted_denominator_zero`; with a missing cost the record stores `null` with `cost_source: absent` and coverage is `incomplete`; usage attached with category `experimental_evaluation` appears in `experimental_evaluation_cost` and not in `observed_workload_cost`.
- AC-32 (REQ-09): for a fixed synthetic attempt set and seed, two `report` runs produce `report.json` files byte-identical apart from `generated_at`, every rate has a numerator and denominator, and `acceptance_interval` is non-null for comparison manifests and `null` with `no-analysis` for regression manifests.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** unit (metrics, mapping, bootstrap over synthetic records), integration (run, import and report subprocesses with the scripted double), contract (DM-12 shape and `summarize_outcomes` agreement), smoke (guard re-pin)
- **Scenarios:**
  - AC-04 → dry-run plan; import then report → `measured` flags; import refusals.
  - AC-05 → four outcomes, `{1, 4}`, `incomplete` coverage.
  - AC-21 → queue free of identifying values; modes; label map in the report.
  - AC-24 → `1`/`complete`; `null`/`accepted_denominator_zero`; `null`/`absent`/`incomplete`; experimental evaluation cost separation.
  - AC-32 → byte-identical reports apart from `generated_at`; numerators and denominators; interval presence per purpose.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; empty/null (zero accepted, unknown costs, null `analysis`); boundary (`n < 5` small-sample marker, single attempt); duplicate (two reports of one experiment); missing dependencies (variant without finished attempts).
