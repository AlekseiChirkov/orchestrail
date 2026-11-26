## Goal
Deliver the isolation preflight with `scripts/golden_probe.py` and control-checked probes, so that a live launch starts only when hidden-material and network probes pass or the approved manifest accepts the matching weaker design, the executor never sees evaluator-only content, and every attempt record states `enforced` or `weakened`.

## Context
- Dependencies: T-04b (launch, workspace, helper home), T-04a (`experiment.json`), T-02c (hidden checks to run under the prefix)
- Constraints: Python 3.11+ standard library only, run as `python3 -I`; probe targets are the case's `hidden/` and `reference/`, every `cases_root`, the artifact root and `blinding.json`, a loopback listener opened by the runner and `network_probe_target` when set; the runner connects to each network target itself first (control); every process launch stays inside `scripts/golden_*.py`; tests use a test-only command prefix that denies the probe's reads and connections; tests extend `tests/golden-runs.py` and the double; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-20, REQ-21, Isolation, DM-3 hidden checks under the isolation prefix, DM-10 `isolation` field.
- Reason: isolation probing is a separate component with its own done-state (probe verdicts and weaker-design accounting) and criteria cluster.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; implementing a sandbox (only the probe contract and the weaker-design path); connecting to any non-loopback host in the suite.

## Scope
- **In scope:** `scripts/golden_probe.py --read <file>… --connect <host:port>…`; probe execution `prefix + [python3, -I, <helper home>/scripts/golden_probe.py, …]` in the workspace for `command-prefix`; `none` → both probes fail; pass rules (every read fails; every control-completed connection fails inside the prefix and `network_probe_target` is set; a target the control cannot reach fails the network probe); acceptance through `accepted_weaker_isolation`; exit 5 `isolation-unverified` before any adapter invocation; probe results in `experiment.json`; attempt `isolation` field with reason; hidden checks under the prefix; double recording the SHA-256 of every file under its cwd and `ORCHESTRAIL_HOME`.
- **Out of scope:** network or file isolation of the harness itself; report statements of weaker designs (T-07a renders them).
- **Target files:** `scripts/golden_probe.py`, `scripts/golden_runner.py`, `scripts/golden_semantics.py`, the test double under `tests/golden/`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` (including a test-only denying prefix and a loopback target) and observe them fail for the right reason (no probe, no isolation verdict).
2. Implement `scripts/golden_probe.py`: attempt each read and connection, report per-target results as JSON.
3. Implement probe target collection and the runner's loopback listener and control connections.
4. Implement the `none` and `command-prefix` mechanisms and the pass rules.
5. Implement weaker-design acceptance, exit 5 `isolation-unverified` with zero launches, probe results in `experiment.json` and the attempt `isolation` field (`enforced`/`weakened`, reason).
6. Run hidden checks under the isolation prefix when the mechanism is `command-prefix`.
7. Extend the test double to record the SHA-256 of every file under its cwd and under `ORCHESTRAIL_HOME`.
8. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-14 (REQ-20, REQ-21): for an approved regression `run` of each catalog pair with a double that records the SHA-256 of every file under its cwd and under `ORCHESTRAIL_HOME`, no recorded hash equals a non-empty file of the case's `hidden/` or `reference/` whose content does not also occur in the case's `project/`, and the helper home has no `tests/`, `.ai/` or `docs/` entry while it holds `scripts/log-step.sh`; with isolation `none` and no weaker design, `run` exits 5 with `isolation-unverified` and the ledger is empty; with a `command-prefix` test prefix that denies the probe's reads and connections and a reachable `network_probe_target`, or with `none` and both weaker-design flags, the attempt launches and its record states `enforced` or `weakened` accordingly.
- Isolation: with `command-prefix` and `network_probe_target` null, or with a target the control connection cannot reach, the network probe fails and `run` exits 5 unless `accepted_weaker_isolation.network` is true; probe results are stored in `experiment.json`.
- Hidden checks under `command-prefix` are executed through the prefix (the prefix observes each hidden-check command).
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (probe subprocesses, loopback listener, double on `PATH`), smoke (guard re-pin)
- **Scenarios:**
  - AC-14 → hash scan per catalog pair; helper-home contents; `none` → exit 5 with empty ledger; denying prefix → `enforced`; `none` with both flags → `weakened`.
  - Missing or unreachable network target → network probe fails → exit 5 unless accepted; results in `experiment.json`.
  - Prefix observes hidden-check commands.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; empty/null (`network_probe_target` null, `accepted_weaker_isolation` null); invalid state (unreachable control target); permission boundaries (reads of evaluator-only material denied).
