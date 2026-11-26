## Goal
Deliver `golden-eval.py calculate --scenario FILE` over DM-13 input with exact `Fraction` arithmetic, range corners and break-even analysis, so that the shipped example yields cheap expected costs `5`, `7` and `8` for `p` = `0.2`, `0.6`, `0.8`, break-even `p = 0.6`, the range `["5", "8"]`, and invalid probabilities exit 2 naming the strategy.

## Context
- Dependencies: T-01b (`golden-eval.py` entry point), T-01a (strict JSON loader)
- Constraints: Python 3.11+ standard library only, run as `python3 -I`; strict JSON and decimal strings as defined in the specification; exact `Fraction` arithmetic; output values as exact decimal strings or reduced `n/d` strings; at most 16 range parameters; a parameter appears only as probabilities or only as costs/acceptances; output labelled `kind: hypothetical`; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-11, DM-13, Calculator, NFR determinism.
- Reason: the calculator is an isolated pure component with one criteria cluster.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; float arithmetic; attempt limits or any observed data.

## Scope
- **In scope:** `scripts/golden_calculator.py` (input validation, fixed evaluation of `E`, `A`, `E/A`, range corners, break-even statuses `found`, `outside-domain`, `none`, `identical`, `not-applicable`); the `calculate` command; `tests/golden/calculator-example.json` (strong path cost 7; cheap path 4 plus repair 5 with probability `p`).
- **Out of scope:** observed reports (T-07); documentation (T-08c).
- **Target files:** `scripts/golden_calculator.py`, `scripts/golden-eval.py`, `tests/golden/calculator-example.json`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (no `calculate`).
2. Implement DM-13 input validation: shape, references to parameters, range limit, parameter role exclusivity, probabilities in [0,1] summing to exactly 1 per strategy (else exit 2 naming the strategy).
3. Implement fixed evaluation: `E` = Σ probability × sum of branch costs, `A` = Σ probability × acceptance, `E/A` or `null` when `A = 0`, exact decimal or reduced fraction output.
4. Implement range evaluation over every corner of the range box with min and max per quantity.
5. Implement break-even: domain from the range or [0,1]; `not-applicable` when acceptances differ at a domain end; affine difference `a + b·x` with `identical`, `none`, `found` or `outside-domain`.
6. Add `calculate` to `scripts/golden-eval.py` and ship `tests/golden/calculator-example.json`.
7. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-06 (REQ-11): for `tests/golden/calculator-example.json`, `calculate` with `p` = `0.2`, `0.6` and `0.8` yields cheap expected costs `5`, `7` and `8` and strong cost `7`, break-even `{parameter: "p", value: "0.6", status: "found"}`, and `kind: hypothetical` in every output; with `p` as range `{low: 0.2, high: 0.8}` the cheap range is `["5", "8"]`; an input whose branch probabilities sum to `0.9` exits 2.
- Calculator rules: differing acceptances at a domain end yield break-even status `not-applicable`; 17 range parameters exit 2; a parameter used both as a probability and as a cost exits 2; a value without a finite decimal form is printed as a reduced `n/d` string.
- Determinism: two `calculate` runs on the same input produce byte-identical output.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** unit (evaluation, ranges, break-even over synthetic inputs), contract (`calculate` JSON output and exit codes), smoke (guard re-pin)
- **Scenarios:**
  - AC-06 → three fixed values, break-even, range, invalid sum.
  - `not-applicable`, range limit, role conflict, `n/d` output.
  - Two runs → identical bytes.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; boundary (probabilities 0 and 1, exactly 16 range parameters, `A = 0`); invalid state (probabilities outside [0,1]); empty/null (`break_even: null`).
