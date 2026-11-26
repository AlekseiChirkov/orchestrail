## Goal
Deliver `golden-eval.py report` with complete DM-12 metrics, cost per accepted result through `summarize_outcomes`, sealed holdout and contamination tracking, privacy and retention guarantees, and the pre-registered promotion verdict, so that every report is deterministic apart from `generated_at`, labelled `kind: observed`, and every rate carries its numerator and denominator.

## Context
- type: composite
- children: T-07a, T-07b, T-07c
- Dependencies: T-06 (outcomes, records, queue), T-05a (attached usage, recorded attempts), T-03c (dry-run plan)
- Constraints: Python 3.11+ standard library only, run as `python3 -I`; strict and canonical JSON as defined in the specification; exact decimal or reduced `n/d` strings, never floats; `scripts/usage_telemetry_outcomes.py` (`summarize_outcomes`, `compare_outcome_groups`) is consumed read-only; the bootstrap index generator is SHA-256 based and seeded; reports carry no prompt, model output, transcript or environment value; no automatic deletion; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; every child re-pins the source guard; contract: `.ai/specs/012-golden-run-tests.md` (delivery part 7 and holdout from part 6; DM-11 mapping, DM-12, Promotion rule).
- Reason: three independently testable components with their own criteria clusters — metrics and cost, report safeguards (holdout, contamination, privacy, retention, record validation), and the promotion verdict (S2 = 3, S5 = 3).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; `scripts/usage_telemetry_outcomes.py` and every other spec 006 file (read only); any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by an earlier subtask; writing under `tests/expected/`; changing any default or adopting a variant.

## Scope
- **In scope:** `report --experiment DIR [--reveal-holdout]`, `report.json` and `report.md`, METRICS, DM-11 mapping to `summarize_outcomes`, acceptance intervals, holdout sealing and the family journal, contamination, privacy, retention, record validation on read, comparisons and verdicts.
- **Out of scope:** the calculator (T-08a); documentation (T-08c).
- **Target files:** `scripts/golden_report.py`, `scripts/golden-eval.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
See children: T-07a (report metrics and cost per accepted result), T-07b (holdout, contamination, privacy and retention), T-07c (promotion verdict).

## Acceptance Criteria
- Integration: for one comparison experiment produced by `run` with the scripted double, an `import-recorded`, an `attach-usage` and `evaluate` records, `report` exits 0, its per-variant `cost` objects equal a direct `summarize_outcomes` call over the DM-11 mapping, its `comparisons` element carries a verdict, and holdout metrics are `sealed`.
- Integration: running `report` twice on that experiment yields `report.json` files identical apart from `generated_at`, neither file contains the double's secret marker, and every attempt directory still exists.

## Test Plan
- **Level:** integration and contract (executed by `/phase-composite-validation`)
- **Scenarios:**
  - End-to-end experiment → report matches `summarize_outcomes`; verdict present; holdout sealed.
  - Double report → deterministic; private; nothing deleted.
- **Edge cases:** happy path; empty/null (unknown costs); permission boundaries (no private text in reports).
