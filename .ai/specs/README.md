# Specifications and execution roadmap

Review date: 2026-11-06. This index separates delivered source cleanup from planned
roadmap work. The owner authorized workflow optimization and specification reconciliation;
that request does not schedule unrelated roadmap implementation, deployment or paid
comparisons. Project artifacts use English.

Start with `/phase-discovery .ai/specs/<file>.md`; use `/discovery` after the command
migration. Completed records are historical evidence, not work to repeat. A completed
task does not authorize merging, tagging, or publication.

## Current implementation status

**Parallel execution direction, 2026-11-25:** The owner requested automatic safe
parallel execution across the task graph in both `spec-run` and `phase-execution`,
parallel-aware Discovery, and preservation of stacked PRs via sequential materialization.
[Program specification and implementation plan](027-parallel-execution-program.md)
records this direction and its unresolved implementation blockers. Former spec 23 was
consolidated into that specification; specs 020 and 024 retain only their independent
decomposition and composite-branch scope and require a fresh readiness review. The
existing sequential runtime remains in force until changes are delivered.

The [delivery review](../../docs/audits/2026-11-06-specification-delivery-review.md)
covers all **23 specifications** at main revision `23bded3`: seven historically
completed foundations (00-06), one partially delivered runtime specification whose
task was closed by owner decision, and fifteen planned/backlog specifications.
Each specification now distinguishes existing foundations from its outstanding scope.
The review does not certify a fresh full suite or deployed installations.

Runtime task closure is administrative. Warning-fixture, identity-scan and source-guard
changes are integrated; concurrent acceptance execution, opt-in timing, an additional
identity-output I/O correction and comparative performance acceptance remain undelivered.
Deleted experimental branch names do not count as delivery. The dated review above remains
historical evidence. The state tool was merged and archived on 2026-11-16, as recorded in
[progress](../memory/progress.md). Current active work is listed in
[task state](../memory/state.md); the rules/workflows audit (08) was delivered, accepted and closed
on 2026-11-19, and the post-merge closure implementation below does not advance other roadmap scope.

## Owner-scheduled post-merge closure

On 2026-11-17 the owner approved [task finalization](completed/025-task-finalization.md) as a separate development task, outside the earlier roadmap ordering. Implementation was independently validated locally on 2026-11-18 on the pinned multi-repository support dependency: full validator 725/0/2 and all 156 finalization acceptance tests passed; staged provider outputs were generated in isolation. The owner authorized integration on 2026-11-18: the dependency and all three implementation branches were merged in order into main at 75168ca; 194 fresh post-merge acceptance tests passed. Live synchronization and this task's own finalization remain separate follow-ups. It does not advance unrelated roadmap scope or authorize deployment. Current execution evidence lives in [task state](../tasks/todo/task-025-task-finalization/state.md).

## Nine token optimization workstreams

There are **nine feature-sized tasks: two expanded existing specs and seven new specs**.
Supporting roadmap items remain separate. Each workstream has one owning spec;
consumers reference its contract rather than redefining it.

| # | Workstream | Owning spec | Boundary and evidence |
|---|---|---|---|
| 1 | Telemetry and baseline | [006 — telemetry](completed/006-cost-and-duration-telemetry.md) | Actual usage, role/stage/attempt attribution, cache accounting, API-equivalent valuation, coverage and accepted-result cost |
| 2 | Compact context preparation | [014 — task context](014-task-context-and-reuse.md) | Stable context reuse, fresh leaf views, task contracts, relevant files, load-once behavior, cache-compatible ordering |
| 3 | Shorter instructions and outputs | [013 — context tiering](013-context-tiering.md) | Compact rules, on-demand reference, explicit loads, concise reports with evidence |
| 4 | Orchestrator overhead | [015 — controller overhead](015-orchestrator-overhead.md) | Fewer status turns, bounded history, deterministic inspection and delta rendering; shared state stays single-writer |
| 5 | Review overhead | [017 — scoped verification](017-scoped-verification.md) | Independent review, evidence reuse for unchanged inputs, finding-led repair review with impact expansion |
| 6 | Bounded tool output | [016 — tool output](016-bounded-tool-output.md) | Bounded previews, full local artifacts, preserved errors and exit status, complete retrieval |
| 7 | Reasoning effort | [018 — effort policy](018-reasoning-effort-policy.md) | Role/stage/complexity-based effort, capability checks, conservative fallback, measured quality |
| 8 | Local repair and escalation | [019 — repair policy](019-local-repair-and-escalation.md) | Opt-in bounded repair, preserved correct code and RED evidence, independent recheck, explicit escalation |
| 9 | Economical decomposition | [020 — decomposition](020-cost-aware-decomposition.md) | Coherent leaves, measured setup/review overhead, architectural boundaries, integration and AC coverage |

This is an ownership map, not a measured ranking of savings. No percentage or dollar
saving is established here. Word/byte reductions are diagnostics; token usage and
API-equivalent valuation are separate measurements.

## Delivered source cleanup — 2026-10-28

The workflow set now has clearer guards, resumable phase/checkpoint handling, explicit
parent-versus-standalone context loading, consistent model-selection scoring, protected
compression, conservative restack recovery, and source-backed spec reconciliation.
A separate token-efficiency pass removed repeated prose; instruction-contract checks
cover these interfaces. The historically cited `docs/audits/2026-10-28-workflow-clarity-and-size.md`
is absent from the current tree and is not available evidence. These are source changes, not evidence of measured token/cost
savings or deployed behavior.

That cleanup alone partially advanced 04/11/08/12/13/15 without completing them.
Cached catalog selection, conservative quality/economic filtering, compatible plan
resolution and installed workflow guidance were subsequently delivered under
[005](completed/005-model-catalog-cache.md), with 594 required checks passing and 87 focused model tests.
Full rule inventory/naming, reference tiers/load metadata, content-hash packets,
effort/repair policies and economic evaluation remain separate work. Completed 00–06
remain foundations, not work to repeat. No deployment or model-usage savings is claimed.

## Shared acceptance gates

These gates are part of each owning spec's acceptance contract. Feature implementation
can be accepted with deterministic evidence. Promotion of a cheaper default also needs
an explicitly approved comparative evaluation under spec 012.

| Gate | Required evidence |
|---|---|
| G1 — Attribution | Source/deployed versions, actual harness/model, configuration, role/stage/attempt, usage coverage, and experiment identity where applicable. Use spec 006's schema; missing counters are not zero. |
| G2 — Comparable measurement | Same initial revision, specification, acceptance criteria and task set. Report input, cached input, cache writes, output/reasoning where available, API-equivalent cost, calls, retries, wall time and coverage separately. No model-run claims from word counts or simulations. |
| G3 — Independent quality | Preserve test-first order, frozen RED evidence, contracts, git rails, owner stops, independent Validator and integration checks. Tests and reviewer verdicts are evidence, neither is absolute truth. Evaluate held-out criteria and later defects under spec 012. |
| G4 — Compatibility | Legacy artifacts remain readable. Missing optional capabilities use a documented conservative path; unsafe or ambiguous state stops before mutation. Unknown usage stays unknown. No hidden model substitution. |
| G5 — Ownership | Only the authorized writer updates shared state and git. Helpers do not spawn models, become a mandatory runtime, or bypass approval/sandbox policies. Spec 009 is scheduled as an optional, unwired tool (ADR-0021). |
| G6 — Testing | New behavior has failing deterministic fixtures before implementation and passing fixtures afterward. Markdown receives contract/reachability checks. Paid runs never start during ordinary validation, sync, or default CI jobs. |
| G7 — Rollback | Document disable/resume from the last verified checkpoint using the previous policy. Preserve task history, evidence and verified code. |
| G8 — Economics | Compare expected total cost of a correct result, including planning, tools, verification, repair and escalation. Subscription payments are actual billing; API-equivalent USD is not an invoice or quota estimate. No production cost/time cap is introduced. |

## Dependency order

Historical foundations follow ADR-0009 and completed work. The requested optimization
program adds the edges below; rows are one valid sequential order. Record changes to
accepted behavioral contracts in an ADR during implementation. This index does not
rewrite historical decisions. Files in `scripts/` are the current helpers; old bare
script names in historical context identify their earlier locations.

| Order | Spec | Prerequisites | Review disposition |
|---|---|---|---|
| Done | [001 — scrub](completed/001-sensitive-data-scrub.md) | — | Retain completed history and approved exceptions |
| Done | [002 — source of truth](completed/002-git-source-of-truth.md) | 001 | Retain license/tag deferrals; unchecked historical boxes do not reopen the task |
| Done | [003 — log vocabulary](completed/003-run-log-vocabulary-validation.md) | 002 | Retain strict grammar, non-blocking writes and read-only lint; merge status belongs to task records |
| Done | [010 — audit](completed/010-rules-workflows-audit.md) | 002 | Pinned audit delivered and accepted (`Accepted: owner 2026-11-18`); follow-ups applied, spec 011 amended; PRs #105–#125 merged; specification archived with its identity-ledger path updated |
| 2 | [011 — harnesses/naming](011-model-only-harnesses-and-rule-naming.md) | 002, 010 | Preserve IDs; capability-based behavior and current script paths |
| 2a–2b | [011 — phased delivery](011-model-only-harnesses-and-rule-naming.md#phase-1--harness-infrastructure-and-inventory) | 002, 010; phase 2 after phase 1 integration | Phase 1 owns infrastructure and inventory; phase 2 owns naming, finalization and integrated verification. Requirements remain pending until their owning phase passes; the original specification is complete only after both phases. |
| Done | [005 — catalog](completed/005-model-catalog-cache.md) | Current-invocation capabilities; wider 011 migration remains separate | Reviewed cached catalog, conservative selection and compatible plan resolution; PRs #31–#36 merged |
| Done | [004 — logging](completed/004-hook-based-logging.md) | 003; minimal harness/registry scaffold | Reviewed explicit correlation, owned hooks and exact timing; minimal hook scaffold only, wider harness migration remains pending |
| Done | [006 — telemetry](completed/006-cost-and-duration-telemetry.md) | 003, 004 | Reviewed offline telemetry and recovery; PRs #37–#63 merged; 619 required checks passed |
| Done | [007 — git rails](completed/007-harness-git-rails.md) | 006 (011 not required, ADR-0017) | Integrated before 08/09: #64 marked merged, #65–#75 closed after local stack integration; historical 717 required checks passed; residual risks X1–X20 retained |
| Closed; partial | [008 — validator runtime](completed/008-test-suite-runtime.md) | — | Owner closed the task after #77–#79 merged. Warning-prefix, per-file scan and bounded guard delivered; scheduling, timing and comparative targets remain unmet. No automatic resumption or passing AC claim |
| 6 | [012 — regression/evaluation](012-golden-run-tests.md) | 002, 011, 006, 007 | Offline checks, paid goldens, independent quality comparisons |
| 7 | [013 — instructions/output](013-context-tiering.md) | 011, 012 | Expanded workstream 3 |
| 8 | [014 — context](014-task-context-and-reuse.md) | 006, 013, 012 | New workstream 2 |
| 9 | [015 — orchestrator](015-orchestrator-overhead.md) | 007, 012, 014 | New workstream 4; no general state engine |
| 10 | [016 — tool output](016-bounded-tool-output.md) | 007, 012, 014 | New workstream 6 |
| 11 | [017 — verification](017-scoped-verification.md) | 012, 014, 015, 016 | New workstream 5 |
| 12 | [018 — effort](018-reasoning-effort-policy.md) | 005, 006, 012, 015, 017 | New workstream 7 |
| 13 | [019 — repair/escalation](019-local-repair-and-escalation.md) | 005, 007, 012, 015, 017, 018 | New workstream 8 |
| 14 | [020 — decomposition](020-cost-aware-decomposition.md) | 005, 006, 012, 014, 015, 017 | New workstream 9 |
| 15 | [021 — references](021-generated-reference-docs.md) | 011, 013 | Render metadata without inlining optional context |
| 16 | [022 — installer and profiles](022-public-installer-and-profiles.md) | 002, 021, 011 | Split from 21 on 2026-11-16: installer, ownership records, neutral core and profiles |
| 17 | [023 — public readiness](023-open-source-readiness.md) | 002, 012, 021, 022 | Accurate docs; license/release remain explicit owner actions |
| 18 | [024 — composite branch model](024-composite-branch-model.md) | 011, 012, 003, 004, 006, 017 (014, 019 when delivered) | Split from 23 on 2026-11-16: one branch per composite, sequential children on temporary branches |
| Delivered | [025 — task finalization](completed/025-task-finalization.md) | Multi-repository support | Implementation integrated; task archival remains separate |
| Partial | [026 — specification-driven PR review](completed/026-spec-driven-pr-review.md) | — | Offline phase delivered; historical comparison and standalone pilot remain deferred |
| Direction | [027 — parallel execution program](027-parallel-execution-program.md) | Reconcile peer contracts; resolve program blockers | Owner direction and staged plan; not an implementation-ready replacement for the dependent specs |
| Delivered | [009 — state tool](completed/009-state-tool.md) | — | Scheduled by the owner on 2026-11-13 (ADR-0021); delivered 2026-11-16 on stacked pull requests #80–#98, merged into main the same day (ADR-0022); specification archived; optional and unwired, not a prerequisite of the nine tasks |

## Renumbering — 2026-11-25

All active and completed specification files now use unique three-digit prefixes.
The previous numbers are shown for historical lookup; requirement, audit and other
identifiers are not renumbered. Task directories were later
aligned with these specification numbers, except the journal-bound review task. Historical
Git paths remain valid only at their recorded revisions. The earlier 2026-11-16 renumbering
is recorded in ADR-0023.

| Previous number | Current number | Specification |
|---|---|---|
| 00 | 001 | [sensitive-data-scrub](completed/001-sensitive-data-scrub.md) |
| 01 | 002 | [git-source-of-truth](completed/002-git-source-of-truth.md) |
| 02 | 003 | [run-log-vocabulary-validation](completed/003-run-log-vocabulary-validation.md) |
| 03 | 004 | [hook-based-logging](completed/004-hook-based-logging.md) |
| 04 | 005 | [model-catalog-cache](completed/005-model-catalog-cache.md) |
| 05 | 006 | [cost-and-duration-telemetry](completed/006-cost-and-duration-telemetry.md) |
| 06 | 007 | [harness-git-rails](completed/007-harness-git-rails.md) |
| 06-1 | 008 | [test-suite-runtime](completed/008-test-suite-runtime.md) |
| 07 | 009 | [state-tool](completed/009-state-tool.md) |
| 08 | 010 | [rules-workflows-audit](completed/010-rules-workflows-audit.md) |
| 09 | 011 | [model-only-harnesses-and-rule-naming](011-model-only-harnesses-and-rule-naming.md) |
| 10 | 012 | [golden-run-tests](012-golden-run-tests.md) |
| 11 | 013 | [context-tiering](013-context-tiering.md) |
| 12 | 014 | [task-context-and-reuse](014-task-context-and-reuse.md) |
| 13 | 015 | [orchestrator-overhead](015-orchestrator-overhead.md) |
| 14 | 016 | [bounded-tool-output](016-bounded-tool-output.md) |
| 15 | 017 | [scoped-verification](017-scoped-verification.md) |
| 16 | 018 | [reasoning-effort-policy](018-reasoning-effort-policy.md) |
| 17 | 019 | [local-repair-and-escalation](019-local-repair-and-escalation.md) |
| 18 | 020 | [cost-aware-decomposition](020-cost-aware-decomposition.md) |
| 19 | 021 | [generated-reference-docs](021-generated-reference-docs.md) |
| 20 | 022 | [public-installer-and-profiles](022-public-installer-and-profiles.md) |
| 21 | 023 | [open-source-readiness](023-open-source-readiness.md) |
| 22 | 024 | [composite-branch-model](024-composite-branch-model.md) |
| 24 | 025 | [task-finalization](completed/025-task-finalization.md) |
| 25 | 026 | [spec-driven-pr-review](completed/026-spec-driven-pr-review.md) |
| 26 | 027 | [parallel-execution-program](027-parallel-execution-program.md) |

## Review record and remaining decisions

The 2026-11-06 reconciliation reviewed all **23 specifications**: seven completed
records retain delivery history and owner deferrals; sixteen root-level records include
the administratively closed, partially delivered runtime scope and fifteen planned/backlog
specifications. The seven optimization specs added on 2026-10-21 remain planned; this
index is not a spec. Shared acceptance gates remain binding; metadata-only context reuse,
textual review/checkpoint rules and existing offline tests do not satisfy the future
content-hash, bounded-output, effort, repair, parallel-scheduler or evaluation interfaces.

The missing historical clarity report was not reconstructed. Broken current local links
were repaired to available canonical records. Historical pinned source links and all
requirement/acceptance identifiers were retained.

The nine workstreams cover the identified mechanisms. Cheap-first execution is still a
hypothesis. Spec 012 compares strong-first, cheap execution plus strong verification,
strong planning plus cheap execution, adaptive chains, tiered verification, and hybrids.
Strong-first remains valid where expected repair cost is higher.

Before paid comparison, the owner chooses the task set, quality tolerances, available
models, sample/repetition counts, experimental spend/time limits and stop conditions.
These limits do not become production run budgets. Unanswered experimental settings
do not block deterministic implementation or authorize paid work.

Later separate candidates: RED-set enforcement hook, secrets/PII review gate, optional
third harnesses and a documentation site. Optimization does not waive existing RED-set
protection, test-first order or independent review.
