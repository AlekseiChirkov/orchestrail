# state-archive — task-012-golden-run-tests

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis
### Goal
Deliver a deterministic, model-free regression suite over whole pipeline runs on four
synthetic golden cases (`flat`, `composite`, `quick`, `bugfix`), plus an owner-authorized
runner `scripts/golden-eval.py` that checks the meaning of each run (capture → extract →
assert → evaluate) before comparing normalized projections with reviewed expected results,
and evaluates strategy variants A–F under a pre-registered protocol with independent
acceptance, blinding, held-out reveal, cost per accepted result through spec 006 and a
promotion verdict. Live execution ships disabled; every acceptance criterion runs offline
with a test double (spec REQ-01–REQ-55, AC-01–AC-46).

### Affected Parts
- New tooling: `scripts/golden-eval.py` (CLI: `check`, `build-reference`, `run`,
  `validate-manifest`, `approve`, `accept-expected`, `import-recorded`, `attach-usage`,
  `evaluate`, `report`, `calculate`) and `scripts/golden_*.py` modules (spec A-03).
- New fixtures: `tests/golden/cases/<case>/` (seed, `case.json`, `hidden/`, `reference/`),
  `tests/golden/adapters/claude.json` and the test double, `tests/golden/manifest-template.json`,
  `tests/golden/calculator-example.json`; expected results `tests/expected/<case>/<workflow>/`;
  wrapper `tests/run-golden.sh`; offline suite `tests/golden-runs.py`.
- Documentation: `docs/GOLDEN-RUNS.md`, a row in `docs/README.md`, an inventory row in
  `scripts/README.md` (REQ-40).
- Guard maintenance: new `.py`/`.sh` files under `tests/` change the source-guard inventory
  digest; re-pin through `tests/fixtures/validator-runtime/README.md:9-28` (spec Notes).
- Read-only consumers: `scripts/usage_telemetry_outcomes.py` (`summarize_outcomes`,
  `compare_outcome_groups`), `scripts/log-step.sh` (helper home, step names), canonical
  pipeline artifact formats in `rules/` and `workflows/` (read, never changed).
- Not changed: `scripts/validate-contracts.sh` (frozen inventory, ADR-0019 Decision 3),
  `scripts/sync.sh`, any rule or workflow, any CI file.

### Codebase Analysis
Every `path:line` citation of the specification (95) was re-verified against `main`
`c7e986f` on 2026-11-26 by the citation audit of the preceding `/spec-draft` refinement
(62 corrected), and the independent critic spot-checked 41. The source files that audit
read, and that this analysis relies on:
1. `scripts/usage_telemetry_outcomes.py` — read to verify the `summarize_outcomes` signature,
   opportunity identity keys and label rules consumed by REQ-33 (lines 13, 87-206).
2. `scripts/log-step.sh` — read to verify that step names come from
   `$ORCHESTRAIL_HOME/workflows/*.md` (lines 371-378), which fixes the helper-home contents.
3. `tests/log-step.sh` — read to verify the helper-home copy pattern (lines 15-30).
4. `tests/fixtures/validator-runtime/source_guard.py` — read to verify the digest over every
   `.sh`/`.py` under `tests/` (lines 809-816).
5. `tests/fixtures/validator-runtime/oracle.py` — read to verify the frozen inventory
   (line 250).
6. `rules/workflow-globals.md` — read to verify the canonical `state.md`, leaf, composite,
   `## Fix-Tasks` and `plan.md` formats DM-3 parses, including the new `finalization` marker
   (line 168), leaf `repo:` and `## Repositories` (lines 160-313).
7. `workflows/pae-tests.md` — read to verify the `tdd:` notes entries (lines 105-112, 208-228).
8. `workflows/spec-run.md` — read to verify the invocation (line 7, with `--repo`), the
   quick-flow stop (163-165) and the per-leaf RED log row (335-339).

Files read: 8/12 (6 entry-points, 2 deeper). No golden code exists yet: there is no
`tests/golden/`, `tests/expected/`, `tests/run-golden.sh`, `scripts/golden*` or `.github/`
(directory listings, 2026-11-26). `pytest` is not importable by the current `python3`
(3.14.4, observed 2026-11-26), so REQ-35 (exit 3 with a provisioning diagnostic) is the
default path on this machine until the owner provisions it (spec A-27).

### Open Questions
None blocking Discovery. Specification Q-01–Q-06, Q-08 and Q-09 are open non-blockers that
limit the live path or later deliveries only; none blocks the offline delivery.

## Archived Solution Design — Variants
1. **Stage modules behind one CLI (spec layout).** `scripts/golden-eval.py` is a thin
   argparse dispatcher; each pipeline stage is one standard-library module
   (`golden_cases`, `golden_capture`, `golden_semantics`, `golden_normalize`,
   `golden_manifest`, `golden_runner`, `golden_probe`, `golden_evaluation`,
   `golden_report`, `golden_calculator`) that exchanges canonical JSON documents on disk
   (`facts.json`, `assertions.json`, `projection.json`, `attempt.json`, ledger events).
   One standalone `unittest` suite `tests/golden-runs.py` drives the CLI and modules with a
   test double. Advantages: matches spec A-03 and the flat `scripts/usage_telemetry_*.py`
   pattern; each stage testable in isolation; on-disk documents make resume, import and
   blinding natural. Disadvantages: ten modules and one shared CLI file touched by many
   leaves. Risks: cross-module drift in JSON shapes — mitigated by one canonical-JSON helper
   and strict loaders in the first leaf.
2. **Package `scripts/golden/` with sub-packages and an in-memory pipeline object.** One
   importable package, stages as classes passing Python objects; files written only at the
   end. Advantages: stronger typing between stages. Disadvantages: a package layout and a
   pipeline object exist nowhere else in `scripts/`; resume and import would need a second
   serialization path; `python3 -I` with a package under `scripts/` needs path handling.
   Risks: diverges from spec A-03 paths named by acceptance criteria.
3. **Single script.** Everything in `scripts/golden-eval.py`. Advantages: one file to deploy.
   Disadvantages: several thousand lines; stage tests need the whole program; every leaf
   edits the same file, maximizing stack conflicts. Risks: unreviewable diffs.

## Archived Solution Design — Rejected
- Variant 2: introduces a package and pipeline-object pattern absent from `scripts/`; adds a
  second serialization path for resume and import; conflicts with paths fixed by the spec.
- Variant 3: one multi-thousand-line file edited by every leaf; stage tests impossible
  without the whole program.
- A single late source-guard re-pin: every stacked branch would fail
  `scripts/validate-contracts.sh` until the last leaf (plan D-2).
