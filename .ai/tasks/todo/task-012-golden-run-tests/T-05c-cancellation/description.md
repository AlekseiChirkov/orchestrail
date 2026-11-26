## Goal
Handle SIGINT/SIGTERM and the per-attempt wall limit, so that the active adapter process group receives SIGTERM and, after `termination_grace_seconds`, SIGKILL; a signalled run captures the workspace, records `cancelled`, launches nothing further and exits 7; a timed-out attempt is `stopped-by-policy` `timeout` and the next unit continues.

## Context
- Dependencies: T-04b (process-group launch, capture, attempt record), T-05b (exit 6 aggregation and refusals)
- Constraints: Python 3.11+ standard library only, run as `python3 -I`; signals are sent to the adapter's process group; every process launch and signal stays inside `scripts/golden_*.py`; tests use short limits with generous margins and assert ordering, never durations; tests extend `tests/golden-runs.py` and the double; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-26, REQ-45, DM-10 rows 2 and 3.
- Reason: termination handling (external signal or wall limit) is one component with one criteria cluster.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; runtime targets asserted by tests; signalling any process outside the adapter's group.

## Scope
- **In scope:** signal handlers that stop scheduling; SIGTERM to the process group, SIGKILL after the grace period; capture after termination; `cancelled` outcome and `finished` event; exit 7; per-attempt timeout with the same termination, `stopped-by-policy` `timeout` and continuation; double behaviours to sleep, ignore SIGTERM and record received signals.
- **Out of scope:** orphan recovery after the runner itself is killed (T-05d).
- **Target files:** `scripts/golden_runner.py`, the test double under `tests/golden/`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (no signal handling, no timeout).
2. Extend the test double to sleep, optionally ignore SIGTERM, and record each received signal to a file.
3. Implement runner signal handling: stop scheduling, SIGTERM to the active process group, SIGKILL after `termination_grace_seconds`, capture, outcome `cancelled`, `finished`, exit 7.
4. Implement the per-attempt timeout with the same termination path, outcome `stopped-by-policy` `timeout`, and continuation with the next unit.
5. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-17 (REQ-26, REQ-45): with a double that sleeps and ignores SIGTERM, when the runner receives SIGTERM, the double's process group receives SIGTERM and, after the grace period, SIGKILL; the attempt is `cancelled`; no further unit launches; `run` exits 7; with a wall limit shorter than the double's sleep, the attempt is `stopped-by-policy` `timeout`, the next unit launches, and `run` exits 6.
- REQ-26: SIGINT to the runner produces the same sequence and exit 7, and the cancelled attempt's capture exists with a `finished` ledger event.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (real processes and signals with the scripted double), smoke (guard re-pin)
- **Scenarios:**
  - AC-17 → recorded SIGTERM then SIGKILL; `cancelled`; no further launch; exit 7; timeout → `timeout`, next unit launched, exit 6.
  - SIGINT → same outcome and exit; capture and `finished` present.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; concurrent operations (signal while the adapter starts); boundary (grace period elapses); invalid state (adapter ignores SIGTERM).
