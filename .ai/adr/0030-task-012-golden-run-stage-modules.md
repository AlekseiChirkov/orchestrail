# ADR-0030: Decisions for Task 012 — Golden-run regression tests and strategy evaluation

## Status

Provisional

## Date

2026-11-26

## Related Task

- Task: [task-012-golden-run-tests](../tasks/todo/task-012-golden-run-tests/state.md)
- Related pull request: not yet known
- Related files: `scripts/golden-eval.py`, `scripts/golden_*.py`, `tests/golden-runs.py`,
  `tests/golden/`, `tests/expected/`, `tests/fixtures/validator-runtime/source_guard.py`,
  `tests/fixtures/validator-runtime/source_guard_exceptions.json`

## Summary

Discovery chose the architecture of the golden-run framework before implementation: one
command-line dispatcher over stage modules that exchange canonical JSON documents on disk,
a standalone offline suite outside the contract validator, a source-guard re-pin in every
subtask, and outcome handling for normalization errors.

## Context

The specification asks for a model-free regression suite over whole pipeline runs and an
owner-authorized evaluation runner, built from the Python standard library, `git` and an
already installed `pytest` (spec 012 REQ-01, A-03, A-04). The contract validator's
inventory is frozen (ADR-0019 Decision 3), and the source guard binds reviewed exceptions to
a digest of every `.py` and `.sh` file under `tests/`
(`tests/fixtures/validator-runtime/source_guard.py:809-816`). Delivery is planned as 26
leaves executed as one sequential stack.

## Decisions

### Decision 1: Stage modules behind one dispatcher, exchanging documents on disk

**What was decided:**
`scripts/golden-eval.py` is a thin argument dispatcher. Each stage is one standard-library
module under `scripts/` (`golden_cases`, `golden_capture`, `golden_semantics`,
`golden_normalize`, `golden_manifest`, `golden_runner`, `golden_probe`,
`golden_evaluation`, `golden_report`, `golden_calculator`). Stages exchange canonical JSON
documents on disk (facts, assertions, projection, attempt records, ledger events) rather
than in-memory objects.

**Why:**
It is the layout the specification names, it follows the flat module pattern already used
by `scripts/usage_telemetry_outcomes.py` and `scripts/repo-set.py`, each stage can be tested
alone, and on-disk documents serve resume, recorded imports and blinding without a second
serialization path. Autonomous scoring: 21 against 15 and 14 (task state → Solution
Design → Autonomous Decision).

**Alternatives:**
A package `scripts/golden/` with an in-memory pipeline object (new pattern, second
serialization path, diverges from paths fixed by acceptance criteria); a single script
(several thousand lines edited by every subtask, stage tests need the whole program).

**Consequences:**
Ten modules plus a shared dispatcher and shared suite; every subtask edits the dispatcher
only to add its own subcommand. JSON shapes are kept consistent by one canonical-JSON helper
and strict loaders introduced first.

**Related files:**
- `scripts/golden-eval.py`
- `scripts/golden_*.py`

### Decision 2: Standalone offline suite and per-subtask source-guard re-pin

**What was decided:**
The suite is `python3 -I tests/golden-runs.py` on `unittest`, not registered in
`scripts/validate-contracts.sh`. Every subtask that adds or changes `.py`/`.sh` files under
`tests/` re-pins the source guard as its last step, following
`tests/fixtures/validator-runtime/README.md:9-28`.

**Why:**
The validator inventory is frozen (ADR-0019 Decision 3). The guard runs inside the
validator, so a single late re-pin would leave every earlier stacked branch failing the
validator.

**Alternatives:**
Registering a validator mode (rejected by ADR-0019 Decision 3); one re-pin at the stack tip
(earlier branches would not pass).

**Consequences:**
Each subtask carries a guard criterion; reviewers must check each re-pin's classification
of new call sites.

**Related files:**
- `tests/golden-runs.py`
- `tests/fixtures/validator-runtime/source_guard.py`
- `tests/fixtures/validator-runtime/source_guard_exceptions.json`

### Decision 3: A normalization error makes an attempt technically incomplete

**What was decided:**
A normalize step `error` (an exception, not a golden mismatch) yields the outcome
`technically-incomplete` and exit 8. A compare `failed` result never changes the outcome.

**Why:**
The specification's edge case N-08 and REQ-19 require every negative-catalog entry to yield
an outcome other than `independently-accepted`, and REQ-15 treats an unparsable source as
an error; DM-10's sentence that normalize statuses never change the outcome conflicts and
yields to the requirements.

**Alternatives:**
Leaving the outcome untouched by a normalization error (would accept a run whose projection
could not be built, violating REQ-19).

**Consequences:**
The DM-10 sentence must be amended through `/spec-sync` after delivery.

**Related files:**
- `scripts/golden_semantics.py`
- `scripts/golden_normalize.py`

## Questions and Answers

No external questions and answers were recorded during this task.

## Rejected Options

A package with an in-memory pipeline object; a single script; validator registration; a
single late source-guard re-pin.

## Implications for Future Work

New stages add a module and a subcommand rather than growing existing modules. Any change
under `tests/` re-pins the source guard in the same change. Expected results change only
through `check --update` and `accept-expected`.

## Verification

Not yet verified — decision recorded before implementation completed.

## References

- Task: `.ai/tasks/todo/task-012-golden-run-tests/`
- Pull request: not yet known
- Related documents: `.ai/specs/012-golden-run-tests.md`; ADR-0019; ADR-0020
