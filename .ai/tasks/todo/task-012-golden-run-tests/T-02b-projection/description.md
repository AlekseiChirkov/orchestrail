## Goal
Normalize facts into the DM-4 semantic projection under rules NR-1–NR-4 (normalization version 1), so that the `flat`/`spec-run` reference yields byte-identical `projection.json` across date bases, rewritten state dates and absolute locations, with distinct aliases for distinct commits and branches.

## Context
- Dependencies: T-02a (facts and `check` step record)
- Constraints: Python 3.11+ standard library and `git` only, run as `python3 -I`; canonical JSON as defined in the specification; every process launch stays inside `scripts/golden_*.py`; free text is excluded after extraction; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-14, DM-4, NR-1–NR-4.
- Reason: the projection is a pure transform of facts with its own done-state (field set, ordering, aliasing, determinism), testable without assertions or comparison.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; comparison and candidates (T-02e).

## Scope
- **In scope:** `scripts/golden_normalize.py` building every DM-4 field from facts; NR-1 paths, NR-2 commit aliases from `git rev-list --all --topo-order --reverse` (full or abbreviated ≥ 7 hex ids that resolve to exactly one captured commit), NR-3 branch aliases, NR-4 volatile values; `normalization_version` 1; the normalize step in `check` writing `projection.json`; normalize `error` when normalization raises.
- **Out of scope:** compare, `diff.txt`, candidates, expected results (T-02e); assertion statuses (T-02d).
- **Target files:** `scripts/golden_normalize.py`, `scripts/golden-eval.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (missing projection).
2. Implement the DM-4 field builders in `scripts/golden_normalize.py`: `case`, `workflow`, `flow`, `branch_model`, `phases` (exactly `discovery`, `execution`, `validation`), sorted `leaves` and `composites`, `contract_check`, `issues`, `fix_tasks`, `changed_paths`, `open_tests`, `stops`, `quick`.
3. Implement NR-1: workspace-absolute paths become workspace-relative POSIX; paths outside become `<EXTERNAL>/<basename>`.
4. Implement NR-2 commit aliases `<C1>`, `<C2>`, … and replacement of resolvable full or abbreviated ids; the seed commit gets type `seed`; commit types from the subject grammar.
5. Implement NR-3 branch aliases: the seed branch keeps its name, other branches become `<B1>`, `<B2>`, … in alias order of their tip commits, ties by name.
6. Implement NR-4 and free-text exclusion; encode canonical JSON with `normalization_version` 1; wire the normalize step into `check` (status `passed`, or `error` with exit 8 when normalization raises).
7. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- REQ-14: the `flat`/`spec-run` reference checked as built, rebuilt with another `--date-base`, with every date in its task `state.md` replaced, and copied to another absolute path yields four byte-identical `projection.json` files, each with `normalization_version` 1.
- REQ-14 (NR-2, NR-3): in every reference projection no two commits share an alias and no two branches share an alias; the seed branch keeps its name and the seed commit has type `seed`.
- NR-1: an absolute path outside the workspace in a leaf's `target_files:` appears as `<EXTERNAL>/<basename>`; an absolute path inside appears workspace-relative.
- DM-4: every reference projection has exactly the DM-4 top-level fields, `phases` has exactly the keys `discovery`, `execution` and `validation`, `leaves` and `composites` are sorted by id, `quick` is null for `full` flows, and no notes, subjects or issue text occur in it.
- REQ-19 (N-08, normalization part): when normalization raises on a mutated fact set, the normalize step is `error` and `check` exits 8.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** unit (field builders, NR rules on synthetic facts), integration (`check` on built references), smoke (guard re-pin)
- **Scenarios:**
  - Four variants of `flat`/`spec-run` → byte-identical projections.
  - Alias uniqueness → no duplicate commit or branch alias in any reference.
  - External and internal absolute paths → `<EXTERNAL>/<basename>` and relative path.
  - Field set and ordering → exact keys; sorted lists; no free text.
  - Raising normalization → normalize `error`, exit 8.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; boundary (7-hex abbreviated id, ambiguous abbreviation left unchanged); empty/null (`quick` null, no composites); duplicate (two branches at one tip ordered by name).
