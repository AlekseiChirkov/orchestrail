# 027. Parallel execution across the task graph

## Source

- Owner request, 2026-11-25, translated from Russian: make `spec-run` and
  `phase-execution` execute subtasks in parallel wherever possible; make
  `phase-discovery` decompose work to enable safe parallel execution; minimize
  development time while maintaining or improving quality.
- Owner clarifications, 2026-11-25: include independent top-level leaves and
  children of different composites; select parallel execution automatically when
  the environment and task permit; preserve the stacked PR model by implementing
  work in temporary branches in parallel and assembling the stack sequentially.
- This is the sole active specification for parallelism. It supersedes
  conflicting future-scope restrictions in the former spec 23 as an owner direction;
  it does not claim that existing runtime rules or accepted ADRs have already changed.

## Context & Problem

The shipped runner refuses concurrent subtask execution (`rules/orchestration.md:10`;
`workflows/spec-run.md:480`; `workflows/pe-execute.md:31`). Discovery explicitly
avoids claiming parallel execution (`workflows/pd-decompose.md:137`). The current
`spec-run` creates each stack branch from its reviewed predecessor
(`workflows/spec-run.md:209`); a composite has no branch of its own
(`workflows/spec-run.md:213`). Spec 024 designs a composite branch with sequential
children; the former composite-only design excluded other leaves and `phase-execution`
(see the historical design below). Spec 020 supplies planned decomposition evidence but
retains a sequential top-level stack. None is evidence of a shipped scheduler.

ADR-0009 Decision 4 limits concurrency to one composite and `spec-run`;
ADR-0004 Decision 3 requires sequential execution. ADR-0024 Decision 3 requires
one shared sequential order across repositories. The owner direction above requires
those decisions to be revised at implementation; the current rules remain binding
until the corresponding changes are delivered. No existing branch or task is migrated
merely by writing this specification.

## Goal

Reduce elapsed time to an independently verified result by identifying coherent,
provably independent work in Discovery and executing it concurrently in both execution
entry points, with isolated work, deterministic integration and preserved quality,
history, recovery and human decision gates.

## Scope

Discovery evidence, shared scheduling and recovery, automatic capability-based mode
selection, both execution entry points, single- and multi-repository dependency graphs,
stack materialization, composite integration, quality evidence and comparative evaluation.
Specs 020 and 024 own their independent non-parallel contracts. This specification owns
all parallel-specific Discovery evidence, scheduling and changes to execution flows.

## Out of Scope

- Concurrent independent task or spec runs, parallel Discovery itself, and a promise
  of a particular speedup, token saving or cost reduction.
- Automatic owner decisions, PR merges, publication authorization, destructive cleanup,
  or bypass of sandbox, Git, test-first or review requirements.
- Silent migration or rewriting of started or published task branches.

## Actors & Roles

The owner sets constraints and resolves existing human gates. Discovery produces a
plan and independence evidence. The root coordinator admits work, owns shared state,
Git integration and recovery. Isolated workers implement within their authorized
write sets and return evidence; an independent validator checks each result. The root
does not infer environmental enforcement merely from instructions to workers.

## Terminology

An **atomic leaf** is a schedulable subtask; a **composite** is an integration gate,
not an atomic job. A **reservation** covers the complete planned write and exclusive
resource set for a live attempt. An **attempt** is one execution on a pinned base in
an isolated workspace. A **candidate** is its validated result. **Materialization**
is the ordered construction of final stack branches from validated candidates.
**Acceptance** requires verification on the actual integrated tree. A **run** belongs
to one task and has one root coordinator even when multiple repositories participate.

## Requirements

- **REQ-01 Coverage.** WHEN Discovery creates or changes a plan, THE SYSTEM SHALL
  map every acceptance criterion and invariant to accountable leaf and integration
  verification without weakening the original contract.
- **REQ-02 Decomposition.** WHEN choosing boundaries, Discovery SHALL consider
  independently verifiable work, real dependencies, interfaces, files, exclusive
  resources, integration risk and expected critical path; it SHALL record selected
  and rejected alternatives and reasons, without fragmenting coherent work solely
  to increase task count.
- **REQ-03 Evidence.** WHEN a plan is finalized, Discovery SHALL record for every
  leaf a complete or explicitly unknown write set, interface effects, resource
  claims, dependencies, repository and evidence supporting independence; unknown
  is not evidence of independence.
- **REQ-04 Design changes.** WHEN design changes those facts, Discovery SHALL
  recompute evidence for unstarted leaves and preserve started work and its history.
- **REQ-05 Common graph.** WHEN either entry point schedules work, THE SYSTEM SHALL
  use the dependency graph of all eligible leaves, including top-level leaves and
  children of different composites, and treat composite integration as a gate.
- **REQ-06 Admission.** WHEN considering a leaf, THE SYSTEM SHALL start it only if
  its prerequisites are accepted, its complete claims are independent of every
  live reservation, the relevant composite gates permit it, and capacity remains.
  Dependency, interface, resource or file uncertainty requires serialization.
- **REQ-07 Automatic mode.** WHEN a run starts or resumes, THE SYSTEM SHALL use
  parallel scheduling when supported capabilities, actual permissions, safe
  isolation, capacity and at least two eligible independent leaves are established;
  otherwise it SHALL use the existing sequential path and report the reason.
  Explicit user or environment restrictions always take precedence.
- **REQ-08 Capacity.** WHILE scheduling, THE SYSTEM SHALL respect the actual
  harness capacity, user and environment limits, and reservations; it SHALL refill
  free capacity as independent work becomes ready and record requested, available
  and effective capacity without treating unknown capacity as unlimited.
- **REQ-09 Isolation.** WHEN dispatching concurrent leaves, THE SYSTEM SHALL give
  each a separately identified workspace and pinned base, record ownership, require
  an effective verified enforcement boundary that prevents workers from writing
  shared state and performing root-owned Git operations, and serialize root-owned
  operations. IF enforcement cannot be verified, THEN THE SYSTEM SHALL use the
  sequential path. Instructions alone are not an enforcement boundary.
- **REQ-10 Quality.** WHEN a leaf runs, THE SYSTEM SHALL preserve its test-first or
  justified existing test mode, frozen evidence, contract and independent validation;
  evidence and handoffs SHALL identify the exact candidate and inputs validated.
- **REQ-11 Actual changes.** WHEN a worker returns and before integration, THE SYSTEM
  SHALL compare actual changed, added, removed, renamed, generated and untracked
  paths and declared interface/resource effects with reservations and other attempts.
  A violation or stale evidence SHALL prevent acceptance.
- **REQ-12 Integration.** WHEN a candidate is ready, THE SYSTEM SHALL integrate in
  deterministic dependency-compatible order, retain test and implementation history,
  recheck affected behavior on the actual combined tree and accept it only after
  checks pass; a child result alone is not proof of integration.
- **REQ-13 Stack.** WHEN `spec-run` executes independent top-level work, THE SYSTEM
  SHALL build it in temporary branches and then materialize the existing review stack
  sequentially, with each final branch based on its accepted predecessor, retaining
  attributable test and implementation history and one reviewable PR per applicable
  top-level unit. Final PR promotion remains subject to existing validation and owner
  authorization.
- **REQ-14 Composite.** WHEN a composite's children are accepted, THE SYSTEM SHALL
  run integration validation against their combined accepted tree before declaring
  the composite gate satisfied, including cross-composite scheduling. A successful
  check is reused only for unchanged validated inputs; a relevant change or fix
  invalidates it and requires another check.
- **REQ-15 Repositories.** WHEN a task spans repositories, THE SYSTEM SHALL keep
  repository ownership and per-repository stack bases distinct, respect cross-repository
  dependency and integration gates, and share no Git base across repositories.
- **REQ-16 Failure.** IF a candidate fails or independence is disproved, THEN THE
  SYSTEM SHALL preserve its work and evidence, stop affected dispatch, block dependent
  work, and allow unrelated work only when no shared invariant or existing broad-stop
  condition requires the whole run to stop. Conflict recovery SHALL never discard work.
  The existing `spec-run` NEEDS WORK stop is preserved until an explicit replacement
  contract maps that verdict and every other stop for both entry points. At a human gate
  the coordinator admits no new work, requests a safe stop from active workers, records
  their last verified checkpoints and preserves their work; it neither answers for the
  owner nor assumes that a dispatched worker has stopped without confirmation.
- **REQ-17 Recovery.** WHEN resuming, THE SYSTEM SHALL reconcile actual live agents,
  reservations, workspaces, branches, candidate identities, checkpoints and integration
  receipts before dispatch; it SHALL not duplicate live work, accept stale evidence or
  release a live writer's reservation.
- **REQ-18 Compatibility.** WHEN handling a legacy or already-started task, THE SYSTEM
  SHALL retain its recorded branch model and history unless an explicitly authorized,
  verified migration contract applies; missing optional evidence uses the sequential
  path rather than invented claims.
- **REQ-19 Measurement.** WHEN a run completes or stops, THE SYSTEM SHALL report
  elapsed time, realized concurrency, integration/rework and available cost/usage
  separately from quality results and unknown measurements. Comparative claims SHALL
  use equivalent inputs and independent quality gates under spec 012.
- **REQ-20 Rollout.** BEFORE enabling the new behavior, THE SYSTEM SHALL update
  relevant ADRs, rules, workflow readers, deterministic contract checks and documentation;
  the rollout SHALL provide a sequential disable path and preserve recovery evidence.

## Data Model

This specification must define before implementation versioned, backward-readable plan and
journal records for run identity; plan and contract revision; graph and gate identity;
leaf/repository; complete or unknown write, interface and resource claims; attempt,
workspace and branch ownership; pinned base and candidate; active reservation; worker
and handoff identity; validation and integration tree/receipt; materialization position;
state transitions and cleanup eligibility. No writer may infer a missing field as an
affirmative safety claim. Exact schemas and atomic update/recovery rules are delivery
contracts still to be designed, not an existing API.

## Contracts & Interfaces

`phase-discovery` supplies plan evidence; `phase-execution` and `spec-run` consume
the same admission and safety semantics while preserving their distinct phase and Git
responsibilities. `phase-execution` retains its stop before phase validation;
`spec-run` retains its existing explicit cross-phase and publication controls.
The detailed contracts in this specification must define invocation/disable controls, capability and
capacity probes, the admission predicate, result formats, errors, journaling, Git
materialization and cleanup, legacy behavior, and the exact independent validation
and post-integration recheck conditions before implementation starts.

## Non-Functional Requirements

Quality and safety are release gates: all applicable existing test-first, independent
review, owner-stop, acceptance and integration obligations remain in force. Deterministic
fixtures must show behavior for concurrent scheduling and crash recovery. Compare elapsed
time and quality on equivalent tasks using spec 012; no numerical speed target or unmeasured
financial claim is asserted. Parallelism may increase cost or rework.

## Edge Cases & Failure Modes

| Case | Required behavior | Requirement |
|---|---|---|
| No independent leaves, incomplete evidence, or unknown permissions | Sequential path with a reason | REQ-03, REQ-07 |
| Dependency cycle, missing prerequisite or ambiguous repository | Do not dispatch affected work; report invalid plan | REQ-05, REQ-06, REQ-15 |
| Resource or write-set overlap; undeclared rename or generated file | Do not accept conflicting candidates; preserve work and serialize affected work | REQ-06, REQ-11, REQ-16 |
| Worker, coordinator or machine interruption | Reconcile live writers and checkpoints before replacement | REQ-17 |
| Validated candidate conflicts with a newly materialized stack tree | Preserve candidate, do not accept stale validation, rework and revalidate the affected tree | REQ-10, REQ-12, REQ-16 |
| Human gate or critical shared invariant violation | Honor existing broad stop and preserve active work | REQ-16, REQ-20 |
| Started legacy task or published branch | Preserve existing history; no silent migration | REQ-18 |
| Cross-repository producer not accepted | Consumer remains blocked irrespective of idle capacity | REQ-06, REQ-15 |

## Acceptance Criteria

- **AC-01** (REQ-01–REQ-04): Given a multi-leaf fixture, when Discovery finalizes it,
  every criterion has an owner and integration check, each independence claim has
  evidence, and unknown claims do not become safe; design changes refresh only
  unstarted work.
- **AC-02** (REQ-05–REQ-08): Given independent top-level leaves and leaves from
  different composites, both entry points admit them concurrently within capacity;
  dependent, overlapping and unknown-claim leaves do not overlap. Unsupported
  environments run sequentially with an explicit reason.
- **AC-03** (REQ-09–REQ-11): Given two admitted leaves, their isolated workspace,
  reservations and pinned input identities are distinct; frozen test and independent
  review evidence bind to each candidate, and an out-of-reservation change blocks it.
- **AC-04** (REQ-12–REQ-14): Given independently completed top-level and composite
  work, final stack bases follow accepted plan order, candidate history is retained,
  merged-tree checks pass before acceptance and each composite gate is checked against
  its current tree; a relevant tree or contract change triggers revalidation.
- **AC-05** (REQ-15): Given two repositories with a cross-repository dependency,
  independent work may overlap but the consumer waits for the producer; final PR
  bases remain within their own repositories.
- **AC-06** (REQ-16–REQ-18): Given a conflict, interrupted live worker and an old
  started task, work is preserved, no live attempt is duplicated or its reservation
  released, dependent work is blocked, and the old branch model is not silently changed.
- **AC-07** (REQ-19–REQ-20): Given a completed or stopped run, the report separates
  observed duration, concurrency, rework, cost/unknowns and quality; delivery includes
  updated contracts, deterministic checks, a disable path and recovery instructions.

## Traceability

REQ-01–04 → AC-01; REQ-05–08 → AC-02; REQ-09–11 → AC-03; REQ-12–14 → AC-04;
REQ-15 → AC-05; REQ-16–18 → AC-06; REQ-19–20 → AC-07. These are program outcomes;
this specification must refine them into independently testable fixtures,
including an explicit graph and event ordering for admission, candidate and integrated
tree identities, expected records, and negative checks for stale evidence. No delivery
starts from these broad criteria alone.

## Risks

Unproven independence can introduce integration defects; use conservative admission
and verify the integrated tree. Excessive splitting, agent overhead or resource
contention can increase elapsed time; compare measured outcomes. Stale handoffs or
premature cleanup can lose evidence; bind records to identities and fail closed.
Incompatible platform permissions can defeat isolation; detect actual capabilities.

## Assumptions

- A-01 | Unknown capability | Resolved: sequential execution with a reason | Source:
  existing safe path and REQ-07 | Reversible: yes.
- A-02 | Published/started tasks | Resolved: preserve their recorded model unless a
  separately specified, explicitly authorized migration applies | Source: REQ-18,
  existing Git history and recovery obligations | Reversible: yes.
- A-03 | Parallel discovery | Resolved: optimize decomposition, not Discovery's own
  execution | Source: owner request distinguishes decomposition from execution |
  Reversible: yes.

## Decisions

- D-01 | Parallelize any proved-independent eligible leaves, including cross-composite
  and top-level leaves | Overrides: planned scope of spec 23 and ADR-0009 Decision 4
  at delivery | Rationale: owner clarification | Follow-up: update affected ADRs,
  specs and their consumers before enabling.
- D-02 | Automatic selection when safe and supported | Overrides: planned opt-in-only
  mode of spec 23 at delivery | Rationale: owner clarification | Follow-up: define
  capacity, disable and fallback contracts here.
- D-03 | Parallel temporary branches followed by sequential stack materialization |
  Overrides: sequential construction timing in current Git rules at delivery |
  Rationale: owner clarification | Follow-up: define exact history, verification,
  recovery and PR contracts before implementation.

## Clarifications

### Session 2026-11-25

- Q: Scope of this work? → A: Update specifications and prepare an implementation plan.
- Q: Include independent top-level and cross-composite leaves? → A: Yes, wherever independence is proved.
- Q: How is parallel mode selected? → A: Automatically when the task and environment permit.
- Q: How should PR order work? → A: Preserve the PR stack, develop on temporary branches in parallel, then assemble the stack sequentially.

## Open Questions

- **Q-01 (blocker for implementation):** Which exact Git operations preserve
  candidate history, frozen test evidence and the final stack without prohibited rebase
  or unsafe rewrite, including composite and cross-repository cases? Resolve with
  disposable-repository prototypes and record the decision before implementation.
- **Q-02 (blocker for implementation):** What concrete isolation and capacity
  evidence can each supported harness provide, and how are write restrictions verified?
  Define adapters and deterministic fallback fixtures; do not assume universal support.
- **Q-03 (blocker for implementation):** What are the exact atomic journal,
  live-worker reconciliation, conflict and partial-integration transitions across both
  entry points? Define and test before enabling concurrency.

## Notes

### Implementation plan

Keep all parallelism requirements in this single specification. Refine the following
bounded delivery slices here and create implementation subtasks from this specification;
no implementation begins until the shared contracts and dependencies below are reconciled
and the specification passes its readiness gate. Ownership is exclusive as listed:

| Delivery | Owner and boundary | Prerequisites and handoff |
|---|---|---|
| A: decomposition | This spec owns the additional graph, claims and independence evidence needed for parallel scheduling; spec 020 owns coverage and general decomposition | Resolve graph and evidence schema with B; existing sequential consumers keep working |
| B: shared execution | This spec owns admission, capacity and capability evidence, isolation, reservations, handoffs, stop matrix, journal and recovery used by both entry points | A's plan contract; resolve Q-02 and Q-03; align 09, 12, 13, 15, 17 and telemetry contracts |
| C: Git and stack | This spec owns stack materialization for concurrent work; spec 024 owns its independent sequential composite branch model | B's candidate and receipt contracts; resolve Q-01; retain per-repository bases from ADR-0024 |
| D: execution entry points | Specify and integrate `phase-execution`/`pe-execute` and `spec-run` adapters; B owns shared semantics, C owns Git | A–C interfaces and compatibility contracts; preserve each entry point's phase and publication gates |
| E: evaluation and rollout | Spec 012 owns comparative evaluation; each delivery owns its deterministic acceptance tests and rollout | A–D integrated on equivalent inputs, with independent quality gates and disable/recovery documentation |

1. Reconcile this specification and the affected peer contracts against this direction;
   preserve historical IDs and separate currently shipped behavior from planned changes.
   Decide whether to amend or replace their implementation slices without duplicating
   ownership. Resolve Q-01–Q-03 and record superseding ADRs at the actual decisions.
2. Specify and deliver Discovery's graph, coverage and evidence, including legacy plans;
   prove no unsafe independence inference and preserve coherent task boundaries.
3. Specify and deliver the common single-writer scheduler, capability selection,
   isolation, reservations, checkpoint and recovery contracts with deterministic fixtures.
4. Integrate `phase-execution` and its direct `pe-execute` path, preserving quick flow,
   standalone behavior, owner gates and the phase stop.
5. Integrate `spec-run` materialized stacks, composite gates and multi-repository
   routing, preserving TDD evidence and existing publication controls.
6. Run contract and fault-injection suites, equivalent sequential/parallel evaluation
   and independent quality review; stage rollout with an explicit disable path. No
   paid comparisons, publication or live deployment are authorized by this document.

The stages are planning boundaries, not claims that all dependencies are delivered or
that their current sequencing is optimal. Discovery must create bounded implementation
tasks after the interfaces and branch model are resolved.

## Readiness Checklist

| Check | Result |
|---|---|
| 1. Goal states the outcome | PASS |
| 2. Concrete exclusions | PASS |
| 3. Stable observable requirements | PASS at program level; detailed contracts must refine them |
| 4. Requirement/criterion traceability | PASS at program level |
| 5. Testable delivery criteria | FAIL — program criteria require concrete fixtures and event sequences |
| 6. Non-functional conditions | PASS — quality gates and comparable measurement are named |
| 7. Data model and contracts | FAIL — schemas, operations and recovery transitions remain open |
| 8. Edge and failure cases | PASS at program level; delivery fixtures must refine them |
| 9. Ambiguities recorded | PASS — unresolved design questions are listed |
| 10. No blocker question | FAIL — Q-01–Q-03 |
| 11. Existing behavior cited | PASS — current workflow claims cite source |
| 12. Terminology | PASS at program level |
| 13. Feature-sized | FAIL — this single specification needs bounded implementation subtasks |
| 14. Independent review | FAIL — two rounds, 69/100 then 80/100; critic: sub-agent; F-05 critical remains open for unresolved Git, isolation and recovery contracts |

Verdict: **NOT READY FOR DEVELOPMENT**. The program and ownership map require further
reconciliation and design before implementation. Automated review is not
sign-off.


## Historical design provenance

The previous composite-only specification and its full requirement, data-model and
acceptance-criterion history are retained at Git revision `42325d2`:
`git show 42325d2:.ai/specs/23-composite-branch-model-and-parallel-children.md`.
The previous decomposition evidence schema is available at the same revision in
`020-cost-aware-decomposition.md` under DM-8. Those historical contracts are inputs to
reconciliation, not independent active specifications or proof of readiness.
