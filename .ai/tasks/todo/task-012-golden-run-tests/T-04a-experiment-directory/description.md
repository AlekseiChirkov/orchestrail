## Goal
Deliver the experiment directory contract — exclusive `fcntl.flock` lock, creation with mode 0700, byte copies of manifest and approval, `experiment.json`, `plan.json`, `blinding.json` (0600) and an append-only fsynced ledger — so that a second process on a locked directory exits 9 with every file unchanged and an interrupted ledger stays readable.

## Context
- Dependencies: T-03c (plan, attempt keys, preflight), T-03b (authorization)
- Constraints: Python 3.11+ standard library only, run as `python3 -I`; strict and canonical JSON as defined in the specification; every ledger event is flushed and fsynced before the next action; default artifact root `<source checkout>/output/golden`, overridden by `--artifact-root` or `data.artifact_root`; the lock is taken after authorization and before preflight, and never by `--dry-run`; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-41, REQ-43 (`experiment.json`), DM-9, Opening an experiment directory, NFR durability and file permissions.
- Reason: the experiment directory and ledger are the shared persistence component every later command opens; their done-state (exclusive, durable, correctly initialized) is testable without launching an adapter.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; automatic deletion of any artifact; launching (T-04b); resume semantics (T-05d).

## Scope
- **In scope:** a shared "open experiment directory" operation (take the lock or exit 9 `busy`; create when absent for `run` and later `import-recorded`, otherwise exit 2 for other commands; copy manifest and approval bytes; write `experiment.json` with `manifest_sha256`, `approval_sha256`, `config_sha256`, `started_at`, `retain_until` = start date + `data.retention_days`; `plan.json`; `blinding.json` with labels `V-` + first 8 hex of SHA-256 of `<config_sha256>:<variant_id>`); existing-directory rules (given manifest or approval bytes differ → exit 4; a `launched` event without `--resume` → exit 2 `experiment-exists`; imports-only directories open normally); the ledger (`seq` from 1, `ts`, event vocabulary, `unit_id`, `attempt_key`, `details`; fsync; an incomplete last line ignored on read; a failed write → exit 8); wiring into `run`.
- **Out of scope:** attempt workspaces and launches (T-04b); isolation results in `experiment.json` (T-04c adds them); resume (T-05d).
- **Target files:** `scripts/golden_runner.py`, `scripts/golden-eval.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (missing experiment directory operations).
2. Implement the lock (`.lock` with `fcntl.flock`, non-blocking; exit 9 `busy` without touching any file).
3. Implement creation: directories with mode 0700, byte copies of manifest and approval, `experiment.json`, `plan.json`, `blinding.json` with mode 0600.
4. Implement the existing-directory rules: stored-copy byte comparison (exit 4), `experiment-exists` (exit 2) for a `launched` event without `--resume`, imports-only directories opened normally, exit 2 for commands that require an existing directory.
5. Implement the ledger writer and reader: append-only JSONL with `seq`, `ts`, `event`, `unit_id`, `attempt_key`, `details`, flush and fsync per event, ignore an incomplete last line, map a write failure to exit 8.
6. Wire the operation into `run` after authorization and before preflight; `--dry-run` skips it.
7. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-30 (REQ-41): while another process holds the experiment lock, a second `run` on that directory exits 9 with reason `busy`, and the SHA-256 of every file of the directory is unchanged.
- REQ-43: `experiment.json` of a new experiment holds `retain_until` equal to the start date plus `data.retention_days`, together with `manifest_sha256`, `approval_sha256`, `config_sha256` and `started_at`.
- DM-9: a new experiment directory has mode 0700, `blinding.json` has mode 0600 and maps each variant to `V-` plus the first 8 hex of SHA-256 of `<config_sha256>:<variant_id>`, and `manifest.json` and `approval.json` are byte copies of the inputs.
- Opening rules: a given manifest whose bytes differ from the stored copy exits 4; a directory whose ledger holds a `launched` event, opened by `run` without `--resume`, exits 2 with `experiment-exists`; a directory holding only import and evaluation events opens without `--resume`.
- Ledger durability: events carry consecutive `seq` values from 1; a ledger whose last line is truncated JSON is read with that line ignored; a ledger write failure makes the command exit 8.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (two processes on one lock, real file modes, injected write failure), unit (label formula, ledger reader), smoke (guard re-pin)
- **Scenarios:**
  - AC-30 → held lock → exit 9, hashes unchanged.
  - Retention → `retain_until` value.
  - Modes and copies → 0700, 0600, byte equality, label formula.
  - Opening rules → exit 4, exit 2 `experiment-exists`, imports-only accepted.
  - Ledger → consecutive `seq`, truncated last line ignored, write failure exit 8.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; concurrent operations (second runner); duplicate (reopening the same directory); invalid state (`launched` without `--resume`); permission boundaries (file modes); missing dependencies (directory absent for a command that needs it).
