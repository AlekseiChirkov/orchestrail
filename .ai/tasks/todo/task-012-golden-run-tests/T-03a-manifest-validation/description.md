## Goal
Deliver DM-6 manifest validation, the configuration hash, the instructions digest with owner policy entries, the shipped `claude` adapter declaration and `golden-eval.py validate-manifest [--print-current]`, so that every invalid manifest exits 2 naming the offending path and the digest is a stable, path-independent value that reflects every owner policy file.

## Context
- Dependencies: T-01a (strict JSON loader, tree and case digests, case validation), T-01b (`golden-eval.py`)
- Constraints: Python 3.11+ standard library and `git` only, run as `python3 -I`; strict JSON (duplicate keys, `NaN`, `Infinity`, non-integer numbers rejected; decimal strings; unknown fields are errors; unknown `schema_version` rejected) and canonical JSON as defined in the specification; every process launch stays inside `scripts/golden_*.py`; the runner's `HOME` and `XDG_CONFIG_HOME` are read, never written; tests extend `tests/golden-runs.py`; the source guard is re-pinned in this subtask; contract: `.ai/specs/012-golden-run-tests.md` REQ-06, REQ-10, REQ-50, REQ-53, REQ-54, REQ-55, DM-6, DM-8, Instructions digest, Configuration hash.
- Reason: the manifest model is a pure validation and hashing component with one done-state (documents classified valid/runnable with exact errors and stable hashes), testable without `run`.

Off-limits: `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and `workflows/`, any CI file; any paid model run or real `claude` invocation; installing anything at run time; non-English content; planning identifiers (subtask ids, spec numbers, `.ai/` paths, requirement or criterion ids) in product code, comments, test names or documentation; deleting, skipping or weakening tests frozen by earlier subtasks; writing under `tests/expected/`; writing to any owner configuration directory; switch semantics beyond shape (T-04d).

## Scope
- **In scope:** `scripts/golden_manifest.py` (every DM-6 field, pattern and rule; valid versus runnable; `purpose` rules; `holdout` multiplicity; `seeded-hash` seed; `owner-selected` rules; `roles` with exactly `orchestrator`, `arbiter`, `implementer`, `validator`; executable-variant rules; `strategy_details` keys per strategy; `switches` shape; referenced case, case workflow and adapter existence; `published-case-holdout`; `parallel-unsupported` for named cases); configuration hash (canonical JSON without `approval`); instructions digest (`~` → `HOME`, `$XDG_CONFIG_HOME/` resolution, `absent  <entry>` lines, files, dot-skipping directory digests, `policy-file-invalid`); `tests/golden/adapters/claude.json` and its validation; `validate-manifest` output `{valid, runnable, missing, errors}` and `--print-current` (source revision, instructions digest, case digests).
- **Out of scope:** approval and `run` stages (T-03b); preflight comparisons (T-03c); the safe template file (T-08b).
- **Target files:** `scripts/golden_manifest.py`, `scripts/golden-eval.py`, `tests/golden/adapters/claude.json`, `tests/golden-runs.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`.

## Steps
1. Write failing tests for every criterion below in `tests/golden-runs.py` and observe them fail for the right reason (missing module and command).
2. Implement DM-6 shape and type validation in `scripts/golden_manifest.py` with offending JSON paths in every error, `null` allowed for owner-chosen values (valid) and the runnable rules (no required `null`, `execution_enabled` true).
3. Implement the cross-field rules: `purpose` variants, baseline, `holdout` multiplicity requiring `decision_split: "holdout"` and `selected_candidate`, `seeded-hash` seed, `owner-selected` provenance, exactly four role keys naming the variant on failure, executable-variant uniformity, `strategy_details` keys per strategy, `switches` shape.
4. Implement document references: case, case workflow and adapter existence; `published: true` with `split: "holdout"` → `published-case-holdout`; a named case whose workflow `parallel` is not 1 → `parallel-unsupported`.
5. Implement the configuration hash as SHA-256 of the canonical JSON of the manifest without `approval`.
6. Ship `tests/golden/adapters/claude.json` exactly as DM-8 states (argv template, alias names, effort values, `per_attempt_cost_cap: "unverified"`, five `instruction_paths`, empty `env_passthrough`, null result mapping) and its validation.
7. Implement the instructions digest: entry resolution, `absent  <entry>\n`, `<sha256>  <entry>\n`, `<tree digest>  <entry>/\n` skipping dot-named entries, owner policy entries kept literal, `policy-file-invalid` for a directory, an unreadable file or content that is not one strict JSON document.
8. Add `validate-manifest --manifest FILE [--print-current]` to `scripts/golden-eval.py` with exit 0 when valid and 2 otherwise; `--print-current` adds source revision, instructions digest and case digests or exits 2 with `policy-file-invalid`.
9. Re-pin the source guard after the last `.py`/`.sh` edit of this subtask: review and classify new call sites in `tests/fixtures/validator-runtime/source_guard_exceptions.json`, recompute `inventory_sha256` and the manifest digest in `source_guard.py` per `tests/fixtures/validator-runtime/README.md:9-28`, then run the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- AC-33 (REQ-10): manifests with invalid JSON, a duplicate key, an unknown field, a float number, and a `holdout` multiplicity without `selected_candidate` each make `validate-manifest` exit 2 naming the offending path.
- AC-38 (REQ-50): a comparison manifest with a `flat` task declared `holdout` makes `validate-manifest` exit 2 with `published-case-holdout`; the same task declared `tuning` validates.
- AC-42 (REQ-54): with the shipped `claude` declaration, a runner `HOME` without owner policy files and `XDG_CONFIG_HOME` unset, the digest input contains the lines `absent  $XDG_CONFIG_HOME/orchestrail/effort-policy.json` and `absent  $XDG_CONFIG_HOME/orchestrail/repair-policy.json`, two computations give the same digest, and creating `effort-policy.json` under `$HOME/.config/orchestrail/` changes it; with `XDG_CONFIG_HOME` set to another directory holding the file, the file there is read and the one under `$HOME/.config` is not.
- REQ-54: a policy entry that is a directory, an unreadable file, or a file whose content is not valid JSON (including a duplicate key) makes `validate-manifest --print-current` exit 2 with `policy-file-invalid` naming the entry, and the digest is not computed as `absent`; two policy files of identical content at different absolute paths give identical digests and configuration hashes.
- REQ-53: a comparison manifest whose variant lacks the `validator` role key, or adds a `planner` key, makes `validate-manifest` exit 2 naming the variant.
- REQ-06, REQ-55, DM-8: a manifest with variants A–F carrying every DM-6 field validates and reports each `availability`; a manifest task naming a case copy whose workflow declares `parallel` 2 exits 2 with `parallel-unsupported`; the shipped declaration equals the DM-8 text field for field.
- Configuration hash: changing only `approval` leaves it unchanged; changing any other field, including `switches` or `sources.instructions_digest`, changes it.
- Guard maintenance: the source guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh` pass with the re-pinned inventory.

## Test Plan
- **Level:** unit (validation rules, hashing, digest lines), contract (`validate-manifest` JSON output and exit codes; shipped declaration shape), smoke (guard re-pin)
- **Scenarios:**
  - AC-33 → five malformed manifests → exit 2 with paths.
  - AC-38 → `holdout` flat task exits 2; `tuning` validates.
  - AC-42 → absent lines, repeatability, `$HOME/.config` versus `XDG_CONFIG_HOME` precedence.
  - Invalid policy entries → `policy-file-invalid`; identical content at two paths → identical digests and hashes.
  - Role keys → missing `validator` and extra `planner` exit 2 naming the variant.
  - A–F manifest valid; `parallel` 2 case rejected; declaration equality.
  - Hash sensitivity → `approval` excluded; other fields included.
  - Guard → all guard suites and the validator pass.
- **Edge cases:** happy path; empty/null (every owner value null → valid, not runnable); boundary (`delta` 0, `confidence` bounds, 64-character ids); duplicate (duplicate JSON key); invalid state (holdout without candidate, published case as holdout); missing dependencies (unknown case or adapter, absent policy file); permission boundaries (unreadable policy file).
