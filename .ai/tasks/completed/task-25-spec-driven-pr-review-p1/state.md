spec_path: .ai/specs/25-spec-driven-pr-review.md
contract_version: 0.9.0
flow: full
active_phase: 1
spec_phase_count: 2

## Phases
- discovery: complete
- execution: complete
- validation: complete

- finalization: complete
## Spec Phases
- phase 1: complete — Offline review comparison — .ai/tasks/todo/task-25-spec-driven-pr-review-p1
- phase 2: deferred — Deferred standalone service — —

## Task Analysis
→ archived to state-archive.md

### Assumptions
- First delivery covers only the offline procedure and fixture acceptance (source: specification Scope and A-10, A-13).
- One common packet and pinned review policy underpin both variants. The treatment adds explicit requirement coverage (source: specification Pair execution and A-11).
- Independent fixture checks may overlap when their outputs are disjoint. Git and shared-state handoffs remain sequential (source: specification A-12 and First delivery handoff).
- flow: full — gate: 1fail 2fail 3pass 4pass. The fixture and documentation surface exceeds three files and introduces offline protocol invariants.

## Open Questions (batch)
None

## Decomposition
- decomposition: complete
- subtasks: T-01, T-02, T-03, T-04, T-05

## Subtask Progress

T-01 | Pin approved case packets | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: Independent validation passed after approval and snapshot rejection fixes
  target_files: docs/offline-review/fixtures/test_case_packets.py, docs/offline-review/fixtures/test_case_packet_rejections.py, docs/offline-review/case-packet.md, docs/offline-review/fixtures/prepare_case.py
  blocker: none
  notes: tdd: contract — three tests, acceptance coverage 2/2
  tdd: red digest — approved PR/milestone and shared digest → test_admission_pins_one_packet_for_both_variants; exclusion with missing approval → test_admission_without_approval_records_exclusion; approval bound to annex contents → test_admission_after_annex_change_rejects_stale_approval
  tdd: regression tests reached RED before the fix and both original and regression suites passed five methods across eleven scenarios.
  proposals: Include both fixture suites in the operator verification command.
  branch: feat/offline-review-case-packets
  base_branch: main
  base_commit: aabc225e12126f4ed3958a1e9c48549810541a56
  commits: 544e3e3c457515e6f5ab566d3951f27a6497f8b0 test: cover approval and packet parity for offline reviews, e272fea77197dc31b3e48393721dc663c845fdb9 feat: prepare pinned packets for offline review, 61efc1e65f915477bb5bff8209da016e17e60454 test: cover incomplete offline review packet inputs, 0d480037f1563f24da23a9db8fcec2e5a61c0701 fix: reject incomplete offline review packet inputs
  pr: #132 ready

T-02 | Verify isolated paired reviews | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: Independent validation passed for isolation, frozen observations and coverage
  target_files: docs/offline-review/fixtures/test_paired_reviews.py, docs/offline-review/fixtures/paired_review.py, docs/offline-review/paired-reviews.md
  blocker: none
  notes: tdd: contract — five tests, acceptance coverage 2/2
  tdd: red digest — isolation, immutable first observation, and due/future coverage. Frozen test SHA-256 674aeed1f78d2c7feb403fb06dfe3acb0afc9f0778a3544eba6fa150fd6168c8.
  proposals: Exercise concurrent archive capture with controlled ordering.
  branch: feat/offline-paired-reviews
  base_branch: feat/offline-review-case-packets
  base_commit: 0d480037f1563f24da23a9db8fcec2e5a61c0701
  commits: f845852a33708b6e0ab0b2e4a983f4f737d08985 test: cover offline paired review isolation and coverage, a5d5d33b53fc1d6dd1d469abcc501c97e8bb919b feat: verify isolated offline paired reviews
  pr: #133 ready

T-03 | Document bounded dispatch and recovery | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: Independent validation passed for bounded dispatch and recovery
  target_files: docs/offline-review/fixtures/test_dispatch.py, docs/offline-review/fixtures/dispatch_fixture.py, docs/offline-review/dispatch.md
  blocker: none
  notes: tdd: contract
  tdd: red digest — budget equality, fair mixed dispatch, capacity release, uncertainty and cutoff; five frozen methods; SHA-256 417b3f184241256168d7b33a9dd366aee4969b8f818c7dc6ebad7b75b2248ee0
  branch: feat/offline-review-dispatch
  base_branch: feat/offline-paired-reviews
  base_commit: a5d5d33b53fc1d6dd1d469abcc501c97e8bb919b
  commits: c9d511acc294f77439e4f89ba40af3874ce7d7a6 test: cover bounded offline review dispatch, 33a9151cac8a9cde3842fd46b36fa9b181ae5945 feat: verify bounded offline review dispatch
  pr: #134 ready

T-04 | Derive blinded paired decisions | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: Independent revalidation passed after canonical severity correction
  target_files: docs/offline-review/fixtures/test_paired_report.py, docs/offline-review/fixtures/test_paired_report_adjudication.py, docs/offline-review/fixtures/paired_report.py, docs/offline-review/adjudication-and-report.md
  blocker: none
  notes: tdd: contract
  tdd: red digest — equality, threshold crossings, deduplication, incomplete cases and frozen adjudication; five methods; SHA-256 9d3068c0e8787a125cc0ddb6ff3b1afa9a95a7c4a943da5feacd859ded136f5c
  tdd: frozen canonical severity regression failed before fix and passed afterward.
  proposals: Cover mixed cohorts with both conflicted and unaffected complete pairs.
  branch: feat/offline-review-decisions
  base_branch: feat/offline-review-dispatch
  base_commit: 33a9151cac8a9cde3842fd46b36fa9b181ae5945
  commits: 640922635aa730b302bc55ad2dc8c71146575745 test: cover blinded paired review decisions, 40fd418898a1c07a5a1760b7fcf2438605ab6ba9 feat: derive blinded paired review decisions, dd40182fdabeb1a27281d75c789d5dd9466368bb test: cover conflicting canonical defect severity, fa57c6dc4c05574cc5eeb0dd2c8775ea04b606eb fix: preserve canonical defect severity in paired reports
  pr: #135 ready

T-05 | Verify offline rehearsal readiness | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: Independent validation passed for integrated rehearsal and readiness gates
  target_files: docs/offline-review/fixtures/test_rehearsal.py, docs/offline-review/fixtures/rehearsal_fixture.py, docs/offline-review/fixtures/rehearsal_probe.py, docs/offline-review/README.md, docs/README.md
  blocker: none
  notes: tdd: contract
  tdd: red digest — packet mismatch, historical exposure, six first observations, approval and settings interlocks; four methods; SHA-256 00f1ac84cf6e08c3bfdea60007892ca0446a19e80613eb963a77577ff8520d92
  branch: feat/offline-review-rehearsal
  base_branch: feat/offline-review-decisions
  base_commit: fa57c6dc4c05574cc5eeb0dd2c8775ea04b606eb
  commits: 3d9d358c7cc61e2ddc93302fa70f8c290a787036 test: cover integrated offline review rehearsal, 975c8db750d100fda406012b1fd08fad3f72119d feat: verify integrated offline review rehearsal
  pr: #136 ready

T-06 | Capture unstarted cutoff observations | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: Independent verification passed for cutoff through dispatch, capture and reporting
  target_files: docs/offline-review/fixtures/test_cutoff_observation.py, docs/offline-review/fixtures/paired_review.py, docs/offline-review/paired-reviews.md
  blocker: none
  notes: tdd: contract
  tdd: red digest — cutoff through dispatch, capture and report; rejection of invalid launched or unstarted observations; SHA-256 bbe2d87e3277193c9905403865010361ded2a7e1651f11dfc698dbeba082adbe
  branch: fix/offline-cutoff-observations
  base_branch: feat/offline-review-rehearsal
  base_commit: 975c8db750d100fda406012b1fd08fad3f72119d
  commits: 6e6c52a896820ade95bf71fd097dcf60b787ae75 test: cover cutoff reviews without an attempt, 3a036e68e4421cd63541bb6653710906a504797b fix: archive unstarted reviews at comparison cutoff, 4aaf005cf293cd236510cd368b8684d4e1d48322 docs: record offline review validation and delivery
  pr: #137 ready

## Model Selection
- selection: complete
- provider: openai
- execution_routing: Codex session default for all five leaves per owner direction. Historical discovery recommendations are retained as evidence. Dispatch uses neither a model override nor a reasoning override.
- catalog: user configuration at orchestrail/model-catalog.md
- catalog_refresh: 2026-11-24
- support: 2026-11-24, current Codex collaboration tool declaration. Sol and medium are exposed. Model-specific context, tool access and execution eligibility require a separate check.
- economics: No comparable-task cost evidence was supplied. The delegated fallback choice uses medium effort on a general-purpose coding model for this bounded offline workload.
- T-01: gpt-6.2-sol (preliminary), reasoning: medium for bounded protocol and fixture work, support: declared by the current Codex worker interface. Independent catalog quality, model-specific context and tool bounds, comparable cost and actual worker identity are unknown.
  description_sha256: c57ab6ba6aaf5d561d8cf855bb155696c66209a8979b2ecdda481f0331d93205
  plan_row_sha256: 82d8e86b834d7ce7b3eefac8e9c53a3d8b13c6ccdee544d46ff88977cc126b9b
- T-02: gpt-6.2-sol (preliminary), reasoning: medium for bounded protocol and fixture work, support: declared by the current Codex worker interface. Independent catalog quality, model-specific context and tool bounds, comparable cost and actual worker identity are unknown.
  description_sha256: a5ad17e5ce8c54ba461fa918d5d5b74b059b3968e81c16c85cb75a68e2ce1e77
  plan_row_sha256: 96b357c8239247914893a2f8ea2197fc85d283030b8f54d687384e468d8a452f
- T-03: gpt-6.2-sol (preliminary), reasoning: medium for bounded protocol and fixture work, support: declared by the current Codex worker interface. Independent catalog quality, model-specific context and tool bounds, comparable cost and actual worker identity are unknown.
  description_sha256: fde6fe40cd1dbba8e3ceecbff7a615fcef492bb0097f88756cf5e788b6b2b06a
  plan_row_sha256: 72263bf8da887ada59a4e56c3de401fe78063c914c7a509f5f3029ec4263a0ff
- T-04: gpt-6.2-sol (preliminary), reasoning: medium for bounded protocol and fixture work, support: declared by the current Codex worker interface. Independent catalog quality, model-specific context and tool bounds, comparable cost and actual worker identity are unknown.
  description_sha256: 43ac2e89233e479f2abf74449385e7aabf2c24f062c59c8ae84009e3b31784db
  plan_row_sha256: 361007173e478daf8fd9c6369be3026473c12904669c76907345b85a1c0a0add
- T-05: gpt-6.2-sol (preliminary), reasoning: medium for bounded protocol and fixture work, support: declared by the current Codex worker interface. Independent catalog quality, model-specific context and tool bounds, comparable cost and actual worker identity are unknown.
  description_sha256: 9e57435535ba69ca4cecf565f0be73f0c84c5ff6cb8f3c7182087df11cbbb29e
  plan_row_sha256: 3d5610cdecc98a73b5d1c7a7298425c8656518128b75daab9d8e19bda4c2d5ce

## Solution Design

### Variants
→ archived to state-archive.md

### Decision
Use local Markdown operator instructions, pinned input and output templates, and executable synthetic checks scoped to the offline materials. Maintain the existing review workflows and the manual operator dispatch boundary specified in the first delivery.
adr: not triggered — the design applies the specification's binding local procedure and the existing file-based project approach without changing repository architecture or establishing a new platform contract.

### Scope
#### In
Operator protocol, record templates and synthetic verification for case admission, paired reviews, bounded dispatch, adjudication and rehearsal.
#### Out
Historical execution, hosted services, automated scheduling and merge gating.

### Rejected
→ archived to state-archive.md

### Off-limits
- Preserve production workflow definitions, remote integrations and historical inputs. Keep the standalone service deferred.

### Invariants
- Both arms share one approved, immutable packet and matching settings.
- Sibling contents and historical claims remain outside reviewer scope. Verdicts freeze before variant disclosure.
- The first attempt and its terminal evidence remain immutable. Uncertain dispatch retains capacity and liability.
- Readiness and decision results disclose insufficient or contaminated evidence and preserve historical execution as pending when applicable.

### Acceptance Criteria
- AC-45: Pin a common packet for each eligible PR and milestone and record missing-approval exclusion.
- AC-46: Demonstrate session isolation and immutable first observation capture.
- AC-47: Check each due criterion has one disposition with evidence or a named gap, and isolate future scope.
- AC-48: Demonstrate that invalid rehearsal evidence blocks main dispatch and that valid rehearsal requires approved inputs and locked settings.
- AC-49: Reproduce bounded dispatch, equality, uncertain recovery and terminal cutoff behavior.
- AC-50: Reproduce blinded adjudication and report deltas, shared spend and outcomes for equal, exceeded and insufficient evidence fixtures.

### Autonomous Decision
| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| Local operator protocol | 5 | 5 | 5 | 5 | 5 | 25 |
| Interactive checklist | 3 | 4 | 3 | 4 | 4 | 18 |

**Winner:** Local operator protocol. The files map directly to the approved manual procedure and keep fixture checks independently reproducible.
**Anti-overengineering check:** Passed. Each record serves an explicitly required acceptance scenario.
**Evidence:** Specification first-delivery scope, .ai/memory/architecture.md and the existing documentation index.

## Execution Report
- T-06 | reviewed | Cutoff observation capture and report compatibility | PR #137
- T-01 | reviewed | Approved PR and milestone packets, exclusion checks, regression fixes | PR #132
- T-02 | reviewed | Isolated sessions, first observations, due and future coverage | PR #133
- T-03 | reviewed | Bounded reservations, recovery and cutoff | PR #134
- T-04 | reviewed | Blinded adjudication, exact decision metrics and canonical severity regression | PR #135
- T-05 | reviewed | Integrated rehearsal and readiness interlocks | PR #136
- Proposals retained for post-delivery review. No proposals applied.
- Historical comparison remains pending approved historical inputs and locked settings.

## Contract Check

### Invariants
| Obligation | Status | Evidence |
|---|---|---|
| Both arms share one approved, immutable packet and matching settings. | PASS | Packet admission verifies matching immutable digests. The paired-review procedure pins common settings. |
| Sibling contents and historical claims remain outside reviewer scope. Verdicts freeze before variant disclosure. | PASS | Landlock rehearsal denies historical and sibling access. The operator protocol freezes blinded verdicts before disclosure. |
| The first attempt and its terminal evidence remain immutable. Uncertain dispatch retains capacity and liability. | PASS | Archive tests preserve first observations. Dispatch tests retain uncertain slots and reservations across restart. |
| Readiness and decision results disclose insufficient or contaminated evidence and preserve historical execution as pending when applicable. | PASS | Report tests retain gaps and exclusions. The nominal rehearsal leaves historical execution pending. |

### Acceptance Criteria
| Obligation | Status | Evidence |
|---|---|---|
| AC-45: Pin a common packet for each eligible PR and milestone and record missing-approval exclusion. | PASS | Case packet fixtures verify PR and milestone digest parity and approval rejection. |
| AC-46: Demonstrate session isolation and immutable first observation capture. | PASS | Paired-review fixtures verify permitted and denied filesystem access and immutable capture. |
| AC-47: Check each due criterion has one disposition with evidence or a named gap, and isolate future scope. | PASS | Coverage fixtures verify three due dispositions, reject missing or duplicate rows, and preserve future scope. |
| AC-48: Demonstrate that invalid rehearsal evidence blocks main dispatch and that valid rehearsal requires approved inputs and locked settings. | PASS | Rehearsal fixtures verify two independent failure gates and both main-run prerequisites. |
| AC-49: Reproduce bounded dispatch, equality, uncertain recovery and terminal cutoff behavior. | PASS | Dispatch and cutoff regression fixtures verify ready work, budget equality, restart and terminal records. |
| AC-50: Reproduce blinded adjudication and report deltas, shared spend and outcomes for equal, exceeded and insufficient evidence fixtures. | PASS | Report and cutoff regression fixtures verify exact paired deltas, blinded verdicts, spend and incomplete-pair evidence. |

### Off-limits
| Obligation | Status | Evidence |
|---|---|---|
| Preserve production workflow definitions, remote integrations and historical inputs. Keep the standalone service deferred. | PASS | Independent review found only local fixtures and operator documentation in the implementation. Historical execution and the standalone service remain deferred. |

## Code Review
### Findings
1. important — Capture rejects the null attempt ID of a queued cutoff observation.
2. optional — Pass only the opaque claim projection and case evidence to the synthetic adjudicator function.

### Summary
One important issue resolved and independently reverified in the cutoff fix. One optional fixture-interface improvement deferred. The final stack review found no other issues.

## Issue List
### Approved
1. Resolved in T-06 and PR #137. The queued cutoff observation is durably captured and included in the paired report as incomplete.

### Deferred
2. Further narrow the internal synthetic adjudicator argument; operator masking already uses its own view.

## Fix-Tasks
fixes-created: complete
fixes-count: 1
Created: T-06-fix-cutoff-observation

### Fix Classification
| Issue | Severity | Gate 1 | Gate 2 | Gate 3 | Gate 4 | Grouping | Branch |
|-------|----------|--------|--------|--------|--------|----------|--------|
| #1 Cutoff observation compatibility | important | pass: three files | pass: preserves existing invariant | pass: synthetic procedure only | pass: existing format | shared | T-06-fix-cutoff-observation |

## Deferred
- [source: issues] Optional fixture refinement to pass only opaque claims and case evidence to the synthetic adjudicator. The operator protocol already conditions adjudication on an arm-free projection.
- Historical comparison awaits approved inputs and locked settings. The standalone service phase awaits the historical comparison and an owner decision.

## Final Verification
- Date: 2026-11-24.
- Implementation revision: 3a036e68e4421cd63541bb6653710906a504797b.
- Independent stack-tip validation: all six acceptance criteria, four invariants and the off-limits boundary passed.
- `python3 -IB -m unittest discover -s docs/offline-review/fixtures -v`: 27 passed. The cutoff regression verifies dispatch, capture and scoring and rejects invalid terminal records.
- Integrated rehearsal: three cases, six immutable first observations, three eligible pairs, exposure of nine synthetic units. Historical execution remained pending without approved inputs and locked settings.
- `bash scripts/validate-contracts.sh`: 725 passed, 0 failed, 2 skipped.
- Regression TDD test file unchanged after its test-only commit. Verification covers local synthetic data and the trusted Linux fixture boundary.

## Spec Sync
sync: complete
synced_at: 2026-11-24T18:07:13+06:00
deltas: 0 (implemented-differently: 0, not-implemented: 0, implemented-beyond: 0)
spec: .ai/specs/25-spec-driven-pr-review.md

Scope: Phase 1 acceptance verified without rewrites. The historical comparison and Phase 2 remain explicitly deferred under the spec.
