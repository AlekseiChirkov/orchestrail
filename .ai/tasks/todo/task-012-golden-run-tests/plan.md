# Golden run tests and strategy evaluation

## Subtasks

| ID | Type | Name | Key Steps (summary) | Depends On | Status | Model (Claude) | Model (Codex) |
|----|------|------|---------------------|------------|--------| --- | --- |
| T-01 | composite | Golden case catalog and reference builds | (children: T-01a, T-01b) | — | not-started |  |  |
| T-01a | leaf | Golden case fixtures and catalog loader | suite harness with pytest gate → strict loader and digests → four cases → hidden tests and defects → guard re-pin | — | not-started |  | gpt-6.2-sol |
| T-01b | leaf | Deterministic reference builder and reference histories | CLI entry → deterministic git and helper home → history steps → build-reference → five reference histories → guard re-pin | T-01a | not-started |  | gpt-6.2-sol |
| T-02 | composite | Offline semantic check and golden comparison | (children: T-02a, T-02b, T-02c, T-02d, T-02e) | T-01 | not-started |  |  |
| T-02a | leaf | Capture and fact extraction | check skeleton → capture → open tests → task, notes, validation, git and log facts → facts.json → guard re-pin | T-01b | not-started |  | gpt-6.2-sol |
| T-02b | leaf | Semantic projection normalization | DM-4 fields → NR-1 paths → NR-2 commit aliases → NR-3 branch aliases → NR-4 and canonical output → guard re-pin | T-02a | not-started |  | gpt-6.2-sol |
| T-02c | leaf | Hidden checks and missed defects | throwaway copies → HC-1 → HC-2 replay → HC-3 and missed defects → missing-pytest path → guard re-pin | T-02a | not-started |  | gpt-6.2-sol |
| T-02d | leaf | Semantic assertions and check outcome | SA-01–04, 14 → SA-05, 06 → SA-07–09, 12, 13, 15 → SA-10, 11 → propagation → outcome and exit → guard re-pin | T-02a, T-02b, T-02c | not-started |  | gpt-6.2-sol |
| T-02e | leaf | Golden comparison, candidates and reviewed expectations | compare and diff → update candidates → accept-expected → recording double → accept five expected results → guard re-pin | T-02b, T-02d | not-started |  | gpt-6.2-sol |
| T-03 | composite | Manifest, approval and run gate | (children: T-03a, T-03b, T-03c) | T-01, T-02 | not-started |  |  |
| T-03a | leaf | Manifest validation, hashing and instructions digest | DM-6 shape → cross-field rules → references → config hash → claude declaration → instructions digest → validate-manifest → guard re-pin | T-01a, T-01b | not-started |  | gpt-6.2-sol |
| T-03b | leaf | Interactive approval and run authorization | approve with terminal confirmation → run validity stage → authorization stage → run-golden.sh → guard re-pin | T-03a, T-02e | not-started |  | gpt-6.2-sol |
| T-03c | leaf | Preflight and dry-run plan | unit plan and keys → argv expansion → pinning → aliases and environment → workspace location → dry-run → double version → guard re-pin | T-03b, T-03a, T-01b | not-started |  | gpt-6.2-sol |
| T-04 | composite | Runner execution | (children: T-04a, T-04b, T-04c, T-04d) | T-02, T-03 | not-started |  |  |
| T-04a | leaf | Experiment directory and ledger | lock → creation and copies → opening rules → fsynced ledger → wiring into run → guard re-pin | T-03c, T-03b | not-started |  | gpt-6.2-sol |
| T-04b | leaf | Attempt launch through the adapter | scripted double → workspace and homes → child environment → reserve and launch → result and model check → usage and record → capture to finished → exit aggregation → guard re-pin | T-04a, T-03c, T-02e, T-01b | not-started |  | gpt-6.2-sol |
| T-04c | leaf | Isolation probes and evaluator-only material | probe script → targets and control → mechanisms → weaker designs and exit 5 → hidden checks under prefix → hashing double → guard re-pin | T-04b, T-04a, T-02c | not-started |  | gpt-6.2-sol |
| T-04d | leaf | Variant switches | switch validation → overlay digest preflight → application at launch → changed-paths baseline → guard re-pin | T-04b, T-03a, T-03c | not-started |  | gpt-6.2-sol |
| T-05 | composite | Recorded evidence, limits, cancellation and resume | (children: T-05a, T-05b, T-05c, T-05d) | T-04 | not-started |  |  |
| T-05a | leaf | Recorded imports and usage attachment | import validation → comparability → import record and capture → attach-usage → guard re-pin | T-04a, T-04b, T-03a, T-01a | not-started |  | gpt-6.2-sol |
| T-05b | leaf | Launch limits and variant halts | count limits → total wall limit → spend bound and reasons → refusal recording → critical halt → guard re-pin | T-04b, T-02c, T-05a | not-started |  | gpt-6.2-sol |
| T-05c | leaf | Cancellation and attempt timeout | signalling double → signal handling → per-attempt timeout → guard re-pin | T-04b, T-05b | not-started |  | gpt-6.2-sol |
| T-05d | leaf | Resume without automatic restart | resume opening → orphan recovery → schedule continuation and retries → guard re-pin | T-04a, T-04b, T-05a, T-05b, T-05c | not-started |  | gpt-6.2-sol |
| T-06 | composite | Independent evaluation | (children: T-06a, T-06b) | T-05 | not-started |  |  |
| T-06a | leaf | Evaluation records, disputes and outcomes | outcome table → evaluate records and events → disputes → late defects and exclusions → guard re-pin | T-05b, T-05c, T-05d, T-04a, T-02d | not-started |  | gpt-6.2-sol |
| T-06b | leaf | Blinded evaluation queue | queue writer → redactions → hooks in run and import → guard re-pin | T-04b, T-05a, T-04a | not-started |  | gpt-6.2-sol |
| T-07 | composite | Reports and promotion | (children: T-07a, T-07b, T-07c) | T-06, T-05, T-03 | not-started |  |  |
| T-07a | leaf | Report metrics and cost per accepted result | report loading → METRICS → spec 006 mapping → report fields and blinding map → bootstrap interval → report.md → guard re-pin | T-06a, T-06b, T-05a, T-03c | not-started |  | gpt-6.2-sol |
| T-07b | leaf | Holdout, contamination, privacy and retention | holdout sealing and reveal → contamination → privacy → retention → record validation and negative-catalog completion → guard re-pin | T-07a | not-started |  | gpt-6.2-sol |
| T-07c | leaf | Promotion verdict | decision tasks, D and R → bootstrap and alpha → verdict rules and comparisons → guard re-pin | T-07a, T-07b, T-03a | not-started |  | gpt-6.2-sol |
| T-08 | composite | Calculator, safe template and documentation | (children: T-08a, T-08b, T-08c) | T-07, T-03 | not-started |  |  |
| T-08a | leaf | Scenario calculator | input validation → fixed evaluation → range corners → break-even → calculate and example → guard re-pin | T-01b, T-01a | not-started |  | gpt-6.2-sol |
| T-08b | leaf | Safe manifest template and paid boundary | template → paid-boundary sweep → offline namespace re-run → guard re-pin | T-08a, T-07a, T-03b, T-03a, T-02e | not-started |  | gpt-6.2-sol |
| T-08c | leaf | Operating manual | GOLDEN-RUNS.md → index rows → command cross-check → guard re-pin | T-08b, T-08a, T-07c | not-started |  | gpt-6.2-sol |

## Execution Strategy

- **Ordering policy.** Strictly sequential stack in table order: T-01a, T-01b, T-02a, T-02b, T-02c, T-02d, T-02e, T-03a, T-03b, T-03c, T-04a, T-04b, T-04c, T-04d, T-05a, T-05b, T-05c, T-05d, T-06a, T-06b, T-07a, T-07b, T-07c, T-08a, T-08b, T-08c. Composites execute their children in listed order, and each composite's integration criteria run in `/phase-composite-validation` after its last child is reviewed and before the next composite's first child starts. Every dependency points backward; no parallel execution is claimed. Parts 1–3 of the specification (T-01, T-02) form a usable offline regression suite on their own; T-03 onward builds the strategy evaluation on top.
- **Cross-repository dependencies:** none (single repository).
- **Shared file `tests/golden-runs.py`.** Created by T-01a; every later leaf extends it by appending its own behaviour-named `unittest.TestCase` classes (one or more per leaf) and may add new shared fixture helpers at module level without changing the behaviour of existing helpers. A leaf never edits, renames, skips or weakens a test frozen by an earlier leaf; a correction to an earlier test is allowed only when that test is wrong, and is stated in the leaf's notes. Every leaf runs the full suite, not only its own classes.
- **Shared suite helpers that keep earlier tests valid.** The manifest-building helper introduced with T-03a defaults to values that later enforcement does not invalidate: `environment.isolation.mechanism: "none"` with both `accepted_weaker_isolation` flags true and a reason, `limits.accept_unverified_cost_cap: true`, `stop.resume_allowed: true`, generous limits, and empty `switches`. T-04c, T-05b and T-05d override these defaults explicitly in their own tests to exercise the strict paths.
- **Shared file `scripts/golden-eval.py`.** Created by T-01b; each leaf adds only its own subcommand or stage and keeps the exit-code table and output conventions.
- **Test double.** Created by T-02e (recording only); extended, never replaced, by T-03c (configurable `--version`), T-04b (scripted results), T-04c (file-hash recording), T-05c (sleep, ignored SIGTERM, signal recording), T-06b and T-07b (writing model ids and secret markers through scripted results). Its invocation ledger format stays `{argv, cwd, env_names, ORCHESTRAIL_HOME, ORCHESTRAIL_LOG_ROOT}` plus additive fields.
- **Reference fixtures and expected results.** T-01b authors the reference histories and overlays; T-02e accepts the five expected results with `origin: synthetic-reference`. A later leaf may correct a reference only when a check proves it non-canonical, and then rebuilds it with `build-reference` and re-accepts the affected expected result through `check --update` and `accept-expected` in the same leaf — never by editing `tests/expected/` as text.
- **Source guard (decision D-2 below).** Every leaf adds or edits `.py`/`.sh` files under `tests/` (at least `tests/golden-runs.py`), which changes the source guard's inventory digest. Each leaf therefore ends with its own re-pin step per `tests/fixtures/validator-runtime/README.md:9-28` (classify new call sites, recompute `inventory_sha256`, update the manifest digest) and runs the guard, its regression and external-source suites, the inventory oracle and `bash scripts/validate-contracts.sh`. Every stacked branch stays green; T-08c holds the final pin.
- **`pytest` on this host.** `pytest` is not importable by the current `python3` (task analysis, 2026-11-26). Until the owner provisions it outside any check run (spec A-27), pytest-dependent scenarios run through the exit-3 path and cannot be observed passing; the RED/GREEN evidence of those scenarios requires a provisioned interpreter. Leaves record which scenarios were observed under which interpreter.
- **Knowledge-base deltas.** No leaf edits `.ai/` files of this repository; state and progress deltas are returned to the orchestrator.

## Decomposition Decisions

| Subtask | Decision | Signals | Rationale |
|---------|----------|---------|-----------|
| T-01 | composite (Type 2) | S1=21, S2=2, S3=2, S4=false, S5=2 | Case catalog and reference builder are separately verifiable (catalog validity versus deterministic correct builds) with separate criteria clusters. |
| T-01a | leaf | S1=10, S2=1, S3=1, S4=false, S5=1 | One component: the self-contained case catalog with the harness that runs its checks offline; one cluster (catalog validity, including the no-`pytest` path that REQ-01 and REQ-35 jointly define). |
| T-01b | leaf | S1=11, S2=1, S3=1, S4=false, S5=1 | Builder and the histories it builds share one done-state (deterministic, correct reference runs). |
| T-02 | composite (Type 2) | S1=41, S2=5, S3=4, S4=false, S5=5 | Capture/facts, projection, hidden checks, assertions/outcome and comparison each have their own done-state and criteria. |
| T-02a | leaf | S1=10, S2=1, S3=1, S4=false, S5=1 | Capture and extraction produce one artifact set (capture plus facts) verified together. |
| T-02b | leaf | S1=7, S2=1, S3=1, S4=false, S5=1 | Pure transform from facts to projection. |
| T-02c | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | Evaluator-side hidden checks with one cluster (defect mapping, replay, environment). |
| T-02d | leaf | S1=9, S2=1, S3=1, S4=false, S5=1 | One rule engine over facts; all criteria are assertion results and the derived outcome. |
| T-02e | leaf | S1=7, S2=1, S3=1, S4=false, S5=1 | Compare, candidate and acceptance all operate on the expected-result store. |
| T-03 | composite (Type 2) | S1=24, S2=3, S3=3, S4=false, S5=3 | Manifest model, owner approval and preflight are separately testable gates. |
| T-03a | leaf | S1=9, S2=1, S3=1, S4=false, S5=1 | Validation and hashing of one document family. |
| T-03b | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | Owner consent and its enforcement; the wrapper is a thin entry to the same gate. |
| T-03c | leaf | S1=9, S2=1, S3=1, S4=false, S5=1 | Refuse-before-side-effect checks plus the reviewable plan they guard. |
| T-04 | composite (Type 2) | S1=31, S2=4, S3=3, S4=false, S5=4 | Directory/ledger, launch, isolation and switches each have separate criteria. |
| T-04a | leaf | S1=7, S2=1, S3=1, S4=false, S5=1 | Shared persistence component. |
| T-04b | leaf | S1=10, S2=1, S3=1, S4=false, S5=1 | One attempt life cycle from reservation to `finished`. |
| T-04c | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | Probe contract and weaker-design accounting. |
| T-04d | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | Switch validation and application. |
| T-05 | composite (Type 2) | S1=23, S2=4, S3=4, S4=false, S5=4 | Recorded intake, admission limits, termination and resume are separately testable. |
| T-05a | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | Intake of externally produced evidence (workspaces and usage) into an experiment. |
| T-05b | leaf | S1=7, S2=1, S3=1, S4=false, S5=1 | Launch admission decisions. |
| T-05c | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | Termination by signal or wall limit. |
| T-05d | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | Continuation of an interrupted experiment. |
| T-06 | composite (Type 2) | S1=11, S2=2, S3=2, S4=false, S5=2 | Outcome engine with records versus blinded queue. |
| T-06a | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | Records feed one outcome table. |
| T-06b | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | What a human evaluator can see. |
| T-07 | composite (Type 2) | S1=20, S2=3, S3=3, S4=false, S5=3 | Metrics/cost, safeguards and verdict are separately testable. |
| T-07a | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | One report builder producing numbers. |
| T-07b | leaf | S1=7, S2=1, S3=1, S4=false, S5=1 | Constraints on what a report may contain or reveal. |
| T-07c | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | One statistical verdict engine. |
| T-08 | composite (Type 2) | S1=17, S2=3, S3=3, S4=false, S5=3 | Calculator, safe default and manual are unrelated components closing the delivery. |
| T-08a | leaf | S1=7, S2=1, S3=1, S4=false, S5=1 | Isolated pure calculator. |
| T-08b | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | "Nothing paid runs by default" and its proof. |
| T-08c | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | Operating manual. |

Type 3 re-slicing does not apply: single repository, no cross-repository frozen contract (S4 = false everywhere).

### D-1 — Top-level shape and size

| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| V1: eight Type 2 composites following the specification's eight delivery parts, 26 healthy leaves | 3 | 4 | 4 | 5 | 4 | 20 |
| V2: 26 flat top-level leaves without composites | 3 | 4 | 2 | 4 | 4 | 17 |
| V3: eight leaves, one per delivery part | 5 | 3 | 3 | 2 | 4 | 17 |

**Winner:** V1 — it keeps the eight-part target the specification and the task analysis name while every leaf satisfies S2 = 1 and S5 = 1 and 3–15 steps.
**Anti-overengineering check:** passed — composites are the canonical Type 2 shape, not a new abstraction; V3 fails the leaf-health invariant (each part has S2 ≥ 2, S5 ≥ 2) and is not admissible.
**Evidence:** `rules/workflow-reference.md → Autonomous Subtask Classifier` (leaf-health invariant, depth-2 cap) and `→ Decomposition Rules` (target 8, do not merge unrelated components); spec Notes → Delivery order. Deviations from the eight parts, each recorded here: holdout reveal and contamination (part 6) move to T-07b because they are only observable in reports; the blinded queue (part 6) is written by the runner but delivered in T-06b; attach-usage joins recorded imports in T-05a as external evidence intake; the per-composite SA-10 variant is built inside the suite by T-02d.

### D-2 — Source-guard re-pin placement

| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| V1: every leaf re-pins after its own last `.py`/`.sh` edit | 3 | 5 | 5 | 5 | 4 | 22 |
| V2: one re-pin in the last leaf that adds a file under `tests/` | 4 | 3 | 2 | 1 | 4 | 14 |

**Winner:** V1 — the guard runs inside `scripts/validate-contracts.sh`, and every leaf edits `tests/golden-runs.py`, so a single late re-pin would leave every stacked branch failing the project's test suite.
**Anti-overengineering check:** passed — follows the documented procedure unchanged.
**Evidence:** `scripts/validate-contracts.sh:6119-6127` (`test_nested_validator_source_guard`); `tests/fixtures/validator-runtime/source_guard.py` `inventory_sources` (every `.sh`/`.py` under `tests/`); `tests/fixtures/validator-runtime/README.md:9-28`; spec Notes → Guard maintenance; ADR-0020 Decision 2.

### D-3 — Ownership of criteria that span components

Several specification criteria need components delivered by different leaves (AC-02, AC-03, AC-04, AC-07, AC-13, AC-16, AC-21, AC-39, AC-43, AC-44, AC-45, AC-46).

| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| V1: the leaf that delivers the last needed component owns the whole criterion; earlier leaves test their own clauses under requirement-cited criteria | 4 | 4 | 4 | 4 | 4 | 20 |
| V2: split each such criterion into per-leaf fragments | 3 | 3 | 2 | 4 | 4 | 16 |
| V3: reorder leaves so every criterion's components land in one leaf | 2 | 2 | 3 | 3 | 3 | 13 |

**Winner:** V1 — every criterion keeps its exact wording and exactly one owner, and the owner's scenario is red for the right reason (its own component is missing).
**Anti-overengineering check:** passed.
**Evidence:** spec Traceability; `rules/tdd.md` (a new test must fail for the right reason); `principles/testing-standards.md`. Consequences: AC-07 is owned by T-08c (its last clause is the manual; T-07c delivers and freezes the verdict tests under REQ-12, which T-08c must not modify); AC-13 by T-07b (N-07's reader clause); AC-02 by T-08b; AC-04 and AC-21 by T-07a; AC-46 by T-05a; AC-39 and AC-45 by T-02d; AC-44 by T-03b; AC-43 by T-03c; AC-16 by T-05b; AC-03 by T-02e.

### D-4 — Position of normalization

| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| V1: projection leaf (T-02b) before assertions (T-02d), comparison last (T-02e) | 4 | 4 | 4 | 5 | 4 | 21 |
| V2: normalization inside the comparison leaf | 4 | 4 | 4 | 3 | 4 | 19 |

**Winner:** V1 — AC-39 and AC-45 assert projection fields next to assertion results, so the projection must exist before the assertion leaf; accept-expected still needs assertion statuses, so comparison stays last.
**Anti-overengineering check:** passed.
**Evidence:** spec AC-39, AC-45, REQ-17, DM-4.

### AC ownership map

| Criterion | Owner | Criterion | Owner | Criterion | Owner |
|---|---|---|---|---|---|
| AC-01 | T-02e | AC-17 | T-05c | AC-33 | T-03a |
| AC-02 | T-08b | AC-18 | T-05d | AC-34 | T-05b |
| AC-03 | T-02e | AC-19 | T-05b | AC-35 | T-03c |
| AC-04 | T-07a | AC-20 | T-06a | AC-36 | T-02d |
| AC-05 | T-07a | AC-21 | T-07a | AC-37 | T-01b |
| AC-06 | T-08a | AC-22 | T-06a | AC-38 | T-03a |
| AC-07 | T-08c | AC-23 | T-07b | AC-39 | T-02d |
| AC-08 | T-04b | AC-24 | T-07a | AC-40 | T-04d |
| AC-09 | T-04b | AC-25 | T-01a | AC-41 | T-07c |
| AC-10 | T-02d | AC-26 | T-04b | AC-42 | T-03a |
| AC-11 | T-02e | AC-27 | T-08b | AC-43 | T-03c |
| AC-12 | T-02d | AC-28 | T-05a | AC-44 | T-03b |
| AC-13 | T-07b | AC-29 | T-03c | AC-45 | T-02d |
| AC-14 | T-04c | AC-30 | T-04a | AC-46 | T-05a |
| AC-15 | T-03b | AC-31 | T-07b | | |
| AC-16 | T-05b | AC-32 | T-07a | | |

Every requirement REQ-01–REQ-55 is cited by at least one leaf criterion; leaves T-02a, T-02b, T-02c, T-06b own no specification criterion and carry requirement-cited criteria only.

### Specification conflict resolved by `/pd-design`

N-08 (Edge Cases) states that a normalization exception yields `technically-incomplete` and exit 8, while DM-10 row 4 lists only capture, extract, evaluate, SA and HC errors and DM-10 states that normalize and compare statuses never change the outcome. T-02b's criterion asserts only the uncontested part (normalize `error`, exit 8); the outcome for a normalization error must be decided in `/pd-design` and recorded.

Resolution (2026-11-26, `/pd-design`): REQ-19 requires every negative-catalog entry, N-08 included, to yield an outcome other than `independently-accepted`, and REQ-15 treats an unparsable source as `error`; so a normalize `error` makes the attempt `technically-incomplete` with exit 8, extending DM-10 row 4, while a compare `failed` still never changes the outcome. T-02d's outcome step and criteria now carry this; T-02b is unchanged. The DM-10 sentence is a `/spec-sync` follow-up (task `state.md` → `## Solution Design → ### Decision`).
