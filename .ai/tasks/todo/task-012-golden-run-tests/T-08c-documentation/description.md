## Goal
Write `docs/GOLDEN-RUNS.md` with every section the specification lists, index it once in `docs/README.md` and once in `scripts/README.md`, and close the promotion-and-documentation criterion, so that an owner can run the offline suite, write, approve and run manifests, evaluate, report, calculate and roll back from the manual alone.

## Context
- Dependencies: T-08b (template), T-08a (calculator example), T-07c (verdict rules and their tests), every earlier subtask (documented behaviour)
- Constraints: English; documentation follows `.ai/principles/coding.md → Documentation` and `→ Document placement`; the manual states behaviour, never planning identifiers or spec numbers; commands are documented as `python3 -I scripts/golden-eval.py <command>`; the provisioning command for `pytest` is the one the suite prints; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask because the suite file changes; contract: `.ai/specs/012-golden-run-tests.md` REQ-12, REQ-40, Contracts & Interfaces → Documentation and Promotion rule.
- Reason: the operating manual is one documentation component with one criteria cluster; it owns the promotion-and-documentation criterion because that criterion's last unmet clause is the manual.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in documentation, test names or code; deleting, skipping or weakening tests frozen by earlier subtasks — in particular the verdict tests of the promotion subtask; writing under `tests/expected/`; documents in the repository root; changing tool behaviour.

## Scope
- **In scope:** `docs/GOLDEN-RUNS.md` with sections for purpose and the three outcome kinds; running the offline suite and provisioning `pytest`; case catalog; writing and validating a manifest; approval; release regression runs; comparison experiments and the promotion rule; isolation limits and weaker designs; cancellation and resume; human evaluation and disputes; reviewing candidates and accepting expectations; reports and their limits; calculator; data retention and export; rollback (stop approving manifests; the tool never changes defaults); one index row in `docs/README.md`; one inventory row for `golden-eval.py` in `scripts/README.md`; suite tests for headings, rows and documented commands, plus the combined promotion-and-documentation scenario.
- **Out of scope:** tool behaviour changes; CI documentation.
- **Target files:** `docs/GOLDEN-RUNS.md`, `docs/README.md`, `scripts/README.md`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests in `tests/golden-runs.py` for the section headings, the two index rows, documented command names and the combined promotion-and-documentation scenario, and observe them fail for the right reason (manual absent).
2. Write `docs/GOLDEN-RUNS.md` with every listed section, using the shipped template, calculator example and exact commands.
3. Add one row naming `docs/GOLDEN-RUNS.md` to `docs/README.md` and one inventory row for `golden-eval.py` to `scripts/README.md`.
4. Cross-check every documented command and option against the command-line parser and correct the manual where they differ.
5. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-07 (REQ-12, REQ-40): for synthetic attempt sets, `report` yields `promote` for a set meeting every promotion condition; the same set with `lower(D)` equal to `−delta`, or with `upper(R)` equal to `r_max`, yields `do-not-promote`; one critical missed defect with an incomplete cost yields `do-not-promote`; one decision task, an incomplete cost alone, or a sealed holdout decision split yields `insufficient-data`; and `docs/GOLDEN-RUNS.md` contains every listed section heading while `docs/README.md` and `scripts/README.md` each contain exactly one line naming it.
- REQ-40: every `golden-eval.py` command and option named in `docs/GOLDEN-RUNS.md` is accepted by the command-line parser, and the manual contains no planning identifier (no subtask id, spec number, `.ai/` path, `REQ-` or `AC-` identifier outside quoted pipeline artifact examples).
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** smoke (heading, row and identifier checks over the documentation files), unit (the verdict matrix over synthetic attempt sets, reused from the promotion subtask's fixtures without modifying its tests), integration (documented commands parsed by `golden-eval.py`)
- **Scenarios:**
  - AC-07 → verdict matrix passes; every section heading present; exactly one line in each index.
  - Documented commands → each accepted by the parser; no planning identifiers in the manual.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; duplicate (index row appears exactly once); missing dependencies (a documented option the parser lacks).
