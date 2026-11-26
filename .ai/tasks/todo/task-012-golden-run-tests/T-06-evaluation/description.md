## Goal
Deliver independent evaluation — append-only human evaluation records, disputes, late defects, exclusions, the full DM-10 outcome table and the blinded evaluation queue — so that acceptance is decided only by the outcome table or a dispute resolution, and human evaluators see attempts only by attempt key and blinded label.

## Context
- type: composite
- children: T-06a, T-06b
- Dependencies: T-05 (every attempt kind an outcome row needs: cancelled, timed out, refused, orphaned, imported)
- Constraints: Python 3.11+ standard library and `git` only, run as `python3 -I`; strict and canonical JSON as defined in the specification; records are never rewritten; revision 1 is reserved for the automated outcome; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; every child re-pins the source guard; contract: `.ai/specs/012-golden-run-tests.md` (delivery part 6 — evaluation, queue, disputes, blinding; DM-9 queue, DM-10 outcome rules, DM-11 records).
- Reason: two independently testable components with their own criteria clusters — evaluation records with outcomes and disputes, and the blinded queue (S2 = 2, S5 = 2). Holdout reveal is reported, so it moves to the report safeguards (T-07b).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by an earlier subtask; writing under `tests/expected/`; authenticating evaluators beyond the stated threat model; editing criteria after results.

## Scope
- **In scope:** `evaluate` with `--verdict`, `--late-defect`, `--resolve-dispute`, `--exclude`; DM-11 records and ledger events; disputes; late-defect window; outcome recomputation rows 1–9; unit outcomes; queue entries with redaction for live and recorded attempts.
- **Out of scope:** reports, holdout reveal and contamination (T-07).
- **Target files:** `scripts/golden_evaluation.py`, `scripts/golden_runner.py`, `scripts/golden-eval.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
See children: T-06a (evaluation records, disputes and outcomes), T-06b (blinded evaluation queue).

## Acceptance Criteria
- Integration: after a comparison `run` and an `evaluate --verdict rejected` on an automatically accepted attempt, the attempt's queue entry is unchanged and still blinded, the dispute is open, and every earlier record and queue file keeps its SHA-256.
- Integration: after the resolver records `--resolve-dispute accepted`, the outcome recomputed from the records equals the unit outcome stored for that unit, and the ledger holds `evaluation-recorded`, `dispute-opened` and `dispute-resolved` in `seq` order.

## Test Plan
- **Level:** integration (executed by `/phase-composite-validation`)
- **Scenarios:**
  - Run → reject verdict → queue unchanged and blinded; dispute open; records immutable.
  - Resolve → recomputed outcome consistent; ledger events ordered.
- **Edge cases:** happy path; invalid state (open dispute); duplicate (records appended, never rewritten).
