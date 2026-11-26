## Goal
Ship the four golden case fixtures with a strict loader and the offline suite harness, so that every `case.json` and defect map validates against the catalog and the suite runs offline with or without `pytest` (exit 3 and one diagnostic when it is missing).

## Context
- Dependencies: none
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; strict JSON (duplicate keys, `NaN`, `Infinity` and non-integer numbers rejected; decimals as strings; UTC millisecond timestamps; canonical JSON as defined in the specification); every process launch stays inside `scripts/golden_*.py`; seed and hidden tests need nothing beyond the standard library and `pytest`; this subtask creates the shared suite `tests/golden-runs.py` (`unittest`, behaviour-named) and re-pins the source guard; contract: `.ai/specs/012-golden-run-tests.md` REQ-01, REQ-35, REQ-55, DM-1, tree digest definition.
- Reason: the case catalog is the fixture base every later component reads; its validity (shape, catalog values, self-contained seeds, defect mapping, offline harness) is one done-state independent of how references are built.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time (the harness only prints the provisioning command); non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names, seed projects or documentation; writing under `tests/expected/`; reference overlays and histories (T-01b).

## Scope
- **In scope:** `tests/golden-runs.py` harness (discovery, `pytest` gate, diagnostic, exit codes); `scripts/golden_cases.py` (strict JSON loader, canonical JSON, tree/case/seed digests, `case.json` and `hidden/defects.json` validation, `parallel` rejection); seed projects, `case.json`, `hidden/tests/*.py` and `hidden/defects.json` for `flat`, `composite`, `quick`, `bugfix` per the DM-1 catalog.
- **Out of scope:** `reference/` overlays and histories, `build-reference`, the helper home (T-01b); any command-line interface.
- **Target files:** `tests/golden-runs.py`, `scripts/golden_cases.py`, `tests/golden/cases/{flat,composite,quick,bugfix}/case.json`, `tests/golden/cases/*/project/**`, `tests/golden/cases/*/hidden/**`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in a new `tests/golden-runs.py` and observe them fail for the right reason (missing module, missing case files).
2. Implement the suite harness in `tests/golden-runs.py`: mark tests that need `pytest`; when `import pytest` fails, run every other test, print exactly one diagnostic naming `pytest` and the provisioning command `python3 -m venv <dir> && <dir>/bin/pip install pytest`, invoke no installer, exit 3; otherwise exit 0/1 from `unittest`.
3. Implement `scripts/golden_cases.py`: strict JSON parsing, canonical JSON encoding, tree digest (byte-ordered POSIX paths; skip `.git/` and `__pycache__/` at any depth; follow a symlink only to a regular file inside the root; any other file type is an error), case digest and seed digest.
4. Add `case.json` and `hidden/defects.json` validation to `scripts/golden_cases.py`: `schema_version` 1 (unknown version rejected), every DM-1 field and type, case id equal to directory name, `commits` true exactly for `spec-run` entries, `parallel` absent or the integer 1 (otherwise reason `parallel-unsupported` naming case and case workflow), every hidden test in exactly one defect's `detected_by`.
5. Author the `flat` case: `textstats` seed with a specification of three numbered criteria (tokenize, counts, top), package skeleton and passing open tests, minimal `.ai/` derived from `templates/.ai/` declaring an unreleased package with no consumers, `.gitignore` containing `.ai/`, `CLAUDE.md`; `case.json` with workflows `spec-run` and `phase-pipeline` (`expect_flow` `full`), `dependency_chain` of the three modules, `published: true`.
6. Author the `composite` case: `money` seed stating integer cents as a cross-module invariant, criteria for `parse_amount`, `format_amount` and the round trip; `case.json` with workflow `spec-run` (`full`).
7. Author the `quick` case: `slug` seed with existing `slugify(text)` and the four `max_length` criteria; `allowed_paths` limited to `src/slug/__init__.py`, `tests/test_slug.py` and `.ai/**`; `case.json` with `phase-pipeline` (`quick`), `max_changed_files` 3.
8. Author the `bugfix` case: `pager` seed with floor-division `total_pages`, neighbour `page_slice`, `docs/defect-total-pages.md` numbering `AC-01`–`AC-03`, `pinned_tests` limited to inputs where floor and ceiling agree; `case.json` with workflow `bugfix` (`quick`, prompt `/bugfix "docs/defect-total-pages.md" --auto-mode`), `max_changed_files` 3.
9. Author `hidden/tests/*.py` and `hidden/defects.json` for every case with the catalog defects and severities (flat D-1 and D-2 important, D-3 optional; composite D-1 critical, D-2 important; quick D-1 critical, D-2 important; bugfix D-1 critical, D-2 important).
10. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-25 (REQ-01, REQ-35): with an interpreter where `import pytest` fails, `python3 -I tests/golden-runs.py` runs every test that does not need `pytest`, prints exactly one diagnostic naming `pytest` and the provisioning command, invokes no package installer, and exits 3.
- REQ-01, REQ-48 (DM-1): each of the four `case.json` files loads with `schema_version` 1, the case id equal to its directory, `test_command` `["python3","-m","pytest","-q","tests"]`, `test_globs` `["tests/**/*.py"]`, exactly the catalog workflows and `expect_flow` values (`flat`: `spec-run`→`full`, `phase-pipeline`→`full`; `composite`: `spec-run`→`full`; `quick`: `phase-pipeline`→`quick`; `bugfix`: `bugfix`→`quick`), `commits` true exactly for `spec-run` entries, `max_changed_files` 3 for `quick` and `bugfix` and null otherwise, and `published` true only for `flat`.
- REQ-01: with `pytest` importable, each seed's `test_command` exits 0 on the seed; no seed or hidden test imports a module outside the standard library, `pytest` and the seed package; each seed contains `.ai/memory/architecture.md` declaring the package unreleased with no consumers, `.ai/context/runbook.md` whose `test:` equals `test_command`, `.gitignore` containing `.ai/`, `CLAUDE.md` and the specification or defect report with numbered criteria.
- DM-1: every hidden test function appears in exactly one defect's `detected_by`, and each defect id and severity equals the catalog row.
- REQ-55: the loader rejects a copy of a case whose workflow declares `parallel` 2, 0 or `"1"` with reason `parallel-unsupported` naming the case and case workflow; every shipped workflow declares `parallel: 1` or omits it.
- Tree digest: the digest of one tree copied to two absolute paths is identical; adding a `.git/` or `__pycache__/` entry leaves it unchanged; a symlink pointing outside the root is an error.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** unit (loader, validation, digests), integration (suite and seed open tests through a real interpreter subprocess), smoke (guard re-pin)
- **Scenarios:**
  - AC-25 → suite subprocess with `pytest` made unimportable exits 3, stderr holds one `pytest` diagnostic with the provisioning command, the other tests ran, no installer process started.
  - Catalog shape → each loaded `case.json` equals the expected catalog values.
  - Seed self-containment → seed open tests exit 0; the import scan finds only allowed modules; required seed files exist.
  - Defect mapping → every hidden test maps to exactly one defect with the catalog severity.
  - `parallel` 2, 0, `"1"` → `parallel-unsupported` naming case and workflow; shipped cases pass.
  - Tree digest → equal across paths; ignored directories ignored; outside symlink rejected.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; empty/null (`parallel` absent, `max_changed_files` null); boundary (`parallel` 0, string `"1"`); duplicate (duplicate JSON key, hidden test in two defects); missing dependencies (`pytest` absent); invalid state (unknown `schema_version`).
