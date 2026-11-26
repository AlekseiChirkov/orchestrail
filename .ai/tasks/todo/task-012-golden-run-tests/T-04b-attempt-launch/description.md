## Goal
Launch each reserved attempt of an `executable` variant once, in a fresh no-remote workspace with the helper home and allowlisted child environment, with the argv expanded from the approved declaration, then capture, evaluate and record it, so that the test double sees exactly the declared invocation, a reported model mismatch stops the variant, and unknown usage stays `null`.

## Context
- Dependencies: T-04a (experiment directory, ledger), T-03c (plan, argv expansion, preflight), T-02e (capture → compare pipeline, test double), T-01b (seed commit and helper home)
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; strict and canonical JSON as defined in the specification; workspace `tempfile.mkdtemp(prefix="orchestrail-golden-")` under the system temporary directory with sibling attempt log root and helper home, all removed after capture; only variable names of the child environment are recorded; the adapter runs in its own process group; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py` and the double; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-02, REQ-03, REQ-13 (mismatch part), REQ-24 (reservation order), REQ-29, REQ-34, REQ-36, DM-8 result mapping, DM-10 record, Run sequence step 4, Workspace and child environment, exit-code aggregation.
- Reason: attempt launch is one component — from reservation to `finished` — with one criteria cluster (correct invocation, capture and attempt record).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; recording environment values; any git remote or `--allow-pr`; limits, signals and timeout (T-05); isolation probes (T-04c); switch application (T-04d); evaluation queue (T-06b).

## Scope
- **In scope:** workspace creation with the deterministic seed commit and no remote; attempt log root; helper home; child environment allowlist with `ORCHESTRAIL_HOME` and `ORCHESTRAIL_LOG_ROOT`; `reserved` (fsync) → launch in a new process group → `launched` → wait; result parsing through the declaration's `result` mapping; model identity check (`stopped-by-policy` `model-mismatch`, no further launch of that variant); usage (`cost_usd`, `cost_source` `adapter-reported` or `absent`, `coverage`, `calls`, `tokens`, `null` when unknown); attempt-record validation (a record with `cost_source: absent` and non-null `cost_usd` is rejected, writer exit 8); capture → compare on the attempt with attempt-origin candidates under `--update`; `attempt.json`; `finished`; temporary-directory removal; exit-code aggregation (highest of 1, 6, 7, 8); scripted test double (files, commits, log events, JSON output, exit code, sleep).
- **Out of scope:** policy refusals, cancellation, timeout, orphan handling (T-05); isolation fields beyond `enforced` defaults (T-04c).
- **Target files:** `scripts/golden_runner.py`, `scripts/golden_capture.py`, `scripts/golden-eval.py`, the test double under `tests/golden/`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (no launch path).
2. Extend the test double to apply a scripted result (write files, make commits, emit log events through the helper home, print JSON output, exit with a code, sleep) and to record `{argv, cwd, env_names, ORCHESTRAIL_HOME, ORCHESTRAIL_LOG_ROOT}`.
3. Implement attempt directories: workspace with the seed commit and no remote, sibling attempt log root and helper home.
4. Implement the child environment from the allowlist, the adapter's `env_passthrough`, `ORCHESTRAIL_HOME` and `ORCHESTRAIL_LOG_ROOT`; record names only.
5. Implement reservation and launch: append and fsync `reserved`, start the adapter in a new process group in the workspace with the expanded argv, append `launched`, wait for exit.
6. Implement result handling: parse the JSON result through the declaration mapping; unparsable output or failure to start → `technically-incomplete`; reported model different from the requested id → `stopped-by-policy` `model-mismatch` and no further launch of that variant.
7. Implement usage storage and attempt-record validation per REQ-34 and DM-10.
8. Run capture → compare on the finished workspace, write `attempt.json`, append `finished`, remove the three temporary directories; under `--update` write candidates with origin `attempt:<experiment_id>/<attempt_key>`.
9. Implement exit-code aggregation after execution starts.
10. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-08 (REQ-02): for an approved regression manifest for `flat`/`spec-run` with model `test-model-1`, effort `high`, permission mode `dontAsk`, allowed tools `["Read","Edit"]`, no disallowed tools and per-attempt cap `0.5`, `run` leaves exactly one double ledger entry whose argv equals the DM-8 template expansion with those values and without the `--disallowedTools` pair, whose cwd is the workspace, whose `ORCHESTRAIL_HOME` and `ORCHESTRAIL_LOG_ROOT` are the attempt's helper home and log root, and whose env names are a subset of the allowlist.
- AC-09 (REQ-13): with model `sonnet`, `run` exits 5 and the ledger is empty; with the double reporting model `other-model` and the declaration's `model` field mapped, the attempt is `stopped-by-policy` with `model-mismatch`, no later unit of that variant launches, and `run` exits 6.
- AC-26 (REQ-36): for each catalog pair's reference build and a `run` attempt, `git remote` in the captured workspace prints nothing, and no shipped case prompt contains `--allow-pr` or `--repo`.
- REQ-24, REQ-29: with a double that exits 1 with no output, the ledger shows `reserved` before `launched`, the attempt is `technically-incomplete`, it counts as one reserved attempt, and no automatic relaunch occurs.
- REQ-34: an adapter result without a cost stores `cost_usd: null` with `cost_source: absent` and coverage other than `complete`; an attempt record with `cost_usd: "0"` and `cost_source: absent` is rejected by the writer, which exits 8.
- REQ-03, REQ-29: an approved run of `flat`/`spec-run` with the double replaying the reference yields an `attempt.json` whose steps `launch` through `compare` are `passed`, outcome `independently-accepted`, `execution_source: live`, and the workspace, log root and helper home temporary directories no longer exist after capture.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (double on `PATH`, real `git`, real processes), unit (result mapping, record validation), smoke (guard re-pin)
- **Scenarios:**
  - AC-08 → one ledger entry with exact argv, cwd, homes and allowlisted names.
  - AC-09 → alias exit 5 with empty ledger; reported `other-model` → `model-mismatch`, variant stopped, exit 6.
  - AC-26 → no remote in reference and attempt captures; prompts free of `--allow-pr` and `--repo`.
  - Silent failing double → event order, `technically-incomplete`, counted, no relaunch.
  - Usage → `null`/`absent`; invalid record → exit 8.
  - Replaying double → passed steps, accepted, temporary directories removed.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; empty/null (no cost, no output); invalid state (model mismatch, `absent` with a cost); duplicate (no automatic relaunch); missing dependencies (adapter fails to start); permission boundaries (environment values never recorded).
