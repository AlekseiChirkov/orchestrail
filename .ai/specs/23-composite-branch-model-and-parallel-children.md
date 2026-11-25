# 23. Parallel children of one composite subtask in isolated worktrees

## Source

- **Split (2026-11-16):** at commit `e3ba41a000c927ac157fd2207df413107ed54cb5` this file held
  both delivery stages of one specification and failed readiness check 13 (56 requirements
  exceed one feature). On the owner's request of 2026-11-16 (translated from Russian: "they are
  very large and must be split in two if this can be done logically; then run each resulting
  spec through `/spec-draft`") stage 23A, the composite branch model at N = 1, moved to
  `.ai/specs/22-composite-branch-model.md`; stage 23B, parallel children of one composite,
  stays here and starts after spec 22 is delivered (merged). Identifiers keep their numbers and each is
  defined in exactly one of the two files. The Source history below, including the translated
  original text, covers both stages and is the canonical copy that spec 22 cites.

- **Request:** `/spec-draft .ai/specs/23-composite-branch-model-and-parallel-children.md --auto-mode`
  (refinement in place, 2026-11-13). The owner authorized in-place replacement of this file
  and declared that no questions are answered during this run.
- **Input:** the existing specification at commit `c4372f881dd544ffbf8d2374dc66a8e468d61a86`,
  file `.ai/specs/23-composite-branch-model-and-parallel-children.md`; sections 1–16 were
  written in Russian, section 17 in English. Its full original text stays in git history
  (`git show c4372f8:.ai/specs/23-composite-branch-model-and-parallel-children.md`). The
  English text below is a faithful translation of sections 1–16; section 17, the
  Implementation review and the Change Log are reproduced unchanged. Links that pointed to
  the old public repository location at pinned commit
  `8c2fa08c18115ffcf38a1798742c41e53a2c7461` are given as repository-relative paths at that
  commit.
- **Governing decisions:** ADR-0009 Decision 4 (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:143-174`)
  rewrote this spec's scope to "one branch and one PR per composite; parallelism only
  inside a composite"; ADR-0009 Decision 2 (`:77-113`) names the capabilities `/spec-run`
  needs for `--parallel > 1`.

### Implementation review — 2026-11-06

- **Disposition:** Planned; parallel runtime not delivered.
- **Verified source scope:** main at `23bded3d96d9c562d16eb7e90285414f4412ac79`; owner-authorized specification/state reconciliation on 2026-11-06.
- **Delivered evidence:** Composite classification, canonical child progress, dependency ordering, and composite validation exist.
- **Outstanding scope and limits:** The branch-per-composite model, temporary child branch lifecycle, admitted parallel leaf scheduler, and per-workflow coordination in section 17 are not implemented by the shipped runner. Detached validator experiments do not deliver this contract.
- **Sources:** [`workflows/spec-run.md`](../../workflows/spec-run.md), [`workflows/pe-execute.md`](../../workflows/pe-execute.md), [`workflows/phase-composite-validation.md`](../../workflows/phase-composite-validation.md), [`rules/workflow-reference.md`](../../rules/workflow-reference.md).
- Existing requirement and acceptance identifiers remain binding. Source inspection and historical validation records do not constitute a fresh full-suite or deployed-environment certification.

### Original text, sections 1–16 (translated from Russian)

**Title.** 23. One branch for a composite task and isolated execution of its children.

**1. Status and verified initial state.** *Status:* planned contract for isolated parallel
subtask execution. Updated 2026-11-06. This specification does not itself enable parallel
execution or authorize publication.

In snapshot `8c2fa08c` the current execution process (`workflows/spec-run.md` at that commit)
is sequential: leaves form a chain of branches, and no separate branch is created for a
composite task. The integration check (`workflows/phase-composite-validation.md` at that
commit) already distinguishes the children's validation, the combined result and open
integration errors. That is not an implementation of temporary worktrees and parallel
workers.

The current write discipline (`rules/orchestration.md` at that commit) lets a worker change
its own leaf block but returns shared changes to the orchestrator. In this specification, for
the new mode, all writes under `.ai/`, including the children's own blocks, pass to the single
orchestrator. This is a target change, not a description of established behaviour.

Basis: ADR-0009, Decisions 2 and 4. The new decision record written at implementation must
state precisely which provisions of ADR-0004 Decision 3 and ADR-0005 Decision 1 are replaced.
The history of earlier decisions is not rewritten.

**2. Goal, boundaries and important clarifications.** A composite task is validated and
reviewed as one result: it has one permanent working branch and, when publication is
permitted, one pull request. Each child works on a temporary branch owned by the run, passes
the applicable checks and is included in the shared branch by a merge commit without
flattening history.

The goal is to reduce elapsed implementation time for one large task by concurrently running
as many eligible atomic subtasks as can be proven independent. This includes direct atomic
subtasks and atomic descendants of composite subtasks within one repository and task run.
Dependencies, file ownership, integration gates and resource locks remain binding. A
speedup, lower token use or lower cost is not guaranteed. Sequential execution retains the
same quality requirements.

Ambiguities of the original edition resolved:

- *"One request" is conditional on publication permission.* Without `--allow-pr` there are
  no branch pushes and no request-creation calls; with permission exactly one request is
  created per composite task, not one per child.
- *The mode without the flag stays sequential.* `--parallel` without a number means a request
  for two executors; `--parallel N` sets an explicit maximum. The value 2 keeps the original
  choice for the enabled parallel mode.
- *Sequential continuation after an overlap starts from the current composite branch*, but the
  child still gets its own temporary branch. It does not start writing directly into the
  shared branch.
- *The child's current test mode applies.* For a new testable function or a behaviour fix,
  RED before implementation is kept. For a change that does not change behaviour,
  `atomic-tests: pinned` is allowed: the tests pin the earlier behaviour, pass before the
  change and move only to `green`; test evidence is committed before the corresponding change
  without an artificial RED. A justified `none`/`n-a` keeps the permitted single commit. For
  an old block without `atomic-tests:` that already has `atomic-execution: in-progress`, the
  narrow continuation with the note `pre-TDD task, TDD step skipped` is kept, without a
  retroactive RED. A new or not-yet-started task does not get this exception. Grounds: the
  canonical state (`rules/workflow-globals.md`) and the commit rules (`rules/git-flow.md`).

These clarifications set the agreed target text but do not replace the record of the
behaviour change required at implementation.

Out of scope: concurrent independent top-level tasks or specifications; parallel discovery;
multiple repositories; parallel ordinary single-session execution; a separate integration
branch; state tool 07; and automatic merging of owner pull requests. Parallel atomic
descendants within one large task are in scope, including across composite boundaries.

**3. Dependencies and single owners of contracts.** Prerequisites per the current index: 09,
10, completed 02 and 03, 05, 12, 13, 15, 17, 18. Applicable constraints of 06 are used through
the common safety contract; effort and model availability are resolved by 16 and catalog 04,
not anew in this document.

| Document | What 23 receives |
|---|---|
| 09 | Verifiable environment capabilities, process names and the registry |
| 10 | Offline scenarios and a separately authorized comparative evaluation |
| 05 | Identity of requests, attempts, roles and intervals; no double counting |
| 06 | Operation constraints and the narrow exception for deleting a provably included child branch |
| 12 | The child's immutable packet, current dependencies and context hashes |
| 13 | Evidence envelopes, the source-revision check, idempotent application by the orchestrator |
| 15 | Verification scope and validity of confirmations by actual inputs |
| 17 | Bounded repair attempts only for an eligible isolated defect |
| 18 | Full criteria coverage, dependencies, file ownership and independence evidence |

**4. Terms and invariants.** *Composite task* — the existing permitted task type with children
and separate integration criteria. *Wave* — a bounded set of independent children launched
concurrently; a scheduling unit, not an additional branch. *Temporary child branch* — a branch
owned by a specific run with a recorded base and tip. *Inclusion* — a verified merge of the
child's exact tip into the composite branch.

Mandatory invariants:

1. Top-level tasks keep the sequential chain. The next starts only from the verified tip of
   the previous one.
2. A composite task has one branch. A child has no separate public pull request.
3. Each child works in an isolated worktree; the orchestrator owns ref changes, commits and
   shared files.
4. Content under `.ai/` is not written by the workers of the new mode. Context packets are
   read-only snapshots; results are messages and the worker's private artifacts.
5. Before new implementation the applicable test evidence is kept: RED for new or fixed
   behaviour, or `pinned` for pinning unchanged behaviour. A legitimate `none`/`n-a` and the
   narrow compatibility of an already started old task do not produce an invented RED. A
   merge does not delete existing history.
6. A successful child check does not prove successful integration. After the merge the actual
   combined result is checked.
7. A clean textual merge does not prove independence: a change to a shared interface can
   conflict without shared files.
8. Branches and worktrees are deleted only after proven inclusion and preservation of results;
   an inconvenient conflict does not justify deleting work.
9. A repeated message, a late result and an orchestrator restart do not create a second merge
   commit, a second pull request or an additional unaccounted repair attempt.
10. An unknown environment capability and undetermined independence are not treated as
    permission for parallelism.

**5. Normative requirements.** REQ-01–REQ-05 are kept from the original additions; the other
identifiers formalize previously unnumbered criteria.

- **REQ-01. Context and writes.** Each child receives the immutable packet of 12 and a fresh
  bounded projection without its neighbours' conversations. The orchestrator verifies and
  applies sequentially all state-change proposals from the envelopes of 13; workers do not
  publish stale confirmations.
- **REQ-02. Accounting.** Children's requests, retries, checks and cache writes are counted
  once per 05. Total waiting time is shown separately from the sum of worker time. A speedup
  is not declared a cost reduction.
- **REQ-03. History and integration.** The applicable order of tests and implementation is
  kept. Before the merge, overlaps and the child's evidence are checked; the required
  integration checks run on the actual combined tree. A failed merge or check does not create
  a verified composite task.
- **REQ-04. Risk and repairs.** 15 applies to the child and to the shared area; confirmations
  are invalidated after significant changes. Policy 17 is allowed only for an isolated
  eligible defect. A dangerous shared contract or a critical finding stops new dispatch of
  work, preserves results and moves to the existing decision procedure.
- **REQ-05. Independence and capabilities.** Evidence comes from 18 and the applicable
  classifier. Required: no file overlap, no shared mutable contract or schema, no dependency
  edge and no ordering constraint. Role and model permissions are not weakened. An
  unsupported explicit parallel request is rejected; the ordinary mode stays sequential.
- **REQ-06. Branching.** The composite branch is created from the verified tip of the
  previous top-level task; for the first, from the permitted base branch. Each child gets a
  temporary branch from the recorded tip of the composite.
- **REQ-07. Merge and preservation.** Children are included with `--no-ff`, without squashing
  commits. Test and implementation commits are kept; deletion is allowed only with
  confirmation of ownership and exact inclusion per 06.
- **REQ-08. Publication.** When publication is permitted, a composite task has exactly one
  request with one stack-position line and a section per child. Without publication
  permission only a local result is created. Automatic merging of the request is outside the
  agent's authority.
- **REQ-09. Plan description.** Decomposition records `Parallel-safe: yes | no`, exact
  files and interfaces, independence grounds and the integration order in
  `plan.md → ## Decomposition Decisions`. Uncertainty equals `no` until resolved.
- **REQ-10. Parallelism limit.** The number of simultaneously active children does not
  exceed the selected positive integer N. For N > 1 actual `worktrees: yes` and
  `concurrent-sub-agents: yes` are required; `sub-agents: yes` alone is insufficient.
- **REQ-11. Overlap recheck.** Before launch, as actual paths become known, and immediately
  before the merge, overlaps with the planned, running, completed and already included
  children of the wave are checked. A detected overlap disables further parallel execution
  of this composite task and starts safe serialization.
- **REQ-12. Single final check.** After the last child is included, the orchestrator runs
  `/phase-composite-validation` (after the command migration, `composite-validation`) on the
  shared branch. The child's closing signal does not launch a second instance of the check in
  its worktree.
- **REQ-13. Recovery.** The journal links the child, worktree, base, current tip, envelope,
  merge operation and check. After an interruption the orchestrator reconciles against the
  real repository and does not rely only on the last recorded status word.
- **REQ-14. Sequential continuation.** On an overlap: stop new dispatches, preserve active
  work and run the remaining children sequentially by fresh executors from the current shared
  base through temporary branches. Usable evidence is reused only after a currency check; an
  unconfirmed result is not mixed in automatically.
- **REQ-15. Regression and equivalence.** Offline scenarios confirm identical criteria,
  constraints and final behaviour at N = 1 and N = 2; permitted live goldens are compared
  separately per 10. Normalization allows different service identifiers but does not hide
  missing evidence.
- **REQ-16. Migration.** Rules, processes, state, constraints and documentation change
  consistently; an accepted decision record fixes the replaced provisions. Active tasks of
  the previous model are not silently moved to the new one on resume.

**6. Mode interface and preflight.** *6.1 Parameter parsing.*

| Invocation | Meaning |
|---|---|
| `/spec-run ...` | Sequential execution, N = 1 |
| `/spec-run ... --parallel` | Explicit parallel request with the default N = 2 |
| `/spec-run ... --parallel 1` | The sequential path of the new composite model |
| `/spec-run ... --parallel N` | Explicit maximum N; a positive integer |
| Zero, negative, fractional or non-numeric value | Error before any branch is created or worker launched |

A configuration limit may restrict parallelism within an already chosen mode, but must not
silently turn an absent flag into a parallel launch. If an explicit request is not supported,
an explained refusal is returned with the option of choosing the sequential mode. N > 1 must
not be silently replaced by 1 while reporting that the request was fulfilled.

*6.2 Checks before the first change.* The orchestrator checks the repository and the
permitted working directory; the absence of conflicting tracked changes; the `.ai/` knowledge
policy; readiness of the previous top-level task; the plan revision; independence; free branch
and worktree names; sufficient environment capabilities; conformance of models and effort;
publication permission when needed. The presence of a worktree mechanism does not prove the
ability to run independent sub-agents safely. The described capabilities must be confirmed by
the adapter of the installed version. The mechanism limiting the number of workers is also
checked, not derived from the model's strength. Untracked user files are preserved per the
current policy; creating a worktree gives no right to delete them for cleanliness.

**7. Independence plan.** Each child requires a record:

| Field | Content |
|---|---|
| `child_id`, `composite_id` | Canonical local identifiers |
| `target_files` | Concrete expected paths; a rename names both sides |
| `interfaces` | Produced and consumed contracts and schemas, including shared configuration |
| `dependencies` | Exact predecessors with readiness conditions |
| `parallel_safe` | `yes` or `no` |
| `independence_evidence` | Grounds for all four conditions, hash of the plan and sources |
| `integration_order` | Deterministic permitted inclusion order |
| `integration_checks` | Shared criteria, checks and owner |
| `packet_digest` | Reference to the packet of 12; the final packet is formed for the actual base |

Different source files are not enough: two children can change one schema through a generator
and a consumer, one library dependency through different modules, global configuration, or one
error contract. Such changes do not run in parallel without proven independence. The actual
path set is taken from the child's diff against the saved base, not only from the worker's
message; new and deleted files, renames, generated artifacts and dependency metadata count.
Going beyond the agreed set triggers a scope review before the merge. Children with
`parallel_safe: no` run as separate sequential steps; they cannot be inserted into an active
wave just because a slot is free.

**8. Branches, worktrees and roles.** *8.1 Names and ownership.* The composite branch name
follows the current domain format `<type>/<feature-slug>`. The temporary branch is
`<composite-branch>--<child-slug>`. Substrings `T-XX`, spec numbers and task directory names
are not added to names. A collision is resolved by a domain refinement or by verified
resumption of the run's own branch, never by accidentally using someone else's. The ownership
journal records the repository and worktree identifiers, the run, the child, the branch name,
the initial hash, the current known tip and the worktree path. A name match alone is not
enough for changing or deleting a branch.

*8.2 Worker actions.* The executor changes code and tests only in its own worktree and hands
over evidence. The orchestrator makes commits and shared writes. The validator receives the
contract, the necessary tests and the actual diff; it does not inherit the executor's
conversation as its only source of understanding.

In the new parallel mode, test preparation and implementation use distinct workflow agents.
The coordinator transfers the verified test checkpoint, test mode, commands, observed RED or
pinned result and frozen-test restrictions to the implementation agent. This supersedes the
existing same-agent RED-to-GREEN rule for this mode; implementation must record the decision
and update all affected rules. A separate validation agent independently reviews the
resulting revision. Sequential rework uses fresh agents and verified evidence.

A read-only `.ai/` or a separate context packet is not system-protected merely because an
instruction says so: the adapter documentation states separately whether the prohibition is
enforced by environment permissions or by role discipline. A worker is not given shared write
access as a convenience of the parallel mode.

**9. Execution order.** *9.1 Creating the composite task.* (1) Check all preconditions and pin
the plan revision. (2) Create one branch from the verified top-level base, or provably
restore it. (3) Record the initial tip and the branching model in the journal; create no
separate integration branch. (4) Prepare sequential steps and independent waves from the
dependency graph.

*9.2 Dispatching a child.* (1) Recheck dependency readiness and the currency of the
independence grounds. (2) Create a run-owned temporary branch and worktree from the recorded
current shared base; children of one wave usually share a base, and the concrete base is
recorded for each. (3) Form the packet of 12 with the exact base, criteria, prohibitions, test
commands, integration risks and reporting rules. (4) Reserve a leaf slot within N and a task
coordinator identity; dispatch each applicable atomic workflow to a distinct workflow agent
under section 17. (5) Receive only significant envelopes of 13; do not reread the whole state
whenever no new event arrives. (6) Determine the applicable test mode. For a new testable
function or fix, verify RED and make the test commit before implementation is allowed. For a
permitted change without behaviour change, verify `pinned`, commit the passing tests before
the change and then allow only the transition to `green`. Verify the final GREEN and make the
corresponding implementation commit. A legitimate `n-a` and an old, already started block
without `atomic-tests:` follow their separate existing paths: in the second case the exact
note about the old format is kept, but RED is not invented retroactively. Removing the field
or substituting the mode for new work is forbidden. (7) Dispatch atomic validation to a fresh
independent workflow agent. Do not admit the result for integration before validation
succeeds.

*9.3 Including a verified child.* Integration uses a deterministic dependency-compatible order
from the plan, not message arrival order. The plan must not place a dependent before its
prerequisite. Independent ready leaves may refill available slots without waiting for an
entire wave; shared writes and merges remain serialized. (1) Verify the identity of the
worktree, branch, initial base, the child's current tip, the envelope and the independent
confirmation. (2) Compare the actual changes with the plan, the wave's children and the
already included changes; also check shared interfaces and invariants. (3) Check the currency
of the packet and of the confirmation per 12/15; changed inputs require widening the check;
the same branch name or one commit hash is not enough. (4) Record the merge intent with the
expected old tip of the shared branch and the exact tip of the child. (5) Prepare the merge
without flattening history; an intermediate tree used before the commit is a separate actual
input set, not an accepted result. (6) On a conflict, preserve the state and evidence; do not
apply a forced reset, an "always ours/theirs" choice or an automatic retry. (7) On the resulting
combined tree, run the affected deterministic and independent checks per 15; the child's
checks do not replace this step. (8) Commit the merge with `--no-ff`; verify that the commit's
tree equals the checked tree; if content changed, repeat the affected check. (9) Save the
merge hash, its parents, the actual tree, the confirmations and the operation state; only then
is the result considered included. If the chosen safe mechanism creates the commit before the
integration checks, the journal distinguishes "commit created" from "inclusion accepted". A
failed check keeps the commit for recovery but assigns no verified state and permits no
dependent work.

*9.4 Completing the composite task.* After all inclusions are accepted, the orchestrator
invokes the single final integration check on the shared branch. It covers the integration
criteria of the composite description, the union of the actually changed areas, shared
invariants and boundaries. Only a successful confirmation on the current result permits
`integration-validation: complete` and moving the composite row to `reviewed`. Completed
children with a failed integration do not allow closing the composite. The call from the last
child's close becomes a readiness signal to the orchestrator, not an independent rerun inside
the child's worktree; binding the operation to the shared tip and the criteria hash prevents
duplicates.

**10. Overlap and transition to sequential execution.** A detected overlap changes the
original independence assumption; it does not permit choosing file versions automatically.
(1) Mark parallel dispatch of this composite stopped; no new children start. (2) Save the
actual paths, the shared contract and the cause; do not hide it after a successful textual
merge. (3) Send running children a safe stop at the nearest provided checkpoint; do not delete
their worktrees, branches, partial tests or reports. (4) Record all received envelopes as
pending decision; a late report is not applied automatically to the new base. (5) Separate the
results: already included and confirmed; completed but not included; active or partial; not
started. No category implies automatic acceptance. (6) Check whether the already included
result can be kept without changing the contract; on a dangerous shared defect stop further
integration and move to the existing decision procedure. (7) Build a sequential order for the
remaining children; each new or rework-requiring child gets a fresh executor and a new
run-owned branch from the current shared base. (8) A previously completed result can become
evidence and source material; accepting it without rework is permitted only if the
significant inputs match and integration is rechecked; transferring changes does not cancel
the applicable test order. (9) If the reproducing test already passes on the new base, do not
fabricate RED: refine the coverage and the remaining goal through the existing plan-change
procedure; this does not turn a new function or behaviour fix into `pinned`, which stays
permitted only for pinning preserved existing behaviour. (10) Keep earlier branches until
proven inclusion or a separate permitted decision about them; do not rewrite history to make
an interrupted wave look successful. The transition to sequence stays active until the
composite completes, unless separately agreed replanning establishes a new safe contract; it
never starts an endless "parallel — conflict — retry" cycle.

**11. State, envelopes and recovery journal.** Existing canonical statuses are kept; the
technical merge state does not replace `atomic-validation` and `integration-validation`.
Minimal additive journal data: run (`run_id`, branching-model version, repository identifier,
plan hash); composite (identifier, shared branch, top-level base, actual shared tip); child
(identifier, branch and worktree, initial hash, last tip, actual paths); context (hash of the
packet, criteria, tests and significant interfaces); parallelism (requested and actual N, wave
number, reason for sequential continuation); validation (identifiers of envelopes, independent
confirmations and open findings); inclusion (operation identifier, expected parent tips, merge
hash, actual tree, check result); cleanup (evidence of ownership and inclusion, worktree
release and absence of new work); repairs (reference to the episode and counters of 17; a
restart creates no new limit). For one merge the journal distinguishes at least the intent,
the started operation, the created commit, the verified acceptance and the completed cleanup.
These are logical journal stages, not a new task status vocabulary. A state change and a ref
update do not form one file transaction; recovery must reconcile both sides.

Two concurrently dispatched children may carry the same initial hash of shared state.
Applying the first result makes the second's source revision stale even if its own work stays
correct. The orchestrator does not rewrite the old envelope or apply its old patch: it
reconciles the current target fields, contract, tree and evidence and, if the preconditions
hold, forms a new derived proposal against the current revision with a separate `proposal_id`
and a reference `original_event_id`. The original `event_id` and its hash stay unchanged. Such
re-preparation is not a new execution, a new repair attempt or a second billable unit; history
links the original message and the single accepted change. A conflict of significant fields
requires a decision, not a mechanical transfer.

*11.1 Resumption.* If the intent is recorded and nothing changed, repeat the precondition
check before executing. If the merge was interrupted by a conflict, preserve the conflict and
do not start another merge on top of it. If the commit was created but the confirmation not
recorded, check its exact parents, tree and actual evidence; do not create a second commit
automatically. If the state is marked accepted but the shared tip or the verified inputs
changed, treat the confirmation as stale and check the affected area. If a repeated envelope
arrives, compare its identifier and content hash: an identical already applied result is not
repeated; a differing one is rejected as a conflict. If a pull request already exists, check its
repository, source and target branches and its ownership by the run, and update it within the
permission instead of creating a second one. If a worker is unknown after a restart, first
check its existence and worktree; do not launch a replacement over live work.

**12. Errors and repairs.**

| Situation | Action |
|---|---|
| A required environment capability is missing | The explicit parallel request is refused; the sequential path stays available separately |
| Independence is not proven | The child runs sequentially |
| Writes outside the target files or a change to a shared contract | Stop dispatch and inclusion, preserve the evidence, review the scope |
| The child's independent check fails | Keep the default stop; apply 17 only when the permitted policy is explicitly enabled |
| Merge conflict | Keep the branches and the conflict; do not resolve automatically or declare the inclusion successful |
| The combined result violates a criterion | The composite stays unverified; use the existing integration-issue process and fixing children |
| A critical violation of an invariant, security or the agreed architecture | Stop new dispatches and move to the provided decision; do not multiply autonomous attempts |
| An output write or accounting error | Record the uncertainty; do not repeat the change to obtain a clean output |
| A provider limit is exceeded | Keep the work and stop new calls; do not switch accounts to bypass the limit |
| A cleanup failure | Leave the branch or worktree and report the reason; a successful result requires no risky deletion |

Integration fixing children are created under the current decision protocol: in interactive
mode by the user's decision; in an already authorized autonomous mode with the provided
automatic `critical`/`important`/`optional` classification. This does not cancel the special
hard stops for violated intent, architecture or invariants. Creating a fixing child does not
mean silently launching it in the remaining parallel wave. Policy 17 keeps at most one local
and one explicitly authorized stronger attempt per episode; the attempt slot is reserved
before launch. An undetermined, already dispatched launch is not a free retry. Serialization,
a worktree change and a new executor do not reset the history.

**13. Publication and cleanup.** *13.1 One pull request.* After a successful shared check and
with `--allow-pr` in force, the shared branch is published and one request is created or
updated. Its target branch is the previous top-level branch, or the initial base for the first
task. Temporary child branches are not published separately to create requests. The content
includes the domain goal, the combined result, one stack-position line and, per child, its
goal, criteria and test evidence, including the test commit hash where required. Domain names
of children are used, not `T-XX`, spec numbers, links to `.ai/` or internal process names; the
mapping to local identifiers stays in state. The text explains the test order in plain language
without forbidden internal jargon. A draft request is not by itself a technical prohibition on
merging; the user chooses the final merge; the agent keeps the constraints of 06 and does not
run `gh pr merge`.

*13.2 Cleanup of temporary work.* Before deletion, check the exact ownership of the branch,
the match of its saved tip, its inclusion in the accepted shared history, and the absence of an
active worker and of unsaved changes. First release the worktree safely; then delete only the
provably run-owned temporary branch by a permitted method. If the branch pointer moved after
inclusion, deletion is forbidden until a new check. Without evidence the branch is kept. Forced
deletions, `reset --hard` and `clean` are never used for cleanup.

**14. Measurement and mode comparison.** The journal keeps `parallel: N` for the run and
`wave: k` for child steps, plus the actual number of active workers and the reason for reduced
parallelism. Telemetry 05 links each attempt and check to the child without duplicating it in
the composite's sum. The report shows the total elapsed time, the sum of worker durations,
orchestrator and integration time, the number of rechecks, context volumes and observed cache
reads and writes; the sum of durations is never added to the total time as another expense of
the user's time. The parallel mode can be faster and more expensive. Comparison per 10 uses the
same source tasks and independent criteria, including integration defects. Normalized
artifacts at N = 1 and N = 2 must match in semantic obligations, not necessarily in every hash
or write moment.

**15. Acceptance criteria (original).**

- AC-01 (REQ-01, REQ-02): interleaved events of two children do not mix context; shared changes
  are applied sequentially; requests are counted once; the sum of worker time does not become
  waiting time.
- AC-02 (REQ-03, REQ-04): conflicts, changed interfaces and failed checks preserve history,
  invalidate stale confirmations and do not close the composite.
- AC-03 (REQ-05): an unsupported environment, overlapping paths and a shared mutable contract
  do not launch a parallel wave. The semantic obligations of the sequential and parallel
  results match; a paid check is authorized separately.
- AC-04 (REQ-06, REQ-07): the task has one shared branch; each child has a temporary branch
  from the recorded base; the merge keeps the parent links and the applicable test commits.
  Forged ownership or a mismatched tip does not allow deleting the branch.
- AC-05 (REQ-08): without `--allow-pr` there are no pushes and no request-creation commands;
  with permission exactly one request is created; a repeat or resume creates no duplicate;
  internal identifiers do not reach public text.
- AC-06 (REQ-09, REQ-10): the plan contains evidence for every independence condition; the
  number of active children never exceeds N; an invalid N is rejected before any effect; an
  absent flag stays sequential.
- AC-07 (REQ-11, REQ-14): an unexpected overlap before or after one child finishes stops new
  dispatches; partial results are kept; the remaining children get fresh executors and
  temporary branches from the current base.
- AC-08 (REQ-12): the last child's signal triggers exactly one shared check on the composite
  branch; without a successful result on its current tree the `reviewed` status is unreachable.
- AC-09 (REQ-13): interruptions before the merge, during a conflict, after the commit and
  before the confirmation is recorded are recovered without a repeated merge, data loss or
  reset attempt counters.
- AC-10 (REQ-15): offline scenarios at N = 1 and N = 2 check identical criteria, results and
  evidence; differences of time and hashes are normalized without erasing errors.
- AC-11 (REQ-16): rules and calls never contain old and new contradictory closing methods at the
  same time; an active task of the old version does not migrate silently on resume.
- AC-12 (REQ-03, REQ-04, REQ-07): a legitimate `n-a` is kept without fictitious tests;
  `pinned → green` passes without an artificial RED; an already started old block without
  `atomic-tests:` keeps the provided note and requires no retroactive RED. For a new testable
  function or fix the mandatory order holds; a false `pinned` and removing the field to bypass
  it are rejected. A repair does not change frozen tests and does not exceed the limits of 17.

All listed scenarios have offline reproducible variants. A live `composite` golden at N = 1 and
N = 2 is needed for claims about real model behaviour, but its absence does not prevent
accepting the deterministic infrastructure separately; such claims stay unverified until
experience exists.

**16. Implementation and rollout order.** (1) Pin the current rules, plan, interfaces and
environment capabilities; record the differences between the old and new model. (2) Agree the
decision record: composite branch, temporary children, conditional publication, one writer,
single final check and the semantics of the parallelism parameter. (3) Implement the sequential
model N = 1 first, including the journal, recovery, merge and cleanup. (4) Check preservation
of test history, legitimate `pinned`/`n-a`, the narrow compatibility of the old already started
block, publication and composite closing. (5) Add independence evidence and parallel dispatch
with limit N; check mutual isolation and serialization of shared effects. (6) Add overlaps, wave
stop, fresh executors and recovery after interruption; the happy path is not sufficient. (7)
Connect telemetry and reports; update the offline projects of 10 and shared documentation. (8)
Roll out for new or explicitly migrated tasks. When parallelism is disabled, keep the new
branching guarantees and the history of an already started composite; do not return it
automatically to the old chain of separate requests. Readiness means fulfilled offline criteria
and described recovery. It does not mean permitted publication, a parallel mode enabled by
default or measured financial benefit.

### Original section 17 (English, unchanged)

**17. Parallel atomic workflows across the task tree**

*17.1. Source and scope.* The owner clarified on 2026-11-06 (translated from Russian): execute
eligible atomic subtasks of one large task in parallel to shorten implementation time; give
each atomic subtask its own coordinating agent and each atomic workflow a separate agent.
Analysis and test preparation, implementation, and validation are examples of distinct
workflows. The [example task](../tasks/completed/task-06-1-test-suite-runtime/plan.md) is
planning evidence, not authorization to change or run it.

The current runner explicitly executes subtasks sequentially and uses one implementer for
test and implementation checkpoints ([dependency ordering](../../workflows/spec-run.md#L163),
[handoff](../../workflows/spec-run.md#L208), [parallelism prohibition](../../workflows/spec-run.md#L367)).
Atomic execution orders test preparation, implementation and finalization
([execution](../../workflows/phase-atomic-execution.md#L100)); atomic validation orders check,
proposals and close ([validation](../../workflows/phase-atomic-validation.md#L73)). This
section defines a future replacement for those runner rules, not current behavior.

*17.2. Scheduler and ownership requirements.*

- **REQ-17. Task tree.** WHEN an authorized parallel run processes a large task, THE SYSTEM SHALL build one dependency graph of its atomic leaves, including descendants of composite nodes and leaves directly under the task. Composite nodes remain containers and integration gates, not atomic implementation jobs. Independent top-level task runs remain sequential.
- **REQ-18. Admission.** WHEN a leaf is considered for dispatch, THE SYSTEM SHALL admit it only after every declared prerequisite is integrated and reviewed, enclosing gates and other applicable prerequisites permit execution, and its file, interface and resource independence from every active leaf is established. A composite prerequisite is satisfied only after its children and composite integration validation pass.
- **REQ-19. File exclusion.** WHILE a leaf holds its write reservation, THE SYSTEM SHALL prevent another active leaf from writing any of the same normalized repository paths, including test, configuration, generated, deleted and both sides of renamed files. A directory or glob that cannot be resolved to a complete stable set is an overlapping reservation. Distinct worktrees do not waive this exclusion; root-owned shared-state updates remain sequential under REQ-01.
- **REQ-20. Leaf coordination.** WHEN an eligible leaf starts, THE SYSTEM SHALL assign it a dedicated task-coordinator sub-agent that owns its atomic execution and validation sequence and reports to the root orchestrator; it shall not coordinate another leaf concurrently. The root remains the sole writer of shared state and owner of git operations.
- **REQ-21. Workflow agent isolation.** WHEN an applicable atomic workflow is invoked for a leaf, THE SYSTEM SHALL dispatch it to a fresh workflow sub-agent dedicated to that invocation. Atomic execution (/phase-atomic-execution), test analysis/preparation (/pae-tests), implementation (/pae-implement), finalization (/pae-finalize), atomic validation (/phase-atomic-validation), and its applicable child workflows (/pav-check, /pav-propose and /pav-close) each have a distinct fresh agent identity, also distinct from the leaf coordinator and root. Phase agents coordinate their ordered child workflow invocations; the root mediates dispatch if necessary. Finalization and close propose state deltas for the root; neither workflow workers nor leaf coordinators directly write shared .ai/ state or perform root-owned git operations.
- **REQ-22. Verified handoff.** WHEN a workflow completes, THE SYSTEM SHALL pass the next workflow an immutable, minimally scoped handoff containing leaf and attempt identities, base and exact candidate tree/commit, task contract and applicable acceptance criteria, allowed paths, test mode, commands, observed results and artifact digests. The implementation agent receives verified frozen RED or pinned evidence before implementation; the validation agent receives implementation and test evidence independently. A failed, missing, stale or mismatched handoff blocks its dependent stage.
- **REQ-23. Limits and refill.** WHILE parallel mode is active, THE SYSTEM SHALL cap active leaves at N, separately count task coordinators and workflow agents against actual platform agent capacity, and dispatch another ready independent leaf when a slot and all required locks are available. A leaf retains its slot and reservations through atomic validation and until its result is integrated or safely withdrawn. Record requested and effective limits and capacity constraints.
- **REQ-24. Failure isolation.** IF a leaf fails or is blocked, THEN THE SYSTEM SHALL block its descendants and dependent joins, retain its work and evidence, and allow unrelated eligible leaves to continue when no shared safety invariant, resource lock or critical defect requires a broader stop. Existing conflict handling in section 10 applies when asserted independence is disproved.
- **REQ-25. Capability preflight.** BEFORE creating branches or dispatching in this mode, THE SYSTEM SHALL verify worktree isolation, concurrent sub-agents, agent messaging, and the ability to run dedicated coordinators and distinct workflow agents under available delegation permissions. If nested delegation is unavailable, root-mediated flat dispatch is permitted only if it preserves the same identities, sequence, handoffs and ownership; otherwise reject the explicit parallel request with the missing capability and perform no partial dispatch.
- **REQ-26. Completion and measurement.** WHEN all leaves and composite gates complete, THE SYSTEM SHALL verify the integrated task result against the parent contract on the final tree, record the verdict, and report wall time, active-leaf concurrency, worker time, integration/rework time and conflicts separately. Compare sequential and parallel runs only on comparable inputs and quality gates; measured acceleration is evidence, not an unconditional acceptance guarantee.
- **REQ-27. Recovery.** WHEN a run resumes, THE SYSTEM SHALL reconcile each leaf coordinator, workflow invocation, attempt, reservation, candidate tree, handoff, dependency and integration receipt against actual live agents and repository state before redispatch. Never duplicate a live invocation, release a reservation held by a live writer, reuse a stale validation, or lose partial work.

*17.3. Execution and integration contract.* The root expands the task tree into a DAG,
preserves composite joins, checks the versioned plan and reserves file and resource ownership
before dispatch. A ready leaf gets its own isolated branch and worktree, a coordinator, and a
bounded sequence of workflow agents. The coordinator directs phase sequence and returns
evidence; it does not mutate shared state or git. The root may mediate workflow-agent creation
when nested spawning is unavailable. An active leaf runs from reservation through integrated
acceptance or safe withdrawal; N limits leaves, not the total number of agents. Platform
capacity includes the root, coordinators and active workflow agents; report any smaller
effective concurrency.

For testable new behavior, a test agent produces RED evidence; the root verifies and commits
the test checkpoint; a fresh implementation agent receives that checkpoint and produces GREEN;
the root verifies and commits implementation. For permitted characterization, transfer pinned
evidence instead. Documented n-a and legacy in-progress paths remain applicable without
invented RED evidence. A fresh atomic-execution phase agent coordinates test preparation,
implementation and execution finalization, each dispatched to a distinct agent. After
execution finalization, a fresh independent validation phase agent coordinates its ordered
check, proposal and close workflows, each dispatched to a distinct agent when applicable. The
root applies validated state proposals in order. No stage starts until its predecessor has
successfully handed off. Validation failure cannot close the leaf.

A leaf branches from an integrated tree containing all reviewed prerequisites. For nested
composites, the root integrates leaves into their owning composite branch in deterministic
dependency-compatible order and runs that composite single integration gate before integrating
its branch into its parent. Direct leaves integrate into the parent task branch. The parent
final verification is separate from each composite gate. Cross-boundary leaves may run
together only when dependencies and ownership permit it; no dependent leaf starts on an
unintegrated candidate. A dependency outside the owning composite becomes usable only after
its verified result is integrated into an ancestor branch and the owning composite branch
incorporates that exact verified ancestor revision. If the prerequisite is inside another
composite, first complete and integrate that composite gate; do not copy unintegrated leaf
changes across branches. Revalidate affected evidence after incorporating ancestor changes.
Existing no-fast-forward history, single-writer, recovery, publication and conflict rules
remain in force.

If a worker requests or is observed to change a path outside its reservation, stop its writes
and new admissions involving the affected set; preserve candidate trees and compare actual
paths before integration. If overlap or a common-contract conflict invalidates independence,
apply section 10 conservative stop and serialization for the affected task scope. Release a
path only after integration or confirmed worker termination and preservation of its work.
Read-only analysis does not acquire a write reservation and cannot be treated as completed
implementation. Host-exclusive checks, benchmarks and resource locks are separate from file
reservations and apply globally.

*17.4. Example and assumptions.* The example plan identifies the baseline as a prerequisite and
final integration and performance work as joins. It lists four candidate lanes after the
baseline, but the guard, identity, timing and lifecycle leaf descriptions all name
scripts/validate-contracts.sh as a target. These leaves therefore cannot hold concurrent write
reservations under REQ-19, even in separate worktrees. A revised plan may permit concurrency
only after establishing complete, disjoint actual write sets and independent interfaces;
otherwise they run sequentially. This example does not claim that the current task has four
parallel-writable leaves.

Assumptions: the existing explicit --parallel opt-in and N=2 default remain unchanged; the
requested parallelism is inside one task. The coordinator and fresh-workflow-agent model
applies to the new mode and requires a capability-aware adapter. No migration of an active
task is implied. The present same-agent test handoff must be replaced for this mode while
retaining frozen-test guarantees.

*17.5. Additional acceptance criteria.*

- [ ] **AC-13** (REQ-17, REQ-18, REQ-23): Given four ready leaves with pairwise disjoint complete write sets, independent contracts and sufficient capacity, when parallel mode runs with N=4, four dedicated leaf coordinators are active concurrently. A fifth leaf waits; when a slot is safely released, an eligible waiting leaf starts without waiting for an unrelated wave. Dependencies and composite join gates are never bypassed.
- [ ] **AC-14** (REQ-19, REQ-23): Given two ready leaves targeting the same normalized file, including a rename destination or generated output, when N exceeds one, their write intervals do not overlap even across worktrees. Unknown or overlapping directory reservations also prevent concurrent admission.
- [ ] **AC-15** (REQ-20, REQ-21, REQ-22): Given a testable leaf, when its atomic workflows run, its coordinator, execution phase, test, implementation, finalization, validation phase and applicable validation child agents all have distinct identities; RED is verified and committed before the implementation agent starts, GREEN precedes validation, and handoff identities and digests are recorded. Shared state and git changes occur only through the root. Missing or stale handoff evidence blocks the next stage.
- [ ] **AC-16** (REQ-17, REQ-18, REQ-24): Given independent leaves in different composites and a failed leaf with a dependent, when scheduling continues, the unrelated eligible leaf can complete; the failed leaf dependent and its composite join cannot start or close. A critical shared invariant failure invokes the broader stop.
- [ ] **AC-17** (REQ-25, REQ-27): Given unavailable nested delegation, root-mediated dispatch preserves required identities and order when supported; otherwise preflight rejects the request before mutation. After interruption, a live workflow is not redispatched and its write reservation remains held until safe reconciliation.
- [ ] **AC-18** (REQ-18, REQ-19, REQ-26): Given the example guard, identity, timing and lifecycle leaves with the same target file, when their dependency is satisfied, the scheduler never admits them as concurrent writers. The final report separates elapsed time, aggregate worker time, integration/rework and actual concurrency; no speedup is claimed without comparable measurements.
- [ ] **AC-19** (REQ-18, REQ-21, REQ-22, REQ-26): Given nested composites and direct leaves, when all atomic validations and composite joins pass, each composite gate runs once on its integrated tree and the final parent contract is checked on the final integrated tree. Failed or stale validation prevents completion.

The new requirements map to AC-13–AC-19 above. Add deterministic scheduler,
isolated-worktree, workflow-identity, handoff, failure, recovery and integration fixtures
before implementation; retain existing N=1/N=2 equivalence scenarios. No paid benchmark is
required for deterministic acceptance.

## Migration

> Superseded on 2026-11-24. [Spec 26](26-shared-parallel-execution.md) is the sole delivery contract for parallel subtask execution. The source and historical quotations below carry no implementation obligations.

On 2026-11-14 the owner deferred cross-composite and top-level concurrency and assigned review-record publication in parallel mode to the orchestrator. Both decisions are carried into spec 26.

The prior normative body and review history are preserved at Git revision `4aaf005cf293cd236510cd368b8684d4e1d48322` at this path. Spec 22 owns sequential composite branches. Spec 26 owns parallel scheduling, worktrees, worker dispatch, checks and integration, with a single execution route shared by both entry points.

- REQ-01 → [REQ-04](26-shared-parallel-execution.md#requirements)
- REQ-02 → [REQ-102](26-shared-parallel-execution.md#requirements)
- REQ-04 → [REQ-104](26-shared-parallel-execution.md#requirements)
- REQ-05 → [REQ-02](26-shared-parallel-execution.md#requirements)
- REQ-09 → [REQ-109](26-shared-parallel-execution.md#requirements)
- REQ-10 → [REQ-02](26-shared-parallel-execution.md#requirements)
- REQ-11 → [REQ-02](26-shared-parallel-execution.md#requirements)
- REQ-14 → [REQ-05](26-shared-parallel-execution.md#requirements)
- REQ-15 → [REQ-115](26-shared-parallel-execution.md#requirements)
- REQ-17 → [REQ-02](26-shared-parallel-execution.md#requirements)
- REQ-18 → [REQ-02](26-shared-parallel-execution.md#requirements)
- REQ-19 → [REQ-02](26-shared-parallel-execution.md#requirements)
- REQ-20 → [REQ-120](26-shared-parallel-execution.md#requirements)
- REQ-21 → [REQ-121](26-shared-parallel-execution.md#requirements)
- REQ-22 → [REQ-122](26-shared-parallel-execution.md#requirements)
- REQ-23 → [REQ-02](26-shared-parallel-execution.md#requirements)
- REQ-24 → [REQ-05](26-shared-parallel-execution.md#requirements)
- REQ-25 → [REQ-125](26-shared-parallel-execution.md#requirements)
- REQ-26 → [REQ-126](26-shared-parallel-execution.md#requirements)
- REQ-27 → [REQ-127](26-shared-parallel-execution.md#requirements)
- REQ-28 → [REQ-128](26-shared-parallel-execution.md#requirements)
- REQ-29 → [REQ-12](26-shared-parallel-execution.md#requirements)
- REQ-38 → [REQ-13](26-shared-parallel-execution.md#requirements)
- REQ-48 → [REQ-12](26-shared-parallel-execution.md#requirements)
- REQ-49 → [REQ-149](26-shared-parallel-execution.md#requirements)
- REQ-52 → [REQ-152](26-shared-parallel-execution.md#requirements)
- REQ-55 → [REQ-155](26-shared-parallel-execution.md#requirements)
- REQ-56 → [REQ-156](26-shared-parallel-execution.md#requirements)
- REQ-57 → [REQ-03](26-shared-parallel-execution.md#requirements)
- REQ-58 → [REQ-158](26-shared-parallel-execution.md#requirements)
- REQ-59 → [REQ-09](26-shared-parallel-execution.md#requirements)
- REQ-60 → [REQ-06](26-shared-parallel-execution.md#requirements)
- REQ-61 → [REQ-161](26-shared-parallel-execution.md#requirements)
- REQ-62 → [REQ-162](26-shared-parallel-execution.md#requirements)
- REQ-63 → [REQ-163](26-shared-parallel-execution.md#requirements)
- REQ-68 → [REQ-04](26-shared-parallel-execution.md#requirements)
- REQ-69 → [REQ-169](26-shared-parallel-execution.md#requirements)
- REQ-70 → [REQ-170](26-shared-parallel-execution.md#requirements)
- REQ-71 → [REQ-171](26-shared-parallel-execution.md#requirements)
- REQ-72 → [REQ-172](26-shared-parallel-execution.md#requirements)
