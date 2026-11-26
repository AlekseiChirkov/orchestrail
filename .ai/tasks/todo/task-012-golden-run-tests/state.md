spec_path: .ai/specs/012-golden-run-tests.md
contract_version: 0.9.0
flow: full

## Phases
- discovery: complete
- execution: not-started
- validation: not-started

## Task Analysis
→ archived to state-archive.md

### Assumptions
- Spec 011 is a declared prerequisite and its naming stage is not integrated (phase 1 awaits
  owner integration; phase 2 is in progress in another workspace) → Discovery proceeds; the
  delivery ships the names that exist at its base revision and follows spec A-34 for later
  renames (source: spec A-34 and Notes → Spec 011 coupling; `.ai/memory/state.md` Active
  Tasks; owner request of 2026-11-26 to run Discovery now).
- Delivery order → the eight parts of spec Notes → Delivery order; parts 1–3 form the
  offline regression suite and parts 4–8 the strategy evaluation (source: spec Notes;
  spec Readiness check 13).
- Suite runner → standalone `python3 -I tests/golden-runs.py` on the standard library
  `unittest`, not registered in `scripts/validate-contracts.sh` (source: spec A-02;
  ADR-0019 Decision 3; standalone-suite pattern of `scripts/check-repo-set.py`).
- `pytest` → needed only by case seeds, open tests and hidden checks, never by the suite
  runner; checks that need it report through REQ-35 (source: spec REQ-01, REQ-35, A-27).
- flow: full — gate: 1fail 2fail 3fail 4fail (far more than three files, a new public CLI and
  fixtures, eight delivery parts) (source: `rules/quick-flow.md:29-51`).

## Decomposition
- decomposition: complete
- subtasks: T-01, T-01a, T-01b, T-02, T-02a, T-02b, T-02c, T-02d, T-02e, T-03, T-03a, T-03b, T-03c, T-04, T-04a, T-04b, T-04c, T-04d, T-05, T-05a, T-05b, T-05c, T-05d, T-06, T-06a, T-06b, T-07, T-07a, T-07b, T-07c, T-08, T-08a, T-08b, T-08c
- composites: T-01 (T-01a, T-01b); T-02 (T-02a, T-02b, T-02c, T-02d, T-02e); T-03 (T-03a, T-03b, T-03c); T-04 (T-04a, T-04b, T-04c, T-04d); T-05 (T-05a, T-05b, T-05c, T-05d); T-06 (T-06a, T-06b); T-07 (T-07a, T-07b, T-07c); T-08 (T-08a, T-08b, T-08c)

## Model Selection
- selection: complete
- provider: openai
- claude_column: intentionally empty (session default). The owner fallback configuration names only an OpenAI identity and the catalog holds no independent quality evidence for any Anthropic model, so no Claude recommendation can be verified or preliminarily assigned; add an Anthropic profile to `model-fallback.json` and rerun `/pd-select-model` to populate it.
- catalog: user configuration at orchestrail/model-catalog.md (status fresh)
- catalog_refresh: 2026-11-24
- support: unknown — this Discovery ran in a Claude Code session; current OpenAI worker support, context and tool bounds were not observed (2026-11-26).
- economics: no comparable-task cost evidence was supplied; cost comparisons empty.
- scoring: C, A, V, R, Ver, Crit, RW per leaf as listed; hard floors: `financial` for approval, spend limits and the paid boundary; `security` for isolation; `core-invariant` for assertions, outcomes and the promotion verdict.
- T-01a: gpt-6.2-sol (preliminary, configured fallback), scores C3 A2 V3 R3 Ver4 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 5cbb4424a6a8a34d6106632ccd61c8ca14876c99e26a486da242e8373cb734fa
  plan_row_sha256: c71efd2ca3d8d03b7a2f43dd605ecf724175e927d27268490fb4c0aefd4ef022
- T-01b: gpt-6.2-sol (preliminary, configured fallback), scores C4 A2 V3 R4 Ver4 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: efa5dd4213d6c8137aed8e34f7fe03db7775e34bd82867aff85c8077b1cdd6fc
  plan_row_sha256: 756f1f179d4974906b900c6b6822aed93e2af08f1494d0ad7cda87479c616786
- T-02a: gpt-6.2-sol (preliminary, configured fallback), scores C4 A2 V4 R4 Ver4 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: daa5bbe8018cfed97134c72ea1ea99c00e76020b65de8e690819078a49336259
  plan_row_sha256: 269804d161c61fd7210f9e53b96334842db8c58e19104c65be30eae5cd5b7cad
- T-02b: gpt-6.2-sol (preliminary, configured fallback), scores C3 A2 V3 R4 Ver4 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 6508ac0853af0d579fc6dfbb55652191450cf844cbd98616c3e8b26c2a308217
  plan_row_sha256: 512f5dd6291f7b0a4f214794e14ab4ae04442f47794031aec211a013d7146451
- T-02c: gpt-6.2-sol (preliminary, configured fallback), scores C3 A2 V3 R4 Ver4 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: caba3f972872a06d097c6fc1df08937ad84c891bf92e92185bcf1183422b8045
  plan_row_sha256: 8561c9701c2401c3b9ec14ee6c44d938767873b107bb8f78d148a95d4db20420
- T-02d: gpt-6.2-sol (preliminary, configured fallback), scores C4 A3 V4 R4 Ver4 Crit2 RW4, hard: core-invariant, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: e94ae2ffb4284072c1ac90ce140d5c560020a6fb1c260990622e0795cade3dc7
  plan_row_sha256: c0a836b10e2de855b87b83c0545f93164fb6d92b552b59ff6f12194eeca682d6
- T-02e: gpt-6.2-sol (preliminary, configured fallback), scores C3 A2 V3 R4 Ver4 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 994790d952f7a2ce50cd63978c3640b4676a5be801fd7f7c7eb133dd0049bee0
  plan_row_sha256: 91f393cb16fb41a01557cfaff5315acb59380a2fb7bc91d3f7134814625b4568
- T-03a: gpt-6.2-sol (preliminary, configured fallback), scores C4 A2 V3 R4 Ver4 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 3bd88ae9480b5922f1f525b7aeb2b360023259b614c3506bad25a2f3ea629633
  plan_row_sha256: 13e63618ed5b449df42fd611a23194b508fc766f149082697b80f8f9e713a481
- T-03b: gpt-6.2-sol (preliminary, configured fallback), scores C3 A2 V3 R4 Ver4 Crit3 RW3, hard: financial, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: c4b42c282b40c05540c86d62deac89314767fccca73352ed2e0cb48b939749b4
  plan_row_sha256: f638f1cbf5728de60b9fb78d350fc946cadc5d9620078500ac200d53ffc6683c
- T-03c: gpt-6.2-sol (preliminary, configured fallback), scores C4 A2 V4 R4 Ver4 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 6baeffb7fccb5a957e984ae45ecfe43c25758203dbe6b1376c59e0ac35696d83
  plan_row_sha256: 087177323506ec6a107c959ad1a8038a0fd7c43c5a697866c06ec74846cf0202
- T-04a: gpt-6.2-sol (preliminary, configured fallback), scores C3 A2 V3 R4 Ver4 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: e086f45b66f7e494f2f954c20072366039911d313fac737a0cb943afd28f188b
  plan_row_sha256: bf6ad2af45a6999f7e1646a3703274da57cc4ecf746f2b313ccf7e5dd6472bf4
- T-04b: gpt-6.2-sol (preliminary, configured fallback), scores C4 A2 V4 R4 Ver4 Crit3 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 78fb52759c12aae79f5185baef71b65c1a3f673f1e4ecd7fbbf76c0c52f0d4cc
  plan_row_sha256: 8afb2b28df5beeb0c7cd3626d357eb1c37c48dca9f6e2cc33eb03c766ca90f85
- T-04c: gpt-6.2-sol (preliminary, configured fallback), scores C4 A3 V4 R5 Ver3 Crit3 RW4, hard: security, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 11d1044fa4e4e9864518ae871c445d82ceefbebca617563e79b24825613bfb6b
  plan_row_sha256: 100973c1860a6eb3860f58e2520b255fa913887fac7aac0f0e8191a2770c3f84
- T-04d: gpt-6.2-sol (preliminary, configured fallback), scores C3 A2 V3 R3 Ver4 Crit2 RW2, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 7e58be694c37f14a935a22276ed0261f4ccf5999e530218efcedfac3c1bb5369
  plan_row_sha256: 36e92148b36d51ed8be77ce3f128c482f08c610c1b0a4ada708afb24d0f62e6c
- T-05a: gpt-6.2-sol (preliminary, configured fallback), scores C3 A2 V3 R4 Ver4 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 428a8f5d1ffe5aa3343f3b5d723aac72ad8d390cf3d679d89cc83b091cbe2e83
  plan_row_sha256: 65ad4fe2f88d39857c498e421d9ea70937ef354dfdd4e341aedad8ea22743c1f
- T-05b: gpt-6.2-sol (preliminary, configured fallback), scores C3 A2 V3 R4 Ver4 Crit3 RW3, hard: financial, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 68a8074f0b8a80772bb68a4f069b0f7c75c38daada470aaf427e3cc21997ddb1
  plan_row_sha256: c98001ae4d404df8e0ab275951dbb6074d48ec42331046f08ee3753991fadfb4
- T-05c: gpt-6.2-sol (preliminary, configured fallback), scores C4 A2 V3 R4 Ver3 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 10d557b0feafa202764128fedb5e91d136334c5a307b513d1319a02a66fda417
  plan_row_sha256: e979eedb9bad6c7142e5b75fe5c52d4ac1e64c4292dae626eacd2ee6cdde8426
- T-05d: gpt-6.2-sol (preliminary, configured fallback), scores C4 A2 V4 R4 Ver4 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 621272b60467a7bf8f3eaa23575d674374e27d7d47e9db039d8145829dedc424
  plan_row_sha256: 9fffff0e49b561296bd4a712fcf5e4834ae7fd8d710bfc0e0bccdeda51d90fe2
- T-06a: gpt-6.2-sol (preliminary, configured fallback), scores C4 A2 V3 R4 Ver4 Crit2 RW3, hard: core-invariant, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: c7160a5cd4ba3980d3b555b80eb5c8ed66350c443a11012d8ca74a932821cae6
  plan_row_sha256: 7f9be801617ae314c3547c0e92d46d5f228e12ad904d52c093be63af2cdfdc25
- T-06b: gpt-6.2-sol (preliminary, configured fallback), scores C3 A2 V3 R4 Ver4 Crit2 RW2, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 1f16a54cd859bf8fffd00178257905f96fe92a1fd6450602ca593131f4e1ef20
  plan_row_sha256: e8046c39bbbb1f01536954ee44ad37b621dd4e27354493fdcd864c1a12212c9d
- T-07a: gpt-6.2-sol (preliminary, configured fallback), scores C4 A2 V4 R4 Ver4 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: f37ce52bde9d76fa68721d7f6b4555d664257060bb58cc310fe1bb07b2a7db2c
  plan_row_sha256: 9d6873726a32436f97fbe2e079a42f699ccb6ad8ca6a85aaba3534b0d6b4601b
- T-07b: gpt-6.2-sol (preliminary, configured fallback), scores C3 A2 V3 R4 Ver4 Crit2 RW3, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: eb3f180231939c4b9b6b9ca9a59dcd520b4c90328595dd9da3c76342d4b20778
  plan_row_sha256: 251eac10404406983f7586c3c8de080546fc1b1f2cf7a83565ffcaecd94c96e7
- T-07c: gpt-6.2-sol (preliminary, configured fallback), scores C4 A2 V3 R5 Ver4 Crit2 RW3, hard: core-invariant, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: c7489d4da39631027d5aa3847ce43c469d20877ed7850e8b17eef1d8a229f171
  plan_row_sha256: ba42bd68a433cc58317eca48b4a5835c1d5ac0ebb949de2e2a7d9cb5f93ef9ce
- T-08a: gpt-6.2-sol (preliminary, configured fallback), scores C3 A2 V2 R3 Ver4 Crit1 RW2, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 905e19661e5dfe39c4273bc2cae99264664b2a09be8c4f74cb895224643c771e
  plan_row_sha256: f42f99330f15711b068f879679e1745d23ab934cc6f498933a28c9f596463d44
- T-08b: gpt-6.2-sol (preliminary, configured fallback), scores C2 A1 V3 R3 Ver4 Crit3 RW2, hard: financial, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: c5cd6da0f2bb24564dd4c1bae4404df402aa1adf1556404e00f0e1a3e70df412
  plan_row_sha256: 4ab47f0edd8e8b5a66656b161f3c45875a9b109111ae31ad95fcdb272ba69fd5
- T-08c: gpt-6.2-sol (preliminary, configured fallback), scores C2 A2 V3 R2 Ver4 Crit1 RW2, reasoning: medium (owner-configured fallback effort; support unverified). Unknown: independent quality, harness availability, context and tool bounds, comparable cost, actual worker identity.
  description_sha256: 12fb0f90df7bbcda0c2af3c270f00cf5bc49a296df9ab15fe9054a5f3eebd67e
  plan_row_sha256: f622cee541b56ce13abdcef7947796336462998756289583db065d9cce3e024a
## Solution Design

### Variants
→ archived to state-archive.md

### Decision
Variant 1 — stage modules behind one CLI exchanging canonical JSON on disk. It is the layout
the specification names (A-03), reuses the repository's flat standard-library module
pattern, and gives every leaf one module of its own, so stacked leaves conflict only in the
dispatcher and the shared suite.

Specification reconciliation (recorded for `/spec-sync`): edge case N-08 says a
normalization exception yields `technically-incomplete` and exit 8, while DM-10 states that
normalize and compare statuses never change the outcome. REQ-19 requires every negative
catalog entry, N-08 included, to yield an outcome other than `independently-accepted`, and
REQ-15 treats an unparsable source as `error`. The binding requirements win: a normalize
step `error` (an exception, not a golden mismatch) makes the attempt `technically-incomplete`
with exit 8, extending DM-10 row 4; a compare `failed` (`golden-mismatch`,
`missing-expected`) still never changes the outcome. The DM-10 sentence is to be amended
through `/spec-sync` after delivery.

adr: [ADR-0030](../../../adr/0030-task-012-golden-run-stage-modules.md) | status: Provisional — promoted by `/pv-finalize` after validation.

### Scope
#### In
- REQ-01–REQ-55 and AC-01–AC-46 of the specification, delivered as the 26 leaves of
  `plan.md` in eight composites.
- Offline `tests/golden-runs.py`, the test double, the five reference histories and the
  five reviewed expected results with `origin: synthetic-reference`.
- `docs/GOLDEN-RUNS.md` and index rows; source-guard re-pins.
#### Out
- Any paid or live model run, any live expected result, CI files, `scripts/sync.sh` or
  `scripts/validate-contracts.sh` registration, rule or workflow changes, run-log emission
  changes (Q-05), parallel children (REQ-55 rejects `parallel` ≠ 1), multi-repository runs,
  a sandbox implementation (Q-03).

### Rejected
→ archived to state-archive.md

### Off-limits
- `scripts/validate-contracts.sh`, `scripts/sync.sh`, every file under `rules/` and
  `workflows/`, any `.github/` file.
- Any real `claude` invocation or paid run; installing anything at run time.
- Planning identifiers (subtask ids, spec numbers, `.ai/` paths, REQ/AC ids) in product code,
  comments, test names or documentation.
- Writing under `tests/expected/` except through `accept-expected`.
- Deleting, skipping or weakening tests frozen by an earlier leaf.

### Invariants
- Only the Python standard library, `git` and an already installed `pytest` are used; every
  command runs as `python3 -I`.
- No adapter is invoked outside `golden-eval.py run` with an approved runnable manifest.
- Every JSON document is written canonically (sorted keys, UTF-8, strict parsing).
- Expected results change only through `check --update` and `accept-expected`.
- Each leaf leaves `bash scripts/validate-contracts.sh` and the source-guard suites passing.
- The suite never needs network access, credentials or a model.

### Acceptance Criteria
- `python3 -I tests/golden-runs.py` with `pytest` importable passes every test, and every
  specification criterion AC-01–AC-46 has at least one named test in it.
- Without `pytest`, the suite runs every check that does not need it, prints one diagnostic
  naming `pytest` and the provisioning command, and exits 3.
- `check` on each of the five catalog pairs exits 0 against the committed expected results.
- `validate-manifest` on `tests/golden/manifest-template.json` reports `valid: true,
  runnable: false`, and `run` with it exits 4 with an empty double ledger.
- `bash scripts/validate-contracts.sh` passes at the stack tip with no change to its own file.

### Autonomous Decision

| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| 1 Stage modules + CLI | 3 | 4 | 5 | 5 | 4 | 21 |
| 2 Package + pipeline object | 2 | 3 | 2 | 4 | 4 | 15 |
| 3 Single script | 4 | 2 | 3 | 2 | 3 | 14 |

Anti-overengineering check: Variant 1 introduces no abstraction absent from the codebase
(flat `scripts/*_*.py` modules with a CLI exist, e.g. `scripts/usage_telemetry_outcomes.py`,
`scripts/repo-set.py`); no penalty. Variant 2's package and pipeline object would address a
hypothetical typing need, so its Simplicity is already the lowest. Winner: Variant 1 (21).
Escalation threshold not reached: no external contract, secret or service is involved.

## Subtask Progress

[composite] T-01 | Golden case catalog and reference builds | rollup: not-started | integration-validation: not-started
  children: T-01a, T-01b
  blocker: none
  notes: Type 2 — 2 independently testable components with 2 criteria clusters (plan.md → ## Decomposition Decisions)

T-01a | Golden case fixtures and catalog loader | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Author golden cases and loader
  target_files: tests/golden-runs.py, scripts/golden_cases.py, tests/golden/cases/{flat,composite,quick,bugfix}/case.json, tests/golden/cases/*/project/**, tests/golden/cases/*/hidden/**, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-01b | Deterministic reference builder and reference histories | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Build deterministic reference histories
  target_files: scripts/golden-eval.py, scripts/golden_cases.py, tests/golden/cases/flat/reference/{spec-run,phase-pipeline}/**, tests/golden/cases/composite/reference/spec-run/**, tests/golden/cases/quick/reference/phase-pipeline/**, tests/golden/cases/bugfix/reference/bugfix/**, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

[composite] T-02 | Offline semantic check and golden comparison | rollup: not-started | integration-validation: not-started
  children: T-02a, T-02b, T-02c, T-02d, T-02e
  blocker: none
  notes: Type 2 — 5 independently testable components with 5 criteria clusters (plan.md → ## Decomposition Decisions)

T-02a | Capture and fact extraction | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Capture workspaces and extract facts
  target_files: scripts/golden-eval.py, scripts/golden_capture.py, scripts/golden_semantics.py, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-02b | Semantic projection normalization | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Normalize facts into projections
  target_files: scripts/golden_normalize.py, scripts/golden-eval.py, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-02c | Hidden checks and missed defects | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Run hidden checks offline
  target_files: scripts/golden_semantics.py (or a hidden-check module chosen by design), scripts/golden-eval.py, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-02d | Semantic assertions and check outcome | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Evaluate semantic assertions and outcome
  target_files: scripts/golden_semantics.py, scripts/golden-eval.py, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-02e | Golden comparison, candidates and reviewed expectations | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Compare, update and accept expectations
  target_files: scripts/golden-eval.py, scripts/golden_normalize.py, tests/expected/{flat/spec-run,flat/phase-pipeline,composite/spec-run,quick/phase-pipeline,bugfix/bugfix}/{projection.json,review.json}, the test double under tests/golden/ (path set by design), tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

[composite] T-03 | Manifest, approval and run gate | rollup: not-started | integration-validation: not-started
  children: T-03a, T-03b, T-03c
  blocker: none
  notes: Type 2 — 3 independently testable components with 3 criteria clusters (plan.md → ## Decomposition Decisions)

T-03a | Manifest validation, hashing and instructions digest | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Validate manifests and digests
  target_files: scripts/golden_manifest.py, scripts/golden-eval.py, tests/golden/adapters/claude.json, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-03b | Interactive approval and run authorization | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Gate runs on interactive approval
  target_files: scripts/golden_manifest.py, scripts/golden-eval.py, tests/run-golden.sh, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-03c | Preflight and dry-run plan | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Preflight pinning and dry-run plan
  target_files: scripts/golden_runner.py, scripts/golden_manifest.py, scripts/golden-eval.py, the test double under tests/golden/, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

[composite] T-04 | Runner execution | rollup: not-started | integration-validation: not-started
  children: T-04a, T-04b, T-04c, T-04d
  blocker: none
  notes: Type 2 — 4 independently testable components with 4 criteria clusters (plan.md → ## Decomposition Decisions)

T-04a | Experiment directory and ledger | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Lock experiment directory and ledger
  target_files: scripts/golden_runner.py, scripts/golden-eval.py, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-04b | Attempt launch through the adapter | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Launch attempts through adapter
  target_files: scripts/golden_runner.py, scripts/golden_capture.py, scripts/golden-eval.py, the test double under tests/golden/, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-04c | Isolation probes and evaluator-only material | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Probe isolation and hidden material
  target_files: scripts/golden_probe.py, scripts/golden_runner.py, scripts/golden_semantics.py, the test double under tests/golden/, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-04d | Variant switches | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Apply and validate variant switches
  target_files: scripts/golden_manifest.py, scripts/golden_runner.py, scripts/golden_semantics.py, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

[composite] T-05 | Recorded evidence, limits, cancellation and resume | rollup: not-started | integration-validation: not-started
  children: T-05a, T-05b, T-05c, T-05d
  blocker: none
  notes: Type 2 — 4 independently testable components with 4 criteria clusters (plan.md → ## Decomposition Decisions)

T-05a | Recorded imports and usage attachment | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Import recorded results and usage
  target_files: scripts/golden_runner.py, scripts/golden_capture.py, scripts/golden-eval.py, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-05b | Launch limits and variant halts | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Enforce launch limits and halts
  target_files: scripts/golden_runner.py, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-05c | Cancellation and attempt timeout | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Handle signals and timeouts
  target_files: scripts/golden_runner.py, the test double under tests/golden/, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-05d | Resume without automatic restart | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Resume without automatic restart
  target_files: scripts/golden_runner.py, scripts/golden-eval.py, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

[composite] T-06 | Independent evaluation | rollup: not-started | integration-validation: not-started
  children: T-06a, T-06b
  blocker: none
  notes: Type 2 — 2 independently testable components with 2 criteria clusters (plan.md → ## Decomposition Decisions)

T-06a | Evaluation records, disputes and outcomes | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Record evaluations, disputes, outcomes
  target_files: scripts/golden_evaluation.py, scripts/golden-eval.py, scripts/golden_runner.py, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-06b | Blinded evaluation queue | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Write blinded evaluation queue
  target_files: scripts/golden_evaluation.py, scripts/golden_runner.py, the test double under tests/golden/, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

[composite] T-07 | Reports and promotion | rollup: not-started | integration-validation: not-started
  children: T-07a, T-07b, T-07c
  blocker: none
  notes: Type 2 — 3 independently testable components with 3 criteria clusters (plan.md → ## Decomposition Decisions)

T-07a | Report metrics and cost per accepted result | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Report metrics and cost
  target_files: scripts/golden_report.py, scripts/golden-eval.py, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-07b | Holdout, contamination, privacy and retention | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Seal holdout, protect report content
  target_files: scripts/golden_report.py, scripts/golden-eval.py, the test double under tests/golden/, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-07c | Promotion verdict | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Compute promotion verdict
  target_files: scripts/golden_report.py, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

[composite] T-08 | Calculator, safe template and documentation | rollup: not-started | integration-validation: not-started
  children: T-08a, T-08b, T-08c
  blocker: none
  notes: Type 2 — 3 independently testable components with 3 criteria clusters (plan.md → ## Decomposition Decisions)

T-08a | Scenario calculator | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Implement scenario calculator
  target_files: scripts/golden_calculator.py, scripts/golden-eval.py, tests/golden/calculator-example.json, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-08b | Safe manifest template and paid boundary | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Ship safe template, prove boundary
  target_files: tests/golden/manifest-template.json, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 

T-08c | Operating manual | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: not started — planned: Write golden runs manual
  target_files: docs/GOLDEN-RUNS.md, docs/README.md, scripts/README.md, tests/golden-runs.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: 
