# Specification-driven, risk-based pull request review pilot

## Source

- [Edition 5.0 architecture and acceptance contract](../review_architecture_spec_v5.md), sections 1–12, supplied for standalone specification authoring on 2026-11-24. Source SHA-256 is `71593fe34d9f1e57c4bf8b47c2e9779acbfefb70e9626c4b02839d7f844ddfda`.
- The source asks the pilot to “Find distinct, consequential defects before the first useful report on a pinned change” and “Evaluate the behavior promised by the approved feature specification, including behavior entirely absent from the diff.” The source proposes resource ceilings and numeric acceptance thresholds for qualification. The Phase 1 change log records the owner's exploratory comparison decision.
- Owner direction, translated from Russian (2026-11-24 repository conversation): “Update the specification. I need the spec-run implementation to proceed as quickly as possible, in parallel wherever possible. After updating the specification, run /spec-draft --auto-mode on it.” The preceding discussion defines a three-case rehearsal, a 10–15-case paired comparison, and independent review and scoring.

## Phase 1 — Offline review comparison

## Context & Problem

Orchestrail's existing code-review workflow inspects the task-owned file set, checks implementation and test quality, and records findings in task state (`workflows/pv-review.md:40–69`). Orchestrail is an instruction-driven SDLC toolkit with local helpers (`README.md:19–20`, `.ai/memory/architecture.md:9–21`). Its accepted architecture keeps execution of pipeline workflows in the harness (`.ai/adr/0001-task-unknown-markdown-only-no-runtime.md:28–38`). The proposed service addresses a separate review problem. A change-focused review can miss required behavior with no corresponding diff, and separate PR reviews can miss defects that appear only in the integrated feature. A report can also overstate confidence when candidate validation or mandatory coverage remains unfinished.

## Goal

Determine whether adding explicit specification coverage to the current Orchestrail review finds enough additional consequential defects to justify its cost. Run a bounded offline comparison on identical pinned PR and integrated feature snapshots and produce evidence for deciding whether to trial an optional review step and invest in the standalone pilot.

## Scope

The first `spec-run` task delivers a reproducible offline protocol, local templates, and verification on synthetic fixtures. Its acceptance scope is REQ-45–REQ-50 and AC-45–AC-50. The exploratory historical comparison is a separate operator run using those deliverables. Its inputs and results are outside the first implementation's completion criteria.

## Out of Scope

- Historical execution during `spec-run`, production workflow changes, a new automated scheduler, a durable review store, hosted intake and publication, and merge gating. A change to `pv-review` requires a separate implementation decision after the comparison.

## Actors & Roles

| Actor | Authority |
|---|---|
| Project owner or trusted delegate | Defines the permitted data boundary and decides whether to pursue the standalone service. |
| Offline review operator | Reconstructs source-backed packets, dispatches isolated reviews using available capacity, and preserves first outputs. |
| Offline adjudicator | Scores findings against pinned evidence with variant identity hidden. The operator reveals pairing and variant identities for aggregate comparison after verdicts are fixed. |

## Terminology

- **Specification** means feature intent recorded in contemporaneous source material. Orchestrail's **spec** is its development task statement (`.ai/principles/domain.md:12–18`).
- **Due criterion** is an observable obligation grounded in contemporaneous source and tied by evidence to the tested composition. **Future criteria** are obligations assigned by evidence to later delivery. Record uncertain assignment as a coverage gap.
- **Case** is one PR or feature milestone and its pinned input packet. **Pair** means the two variants' first observations for the same case. A **first observation** is the original attempt's terminal status and, when available, the immutable digest of its first submitted report. A **rehearsal** checks the procedure on cases held apart from the main comparison.

## Requirements

| ID | EARS requirement |
|---|---|
| REQ-45 | WHEN an offline case is admitted, THE SYSTEM SHALL pin one source-backed input packet for both reviews. |
| REQ-46 | WHEN a paired review is dispatched, THE SYSTEM SHALL isolate the reviewers from each other's outputs and from historical findings and labels through both terminal first observations. |
| REQ-47 | WHEN the coverage-enhanced review reports, THE SYSTEM SHALL provide one evidence or gap disposition for each due criterion. |
| REQ-48 | WHEN the rehearsal is complete, THE SYSTEM SHALL record whether the fixed procedure permits the main comparison to start. |
| REQ-49 | WHILE the main comparison runs, WHEN a review or adjudication unit is ready, THE SYSTEM SHALL dispatch eligible units as capacity becomes available. |
| REQ-50 | WHEN the comparison closes, THE SYSTEM SHALL produce a paired evidence report from frozen first observations and blinded adjudication. |

For the offline experiment, operators can execute the protocol with local files and independent sessions. The acceptance checks exercise the local procedure using controlled fixtures.

## Data Model

| Record | Identity and minimum fields |
|---|---|
| Shared reviewer packet | Opaque case ID, readable base and tested tree of a PR with base/head/target identities or of a milestone with the integrated tree, target and constituent revisions, scoped diff and tests, task-owned paths, sanitized task design and upstream contract context, pinned review instructions, contemporaneous specification and available binding annex contents and digests, and reconstructed delivery assignment version and due/future roster with traceable sources. The coordinator pins the packet digest. |
| Coordinator manifest | Case ID, feature group, cohort, controlled source references, historical labels, dispatch and variant map, first observation identities and available resource observations. Only the coordinator can access the full manifest. The adjudicator receives opaque findings, case evidence and historical claims stripped of variant and dispatch metadata. Reviewers receive only their shared packet and their assigned instructions. |
| Experiment record | Cohort and selection rationale, model and tools used, severity and matching approach, observed configuration changes, access and retention policy, closure reason, and available time and spend observations. |
| First observation | Case ID, packet digest, variant, attempt ID, terminal status `completed`, `partial`, `failed`, `timed out`, `invalid` or `not started`, digest of any frozen artifact or null, elapsed time from dispatch to freeze or failure or null when not started, settled cost when known, and reason for any non-completed status. Partial or missing output remains visible in pair status. |
| Adjudication | Case batch identity and status `complete` or `incomplete`. Each assessed finding has an opaque finding ID, case ID, anchor and evidence, canonical defect ID if matched, verdict `confirmed`, `refuted` or `unresolved`, severity and rationale. A pending claim at cutoff has an evidence-gap reason and no independent verdict. Keep variant mapping private until all batches freeze. |
| Comparison report | Cohort and actual configuration, enrolled and completed case counts, complete or incomplete pair status, per-variant and exclusive confirmed defects, false and unresolved findings, time and costs, coverage gaps, and exploratory findings or reasons for insufficient evidence. |

## Contracts & Interfaces

- **Case preparation.** Prepare three distinct rehearsal cases. Enroll a disjoint historical cohort of 10–15 cases from one permitted repository, including clean controls, an omitted due requirement, and a multi-PR integration defect. Keep related changes together and count each milestone once. Reconstruct criterion assignments from contemporaneous sources, preserve anchors privately, and record uncertainty. Exclude unreadable snapshots or cases without a traceable due roster. Record inaccessible annexes as evidence gaps. Missing formal approvals alone permit admission. Omit historical findings, later fixes, review comments and outcome-bearing state from packets. Record insufficient evidence when the history lacks the required mix.
- **Pair execution.** Give both arms identical pinned inputs and matching model and tool access. Adapt the pinned review rules and task-owned paths to the snapshot. Use isolated sessions with read-only packets and separate outputs. The treatment records one `satisfied`, `violated`, or `undetermined` row per due criterion with evidence or a named gap. Keep future scope separate. Preserve first reports and terminal observations, including missing reports. Retries remain diagnostic.
- **Rehearsal and dispatch.** Rehearse six independent reviews across three cases and verify parity, isolation, capture and scoring. Main dispatch requires prepared historical packets and a successful rehearsal. Record the actual model, tools, severity and matching conventions. Start eligible work as capacity becomes available. Record initial attempt identities and reconcile them after interruptions. Preserve uncertain attempts without resubmission. Formal approvals, locked settings and enforceable time or spend limits are optional for this historical procedure.
- **Close and contamination.** Close when work is terminal or the operator records a stop and its reason. Freeze waiting reviews as `not started`, unresolved launched reviews as `partial` or in their observed terminal state, and unfinished adjudication as `incomplete` with pending gaps. Keep late results separate. Exclude pairs exposed to sibling reports or historical labels, including related cases with the same possible exposure. Invalidate the cohort when exposure cannot be bounded.
- **Scoring.** Freeze blinded adjudication before unmasking. Score complete, uncontaminated pairs with matching first observations and complete adjudication. Deduplicate confirmed defects and refuted claims per case and arm. Report signed deltas, exclusions, unresolved claims, gaps and actual configuration. Report time and settled charges when observed. Mark unavailable measurements as unknown and label observed spend as a partial subtotal when incomplete. Report eligible results as exploratory and disclose insufficiency when no eligible pairs remain or the required cohort mix is unavailable. Use the outcome for a separate investment decision.

## Non-Functional Requirements

Verify input and output isolation and reproducibility on fixtures. Record elapsed seconds and exact charges in one currency when available. Preserve original observations and slot ownership across interruption. Controlled fixtures may still exercise enforceable budgets and threshold-driven decisions.

## Edge Cases & Failure Modes

| Case | Expected behavior |
|---|---|
| Mismatched packet digest, unreadable snapshot or untraceable due roster | Exclude with reason, preserve the shortfall, and keep any synthetic results separate. REQ-45, REQ-50 |
| Output or label leakage | Exclude affected cases or invalidate the cohort when exposure cannot be bounded. Preserve affected IDs and reasons. REQ-46, REQ-50 |
| Missing or ambiguous evidence | Mark the due criterion undetermined and name the evidence gap. REQ-47 |
| Rehearsal failure or missing prepared historical packets | Hold main dispatch and record the unmet precondition. REQ-48 |
| Capacity exhausted, timeout, failed session or unknown charge | Queue ready work, retain uncertain attempts, and mark unavailable measurements as unknown. REQ-49, REQ-50 |
| Interrupted coordinator or adjudication pending at closure | Resume from recorded attempts and retain existing first observations. At closure, freeze unfinished adjudication as incomplete and exclude its pair from scoring while preserving its enrollment and spend. REQ-49, REQ-50 |

## Acceptance Criteria

| ID and requirement | Given | When | Then |
|---|---|---|---|
| AC-45 / REQ-45 | A PR and milestone have readable snapshots and sourced rosters without approval records. Another snapshot is unreadable. | Packets are prepared | Each eligible case pins the same digest across both variants. The milestone identifies its composition, and the unreadable case is excluded. |
| AC-46 / REQ-46 | A labeled fixture seeds identifiable historical labels and the sibling session's report in out-of-packet locations | A session reads via its allowed tools and writes its own report | The session can read the pinned packet and write its own output. It cannot read either seeded source through the packet, tool scope, filesystem paths or links. Each terminal observation refers to the first report digest, when present. |
| AC-47 / REQ-47 | A packet contains positive evidence for one due criterion, evidence of a consequential omission outside the diff for another, a due criterion with missing evidence and a source-backed future criterion | The treatment report is checked | The three due criteria have exactly one row each. The rows are `satisfied` with the positive evidence, `violated` with omission evidence at the owning boundary outside the diff, and `undetermined` with the named gap, respectively. The future criterion appears separately and is excluded from due counts. |
| AC-48 / REQ-48 | Three rehearsal cases produce six observations. Separate fixtures inject digest mismatch or historical label exposure. | Readiness is checked | Either fault blocks with the affected case ID. Successful rehearsal and prepared historical packets pass readiness without approvals or locked settings. Missing packets remain pending. |
| AC-49 / REQ-49 | Ready units contend for available slots and an earlier attempt has uncertain termination. | Capacity changes or the coordinator resumes | Start eligible work when slots become available. Retain the uncertain attempt without resubmission and record unstarted reviews and incomplete adjudications at closure. Historical dispatch accepts absent time and spend limits. |
| AC-50 / REQ-50 | A complete pair reports one shared defect, one additional treatment defect, and one refuted treatment claim. Some time or cost is unavailable. Another pair has unfinished adjudication. | The blinded comparison closes | Report signed defect and false-finding deltas of one each, unknown time or cost deltas as applicable, and a partial observed spend subtotal. Retain incomplete evidence and report exploratory results, or insufficient evidence when no eligible pairs remain. |

## Traceability

Each `REQ-NN` maps to the same-numbered `AC-NN`. Each acceptance criterion names its requirement above. Source coverage by section is listed here.

| Source sections | Requirements |
|---|---|
| Owner direction and initial offline comparison | REQ-45–REQ-50 |

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Data crosses approval or isolation boundary | Unauthorized disclosure or execution | Medium | Enforce access-domain partitioning, project data policy and bounded isolation with a stop transition. |
| Correlated labels or future leakage bias evaluation | Misqualified routing | Medium | Freeze historical snapshots, blind labels, pool newly adjudicated discoveries and cluster related changes. |
| Pilot is delivered as one broad implementation | Delayed feedback on critical dependencies | High | Validate the offline comparison first. Keep later service acceptance outside the initial task. |
| Related PRs or historical material reveal known outcomes | Biased comparison | Medium | Keep each feature group in one cohort and audit packet contents and session isolation at rehearsal. |

## Assumptions

- A-10 | First implementation boundary | Resolved: Deliver REQ-45–REQ-50 with synthetic verification. Historical comparison is a separate operator run. Retain REQ-01–REQ-44 in the deferred numbered phase | Source: owner direction and preceding discussion, 2026-11-24, and `workflows/phase-discovery.md:63–79` | Reversible: yes
- A-11 | Review counterfactual | Resolved: Reconstruct the baseline's approved task context and change only the treatment's explicit coverage instructions | Source: `workflows/pv-review.md:33–69`, `workflows/pv-contract.md:30–42` and preceding discussion, 2026-11-24 | Reversible: yes
- A-12 | Parallel execution mechanism | Resolved: Keep delivery on the existing stack. Parallelize independent tool checks within the current worker. The separate operator run uses independent review sessions under a coordinator and existing authorized capacity | Source: `rules/orchestration.md:7–14`, `workflows/spec-run.md:271–277,480` and smallest reversible choice | Reversible: yes
- A-13 | Historical admission | Superseded on 2026-11-25 by the owner's exploratory comparison decision. Use source provenance and observed measurements for historical runs.

## Decisions

N/A — Auto mode recorded its resolutions in Assumptions.

## Clarifications

The original source brief used auto mode without an interactive clarification session.

### Session 2026-11-24

- Q: How should the first delivery be scoped and accelerated? → A: The owner asked to update the specification, maximize parallel work wherever possible for the eventual implementation, and review the updated specification in auto mode. The preceding discussion set the offline comparison as the first experiment.

## Open Questions

- Q-03 | resolved 2026-11-25 | The owner removed formal case approvals, locked settings, and enforceable time and spend limits from historical admission. The exploratory run still needs a traceable cohort and reviewer isolation.

## Notes

### First delivery handoff

Planning estimate: 2–3 working days for the operator-run comparison once historical inputs and sufficient concurrent capacity are available.

On a fresh `spec-run`, Discovery selects the first numbered phase. Analysis reads the shared preamble and the selected phase (`workflows/spec-run.md:103–105,131–135`, `workflows/phase-discovery.md:63–79`, `workflows/pd-analyze.md:20–26`). Use that boundary for decomposition, validation and reconciliation. Allocate the acceptance clusters below using the smallest coherent leaf set and one shared record format. Pin check inputs during Discovery so independent fixture checks can overlap. Historical comparison uses source-backed inputs and exploratory results.

| Work | Prerequisite | Acceptance |
|---|---|---|
| Prepare case manifest, packet checks and rehearsal fixtures | Agreed record format | AC-45 |
| Prepare the two review templates and the bounded dispatch procedure | Agreed record format | AC-46, AC-47, AC-49 |
| Prepare blinded adjudication and the paired report template | Agreed record format | AC-50 |
| Rehearse the combined process and record readiness | Prepared packets, review and scoring templates | AC-48 and integrated verification of AC-45–AC-50 |

The current runner creates each new leaf branch from the preceding reviewed tip and runs one subtask and one orchestration agent at a time (`workflows/spec-run.md:271–277,380–381,480`, `rules/orchestration.md:7–14`). Inside a worker, batch independent reads and run independent fixture checks concurrently where they have disjoint outputs. Keep test-first and independent validation checkpoints, shared writes and branch handoffs serialized. Use the bounded parallel review sessions for the separate operator-run rehearsal and historical comparison. The [parallel-children contract](../23-composite-branch-model-and-parallel-children.md) remains a separate initiative.

Implementation completion records fixture evidence. Run the historical comparison when source-backed packets are prepared and the isolation rehearsal passes. A repeated `spec-run` can select the next numbered phase after the first phase validates. Invoke that next phase only after the owner decides to proceed and refines its scope. Whole-spec completion requires the deferred phase (`workflows/pv-finalize.md:62–67`).

## Readiness Checklist

| # | Result | Reason |
|---|---|---|
| 1 | PASS | One domain-language goal identifies the review outcome and pilot selection objective. |
| 2 | PASS | Exclusions name historical execution, workflow changes, automated scheduling, the hosted service and merge gating. |
| 3 | PASS | Six current-phase requirements retain stable EARS IDs. The 44 deferred requirements retain their original IDs. |
| 4 | PASS | Every requirement and acceptance criterion links to its same-numbered counterpart. |
| 5 | PASS | Given/When/Then fixtures establish observable contract outcomes with explicit inputs. |
| 6 | PASS | Isolation, first-observation integrity and historical readiness have observable checks. |
| 7 | PASS | Proposed records, identities, lifecycle, authority, and success and failure interfaces are defined. |
| 8 | PASS | Fixtures and failure modes cover invalid and missing inputs, boundaries, concurrency, cutoff and retry. |
| 9 | PASS | Resolved choices and remaining owner inputs are recorded in Assumptions and Open Questions. |
| 10 | PASS | Controlled replay can use fixture settings. Historical replay accepts absent formal settings. |
| 11 | PASS | Existing workflow and repository behavior are backed by verified path and line citations. |
| 12 | PASS | The offline phase defines the case, pair, first observation and rehearsal independently of deferred service outcomes. |
| 13 | PASS | The first delivery contains six acceptance cases and four implementation clusters. Later service work is explicitly deferred. |
| 14 | PASS | Review: 4 rounds, score 99/100, critic: sub-agent, open: none. The planning estimate was moved to Notes after the scored round. |

**READY FOR DEVELOPMENT — Phase 1.** The offline protocol and synthetic verification can proceed. Historical execution requires traceable packets and an isolation rehearsal. Phase 2 remains deferred pending the historical comparison and an owner decision.

## Change Log

- 2026-11-25 | Owner-authorized exploratory historical comparison | REQ-45, REQ-48–REQ-50 and matching acceptance criteria | Replace formal case and settings gates with traceable input preparation, successful rehearsal, observed capacity and descriptive reporting. Preserve matched inputs, masking, immutable first observations and the standalone service contract.

## Phase 2 — Deferred standalone service

This phase preserves the original service contract for future delivery. Starting it requires a separate owner decision informed by the historical comparison, followed by refinement into the delivery boundaries below. Completion of the offline task leaves this phase deferred.

### Goal

Review pinned pull requests and feature milestones against approved expected behavior and technical invariants, then produce an evidence-backed first report that identifies consequential defects, distinguishes current work from approved future work, and makes missing verification explicit. Use a bounded single-host pilot to determine which review configuration meets the owner's quality and latency gates at the lowest total cost.

### Scope

- A standalone modular review service with one transactional local store, immutable artifacts, bounded workers, a model gateway, and restricted intake/publication adapters.
- Trusted specification and delivery scope, independently reconciled inventories, two-way coverage, impacted-consumer analysis, pinned multi-PR acceptance, mandatory risk checks, and blind review where required.
- Defensive source review, bounded deterministic verification of ordinary contract behavior, internal candidate adjudication, resource admission and recovery, snapshot-bound publication, and offline evaluation.
- Core implementation uses a fixed, versioned route catalog, conservative same-input reuse, and a simple eligible-job scheduler. Replay evaluation establishes the value of richer context, cross-revision reuse, and more advanced scheduling before subsequent delivery.

### Out of Scope

- Changes to Orchestrail workflow execution, state formats, deployment, or existing review commands. The roadmap's workflow evaluation and scoped verification remain separate workstreams ([specifications roadmap](../README.md)).
- Distributed workers, learned routing, unrestricted command execution, intrusive testing, and exploit development.
- Automated merging, remediation, issue creation, specification changes, or owner waivers.
- Production qualification before held-out evaluation. Any platform-specific merge gate without an atomic full-identity enforcement mechanism is outside the pilot's blocking integration scope.

### Actors & Roles

| Actor | Authority |
|---|---|
| Project owner or trusted delegate | Approves exact specification revisions and delivery assignments, sets pilot thresholds and project policy, resolves product ambiguity, authorizes scoped waivers, and controls merges and changes. |
| Intake/context builder | Resolves inputs and builds a pinned manifest and bounded index with provenance and coverage limitations. |
| Deterministic supervisor | Owns all review state transitions, admission, coverage gates, evidence validation, and report freeze. |
| Lead reviewer | Plans substantive checks, examines cross-component questions, and returns evidence and bounded job proposals. |
| Worker or independent validator | Examines assigned pinned inputs and submits private structured results. |
| Publication adapter | Delivers permitted report and check records through restricted credentials. |
| Pilot evaluator | Maintains blind labels, locks the evaluation plan, and compares configurations. |

### Terminology

- **Specification** means approved product intent in the pilot. Orchestrail's **spec** is its development task statement (`.ai/principles/domain.md:12–18`).
- **Source unit** is a meaningful unit of the pinned specification or annex. A **criterion** is a versioned, project-scoped observable obligation derived from binding source text. A **slice** is independently testable delivery scope within a criterion.
- **Obligation** is a particular scenario and evidence contract from an applicable criterion or risk rule. **Coverage** describes what was examined and supported. **Conformance** is the criterion outcome in scope.
- **Candidate** is a private submitted claim with a durable receipt. A **canonical finding** groups equivalent claims and preserves their distinct conditions. **Action** is the authorized timing or disposition.
- **Snapshot** is the pinned review composition. **Gate identity** adds every version or expiry affecting eligibility. A **first report** is the immutable initial freeze. A **continuation** holds later work and may yield a linked correction. Late findings are classified as initially missed, subsequently introduced, pre-existing or undetermined before quality metrics are computed.
- **Machine outcome** is `pass`, `fail` or `incomplete`. **Freshness** is `current`, `stale` or `unknown`. **Delivery** is `local only`, `delivered`, `delivered late` or `uncertain`. **Advisory** describes publication without merge authority. A receipt or report can be stale and historically delivered.
- **Independent** means the reviewer records its initial trace from the required pinned inputs before seeing the earlier conclusion. Critical rules can require stricter method or input separation.

### Requirements

| ID | EARS requirement |
|---|---|
| REQ-01 | WHEN a review request is admitted, THE SYSTEM SHALL pin a review envelope with the requested and tested compositions. |
| REQ-02 | WHEN specification material is considered for feature review, THE SYSTEM SHALL establish normative authority from trusted approval evidence for its exact revision and accessible normative annexes. |
| REQ-03 | IF normative inputs or required interpretation are unavailable, ambiguous, or unapproved, THEN THE SYSTEM SHALL continue independently admissible checks with an explicit affected conformance and coverage gap. |
| REQ-04 | WHEN criteria are assigned to a delivery composition, THE SYSTEM SHALL reconcile their assignments against an approved delivery manifest. |
| REQ-05 | WHEN an integration milestone is reviewed, THE SYSTEM SHALL evaluate due feature criteria against the pinned integrated composition. |
| REQ-06 | WHEN a feature ledger observation is written, THE SYSTEM SHALL advance the current view only through a matching version and target comparison. |
| REQ-07 | WHEN a specification inventory is built, THE SYSTEM SHALL reconcile every meaningful source unit against a separately grounded classification of the pinned material. |
| REQ-08 | WHEN a criterion or slice is due, THE SYSTEM SHALL plan evidence at the applicable behavior boundary, including omission, disallowed behavior and relevant adverse cases. |
| REQ-09 | WHEN changed behavior is identified, THE SYSTEM SHALL investigate its supported rationale or applicable technical invariant. |
| REQ-10 | WHEN a route is selected, THE SYSTEM SHALL derive mandatory obligations from the union of applicable versioned risk rules and applicable criterion obligations. |
| REQ-11 | WHEN a high or critical route applies, THE SYSTEM SHALL schedule blind discovery against the pinned raw sources before exposing earlier conclusions. |
| REQ-12 | WHEN a critical conclusion is evaluated, THE SYSTEM SHALL enforce the specific property's independent evidence contract. |
| REQ-13 | WHEN an obligation is grouped, split or deduplicated, THE SYSTEM SHALL preserve its individual scope, answer and independence needs. |
| REQ-14 | WHEN a worker result is received, THE SYSTEM SHALL accept only individually complete answers that satisfy the pinned result contract. |
| REQ-15 | IF lead planning fails, THEN THE SYSTEM SHALL continue admissible rule- and criterion-derived checks with a recorded semantic planning gap. |
| REQ-16 | WHEN experiment evidence is used, THE SYSTEM SHALL evaluate it against a trusted oracle and retain enough provenance to reproduce the observation. |
| REQ-17 | WHEN a candidate is accepted, THE SYSTEM SHALL preserve its receipt and evidence under reversible grouping. |
| REQ-18 | WHEN a candidate is adjudicated, THE SYSTEM SHALL record a factual verdict grounded in expectation, reachability, observation, consequence, counterevidence and attribution. |
| REQ-19 | WHEN a confirmed finding is considered for publication, THE SYSTEM SHALL validate its comment against the publication quality contract. |
| REQ-20 | WHEN the supervisor determines action, THE SYSTEM SHALL apply the trusted gate, exposure, delivery scope and waiver policy to the factual verdict. |
| REQ-21 | WHEN the first report freezes, THE SYSTEM SHALL seal exactly one complete decision row per accepted receipt in the closed input epoch. |
| REQ-22 | WHEN a job is considered for dispatch, THE SYSTEM SHALL apply host-wide atomic admission across operating resources and model-provider quotas. |
| REQ-23 | WHEN metered work is considered for dispatch, THE SYSTEM SHALL reserve enforceable maximum liability at both run and shared budget scopes. |
| REQ-24 | WHEN receipt-based feasibility changes materially, THE SYSTEM SHALL select the admissible complete or partial path while preserving downstream validation and local finalization capacity. |
| REQ-25 | WHEN concurrent runs compete for capacity, THE SYSTEM SHALL schedule eligible work using configured fair shares and aging while preserving protected work capacity. |
| REQ-26 | WHEN dispatch, result acceptance or restart occurs, THE SYSTEM SHALL reconcile work by durable attempt generation, resource accounting and the original deadline. |
| REQ-27 | WHEN evidence is considered for reuse or a relevant input changes, THE SYSTEM SHALL enforce provenance-dependent validity for evidence, conformance and action. |
| REQ-28 | WHEN material is read, persisted or transferred, THE SYSTEM SHALL enforce the project's access domain and approved data policy. |
| REQ-29 | WHEN an operation requires execution of untrusted code or parsing in a job sandbox, THE SYSTEM SHALL enforce the approved isolation boundary before execution. |
| REQ-30 | IF a boundary violation is detected, THEN THE SYSTEM SHALL enter a contained state that stops dispatch and external data transfer and withholds success. |
| REQ-31 | WHEN a local report freezes, THE SYSTEM SHALL persist its observable review summary and allowed delivery intent atomically. |
| REQ-32 | WHEN machine outcome is evaluated, THE SYSTEM SHALL apply deterministic precedence to confirmed unwaived blockers, mandatory gaps and configured pass criteria. |
| REQ-33 | WHEN a report or check is delivered, THE SYSTEM SHALL reconcile freshness and delivery identity through the restricted publication adapter. |
| REQ-34 | WHEN a project uses a passing review to authorize merge, THE SYSTEM SHALL require atomic enforcement of the still-current full gate identity at merge time. |
| REQ-35 | WHEN evidence arrives after the first freeze, THE SYSTEM SHALL preserve the first report and record new observations in a continuation or linked new run. |
| REQ-36 | WHEN an eligible audit sample is selected, THE SYSTEM SHALL persist the selection stratum, probability and independent audit observation. |
| REQ-37 | WHEN the pilot compares configurations, THE SYSTEM SHALL evaluate them on matched held-out snapshots using locked metrics, blinded labels and separate internal and delivered outcomes. |
| REQ-38 | WHEN a route is considered for qualification, THE SYSTEM SHALL select the lowest total cost among configurations meeting predeclared absolute gates and the paired comparison rule. |
| REQ-39 | WHEN review knowledge is retained across runs, THE SYSTEM SHALL version authoritative facts, hypotheses, conflicts and superseded observations with scope and invalidation provenance. |
| REQ-40 | WHEN a review plan is finalized, THE SYSTEM SHALL reconcile the planned and completed work against the criterion and mandatory risk inventories. |
| REQ-41 | WHEN repository text, specification or annex content, linked material or tool output is processed, THE SYSTEM SHALL treat that content as data with zero operational authority. |
| REQ-42 | WHEN a fix is reviewed, THE SYSTEM SHALL recheck the root cause, affected scenarios and new impact area. |
| REQ-43 | WHEN a late finding is attributed for evaluation, THE SYSTEM SHALL classify it before assigning it to quality metrics. |
| REQ-44 | WHEN a run reaches its local cutoff without a finalized report and the host and store remain available, THE SYSTEM SHALL let the watchdog seal a minimal local report under the first-report transaction and the normal verdict precedence. |

### Data Model

All product records below are new to the standalone service. IDs are opaque strings unless a composite key is stated. Revisions, digests, versions and external references are typed opaque strings. Timestamps are timezone-aware instants, counters and normalized resource units are nonnegative integers, and money uses exact amounts in an explicitly configured currency and unit. Versioned enums use the values defined here or in the pinned project's policy where named.

| Entity and identity | Required fields, relationships and lifecycle |
|---|---|
| Project and policy, keyed by project and policy version | Access domain, trusted approval sources, catalog, resource/spend/deadline profiles, exemptions, independence rules, audit strata, allowed actions and data controls. Immutable version per run. |
| Review and snapshot, keyed by run ID and snapshot digest | Project, PR or milestone, receipt/deadline, base/head/merge base, parent, target and actual tested tree, dependencies, policy/tool/resource versions, state and typed gaps. Composition tracks branch, integration, or both. Missing optional revisions retain explicit reasons. |
| Specification version and source unit | Project-scoped canonical specification ID plus revision/digest, authority/approval and owner, annex fingerprints and access domain. Units retain source anchor and classification. Criteria retain project-scoped key, version, exact span, observable property, prerequisites, exceptions and milestone. Cross-version links retain meaning checks. |
| Delivery plan and feature ledger | Plan version, criterion/slice assignments, owner/milestone/PR, dependencies, acceptance point, intermediate invariants and approval. Append observations tied to run, target and criterion version. Current projection advances by expected ledger revision and matching spec/target. On conflict recalculate from the latest authorized snapshot, mark superseded revisions and reopen affected criteria where verification cannot carry forward. |
| Obligation and task attempt | Obligation links many-to-many to source criteria, rules, evidence and jobs. Store property, scope, scenario, assumptions, evidence contract, mandatory flag, independence, stop condition, applicability, execution, explored scope, result and sufficiency. Attempt stores run/job ID, generation, lease, dependencies, method/version and reservation. |
| Evidence and knowledge entry | Artifact digest, access domain, run/snapshot and scope, source anchors, method, observations, trusted oracle and limitations where applicable. Knowledge entries classify authority, verified fact, hypothesis, conflict or supersession and carry invalidation prerequisites. |
| Candidate receipt, finding and decision | Receipt ID, epoch, original submission, evidence access, canonical record and grouping history. Decision stores verdict `confirmed`, `refuted` or `unresolved`, comment outcome `pass`, `needs repair` or `inapplicable`, action, reason, authority, severity, scope, exposure, attribution, evidence and follow-up. Attribution is introduced, activated/aggravated, integration-only, pre-existing or unknown. Duplicate receipts retain their own impact check. |
| Owner authorization | Verified issuer, finding, exact scope and snapshot, rationale, expiry, follow-up and version/status. Waivers change permitted action only. |
| Resource ledger and outbox | Disjoint settled, reserved and uncertain liabilities, price version, leases, provider reconciliation data and resource scopes. Report and outbox hold gate identity, immutable report digest, publication key, attempt history, freshness, delivery status and timestamps. |
| Evaluation record | Snapshot and feature cluster, blind labels, matched configurations, eligibility, first-report identifiers, coverage, charges, measurements and sample probabilities. |

Initialize a new store. Existing Orchestrail Markdown task state needs no migration. Reuse historical evidence only through the provenance and access contract.

### Contracts & Interfaces

- **Intake.** Supply authenticated project and PR or milestone identity, target revision and idempotent trigger identity. Obtain trusted receipt time, policy, resource profile, specification approval and plan through configured adapters. Repeating a trigger returns its original run. Reuse of the identity with different immutable inputs is a conflict. Invalid or unauthorized requests are rejected before jobs are dispatched. Missing review evidence is a typed gap on an admitted request.
- **Review job.** Supervisor sends run, snapshot, job, attempt generation, property, questions, scope, assumptions, depth, expected evidence, escalation conditions, allowed inputs/tools, and resource envelope. Worker returns the same identities, method/version, one answer per scenario, checked source, evidence, criteria, candidate submissions, gaps, dependencies and bounded proposals. Runtime-recorded reads and observations accompany results. Validate envelope schema and exact run, snapshot, job and attempt identities, generation and access before accepting any answer or candidate. Store typed rejection reasons for invalid envelopes or artifact references without advancing the affected work. Only independently delimited, complete answers with valid scoped evidence can survive truncation within a valid envelope. A grouped job keeps separate scenario answers. Deduplication requires matching snapshot, property, scope, question, assumptions, method/depth, evidence contract, escalation and stop conditions, resource envelope and independence needs.
- **Specification and delivery authority.** Resolve identity, access and approval independently. A PR link is a lookup hint. A self-edited specification uses its approved baseline until a separately verified exact-revision approval exists. Classify text as binding, illustrative, advisory, non-goal or explanatory at the source-unit level. Record competing interpretations and missing annexes for owner clarification. Assign slices as due now, shared, approved future, previously delivered, or uncertain. A single-PR approved whole-feature intent assigns all binding criteria. Check duplicates with inconsistent expectations, missing assignments/dependencies and cycles. Check stacked dependencies in the actual tested composition before credit.
- **Coverage and risk policy.** Criterion results are `satisfied in scope`, `violated`, `undetermined` or `justified inapplicable`. Govern applicability, execution, checked scope, outcome and sufficiency independently. Each rule defines applicability signals, source coverage, exclusion, depth, evidence and independence, backed by fixtures. Catalog includes behavior, trust, state, delivery, interfaces, numeric/time/serialization concerns, operation, testing and project constraints. Executable changes trigger functional, boundary, error, regression and dependency checks. Mechanical routing requires positive whole-scope equivalence and trusted exemption where required. Local routing uses relevant tools and narrow review. Substantive routing uses lead planning with ready independent checks. High/critical routing adds deep scenarios and blind discovery. Unsupported parsing, unknown wiring and missing consumers leave gaps unless resolved. Before report freeze, the supervisor accounts for each mandatory obligation from both inventories as completed with sufficient evidence, justified inapplicable, or an explicit gap. The lead and workers cannot cancel mandatory work or approve exclusions.
- **Evidence.** Record checked paths, preconditions, relevant source and uncovered paths for consequential negatives and satisfied criteria. Review notes distinguish observations from assumptions. Experiments store inputs, environment, versions, oracle, outputs and limits. A failed run, flake, unsupported environment or irrelevant passing test cannot settle the claim. Critical validators see property and source anchors first and commit their own trace before the proposed conclusion is disclosed. A critical blocker's author cannot be its sole validator. Record each validator's identity and independent method. New hypotheses enter regular receipt handling. Use deterministic adjudication when the oracle and scope/action are sufficient, narrow independent analysis for contested behavior and cross-component analysis where traces or attribution conflict.
- **Action.** A confirmed current gate breach recommends fix before merge. A material attributable advisory issue recommends fix in this PR. An approved safe follow-up needs scope, owner or role, milestone/date, rationale and residual risk. A proposed unsafe or unauthorized deferral requires owner decision and preserves an existing block. Approved future scope appears in the matrix. Refutation records counterevidence. Duplicate decisions link to a canonical predicate. Unresolved decisions name the missing verification. Pre-existing debt and optional improvements appear separately when configured. Comment quality requires a reliable location or criterion/boundary anchor, trigger, expected and observed effect, material consequence and evidence. Suggested remedies need separate verification.
- **Report and publication.** Return local report ID, revisions, spec/plan/approval, criterion matrix and evidence, separate outcomes for execution, coverage, conformance, findings, action, feature acceptance, freshness and delivery, candidate totals, budget/resource totals, and receipt-to-freeze/delivery times. External findings require a confirmed fact, comment quality pass and authorized disposition. Expose material open checks in neutral terms and keep theories/refutations private. A material confirmed claim held for wording repair stays accounted for and cannot enable pass. Use a stable project/PR/snapshot/report delivery key and record freshness and delivery using their independent enums. For example, a historically delivered report can now be stale. Reconcile ambiguous writes before retry.
- **Gate.** Gate identity includes head, target/integration revision, specification and approval versions, plan, policy, and applicable waiver versions and expiry. Verify freshness at publication and at merge for binding checks. Changes including approval withdrawal invalidate eligibility even at the same head. Poll to reconcile missed events and retire superseded checks. Offer advisory snapshot results where the platform lacks binding support.
- **Recovery.** Journal intent, generation, lease and reservation atomically before external dispatch. Accept a validated result and associated local transitions atomically. Expired local leases do not release uncertain external occupancy or liability. Provider status/idempotency can settle it. Report freeze and delivery intent share a transaction. Freeze enforces exact equality of the accepted receipt and decision ID sets, unique original ownership and valid external finding references. Pending or inapplicable decision fields carry explicit reasons, including the missing evidence for unresolved receipts. At configured local cutoff the watchdog can contend for the same single first-report transaction, close the epoch, seal unresolved receipts and mandatory gaps and issue a minimal local report using the normal verdict precedence. A known confirmed unwaived blocker yields fail even if unfinished work creates mandatory gaps. Without such a blocker, a mandatory gap yields incomplete. If freeze integrity fails, only a technical incomplete record without substantive findings or passing check is permitted while the store is available.

### Non-Functional Requirements

| Attribute | Standard and verification |
|---|---|
| Resources | Configured host, run and job ceilings apply to the whole descendant tree for CPU, memory, processes, scratch and output. Preserve OS/controller/finalizer headroom and include applicable accelerator use. Linux jobs use delegated cgroups and quota-limited scratch. Policy bounds intake, total jobs, descendant jobs, review rounds, context expansion and result output. Technical retries and substantive rechecks have separate counters and caps. Deny over-limit proposals, preserve admissible work and report overload or an affected coverage gap. Verify with controlled saturation, capped proposal chains and unavailable-isolation cases. |
| Spend and quota | Settled spend + active reservations + uncertain liabilities + proposed maximum charge must be at or below both ceilings. Reserve conservative uncached input plus maximum billable generation under the pinned tariff, including fees, retries, applicable reasoning charges, paid tools and nested charges. Broker nested charges under a verifiable maximum or disable the route when maximum liability cannot be enforced. Track rolling request/token buckets and provider concurrency. Exercise exact cap, over-cap, lost response and provider delay. |
| Deadline | Back-schedule from original receipt using the configured deadline and protected capacity. A ready job requires resolved dependencies, permissions, measured and reserved capacity, spend and enough time for downstream work. Never lend protected discovery, validation or finalization capacity to work whose release cannot be bounded, even between mandatory work classes. Report limits when provider quota isolation is best-effort. Validate with fake clocks and a watchdog test against the real store. Five-minute ordinary-PR p95 and eight-minute local cutoff are pilot hypotheses from the source. Track delivery separately, including outages and oversized or overloaded PRs. |
| Isolation and confidentiality | Approved policy controls commands, network, artifact capture, redaction, providers, residency, retention and deletion. Read-only snapshots and disposable job environments exclude host/control credentials and production services. Deny network by default, fetch approved dependencies separately, and prevent untrusted setup hooks from running in trusted setup. Reject out-of-root paths and links in archives and snapshots before unpacking or capturing artifacts. Treat accepted specifications as product authority only. Operational permissions, tool and provider selection, policy overrides and publication come from trusted configuration and the supervisor. Verify with controlled policy and boundary fixtures. |
| Integrity and recovery | Transactional conservation of receipt IDs, idempotent acceptance and delivery reconciliation, and immutable first report. Validate with competing writes and injected crash/restart at each external transition. |
| Evaluation | Before held-out scoring, lock absolute floors, margin, confidence method, rare-class sample sizes, availability, spend, latency and matching rules. Measure first-report severity-weighted and per-class critical recall, precision, missed clauses, wrong omissions, unsafe deferrals, false blockers, wrong dismissals, action agreement, human triage time, peak RAM, coverage, delivery, latency and total cost. Track overload, partial, cancelled and undelivered work in the declared denominator. Score detections from frozen report content against the common label set using the locked matching and pooled adjudication protocol. A newly recognized original miss can affect recall but a continuation cannot count as first-report detection. Audit sampling uses a predeclared design and eligible frame within each stratum, draws randomly and records the actual inclusion probability. Retain the seed or draw record for reproducibility. |

### Edge Cases & Failure Modes

| Case | Expected behavior |
|---|---|
| Missing or empty inventory, conflicting authority, inaccessible annex, unsupported parser | Preserve independently available work, record affected gaps and withhold a successful coverage gate. REQ-02, REQ-03, REQ-07, REQ-10 |
| No diff hunk for required behavior | Anchor evidence to the criterion and owning boundary. An empty search alone leaves absence unproven. REQ-08, REQ-18, REQ-19 |
| Scope cycles, future work, missing stacked revision, previous delivery affected by a new consumer | Preserve uncertainty or check actual current invariants. Credit only applicable valid evidence. REQ-04, REQ-05, REQ-27 |
| Invalid/truncated result, stale generation, cancellation or uncertain external charge | Keep admissible evidence and unanswered work distinct. Preserve external occupancy/liability until settled or conservatively accounted for. REQ-14, REQ-23, REQ-26 |
| No candidates or an unresolved candidate at cutoff | Finish required independent negative checks or retain gaps. Seal receipts in the correct epoch, including unresolved rows. REQ-12, REQ-21 |
| Conflicting duplicate impact, poor wording, flaky refutation, unauthorized deferral | Preserve individual action, factual verdict and evidence. An unproven refutation remains unresolved. REQ-17–REQ-20 |
| Oversized request, saturated host, absent isolation, unusable provider or infeasible route | Dispatch admissible useful work only within limits and leave explicit gaps. Report technically incomplete where available. REQ-22–REQ-25, REQ-29, REQ-31 |
| Concurrent feature update, same-head approval change, expired waiver or lost publication response | Use optimistic ledger advancement, invalidate affected gate identity and reconcile before retry. REQ-06, REQ-27, REQ-33, REQ-34 |
| Deceptive repository text, disallowed data, or cross-project artifacts | Treat content as data, deny unauthorized access/transfer and record safe evidence and gaps where permitted. REQ-28–REQ-30 |
| Empty cohort or no qualifying reference | Report insufficient evaluation evidence or no qualified configuration. Preserve all workload outcomes for the locked analysis. REQ-37, REQ-38 |

### Acceptance Criteria

Each row is independently observable. Fixture inputs configure policy, limits and authority explicitly.

| ID and trace | Given | When | Then |
|---|---|---|---|
| AC-01 / REQ-01 | A stacked PR with a failed integration-tree construction | Intake admits it | Its envelope records base, head, merge base, parent, dependencies, versions, timestamps and branch scope, and contains a typed integration gap. |
| AC-02 / REQ-02 | A PR edits its own spec and cites an unapproved postponement | Intake resolves authority | The approved baseline governs and the disputed revision and postponement are recorded. |
| AC-03 / REQ-03 | An inaccessible normative annex and an independently runnable compatibility check | The review completes | Compatibility produces its own result and affected criteria remain undetermined with mandatory gaps. |
| AC-04 / REQ-04 | An approved two-PR plan assigns schema to the first PR and replay activation to the second | The first PR is reviewed | The schema and intermediate safety are in scope and activation is pending. A fixture with a missing dependency or cycle records uncertainty for affected slices. |
| AC-05 / REQ-05 | Individual PR checks passed but the pinned integrated producer and consumer disagree | The final milestone is reviewed | Feature acceptance records the integration violation and preserves individual PR observations. |
| AC-06 / REQ-06 | Concurrent writers use the same ledger version while the target or spec advances | Both submit completed observations | Both admissible observations remain addressable. The stale update cannot advance the view, which is recomputed from the trusted current inputs with superseded revisions recorded and affected criteria reopened where evidence cannot carry forward. |
| AC-07 / REQ-07 | A brief spec has a binding exception embedded in an example and the first extractor misses it | The independent inventory gate runs | The exception is mapped or a reasoned unknown is recorded and affected coverage cannot pass. |
| AC-08 / REQ-08 | An approved single-PR behavior is absent from the diff and the owning entry point | The pinned review traces the owning entry point and applicable paths | Trusted evidence of the absent path yields a confirmed omission anchored to the criterion and boundary. In a companion fixture with only an empty search, conformance remains undetermined. |
| AC-09 / REQ-09 | One changed behavior has no spec clause but violates a known compatibility contract, and another is a supported refactor | Reverse coverage runs | The compatibility mismatch is investigated and the refactor's rationale is recorded without a defect solely for missing mapping. |
| AC-10 / REQ-10 | A one-line configuration change triggers an applicable critical tenant invariant and an unsupported parser | A reviewer proposes mechanical routing | The mandatory risk obligation survives, and lack of equivalence evidence prevents the shortcut. |
| AC-11 / REQ-11 | A high-risk assignment and an existing lead conclusion | The blind discovery worker begins | Its initial context contains the pinned raw sources and excludes the lead's plan and conclusion until its trace is committed. |
| AC-12 / REQ-12 | A critical negative result lacks evidence about a material consumer | The supervisor evaluates coverage | The property stays open until independent evidence covers that consumer. In a companion critical blocker fixture, a sole validation by the candidate's author leaves the independence requirement open. |
| AC-13 / REQ-13 | Two scenarios share files but differ in scope or independence | Work is grouped or deduplicated | The differing assignments are not deduplicated. A grouped job retains both verifiable answers and their separate supporting evidence. A fully identical eligible assignment may reuse a single job. |
| AC-14 / REQ-14 | A valid current envelope is truncated after one complete answer, and separate fixtures have bad identity, invalid schema or stale generation | Results are validated | Only the first complete supported answer advances. The unanswered scenario stays open. Invalid envelopes record a typed rejection and neither advance coverage nor admit candidates. |
| AC-15 / REQ-15 | Lead planning times out while a mandatory rule job fits protected resources | The supervisor chooses fallback work | The rule job runs and the missing semantic pass is recorded. |
| AC-16 / REQ-16 | A flaky run fails to reproduce and a passing experiment uses a different precondition | Factual evaluation consumes the results | Neither settles the claim and the original observations and limitations remain inspectable. |
| AC-17 / REQ-17 | Twenty original receipts include four duplicates and two otherwise grouped claims with materially different impact | Grouping is applied | All twenty remain traceable, the four duplicates retain canonical pointers and materially distinct actions remain separately represented. |
| AC-18 / REQ-18 | A claim lacks comparable base evidence and another has trusted counterevidence | Factual adjudication runs | The first retains unknown attribution or the corresponding unresolved fact and the second is refuted with linked counterevidence. |
| AC-19 / REQ-19 | A confirmed omission has vague wording and no truthful diff anchor | A comment is evaluated | A publishable rewrite cites the criterion and responsible boundary with verified trigger, effect, consequence and evidence, or is withheld with `needs repair`. |
| AC-20 / REQ-20 | A confirmed blocker is suggested for deferral with no applicable authorization | Action is assigned | Existing block remains and owner decision is recorded with the affected risk. |
| AC-21 / REQ-21 | An unresolved receipt precedes cutoff and a second receipt races after epoch close | Freeze commits | Exactly one complete unresolved row belongs to the first receipt, and the later receipt belongs to a continuation. A fixture with equal counts but a substituted receipt ID or an orphan external finding reference yields only technical incomplete output. |
| AC-22 / REQ-22 | Two simultaneous jobs fit individually but exceed an aggregate descendant resource or provider quota together | Both are considered | At most the set within the combined limit dispatches, with controller headroom preserved. |
| AC-23 / REQ-23 | Uncertain cancellation liability and a new metered fee would exceed either configured ceiling | A retry or paid tool requests admission | That dispatch is declined, prior uncertain liability remains held, and reported maximum includes all outstanding charges. Equality permits admission when other constraints also pass. A charge without an enforceable maximum is rejected. |
| AC-24 / REQ-24 | The minimum required route already exceeds remaining time | Feasibility is evaluated | The full route is not dispatched, the reason is visible and independently useful work fitting the protected cutoff can contribute to a partial local report. |
| AC-25 / REQ-25 | Multiple PRs, an unbounded provider tail and a candidate flood compete under a known fair-share policy | The scheduler runs | A ready fitting job can progress without siblings completing. Unbounded provider work cannot use another class's protected capacity, and eligible discovery, validation and finalization retain theirs. Intake beyond policy is recorded as overload, and capped chained proposals or retries cannot dispatch. |
| AC-26 / REQ-26 | The service crashes after journaling a provider call whose outcome is unknown | It restarts and receives a late stale response | Deadline and uncertain occupancy survive; stale response cannot advance state and a current valid generation is committed at most once. |
| AC-27 / REQ-27 | An unchanged file has a changed transitive input or newly discovered consumer | Reuse is checked | Affected evidence is excluded from current conformance until revalidated and historical evidence remains accessible to authorized readers. |
| AC-28 / REQ-28 | Two projects share a content digest, and one provider transfer violates the project's redaction policy | The jobs request reuse and transfer | Cross-domain artifact reuse and disallowed egress are denied and the affected evidence gap is recorded. |
| AC-29 / REQ-29 | A fixture includes an untrusted setup hook, child process, archive entry and link referring out of root, or lacks verified isolation | A job prepares execution | Trusted setup does not run the hook, controlled child work stays within its limits, and the job cannot access out-of-scope data or execute without the required isolation. Ingest and artifact capture reject the out-of-root paths without creating or exposing outside files. |
| AC-30 / REQ-30 | The isolation monitor signals a boundary violation during a run | The supervisor handles the event | New dispatch and external transfers stop, safe incident evidence is retained and success is withheld. |
| AC-31 / REQ-31 | A mixed review includes confirmed, duplicate, refuted and unresolved receipts, and the process crashes at freeze | The store recovers | Report and allowed intent both exist or neither exists. The report reconciles counts, includes required summary fields and exposes only authorized findings and neutral material gaps. |
| AC-32 / REQ-32 | A confirmed unwaived blocker lacks publishable wording and a mandatory scenario is still open | Machine outcome is computed | Outcome is fail with a separately stored gap. With the blocker validly waived, the same gap yields incomplete. A fresh otherwise eligible fixture with all gates met passes. Toggling required coverage, conformance or policy prevents pass, and stale or unknown freshness prevents publication of a current pass. |
| AC-33 / REQ-33 | Publication has an ambiguous response and the same head loses spec approval or changes its plan before retry | The adapter reconciles | It searches by stable delivery identity before retry, never delivers a current pass for outdated eligibility and preserves historical delivery evidence. |
| AC-34 / REQ-34 | Approval, target or waiver expiry changes at the same head before or during a merge attempt | The gate is evaluated | A stale tuple cannot authorize merge. A head-only platform exposes advisory snapshot results. |
| AC-35 / REQ-35 | Useful evidence arrives after first local freeze | The continuation completes | The first report digest, findings and observed run measurements are unchanged, and any correction links to the original report. A newly pooled label for an original miss can change evaluated recall, and later evidence cannot increase first-report detections. |
| AC-36 / REQ-36 | A locked audit design makes a seeded uniform draw of two items without replacement from a stratum of ten eligible clean routes, negatives or dismissed claims | The configured audit runs twice with the same seed and frame | Both draws select the same two identities and each has recorded inclusion probability 0.2, its stratum and an independent audit result. The selected work survives a lead cancellation proposal. |
| AC-37 / REQ-37 | A locked, blinded evaluation includes a feature series, clean controls, rare cases and partial/undelivered runs | Configurations are scored | Identical pinned cases, shared labels and matching rules are used, related PRs stay together in splits and uncertainty estimates, and internal, first-report and delivered outcomes are distinct. |
| AC-38 / REQ-38 | Several configurations have known total costs and paired results, including a cheap route below an absolute floor | Qualification runs | The least costly eligible route is selected, and a cohort with no qualifying reference yields no qualified route. |
| AC-39 / REQ-39 | A previously verified fact is superseded after a fix and a new observation has uncertain attribution | Knowledge is reconciled | History preserves both versions, provenance and classification, and the superseded fact cannot silently support current conformance. |
| AC-40 / REQ-40 | A lead plan omits a due criterion and asks to cancel an applicable mandatory risk check | The supervisor verifies the plan and freezes a report | Both obligations remain required. Each appears with sufficient execution evidence or an explicit mandatory gap. |
| AC-41 / REQ-41 | An otherwise approved specification and ordinary tool output ask for an unapproved tool, route, policy override or publication | The system processes those inputs | Operational authority is unchanged and requested side effects do not occur. Authorized ordinary review continues. |
| AC-42 / REQ-42 | A fix changes the reported root cause and introduces a new consumer boundary | The fix is reviewed | Its records show checks of the root cause, affected scenarios and the new boundary, including any unresolved gaps. |
| AC-43 / REQ-43 | Four late findings have evidence of an original miss, subsequent introduction, pre-existing behavior and ambiguous chronology respectively | Evaluation assigns attribution | Each receives its fixture's expected class. Only an originally missed in-scope finding is assigned to the first-report missed class. |
| AC-44 / REQ-44 | A hung worker and an unresolved candidate remain at local cutoff while the store and watchdog operate | The watchdog and normal finalizer contend | One first report and epoch closure commit. If the watchdog wins, the report includes the mandatory gap and unresolved receipt. Outcome is incomplete without a confirmed unwaived blocker and fail in the companion fixture with one. Neither enqueues a passing check. |

### Traceability

Each requirement maps to the same-numbered acceptance criterion.

| Source sections | Requirements |
|---|---|
| 1–2 | REQ-01, REQ-10–REQ-16, REQ-21–REQ-26, REQ-31, REQ-38 |
| 3–4 | REQ-01–REQ-06, REQ-18, REQ-27 |
| 5–7 | REQ-07–REQ-16, REQ-36, REQ-40 |
| 8 | REQ-17–REQ-21, REQ-36 |
| 9–10 | REQ-12, REQ-22–REQ-30, REQ-39, REQ-41–REQ-44 |
| 11–12 | REQ-31–REQ-38, REQ-43–REQ-44 |

### Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Extractor and verifier miss the same clause | False conformance | Medium | Require separate source-grounded reconciliation and audit examples/annexes. |
| Effective gate identity changes at the same head | Stale pass authorizes merge | Medium | Require full-tuple merge-time enforcement for binding integration. |
| Provider uncertainty ties up resources | Fewer timely reviews | Medium | Retain liability, isolate protected slots and prefer independently useful partial work. |
| Data crosses approval or isolation boundary | Unauthorized disclosure or execution | Medium | Enforce access-domain partitioning, project data policy and bounded isolation with a stop transition. |
| Correlated labels or future leakage bias evaluation | Misqualified routing | Medium | Freeze historical snapshots, blind labels, pool newly adjudicated discoveries and cluster related changes. |
| Pilot is delivered as one broad implementation | Delayed feedback on critical dependencies | High | Split the acceptance surface as recorded in Notes. |

### Assumptions

- A-01 | Hosting boundary | Resolved: Treat the service as standalone within the pilot contract and leave placement for Discovery | Source: Edition 5 §2 and accepted instruction-driven pipeline decision | Reversible: yes
- A-02 | Initial integrations | Resolved: Use capability-based adapters and controlled fixtures for intake, publication and metering with a stable local interface | Source: Edition 5 §§2, 9, 11 and smallest reversible choice | Reversible: yes
- A-03 | Record representation | Resolved: Use opaque scoped identities, immutable versioned inputs and exact ledger arithmetic in a new store | Source: Edition 5 §§9–10 and project architecture principles P2–P4 | Reversible: yes
- A-04 | Minimum scheduling and reuse | Resolved: Start with fixed rules, eligible-job scheduling and exact-input evidence reuse | Source: Edition 5 §§9–10, 12 | Reversible: yes
- A-05 | Pilot thresholds | Resolved: Treat source latency values as hypotheses and make evaluation gates owner-supplied and locked before holdout | Source: Edition 5 §§1, 9, 12 | Reversible: yes
- A-06 | Missing event source | Resolved: Use a trusted explicit milestone request and polling reconciliation as applicable | Source: Edition 5 §§4, 11 | Reversible: yes
- A-07 | Publication rollout | Resolved: Start with replay and shadow reporting and use advisory output by default where binding enforcement is unavailable | Source: Edition 5 §§11–12 and smallest reversible choice | Reversible: yes
- A-08 | Ingress idempotency | Resolved: Deduplicate a trigger within its authenticated project and reject reuse with different immutable inputs | Source: Edition 5 §§10–11 recovery model and smallest reversible choice | Reversible: yes
- A-09 | Sensitive material | Resolved: Require a configured, approved project data policy for any real-data processing and exercise the contract with synthetic fixtures first | Source: Edition 5 §10 | Reversible: yes

### Open Questions

- Q-01 | non-blocker | Which repository, workload, hardware, provider, publication platform and project data policy will the owner approve for the real pilot? Controlled fixtures can implement the contracts. Live intake needs these inputs.
- Q-02 | non-blocker | What thresholds, sample sizes, comparison margins and fair-share profiles will the owner lock? Fixtures can use explicit settings. Held-out qualification and live operating limits require the selected values.

### Notes

- Use the paired offline result to decide whether to trial optional explicit coverage and whether to fund any standalone service work. For the service, deliver replay-only authority, delivery planning, coverage and adjudication with controlled worker results first. Then deliver isolated execution, hard admission, recovery and evaluation on pinned snapshots. Finally add live intake, delivery reconciliation and conditional gating. Stop new admissions and external delivery to suspend a live pilot, retain immutable records under project policy, and retire any active gate eligibility.
- In the later qualification, compare tools alone, tools plus narrow workers, the same workers with lead planning, a context-matched singleton, singleton plus a blind pass, and the two-lane design. Ablate mapping and semantic adjudication independently offline. Compare under matched cost/deadline and at matched quality using simultaneous paired bounds against one achievable reference. Lock the matching rule and pool newly adjudicated discoveries before comparative scoring.
- Later optimization can improve context grouping, cross-revision reuse and scheduling when replay and pilot data establish benefit. Keep simple routes where they meet the acceptance gates.
