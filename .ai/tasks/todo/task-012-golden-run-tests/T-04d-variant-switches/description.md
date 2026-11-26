## Goal
Apply variant `switches` (prompt arguments, `ORCHESTRAIL_*` environment entries and a digest-checked overlay) at launch and reject unsafe switches, so that two variants differing only by switches produce launches that differ exactly by those switches and the overlay never counts as a changed path.

## Context
- Dependencies: T-04b (launch, child environment, changed-paths baseline), T-03a (switches shape, configuration hash), T-03c (preflight)
- Constraints: Python 3.11+ standard library and `git` only, run as `python3 -I`; strict and canonical JSON as defined in the specification; `prompt_args` are appended space-separated to the case workflow prompt; `--allow-pr`, `--repo` and `--parallel` are rejected; `env` names match `^ORCHESTRAIL_[A-Z0-9_]{1,56}$` and are not `ORCHESTRAIL_HOME` or `ORCHESTRAIL_LOG_ROOT`; the overlay is a directory relative to the manifest, copied after the seed commit and before launch; the seed digest is taken before the overlay; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-36, REQ-52, Variant switches, DM-3 changed-paths baseline.
- Reason: switches are one component with one criteria cluster (application and rejection), testable on top of the launch path.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; any switch that changes the model, harness configuration or an allowlisted variable; defining experiments for other specifications.

## Scope
- **In scope:** semantic validation of switches (exit 2 for forbidden prompt arguments, invalid or reserved `env` names, `overlay-conflict` when an overlay file exists in the seed); `overlay_digest` check in preflight (exit 5 on mismatch); application at launch (prompt suffix, environment entries, overlay copy); the changed-paths baseline including the overlay.
- **Out of scope:** switch-specific experiments of other specifications; recorded imports (T-05a).
- **Target files:** `scripts/golden_manifest.py`, `scripts/golden_runner.py`, `scripts/golden_semantics.py`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` (A1/A2 manifest with an overlay holding `.ai/example-policy.json`) and observe them fail for the right reason (switches not applied).
2. Implement semantic switch validation with exit 2 and reasons, including `overlay-conflict`.
3. Implement the `overlay_digest` preflight check (tree digest of the overlay directory, exit 5 on mismatch).
4. Implement application at launch: append `prompt_args` to the prompt, add `env` entries to the child environment, copy the overlay after the seed commit and before launch.
5. Include overlay files in the changed-paths baseline while taking the seed digest before the overlay.
6. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-40 (REQ-52): for an approved comparison manifest whose variants A1 and A2 differ only in A2's `switches` (`prompt_args` `["--example-switch","on"]`, `env` `{"ORCHESTRAIL_EXAMPLE_SWITCH":"on"}`, an overlay holding `.ai/example-policy.json`), `run` leaves double ledger entries where A2's prompt ends with ` --example-switch on`, `ORCHESTRAIL_EXAMPLE_SWITCH` is among A2's env names, the overlay file is present in A2's cwd, and `.ai/example-policy.json` is absent from A2's `changed_paths`; A1's entries show none of these; manifests with `--allow-pr`, `--repo` or `--parallel` in `prompt_args`, an `env` name `ANTHROPIC_MODEL` or `ORCHESTRAIL_HOME`, or an overlay file that exists in the seed each exit 2.
- Overlay digest: a manifest whose `overlay_digest` differs from the overlay's tree digest makes `run` exit 5 with the ledger empty.
- Seed digest: the attempt's `seed_digest` for A2 equals the case seed digest (taken before the overlay).
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (double on `PATH`, real workspaces), unit (switch validation), smoke (guard re-pin)
- **Scenarios:**
  - AC-40 → A2 prompt suffix, env name, overlay file, excluded changed path; A1 unchanged; six rejected manifests exit 2.
  - Digest mismatch → exit 5, empty ledger.
  - Seed digest for A2 equals the case seed digest.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; empty/null (empty switches, null overlay); boundary (56-character env suffix); invalid state (overlay file present in the seed); permission boundaries (reserved variable names).
