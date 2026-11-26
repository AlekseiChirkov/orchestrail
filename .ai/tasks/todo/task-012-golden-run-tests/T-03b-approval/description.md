## Goal
Deliver `golden-eval.py approve` (interactive terminal and typed 12-hex confirmation only) and the first two stages of `run` plus the `tests/run-golden.sh` wrapper, so that `run` exits 2 for an invalid manifest or owner policy file and 4 for any missing, non-runnable, disabled, unreadable or mismatched approval, before any workspace or adapter invocation.

## Context
- Dependencies: T-03a (manifest validation, configuration hash, policy entry validation), T-02e (test double for the empty-ledger checks)
- Constraints: Python 3.11+ standard library and `git` only, run as `python3 -I`; strict JSON as defined in the specification; approval reads the confirmation only when standard input and standard output are terminals; `tests/run-golden.sh` uses `set -uo pipefail` and a header comment (contract, usage, exit codes); every process launch stays inside `scripts/golden_*.py`; tests use the standard `pty` module for terminal scenarios and extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-05, REQ-10, REQ-22, REQ-23, REQ-54, DM-7, Run sequence step 1, Command-line interfaces (`approve`, `run`, wrapper).
- Reason: approval and authorization form the owner-consent component with one done-state (an approval record bound to one configuration hash and a gate that honours it).

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; authenticating approvers beyond the terminal requirement; preflight, lock and launch (T-03c, T-04).

## Scope
- **In scope:** `approve --manifest FILE --approved-by NAME --out FILE` (prints the configuration hash, reads the confirmation, writes DM-7 with `uuid4` id, timestamp, scope `{max_attempts, max_cost_usd}` and confirmation; exit 4 without writing otherwise); `run` stage 1 (argument parsing, manifest validity, owner policy entries → exit 2) and stage 2 (no manifest, not runnable, `execution_enabled: false`, approval null/missing/unreadable/invalid, `approval-mismatch` → exit 4); `tests/run-golden.sh <case> <workflow> [options]`.
- **Out of scope:** preflight (T-03c); experiment directory and lock (T-04a).
- **Target files:** `scripts/golden_manifest.py`, `scripts/golden-eval.py`, `tests/run-golden.sh`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (missing `approve`, missing `run` gate, missing wrapper).
2. Implement `approve`: refuse with exit 4 unless both standard streams are terminals; print the configuration hash; compare the typed confirmation with its first 12 hex characters; write the DM-7 record only on equality.
3. Implement `run` stage 1: parse arguments, validate the manifest and read owner policy entries, exit 2 with the reason (`policy-file-invalid` naming the entry).
4. Implement `run` stage 2: exit 4 for a missing `--manifest`, a non-runnable manifest, `execution_enabled: false`, an approval that is null, missing, unreadable or invalid, and `approval-mismatch` when the configuration hash differs from the record's `config_sha256`.
5. Create `tests/run-golden.sh`: header comment, `set -uo pipefail`, run `python3 -I scripts/golden-eval.py run --case <case> --workflow <workflow> [options]` from the source checkout, return its exit code, exit 4 without `--manifest`.
6. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-15 (REQ-22, REQ-23): with an approved manifest, changing one limit value after approval makes `run` exit 4 with `approval-mismatch` and the test double's ledger stays empty; `approve` with standard input from a pipe, or through a pseudo-terminal with a wrong 12-character confirmation, exits 4 and writes no file; with the correct confirmation it writes a DM-7 record carrying the current configuration hash.
- AC-44 (REQ-54): a policy entry that is a directory, an unreadable file, or a file whose content is not valid JSON (including one with a duplicate key) makes `validate-manifest --print-current` and `run` each exit 2 with reason `policy-file-invalid` naming the entry, the test double's ledger is empty, and the digest is not computed as `absent`.
- REQ-05, REQ-10: `run` without `--manifest`, with a non-runnable manifest, with `execution_enabled: false`, and with a missing approval file each exit 4, create no workspace or experiment directory, and leave the test double's ledger empty.
- Wrapper: `tests/run-golden.sh flat spec-run` without `--manifest` exits 4; with arguments it returns the exit code of the `run` command it starts; `bash -n tests/run-golden.sh` passes.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (pseudo-terminal and pipe subprocesses, wrapper subprocess), contract (exit codes and DM-7 shape), smoke (guard re-pin, `bash -n`)
- **Scenarios:**
  - AC-15 → limit edited after approval → exit 4 `approval-mismatch`, empty ledger; pipe and wrong confirmation → exit 4, no file; correct confirmation → DM-7 with current hash.
  - AC-44 → three invalid policy entries → exit 2 from both commands, empty ledger.
  - Authorization matrix → four refusals with exit 4 and nothing created.
  - Wrapper → exit 4 without manifest; exit code pass-through.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; empty/null (`approval: null`); boundary (confirmation of 11 or 13 characters); invalid state (manifest edited after approval); missing dependencies (approval file absent); permission boundaries (non-terminal approval, unreadable approval file).
