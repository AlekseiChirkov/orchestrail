## Goal
Compute the pre-registered promotion verdict in every comparison report — decision tasks, paired quality difference `D`, cost ratio `R`, seeded paired-cluster bootstrap intervals with Bonferroni or holdout multiplicity, and the four ordered verdict rules — so that each candidate gets exactly the verdict of the first matching rule and the verdict stays advisory.

## Context
- Dependencies: T-07a (metrics, bootstrap generator), T-07b (sealed holdout, contamination), T-03a (role-key validation)
- Constraints: Python 3.11+ standard library only, run as `python3 -I`; exact `Fraction` arithmetic with exact decimal or reduced `n/d` output; bootstrap indices from the SHA-256 generator with `analysis.seed`; `α` = 1 − `confidence`, divided under `bonferroni` by the number of non-baseline variants with availability `executable` or `recorded`; interval bounds at sorted indices `floor(α/2 · B)` and `ceil((1 − α/2) · B) − 1`; the tool changes no default; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-12, REQ-53, Promotion rule, DM-12 `comparisons`.
- Reason: the verdict engine is one statistical component with one criteria cluster (which verdict a comparison yields and why).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; changing defaults or adopting a variant; float arithmetic.

## Scope
- **In scope:** decision tasks (decision split minus contamination; under `holdout` multiplicity only `selected_candidate`); `a(t,v)` with `planned` or `completed-with-censoring` denominators; `D`, `R` with summed known cost of started units and accepted counts; bootstrap `D_b`, `R_b`; `α` and interval bounds; verdict rules (`do-not-promote` for a critical missed defect or an SA-05 failure in any candidate attempt; `insufficient-data` for a sealed holdout decision split, fewer than two decision tasks with units of both variants, an undefined `R_b`, incomplete cost coverage, an unknown actual model, an open dispute, or null `analysis`; `promote` when `lower(D) > −delta` and `upper(R) < r_max`; `do-not-promote` otherwise); `comparisons` entries with `candidate`, `baseline`, `decision_split`, `quality_diff`, `cost_ratio`, `confidence_adjusted`, `hard_constraints`, `verdict`, `reasons`.
- **Out of scope:** documentation of the rule (T-08c).
- **Target files:** `scripts/golden_report.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` (synthetic attempt sets for each verdict rule) and observe them fail for the right reason (no `comparisons`).
2. Implement decision-task selection and `a(t,v)`, `D` and `R` with both denominator modes.
3. Implement the bootstrap of `D_b` and `R_b`, `α` with Bonferroni and holdout multiplicity, and the interval bounds.
4. Implement the four ordered verdict rules with hard constraints, reasons and the `comparisons` entries.
5. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-41 (REQ-53): comparison manifests whose variant lacks the `validator` role key or adds a `planner` key make `validate-manifest` exit 2 naming the variant; for a valid comparison yielding `promote`, `report.json` has `kind: "observed"`, the manifest's `experiment_id` and a `comparisons` element with `candidate`, `baseline` and `verdict`, while the manifest's variants carry `adapter` and `roles.<key>.model`/`effort` for `arbiter`, `implementer` and `validator`.
- REQ-12 (verdict matrix): a synthetic set meeting every promotion condition yields `promote`; the same set with `lower(D)` equal to `−delta`, or with `upper(R)` equal to `r_max`, yields `do-not-promote`; one critical missed defect together with an incomplete cost yields `do-not-promote`; one decision task, an incomplete cost alone, or a sealed holdout decision split yields `insufficient-data`; zero accepted units of a variant yields `insufficient-data`.
- Bootstrap: for a fixed seed the interval bounds are identical across two reports and equal the values at indices `floor(α/2 · B)` and `ceil((1 − α/2) · B) − 1` of the sorted resamples; under `bonferroni` with two non-baseline executable or recorded variants `α` is halved.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** unit (verdict rules, bootstrap and interval arithmetic over synthetic sets), contract (`comparisons` shape in `report.json`), smoke (guard re-pin)
- **Scenarios:**
  - AC-41 → role-key rejections; promote report shape and manifest role fields.
  - Verdict matrix → `promote`; two boundary `do-not-promote`; hard constraint first; four `insufficient-data` cases.
  - Bootstrap → repeatable bounds at the specified indices; Bonferroni halving.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; boundary (`lower(D)` = `−delta`, `upper(R)` = `r_max`); empty/null (zero accepted, null `analysis`); invalid state (open dispute, unknown actual model); missing dependencies (one decision task).
