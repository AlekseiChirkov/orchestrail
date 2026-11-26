## Goal
Complete `check` with golden comparison, `--update` candidates and `golden-eval.py accept-expected`, and accept reviewed expected results for all five catalog pairs, so that each reference exits 0 with compare `passed`, mismatches and missing expectations exit 1 with a diff, and `tests/expected/` changes only through a reviewed, fully passing candidate.

## Context
- Dependencies: T-02b (projection), T-02d (assertion statuses and check outcome)
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; canonical JSON (`indent=2` for diffs) as defined in the specification; every process launch stays inside `scripts/golden_*.py`; compare never changes the outcome; initial expected results carry `origin: synthetic-reference` and are reviewed in this change; default artifact root `<source checkout>/output/golden` (ignored by `.gitignore`); tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-03, REQ-04, REQ-14, REQ-16, REQ-17, REQ-19 (N-09), DM-5, A-07.
- Reason: comparison, candidate writing and reviewed acceptance form one component around the expected-result store with one criteria cluster.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/` by any path other than `accept-expected`; a text-only edit of expected results.

## Scope
- **In scope:** the compare step (`golden-mismatch`, `missing-expected`, unified diff of canonical `indent=2` texts to `compare/diff.txt`, exit 1); `--update` candidate directories `<artifact-root>/candidates/<case>/<workflow>/<first 12 hex of projection_sha256>/` with `projection.json`, `diff.txt`, `changed-facts.json`, `candidate.json`; `accept-expected --candidate DIR --reason TEXT --reviewed-by NAME` with refusal of non-`passed` capture/extract/assert/evaluate and the DM-5 review record; expected results for the five pairs; a recording test double (`claude` executable placed first on `PATH` that appends `{argv, cwd, env_names, ORCHESTRAIL_HOME, ORCHESTRAIL_LOG_ROOT}` to a ledger file) used to prove `check` invokes no adapter.
- **Out of scope:** attempt-origin candidates (T-04b), scripted double behaviours (T-03c, T-04b, T-04c, T-05c).
- **Target files:** `scripts/golden-eval.py`, `scripts/golden_normalize.py`, `tests/expected/{flat/spec-run,flat/phase-pipeline,composite/spec-run,quick/phase-pipeline,bugfix/bugfix}/{projection.json,review.json}`, the test double under `tests/golden/` (path set by design), `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (missing compare, missing `accept-expected`, missing expected results).
2. Implement the compare step: load `tests/expected/<case>/<workflow>/projection.json`, compare canonical bytes, write the unified diff of the two `indent=2` texts to `compare/diff.txt`, set `failed` with `golden-mismatch` or `missing-expected`, contribute exit 1 without changing the outcome.
3. Implement `--update`: write the DM-5 candidate directory (diff against the current expected projection or an empty object, top-level changed keys, `candidate.json` with steps, origin `check` or `synthetic-reference`, source revision) and nothing under `tests/expected/`.
4. Implement `accept-expected`: refuse with exit 1 a candidate whose recorded capture, extract, assert or evaluate status is not `passed`; otherwise write `projection.json` and `review.json` (`projection_sha256`, `normalization_version`, 40-hex `source_revision`, `origin`, `reason`, `reviewed_by`, `reviewed_at`).
5. Create the recording test double and a suite helper that places it first on `PATH` and reads its ledger.
6. Build all five references, run `check --update`, review each candidate and accept it with origin `synthetic-reference` into `tests/expected/`.
7. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-01 (REQ-01, REQ-04, REQ-08): with `pytest` importable, `check` on the reference workspace and run-log store of each of the five catalog pairs exits 0 with outcome `independently-accepted` and compare `passed`, and the test double's ledger is empty.
- AC-03 (REQ-03, REQ-04, REQ-14, REQ-16): the `flat`/`spec-run` reference checked as built, rebuilt with another `--date-base`, with every date in `state.md` replaced, and from another absolute path yields four byte-identical projections; with one open test made to fail SA-12 is `failed`, compare is `failed`, `compare/diff.txt` is non-empty and the outcome is `rejected-by-criteria`; with `tests/expected/flat/spec-run/` absent compare is `failed` with `missing-expected` and exit 1; no projection gives two commits or two branches the same alias, and an absolute path outside the workspace in `target_files:` appears as `<EXTERNAL>/<basename>`; with `--update` the SHA-256 of every file under `tests/expected/` is unchanged while the candidate directory holds `projection.json`, `diff.txt`, `changed-facts.json` and `candidate.json`.
- AC-11 (REQ-17): a candidate whose `candidate.json` records assert `failed` makes `accept-expected` exit 1 with `tests/expected/` unchanged; a passing candidate makes it write `projection.json` and `review.json` whose `projection_sha256` matches the projection and whose `origin` equals the candidate's.
- REQ-19 (N-09): a corrupted projection offered through `--update` produces only a candidate, and `accept-expected` refuses that candidate when any of its capture, extract, assert or evaluate steps is not `passed`.
- A-07: each shipped `tests/expected/<case>/<workflow>/review.json` has `origin` `synthetic-reference` and a `projection_sha256` equal to the SHA-256 of the sibling `projection.json`.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (`check`, `--update`, `accept-expected` on built references with real `git` and `pytest`), unit (diff and candidate naming), smoke (guard re-pin)
- **Scenarios:**
  - AC-01 → five pairs exit 0, accepted, compare `passed`, empty double ledger.
  - AC-03 → four identical projections; failing open test; absent expected; alias and external-path checks; `--update` leaves `tests/expected/` hashes unchanged and writes four candidate files.
  - AC-11 → refused failing candidate; accepted passing candidate with matching hash and origin.
  - N-09 → candidate only; refusal of non-passing candidate.
  - Shipped review records → origin and hash consistent.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; empty/null (absent expected directory, diff against an empty object); duplicate (re-accepting an identical candidate); invalid state (candidate with a non-`passed` step); permission boundaries (no write path into `tests/expected/` other than acceptance).
