## Goal
Deliver the `run` preflight (source and instruction pinning, model aliases, workspace location, adapter version, `pytest` under the child `PATH`), the unit plan with attempt keys and adapter argv expansion, and `run --dry-run`, so that any pinning, alias or location fault exits 5 (environment faults 3) naming the mismatch with zero adapter invocations, and a dry run prints the plan without creating or changing any file.

## Context
- Dependencies: T-03b (`run` stages 1–2), T-03a (digests, declaration), T-01b (helper home, deterministic git helper)
- Constraints: Python 3.11+ standard library, `git` and an already installed `pytest` only, run as `python3 -I`; strict and canonical JSON as defined in the specification; the project registry `${XDG_CONFIG_HOME:-$HOME/.config}/orchestrail/projects` is read only; every process launch stays inside `scripts/golden_*.py`; tests extend `tests/golden-runs.py` and the test double; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-06, REQ-13 (alias part), REQ-39, REQ-47, Run sequence step 3, DM-8 argv, DM-9 ordering and attempt keys, Command-line interfaces (`--dry-run`).
- Reason: preflight plus plan is one component with one done-state (a run is either refused before any side effect or yields a reviewable plan), testable without launching.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; writing the project registry; isolation probes (T-04c); overlay digest checks (T-04d); launching (T-04b).

## Scope
- **In scope:** units from tasks × variants × repetitions for `executable` and `recorded` variants (recorded units marked `source: recorded`, none for `manual` or `unavailable`), `fixed` and `seeded-hash` order, `unit_id`, attempt keys; DM-8 argv expansion (`--effort` pair omitted for `session-default`, tool lists joined with `,`, empty list omits its pair); REQ-39 pinning (HEAD, dirty tracked tree, case digests, instructions digest, `version_argv` first token against `verified_cli_version`); REQ-13 empty or alias model → exit 5; REQ-47 workspace location against the checkout, artifact roots, `cases_root` entries and registered roots (unreadable registry → exit 5); adapter executable missing and `python3 -m pytest --version` failing under the child `PATH` → exit 3; `--dry-run` output; the double's configurable `--version` answer.
- **Out of scope:** lock and experiment directory (T-04a); launch (T-04b); isolation (T-04c); switches (T-04d).
- **Target files:** `scripts/golden_runner.py`, `scripts/golden_manifest.py`, `scripts/golden-eval.py`, the test double under `tests/golden/`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (missing preflight, missing dry-run output).
2. Implement the unit plan in `scripts/golden_runner.py`: unit enumeration, `fixed` and `seeded-hash` ordering, `unit_id`, attempt keys, recorded units.
3. Implement DM-8 argv expansion from a variant and the declaration.
4. Implement REQ-39 pinning checks with exit 5 naming the mismatch (`source_revision`, dirty tracked tree, case digest, instructions digest, adapter CLI version).
5. Implement the REQ-13 alias and empty-model check (exit 5) and environment checks (adapter executable on `PATH`, `pytest` under the child `PATH`, exit 3).
6. Implement REQ-47 location checks for the planned workspace, attempt log root and helper home parents, reading the registry when it exists.
7. Implement `--dry-run`: no lock, no file created or changed; print the plan, the preflight results and the planned argv per unit as one JSON object.
8. Extend the test double so that its `--version` answer is configurable per test.
9. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-29 (REQ-39): a manifest whose `source_revision`, one case digest or the instructions digest differs from the values printed by `validate-manifest --print-current`, a dirty tracked tree, or a test double reporting another version each make `run` exit 5 naming the mismatch, with the double's ledger empty.
- AC-35 (REQ-47): a registry file listing the system temporary directory, or an artifact root that contains the system temporary directory, makes `run` exit 5 with `workspace-location` and leaves the double's ledger empty.
- AC-43 (REQ-54, REQ-22): with an approved manifest and a present `repair-policy.json`, changing one byte of that file makes `validate-manifest --print-current` print another instructions digest and a manifest pinned to the old digest makes `run` exit 5 with the ledger empty; the manifest rewritten with the new digest has another `config_sha256`, so its old approval record makes `run` exit 4 `approval-mismatch`; two policy files of identical content at different absolute paths give identical instructions digests and configuration hashes.
- REQ-06 (dry-run): for an approved comparison manifest with variants A–F where D is `unavailable` and C is `recorded`, `run --dry-run` prints a plan listing the same task ids, case digests and source revision for every variant, C's units with `source: recorded`, no unit for D, and creates no experiment directory or other file.
- REQ-13: a variant model `sonnet`, or an empty model, makes `run` exit 5 before any launch with the ledger empty.
- DM-8, DM-9: the planned argv for model `test-model-1`, effort `high`, permission mode `dontAsk`, allowed tools `["Read","Edit"]`, no disallowed tools and cap `0.5` equals the template expansion without the `--disallowedTools` pair, and `session-default` omits the `--effort` pair; `seeded-hash` order with the same seed is identical across two dry runs and attempt keys equal `a-` plus the first 16 hex of SHA-256 of `<config_sha256>:<unit_id>:<attempt_no>`.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** integration (real `git` checkout copies, registry files, double on `PATH`), unit (argv expansion, ordering, keys), smoke (guard re-pin)
- **Scenarios:**
  - AC-29 → five mismatches → exit 5 naming each; empty ledger.
  - AC-35 → registry and artifact-root locations → exit 5 `workspace-location`.
  - AC-43 → policy byte change → digest change, exit 5, re-pinned manifest exit 4; identical content at two paths → identical values.
  - Dry run with A–F → plan content; no directory created.
  - Alias and empty model → exit 5.
  - Argv and ordering → exact expansion; repeatable order; key formula.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; empty/null (empty tool lists, `session-default`, absent registry); boundary (abbreviated version token, single repetition); invalid state (dirty tree, stale digest); missing dependencies (adapter not on `PATH`, `pytest` missing → exit 3); permission boundaries (unreadable registry → exit 5).
