# Shared parallel execution

## Source

Owner request in the Codex conversation, 2026-11-24, translated from Russian: “Analyze spec-run and design parallel subtask execution during phase-execution. Design changes to spec-run and phase-execution so they can run eligible subtasks concurrently. Address simultaneous edits to the same file through separate workspaces and GitHub-style conflict resolution. Write the specification in .ai/specs, then run spec-draft --auto-mode.”

Design input: [Parallel subtask execution design](../../docs/analysis/2026-11-24-parallel-phase-execution.md).

## Context & Problem

The full-tier phase delegates to a serial leaf loop and finalizes after that loop succeeds (`workflows/phase-execution.md:82-97`, `workflows/pe-execute.md:29-38`). Spec-run has a separate stack loop with pinned branch bases and optional PR publication (`workflows/spec-run.md:264-284`, `:388-399`) and forbids concurrency (`workflows/spec-run.md:470-482`). Spec 22 defines the sequential composite branch foundation. The former spec 23 design required disjoint paths and retried conflicted attempts. Those proposals were undelivered at review baseline `4aaf005` and are revised here. ADR-0009 Decision 4 restricts parallelism to one composite and to spec-run (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:143-160`).

## Goal

Run independent children of one composite concurrently from either execution entry point and combine compatible same-file changes in isolated Git worktrees while retaining sequential integration, verified TDD evidence and caller-specific delivery rules.

## Scope

One shared composite scheduler and integration loop, full-tier entry points, per-child worktrees, explicit compatible path overlap, source-side conflict resolution, check gates, and interrupted-run recovery. This specification consolidates the undelivered parallel execution design previously assigned to spec 23. It builds on the sequential composite branch model in spec 22.

## Out of Scope

Concurrent top-level stack entries, separate composites or repositories, quick-tier parallelism, running integration checks concurrently against the same target, browser or GitHub conflict APIs, automatic PR merging, new model policy, and new latency targets.

## Actors & Roles

- Orchestrator owns Git writes, admission, journal transitions and shared project records.
- Worker edits product files only in the assigned child worktree and returns checkpoint reports and deltas. The independent validator reviews the pinned candidate.
- Resolver proposes an edit within the authorized conflict scope. The orchestrator classifies the resolution under existing ambiguity rules and commits accepted edits.
- Owner decides incompatible intent, scope or requirement changes and retains all Git rail approvals.

## Terminology

A composite is the parent of multiple atomic leaves. A child attempt is one isolated execution of a leaf under the composite journal. The target is the composite branch. The candidate is the child branch being considered for integration. A compatible overlap is an explicitly reviewed file path that two sibling attempts may edit within their independent contracts. A resolution is a candidate-side merge of the pinned target followed by fresh review. The expected target SHA is the pre-integration tip, the proposal SHA is the verified merge, and the delivery tip may also contain later bookkeeping commits.

## Requirements

- **REQ-01** WHERE full-tier parallel execution is selected, THE SYSTEM SHALL route both callers through one composite execution engine.
- **REQ-02** WHEN the engine admits a child, THE SYSTEM SHALL apply the dependency, resource, path and capacity conditions in Contracts & Interfaces. The effective limit is 1 while serialized and otherwise is the requested limit capped by observed spawn capacity. Lowering the limit does not terminate existing attempts.
- **REQ-03** WHILE an attempt is active, THE SYSTEM SHALL isolate its product edits to its assigned Git worktree.
- **REQ-04** WHILE parallel execution is active, THE SYSTEM SHALL serialize parent record and target-ref writes through one orchestrator.
- **REQ-05** WHEN validated attempts await integration, THE SYSTEM SHALL integrate them in the composite's pinned topological order.
- **REQ-06** WHEN integration reports a conflict on a compatible overlap, THE SYSTEM SHALL prepare source-side resolution against the pinned target in the candidate worktree.
- **REQ-07** IF a proposed or completed resolution requires a class-B decision or exceeds its authorized resolution scope, THEN THE SYSTEM SHALL pause integration and report the evidence and required decision.
- **REQ-08** WHEN a candidate head changes during target synchronization, THE SYSTEM SHALL obtain fresh acceptance of that exact head under the validation contract.
- **REQ-09** WHEN considering a candidate merge result, THE SYSTEM SHALL mark it accepted only after the composite checks pass on the exact proposed merge commit and the target update succeeds.
- **REQ-10** WHEN an interrupted run resumes, THE SYSTEM SHALL reconcile the journal and Git evidence before dispatch, merge or cleanup.
- **REQ-11** WHEN the shared loop completes, THE SYSTEM SHALL return the integrated head and outcome to the caller for its normal delivery actions.
- **REQ-12** IF explicit concurrency cannot be used safely, THEN THE SYSTEM SHALL report the blocking preflight or admission reason under the specified fallback rules.
- **REQ-13** WHEN a spec-run parallel dry run is requested, THE SYSTEM SHALL report the planned admission and delivery route without mutation.

### Worker lifecycle and supporting requirements

- **REQ-102 Attribution.** WHEN a child attempt reaches an end stage (`accepted`, `failed`,
  `blocked`, `check-failed`, `conflict` or `superseded`) for the first time, THE SYSTEM [root]
  SHALL write exactly one synthetic per-subtask run-log aggregate for that attempt through the
  existing helper path (`workflows/spec-run.md:45-47`), so concurrent attempts never share or
  duplicate an aggregate.
- **REQ-169 Packet location (split from 22 REQ-53).** WHERE spec 12's `packet` command is
  delivered, WHEN the root builds a packet for an agent of an attempt that has a worktree, THE
  SYSTEM [root] SHALL set `--work` to that worktree instead of the root worktree.
- **REQ-128 Worker context.** WHEN the root dispatches any agent for a child, THE SYSTEM [root]
  SHALL give it only that child's description path, its handoff, its worktree path (parallel
  mode), the absolute path of the root worktree's `.ai/` directory as read-only context and,
  under spec 22 REQ-53, its context packet, and never another child's transcript, report or handoff.
- **REQ-158 Worktree removal (split from 22 REQ-31).** WHEN an `accepted` attempt with a
  worktree and a null `cleanup.failure` is cleaned up, THE SYSTEM [root] SHALL run `git worktree
  remove <path>` (never `--force`) as its own Bash call before spec 22 REQ-31's branch deletion,
  and on any failure, hook ask or hook deny keep the worktree and the branch, record the reason
  in `cleanup.failure`, never retry or rephrase it in this or a later run, and continue.
- **REQ-170 Superseded attempts.** WHEN a composite completes, THE SYSTEM [root] SHALL, for each
  `superseded` attempt, run `git worktree remove <path>` (never `--force`) when the attempt has
  a worktree with no tracked change and no untracked, non-ignored path, keep its branch, and
  report the branch and any kept worktree in Step 8; spec 22 REQ-47 deletes the journal only
  when no superseded attempt still has a worktree.
- **REQ-161 Handoff retention (split from 22 REQ-47).** WHEN spec 22 REQ-47 deletes a task's
  composite journal, THE SYSTEM [root] SHALL delete the task's handoff directory (DM-6) in the
  same step; otherwise it keeps it.
- **REQ-125 Capability preflight.** On either entry point, apply the capability, helper and runbook checks before mutation. For explicit N > 1 require current evidence for `sub-agents`, `agent-messaging`, `git`, `worktrees` and `concurrent-sub-agents` per spec 09 DM-4 and REQ-37, Python 3.11+, a compatible composite helper at the verified source root and a concrete runbook `test:` command. Recheck resume prerequisites for recorded worktrees. A reduced limit cannot bypass those prerequisites.
- **REQ-149 Worktree probe.** Before dispatch, run the runbook test command in the child worktree and in a disposable baseline worktree at the same attempt base. If exit codes differ or a probe leaves new tracked or non-ignored untracked changes, preserve affected worktrees and serialize with reason `worktree-probe`. Never switch the root checkout to probe an older base.
- **REQ-109 Independence record.** WHEN `/pd-decompose` writes a plan containing a composite,
  THE SYSTEM [`/pd-decompose`] SHALL render one `### Parallel Safety` row per child (DM-5) from
  that child's spec 18 DM-8 object, with `Parallel-safe: no` whenever DM-8 `disqualifiers` is
  non-empty, the write set is not a complete explicit file list, the child needs an exclusive
  resource, an `## Execution Strategy` ordering constraint names it (under spec 18 REQ-13 and
  REQ-135 such ordering is a `Depends On` edge, so this clause matters only for older plans), or
  any independence condition is unproven.
- **REQ-152 Design reconciliation.** WHEN `/pd-design` finishes on a plan containing a composite,
  THE SYSTEM [`/pd-design`] SHALL re-render every `### Parallel Safety` row from the child's
  current spec 18 DM-8 object (whose interface contracts `/pd-design` has just resolved) and
  apply REQ-109's `Parallel-safe` rule again, changing no row of a child that has started in
  the sense of spec 18 REQ-24.
- **REQ-104 Broad stop.** IF a critical finding, an Invariant or Off-limits violation, a
  class-B question, a composite-promotion tripwire or any other condition of
  `rules/orchestration.md:180-187` occurs during a parallel run — except `atomic-tests: failed`
  and a worker blocker of one child, which follow the ordered blocker stop (spec 22 DM-3 `tests-failed`, `blocker`) —
  THEN THE SYSTEM [root] SHALL
  admit no new child anywhere, send every active coordinator a stop, record each
  acknowledgement with the last verified checkpoint, preserve all branches and worktrees, and
  stop the run. A worker already dispatched, a spec 22 REQ-54 repair worker included, is not
  interrupted: its running agent finishes (C-6 row 8), no further attempt, repair attempt or
  validation recheck starts, its result is recorded through spec 17's `outcome` step and an
  open episode stays open (17 C-10 row 23), and the attempt keeps the journal stage it had at
  the stop for the resume (REQ-127).
- **REQ-163 Repair in a parallel run (split from 22 REQ-54).** WHILE the effective limit is above
  1, WHERE spec 17's repair policy is active for the run, WHEN spec 22 REQ-54 repairs a child,
  THE SYSTEM [root] SHALL run the repair instead of the ordered blocker stop and keep the attempt's
  concurrency slot and reservation; after an accepted
  repair apply the current admission-scope and integration rules; start no further
  repair attempt or recheck on a REQ-104 broad stop while letting a repair worker already
  dispatched finish, as REQ-104 states; copy the episode key into the next attempt's
  `repair_episode` when serialization supersedes an attempt with an open episode (17 C-10: an episode
  survives serialization, worktree change and new workers); apply the ordered blocker stop when a repair
  loop ends without acceptance (without the active policy, use the same ordered blocker stop); and run the `/pae-repair` invocation as one workflow invocation:
  the root spawns one fresh agent for it (REQ-121), the agent returns its leaf-block writes as
  deltas (REQ-04), the root commits 17's checkpoints and builds a DM-6 handoff with stage
  `repair`, and the coordinator then requests a fresh validation phase (C-6 rows 6 and 10).
- **REQ-155 Review records.** WHERE spec 15's `record` command is available (15 C-1), WHILE
  N > 1, WHEN a review agent of the run returns its final report (the `/pav-check` workflow
  agent of a child attempt, REQ-121, the Validator of a child of a serialized composite, which uses
  the effective-limit-1 model and has no coordinator or phase agent, or the composite validation
  agent, spec 22 REQ-12), THE SYSTEM [root]
  SHALL be the only invoker of `record`: the agent runs `prepare` and `run` but never `record`,
  never writes under `<task>/verification/` and returns its review draft in the report's
  `review` object (C-6 row 11). The root SHALL write the returned DM-7 draft object of spec 15
  to `<task>/verification/drafts/<scope key>-attempt-<k>.json` of the root worktree's task
  directory, and run `record --draft` on it with the options the agent passed to `prepare`, only
  after confirming that `--work` names the attempt's location and `--task` and `--ai-dir` name
  the root worktree's task directory and `.ai/`, before it applies any other delta of that
  report and before the root's checkpoint commit or the next dispatch for the attempt. When
  `record` publishes, the root SHALL apply the report's verdict and notes deltas and then append,
  as the last entry, the 15 DM-8 entry `verification: review <scope key> <step> #<seq> <scope>
  sha256:<file hex>` built from the `record` result (`seq`, `file_sha256`); an agent never writes
  that entry. WHEN the report carries `draft: null` with a `none_reason`, THE SYSTEM [root]
  SHALL append the DM-8 entry `verification: review <scope key> <step> none — <reason>` instead
  and write no record. At N = 1 this requirement does not apply: the Validator runs `record`
  itself as 15 C-4 states.
- **REQ-156 Refused or unusable review draft.** WHERE REQ-155 applies, IF the `review` object is missing, is not JSON of the C-6 row 11 form, or
  names a different `--work`, `--task` or `--ai-dir` (an unusable draft), or `record` exits 1
  (refused), THEN THE SYSTEM [root] SHALL write no record and apply none of that report's
  verdict, `verification:` entry or other review deltas, and SHALL spawn the same review role
  once more as a fresh agent whose message carries the refusal `reasons` (the correction, spec
  15's `Record:` rule), replying to a requesting phase agent per C-6 row 12; IF the correction's
  draft is also unusable or refused, or `record` exits 2, 3 or 4, THEN the root SHALL spawn the
  review role one further time with `"helper": "off"`, whose full review without the helper
  returns `draft: null` with `none_reason: helper-error` (15 DM-8), and when that agent also
  returns no usable report the attempt is `blocked` with reason `record-failed` (REQ-05); for
  the spec 22 REQ-12 composite validation agent, which has no attempt, the root writes
  `blocker: record-failed: <one-line detail>` in the composite block and stops the run.
- **REQ-162 Owner-cleared resume with a worktree (split from 22 REQ-50).** WHEN spec 22 REQ-50
  restarts an attempt that has a worktree, THE SYSTEM [root] SHALL restart it in that worktree,
  count it as active and use the restart mapping in DM-7 after verified reconciliation.
- **REQ-120 Leaf coordinator.** WHEN a child attempt is admitted with an effective limit above 1
  (N > 1 and its composite not serialized), THE SYSTEM [root]
  SHALL spawn one fresh leaf coordinator for that attempt only, record its agent identity in
  the journal, and exchange the C-6 messages with it.
- **REQ-121 Workflow agents.** WHEN a phase or workflow agent of a child attempt admitted under
  REQ-120
  requests an invocation (C-6), THE SYSTEM [root] SHALL spawn a fresh agent for that single
  invocation whose identity differs from every other agent of the run and record the identity
  in the journal; the sequence is `/phase-atomic-execution` (requesting `/pae-tests`,
  `/pae-implement`, `/pae-finalize`) then `/phase-atomic-validation` (requesting `/pav-check`,
  `/pav-propose --batch`, `/pav-close`).
- **REQ-122 Verified handoff.** WHEN a workflow agent of a child returns, THE SYSTEM [root] SHALL
  commit the checkpoint its report represents (if any) in the attempt's worktree in the commit
  sequence of spec 22 REQ-41 (`test:` before the implementation commit for `red` and `pinned`,
  one commit for `n-a`, the legacy note unchanged), build the handoff (DM-6) from that
  report and the worktree, record its digest in the journal, run C-9 `check-handoff` on it
  immediately before dispatching the next workflow, and dispatch the next workflow with only that
  handoff when the verdict is `ok`; a missing report (`blocker`), a `stale` verdict or a report whose test files differ from the
  frozen set (`handoff-stale`) blocks the next workflow and sets the child `blocked` with that
  reason.
- **REQ-171 Spawn refusal.** IF the harness refuses to spawn an agent for a child attempt, THEN
  THE SYSTEM [root] SHALL keep the attempt `branched` with `spawn_refused: true`, record the
  composite's `capacity_limit` as the number of its other active children (DM-7), retry the
  spawn when `admit` lists the attempt in `respawn` after an attempt leaves the active stages
  (clearing `capacity_limit`), and, when no other child of the composite is active, set the attempt `blocked` with
  `blocker` and write `blocker: blocker: spawn refused by the harness`, then stop the run under
  the ordered blocker stop instead of recording a limit (spec 22's `blocker` resume row applies).
- **REQ-172 Unwritable worktree.** IF a workflow agent's report carries `"worktree_unwritable":
  true` (its edit tool refused a path inside the attempt's worktree), THEN THE SYSTEM [root]
  SHALL set the attempt `blocked` with `worktree-not-writable` and serialize the composite with
  reason `worktree-probe` (REQ-05).
- **REQ-127 Agent recovery.** WHEN a parallel run resumes, THE SYSTEM [root] SHALL, for every
  attempt in stage `dispatched`, send its recorded coordinator and every recorded workflow agent
  not reported finished a status message and classify each outcome as `live` (the coordinator answers with its current stage), `gone` (the harness reports
  the agent identity unknown or finished) or `unknown` (any other outcome); it redispatches only
  a `gone` attempt whose `reconcile` action is `none`, from its last verified checkpoint; an attempt is `live` when any of its agents is `live`; for a
  `live` attempt it sends the C-6 stop (row 8) and waits for `stopped` for at most one further
  status round, then treats the attempt as `gone`, or as `unknown` when an agent is still live; and it sets an `unknown` attempt, or a `gone` one with `inspect-worker`, `blocked` with
  reason `liveness-unknown` or `uncommitted-work`.
- **REQ-126 Run measurement.** WHEN a parallel-enabled run with a composite ends, THE SYSTEM [root] SHALL report,
  per composite, the requested N, serialization events with reasons, and the output of C-9
  `measure`, printing `not measured` for each null value and claiming no speedup.
- **REQ-115 Equivalence.** WHERE an owner-approved spec 10 `composite` golden run exists for
  both `--parallel 1` and `--parallel 2`, THE SYSTEM [`scripts/check-composite-run.py`; spec 10
  defines no comparison between two runs' projections] SHALL compare the common required outcomes in their normalized structural assertions. Each route must satisfy its own ancestry and ordering assertions. Treat a difference in required outcomes after aliasing hashes, branch names and timestamps as a defect.

## Data Model

Reuse the spec 22 composite journal, its repository, composite and attempt keys, and extend it with the worktree and handoff records below:

| Record | Fields and authority |
|---|---|
| Parallel Safety row | Optional `compatible_overlap` list of peer leaf ID, exact repository-relative path and Discovery rationale. Both rows must name the same path and each other. Omission means an empty list. Discovery owns it and rechecks it after design. |
| Attempt integration record | Target ref, expected target head, original validated candidate head, current candidate head, optional sorted conflict paths and resolution head, optional proposed integration commit and tree, review/check receipts tied to commit and tree, and state. Git object identities are full hashes in the repository's object format. |
| Check receipt | Kind (`atomic-review`, `test-command`, `manual-acceptance`, or `composite-command`), full commit and tree SHAs, command or recorded check identifier, verdict and worker/runner provenance. The orchestrator records receipts from observed outcomes and matches the expected check and pinned identities at every acceptance boundary. |
| Composite integration order | Revision 2 stores the pinned topological child-ID list and the accepted prefix length. The writer verifies the prefix against acceptance records and updates the suffix only at a quiescent planning boundary. |
| Integration state | `intent` → `resolving` or `proposed` → `accepted`; `blocked` preserves the last durable boundary and reason for retry. Acceptance requires durable target and parent-report reconciliation. |
| Ownership | One exclusive run writer per Git common directory while the engine is active. Lock is released on process termination. The journal persists through interruption and uses the existing durable write and reconciliation contract. |

The spec 22 DM-3 journal uses integer `schema_version: 1`. Revision 2 adds a required integration record to extended attempts once integration starts. Before that boundary the field is absent. Upgraded readers support both revisions, reconcile active revision 1 attempts under their legacy procedure, and migrate under the writer lock only when no revision 1 attempt is in flight. Historical attempt records can omit the field. Revision 1 readers must refuse revision 2. Never down-convert an active journal.

| Durable boundary | Required evidence and recovery |
|---|---|
| `intent` | Target ref, expected target SHA and both candidate SHA fields. Record before the trial merge. Trial worktree identity is recorded before creation. Recreate an absent trial only with matching heads. |
| `resolving` | Intent and nonempty conflict paths. An in-progress merge must have the expected original candidate and target as HEAD and MERGE_HEAD. A completed resolution must have those parents and permitted edits. Record the resolution head when verified. |
| `proposed` | Intent plus exact proposal HEAD and tree, and candidate receipts. Preserve the commit by keeping the registered detached worktree at that HEAD until reconciliation. Persist passing composite check receipts before updating the target. |
| `accepted` | The target is at the verified proposal or at a recorded bookkeeping descendant and parent state contains the matching acceptance. Reuse the proposal SHA as the idempotency key. |
| `blocked` | Last durable boundary, reason and diagnostic evidence. Resume only by its recorded decision or retry route. |

### DM-4 Worktree location (new)

`<git-common-dir>/orchestrail-worktrees/<task-key>/<child-branch with "/" replaced by "-">`.
Inside the common directory the worktree is invisible to the root worktree's `git status` and is
under the registered project root, so the git-rails hook governs commands run there (the
registry matches by directory prefix, `hooks/git_rails.py:330`) (verified
with git 2.53.0 in a disposable repository on 2026-11-13: `git worktree add` there succeeded,
the root status stayed clean, and git refused `branch -d` while the worktree existed). Tools
that skip `.git` path segments, missing untracked dependencies and edit tools that refuse paths
under `.git` are not verified; REQ-149 and REQ-172 cover them by serializing the composite.

### DM-5 Parallel Safety

One row per child of each composite, keyed by child and composite. Its columns are Child, Composite, Parallel-safe, Write set, Interfaces, Independence evidence and Compatible overlap. Render from spec 18 DM-8 and separately recorded reciprocal overlap rationale. An absent row reads as `no`. A directory, glob, unknown interface or resource, or ordering constraint outside the dependency graph disqualifies parallel admission. Represent renames with both exact paths. `Parallel-safe: yes` is necessary for concurrency and remains subject to pairwise checks at dispatch and integration.

### DM-6 Handoff

One JSON object per completed workflow stage, built by the root from the returning agent's report
and the worktree after the root's checkpoint commit, carried in the root's message to the next
agent, and stored by the root under `<git-common-dir>/orchestrail-composite/handoffs/<task-key>/<child>-<attempt>-<stage>.json`.

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | `1` | — |
| `child`, `attempt`, `stage` | text, int, `tests \| implement \| finalize \| check \| propose \| close \| repair` | Identity (`repair`: spec 22 REQ-54) |
| `worktree`, `branch`, `base_commit` | path, text, SHA | Child attempt |
| `candidate_commit` | SHA | Worktree HEAD after the root's checkpoint commit |
| `description_path` | path | The child's `description.md` |
| `ac_ids` | list of text | Acceptance Criteria covered |
| `allowed_paths` | list of paths | The reservation |
| `test_mode`, `test_command` | as spec 22 DM-3 | — |
| `observed` | `{"exit_code": int or null, "label": text or null, "failing_tests": [...]}` | RED, pinned or GREEN observation; see the spec 14 mapping below |
| `test_files` | `{path: sha256}` | Frozen test set identity |
| `previous_digest` | sha256 hex or `null` | Chain link |

The digest is SHA-256 over the object serialized with sorted keys, `","`/`":"` separators and
UTF-8. Handoffs pass between child workflows (`/pae-tests` → `/pae-implement` → `/pae-finalize`
→ `/pav-check` → `/pav-propose` → `/pav-close`); phase agents relay them (C-6) and produce none.
Once spec 14 is delivered, test commands run through its output store, one store shared by the
root and every child worktree (14 REQ-07), safe under concurrent use (14 REQ-11, REQ-112); `observed.exit_code` is 14's DM-3 `exit_code`
only when 14's outcome `kind` is `exit`, and `null` otherwise, with `observed.label` set from
14's outcome `label` (kinds `signal`, `interrupted`, `timeout`, `launch-error`). Before 14,
`label` is `null` and `exit_code` is the shell's exit status.

Spec 13 does not carry the DM-6 object: when 13 is delivered, its attempt record carries the
digest of the handoff given to the workflow as `input_handoff_digest`, and its receipt carries
the digest of the handoff the root builds after that checkpoint as `output_handoff_digest`
(13 REQ-41); the object itself exists only in the file above. For stage `repair` (spec 22 REQ-54) no
receipt exists (13 C-10 row 26), so no `output_handoff_digest` is recorded for it (the field,
where 13's record has it, stays `null`), while `input_handoff_digest` follows 13 REQ-41 as for
every other stage; no rule of this spec requires a receipt for a repair, and the root records
the handoff digest in the journal `handoffs` list as for any stage.

### DM-7 Journal extension (new, parallel mode)

Spec 22 DM-3 is canonical; this spec writes these optional fields and values, accepted by the revision 2 reader:

| Object | Field or value | Type | Writer | Meaning |
|---|---|---|---|---|
| journal | `requested_parallel` | positive integer | root (REQ-12) | N resolved by the latest invocation; a resumed run overwrites it; absent reads as 1 |
| composite | `serialized` | null or `{"at": <timestamp>, "reason": "overlap\|scope-exceeded\|conflict\|interface\|worktree-probe", "paths": [...], "children": [ids]}` | root (REQ-05, REQ-149) | Absent reads as null |
| attempt | `attempt` ≥ 2 and branch `<composite-branch>--<child-slug>-attempt-<k>` | — | root (REQ-05, `next-attempt`) | A new attempt after serialization |
| attempt | `worktree` | null or absolute path (DM-4) | root (REQ-03) | null when the attempt runs in the root worktree |
| attempt | `agents` | `{"coordinator": <agent id>, "workflows": [{"workflow", "agent"}]}` | root (REQ-120, REQ-121) | Agent identities |
| attempt | `handoffs` | list of `{"stage", "digest"}` | root (REQ-122) | Digests of DM-6 handoffs, in order |
| attempt | `actual_write_set` | sorted list of repository paths | root (REQ-02) | Last `check-merge` paths |
| attempt | `unexpected_messages` | integer | root (C-6) | Count; absent reads as 0 |
| attempt | stage `superseded` | — | root (REQ-05, REQ-149) | Terminal; `ended_at` is set when not already set |
| attempt | `spawn_refused` | bool | root (REQ-171) | true while a refused spawn keeps the attempt `branched`; such an attempt is a waiting candidate, not active |
| composite | `capacity_limit` | null or positive integer | root (REQ-171) | Set on a refused spawn while at least one other child is active; cleared when an attempt leaves the active stages |
| attempt | `blocked_reason` `handoff-stale`, `liveness-unknown`, `worktree-not-writable`, `record-failed` | — | root (REQ-122, REQ-127, REQ-156) | Restart mapping below |
| attempt | `cleanup.worktree_removed` `true` | — | root (REQ-158) | After `git worktree remove` |

`task-key` (DM-4 worktree path) = the first 16 hex characters of the journal's file-name digest.

For verified owner-cleared worktree outcomes, use spec 22's base restart mapping plus these cases. Rebuild a `handoff-stale` handoff from the last verified checkpoint and restart the blocked workflow. Restart `liveness-unknown` at the first workflow after the last checkpoint only once prior workers are confirmed gone. Restart `record-failed` at independent atomic validation. Supersede `worktree-not-writable` through serialization and retry on the serialized route. Extended integration failures follow the pinned proposal recovery path.

## Contracts & Interfaces

### Entry points

- `/spec-run <spec> [--allow-pr] [--dry-run] [--parallel [N]]` hands the current composite to the common engine from its Execution step. It owns stack routing, composite PR bases, publication and later phases.
- `/phase-execution <task-directory> [--parallel [N]]` passes the execution policy to `pe-execute` for full tasks. With N > 1 it uses the same local spec 22 branch routing for delivery units, starting from the explicitly verified local base ref for each repository. Standalone execution reports the resulting branch tips and invokes `pe-finalize` after local success. Network push, PR operations and Phase Validation are outside this caller's authority.
- No flag or N = 1 uses established sequential routing and spec 22 resume rules. Bare `--parallel` means 2. Accept `--parallel N` and `--parallel=N` with positive decimal integers and reject invalid values before writes. Reject N > 1 on a quick task or a plan without an eligible composite branch model. Pin the route and journal to each active attempt so changing N or entry point cannot switch its procedure or grant publication authority. For an active extended attempt, even N = 1 reconciles the recorded parallel route before new work.
- Engine input: task directory, repository identity and Git common directory, composite ID, verified target ref/head, requested N, and invocation capabilities. Output: `complete`, `blocked` or `unavailable`, with current delivery tip, accepted child-to-proposal SHA pairs and any blocker. Only the caller owns the transitions following a successful return.

### Admission and integration

For each current composite, use the dependency graph, plan order and required model/capability checks. Require completed integration of every prerequisite on the declared route and verify same-repository prerequisite ancestry on the attempt base. Cross-repository prerequisites use their recorded reviewed delivery evidence and remain serialized. Across candidates require no direct or transitive dependency, exclusive resource, or shared produced/consumed interface. Write sets must be explicit. An intersecting path is eligible only if both rows explicitly record compatible overlap for that peer and path. An unproven leaf uses the serialized route. Re-read plan/state after accepted deltas and approved fixes. Reject graph cycles and unknown references before dispatch. Check actual additions, deletions and both rename endpoints before staging or integration. Paths outside authorization use scope-exceeded serialization. Worker-generated changes to shared records never enter a candidate commit.

Pin a stable topological order at each quiescent planning boundary. Break ties by the execution strategy and then by table order. Keep the accepted prefix immutable. Admit a contiguous prefix of currently runnable pending children in that order. Stop filling the prefix at a child with an unmet prerequisite, incompatible reservation, or exclusive requirement. An exclusive or serialized child may start once earlier integrations are accepted and active attempts have drained. A validated attempt waiting to integrate keeps its reservation and admission slot until accepted or safely withdrawn. Before localized failure or broad stop, preserve pending parent deltas durably. A finished worker releases its harness agent capacity. A later child cannot integrate ahead of an earlier child. On a blocked earlier attempt, allow already dispatched workers to finish, then stop with their outcomes recorded. Recompute the unstarted suffix after the queue drains and an approved plan change adds work. Any change that invalidates an active attempt pauses admission and uses existing reconciliation before proceeding. A failed leaf records its reason and holds its reservation. Once it is the earliest unresolved child, drain already dispatched workers and return blocked. The writer records a pinned intent before any trial or resolution Git mutation. Before every integration trial, apply C-9 `check-merge` to the candidate's work and compare with active reservations and accepted peers. Verify all target changes since the attempt base against accepted peer changes and journal-owned bookkeeping, even if the merge is textually clean. Allow an overlap verdict only for reciprocal named peers and paths. Source synchronization imports target changes, so check the pre-synchronization candidate contribution and separately verify resolution paths and synchronized ancestry. Unexplained changes use the drift safety path. Build the proposed `--no-ff` merge commit on a detached disposable integration worktree at the pinned target. If Git reports conflicts, record the unmerged paths and abort that integration trial. If every conflict path is compatible for the relevant changed sibling, merge the pinned target into the original candidate branch in its worktree. Conflict paths outside the compatible set trigger the serialization procedure below. Retain original candidate checkpoint commits in ancestry.

Before loading a resolver, snapshot the clean merge output for paths outside the unmerged set. A class-A resolution may edit only the unmerged paths and must preserve both contracts and frozen tests, as verified by review. Compare the resolved tree with the snapshot outside that set before accepting a resolution, including an owner-produced merge. A class-B or uncertain resolution stops with the candidate state preserved, conflict paths, both heads and a decision request. An owner-authorized scope or test change follows the existing amendment and TDD rules in a new attempt. A compatible owner resolution can resume on the same attempt after verifying merge ancestry, edit scope and evidence. Resume never treats an unmerged index as resolved. A merge command failing for another reason records a blocker and preserves both heads.

After source synchronization require fresh atomic validation and the recorded test command for the exact resolution head before preparing a fresh integration proposal. If the original TDD mode legitimately has no test command, repeat its recorded manual acceptance checks. Run the spec 22 post-merge command list on the exact proposed commit. Advance the target with the literal `git update-ref refs/heads/<composite> <proposed-sha> <expected-sha>` form. The canonical Git policy and hook must explicitly permit only this journal-proven local fast-forward: an owned, non-symbolic, unprotected composite branch, the target absent from all checked-out worktree branches, and first parent exactly the expected SHA with matching receipts. The orchestrator may first detach its own clean checkout at the expected SHA. A dirty or foreign checkout, protected target, bad receipt or denied command blocks the update. No alternate write form is permitted. Release the proposal worktree only after its commit is reachable from the accepted target and all acceptance records are durable. Reconcile the checkout and parent state before admitting dependents or returning. A moved target invalidates stale proposal and review evidence tied to that target. On unexplained external drift, stop. On a reconciled target change allowed by the journal, re-enter integration with a new pinned intent and rerun affected checks. For extended attempts, this pre-update check gate replaces spec 22 REQ-07/35/45 and their check-failed transitions that assume the target already contains the merge. An integration-check failure writes `blocked` with the failed command/receipt, leaves the target at the expected pre-integration SHA and retains the candidate and proposal. Persist pending blocker and report deltas in the durable journal while a proposal is pinned. In a repository that tracks task records, commit those deltas at the next safe bookkeeping boundary under the record-commit policy below, after acceptance or after explicitly retiring the proposal. A bookkeeping commit does not accept a child. Retiring a proposal invalidates its receipts and requires a fresh intent on retry. Owner clearance permits retry only after reconciliation. With the same target and candidate heads and unchanged check commands, retry the full list on the retained proposal. If the candidate changed, obtain fresh atomic validation and rebuild the proposal. If the target moved, apply the drift policy above. Composite-level validation runs through the spec 22 trigger after all required children are accepted.

### Contract precedence

Unknown or unauthorized overlap triggers serialization. Drain dispatched workers without starting new stages, preserve the accepted prefix, supersede every non-accepted attempt in that composite under the journal rules, and retry the remaining work one child at a time from the current target in the pinned topological order. Use fresh TDD and validation evidence for a superseded attempt. A blocked resolution that needs an owner decision uses REQ-07 instead of automatic retry.

Spec 22 REQ-39 acceptance accounting and REQ-41 TDD history apply. For extended isolated attempts the orchestrator publishes shared deltas outside the candidate worktree and records pending commit SHAs through spec 22 DM-3. Commit tracked records before composite validation, after applying its deltas and before stopping when the target can safely move. A pinned proposal defers record writes that would invalidate it. Root detachment for the guarded ref update is temporary. Serialized fallback uses spec 22 REQ-43 for orchestrator-authored record commits, including its child-branch record point. Workers never modify shared records.

The parallel route uses separate fresh agents for RED and GREEN, with the orchestrator creating the test checkpoint and validating the handoff before dispatching GREEN. The delivery ADR must document the limited amendments to ADR-0004 and ADR-0009. Model selection follows the existing leaf policy for test and implementation agents. Other parallel agents retain the session default. Spec 16 effort policy v1 does not cover these new roles.

### Recovery and safety

Before dispatch apply REQ-125 and REQ-149. For a recorded child with an absent worktree, recreate it from the recorded branch and base only when Git evidence agrees. Treat tracked changes or unexpected untracked, non-ignored paths as `uncommitted-work`. Apply returned deltas sequentially after rereading the current parent section and use spec 13 REQ-18 for stale proposals. After a failed proposal check, admit no new child, let dispatched workers complete without starting further stages, then stop. Missing required capability for explicit N > 1 returns `unavailable` before branch or task mutation. A runtime worker loss follows REQ-127 agent recovery. Reconcile in-progress candidate merges, detached proposals, compare-and-update outcomes and parent-report updates by persisted intent plus actual refs, index, ancestry and receipts. Resume when the evidence agrees. Preserve refs/worktrees and report a blocker on inconsistent evidence. Record accepted changes idempotently. Clean only journal-owned, clean worktrees and branches whose integration is verified and whose removal is permitted by the existing Git rails. Standalone execution retains child branches unless the owner separately authorizes deletion under the applicable rail; the spec 22 spec-run-only deletion exception does not transfer.

### Dry-run output

Include preflight results and per-composite safety rows. Include the compatible overlaps, first admission set for an existing plan, effective limit and delivery route. If no plan exists, print that admission requires Discovery and avoid creating it.

### C-8 Worktree operations

Use explicit paths in separate Git calls. Create an isolated child with `git worktree add -b <branch> <path> <base-sha>`. Use `git -C <path> add <explicit-paths>` and the existing commit rules for candidate checkpoints. Remove an eligible worktree with `git worktree remove <path>`. The guarded target ref update is defined under Admission and integration.

### C-9 Composite helper

| Subcommand | Arguments | Result |
|---|---|---|
| `write-set` | `--repo D --base S --tip S [--include-worktree]` | `{"paths": [...]}`: sorted unique repository-relative POSIX paths from `git diff --name-status -z -M <base> <tip>` (both rename sides) plus, with the flag, every path of `git status --porcelain=v1 -z --untracked-files=all` in D |
| `admit` | `--plan P --journal J --composite ID --limit N` | `{"active": [...], "admit": [...], "respawn": [...], "waiting": [{"id", "reason"}], "integrate_next": id or null, "done": bool}`; an admitted respawn candidate is listed in `respawn` (retry the spawn for its existing attempt) instead of `admit` (start a new attempt) |
| `check-merge` | `--plan P --journal J --composite ID --child ID --repo D` | `{"verdict": "ok" \| "scope-exceeded" \| "overlap", "paths": [...], "with": [...]}` |
| `check-handoff` | `--handoff P --journal J` | `{"verdict": "ok" \| "stale", "digest": <sha256>, "reasons": [...]}`; `stale` when `candidate_commit` ≠ `git -C <worktree> rev-parse HEAD`, a `test_files` hash differs from the file in the worktree, `previous_digest` ≠ the attempt's last recorded handoff digest, or `child`/`attempt`/`branch` differ from the journal's latest attempt |
| `next-attempt` | `--journal J --composite ID --child ID --slug S` | `{"attempt": k, "branch": ..., "worktree": ...}`: k = latest attempt + 1 (1 when none); branch per DM-7; worktree per DM-4, or `null` when the composite is serialized |
| `measure` | `--journal J` | `{"composites": [{"id", "requested_parallel", "elapsed_s", "active_sum_s", "max_concurrency", "merges", "check_failures", "serializations"}]}` |

`measure` formulas per composite, over attempts with both `dispatched_at` and `ended_at`:
`elapsed_s` = latest `ended_at` − earliest `dispatched_at`; `active_sum_s` = Σ(`ended_at` −
`dispatched_at`); `max_concurrency` = the largest number of such intervals
[`dispatched_at`, `ended_at`) containing one instant; `merges` = accepted integrations; `check_failures` = the recorded count of failed proposal check runs; `serializations` = 1 if `serialized` is set, else 0. With no such attempt
the three time values are `null`.

The helper follows spec 22 C-3 for invocation and base subcommands. The child base must descend from every same-repository prerequisite accepted in this composite. An eligible child can therefore start from an earlier composite tip than the merge immediately preceding its integration. `admit` returns only the eligible prefix under the ordered scheduler. An active stop or unresolved earlier blocker prevents new admissions and integration. `integrate_next` is the first unresolved child in the pinned order only when it is validated. `done` requires every required child accepted, including cleanup-pending accepted attempts. For `check-merge`, classify scope violations before overlap and report associated peers and paths. Apply the reciprocal approval and synchronization checks above to determine admissibility. The helper must negotiate journal revision 2 before extended attempts.

### C-10 Delivery surfaces

Update both entry points and the shared execution step, atomic and composite worker workflows, decomposition and design producers, capability preflight, Git rails and user reference docs. Add deterministic helper tests and failing canonical contract checks for the changed rules. Follow spec 09 REQ-69 for affected validator checks and its naming migration if delivered. Spec 10 owns the golden format. Delivery here adds the parallel-2 case variant and comparator after approval, with branch ancestry and review outcomes checked in both modes.

### C-6 Message protocol in parallel mode

The root spawns every agent (A-16); an agent's final report returns to the root; the root,
coordinators and phase agents exchange messages only with the root, never directly between two
non-root agents (`agent-messaging`). Each message is one JSON object.

| # | From → To | Message | Root action |
|---|---|---|---|
| 1 | root → coordinator (spawn) | `{"attempt": {child, attempt, branch, worktree, base_commit}, "description_path", "ai_dir"}` | Journal `dispatched`, `agents.coordinator` |
| 2 | coordinator → root | `{"request": "phase", "workflow": "phase-atomic-execution"}` | Spawn execution phase agent with message 1's fields |
| 3 | phase agent → root | `{"request": "workflow", "workflow": "pae-tests" \| "pae-implement" \| "pae-finalize", "handoff_digest": <sha256 or null>}` | `check-handoff` on the named handoff (none for `pae-tests`); spawn the workflow agent with that handoff |
| 4 | workflow agent → root (final report) | Workflow report: changed paths, test files, observed command and result, deltas, and `"worktree_unwritable": true` when its edit tool refused a worktree path (REQ-172) | REQ-02, checkpoint commit, REQ-122 handoff, apply deltas; reply to the phase agent `{"stage-done": <workflow>, "handoff_digest", "verdict"}` |
| 5 | phase agent → root (final report) | `{"phase-done": "execution", "result": "complete" \| "blocked" \| "failed", "reason"}` | Forward to the coordinator |
| 6 | coordinator → root | `{"request": "phase", "workflow": "phase-atomic-validation"}` only after a `complete` execution phase or, under spec 22 REQ-54, after the root reports a finished repair (row 10) | Spawn validation phase agent; it requests `pav-check`, `pav-propose`, `pav-close` as in row 3 |
| 7 | phase agent → root (final report) | `{"phase-done": "validation", "verdict": "DONE" \| "NEEDS WORK", "composite_ready": <id or null>}` | Apply deltas; journal `validated`, or on NEEDS WORK `failed` (or, under spec 22 REQ-54, keep `dispatched` and run the repair); forward to the coordinator, which ends unless a repair runs, in which case it requests a validation phase again after the repair |
| 8 | root → coordinator and root → its live phase agent | `{"stop": <reason>}` (REQ-104, REQ-05, REQ-127) | The phase agent lets its running workflow agent finish, requests nothing more and sends its final report; the coordinator replies `{"stopped": <last stage-done workflow>}`; a running `repair` workflow agent finishes the same way and starts no recheck (REQ-104, spec 22 REQ-54) |
| 9 | root → coordinator or workflow agent | `{"status?": true}` (REQ-127) | Reply `{"status": <current workflow or "idle">}`. One status round is one such message to every probed agent followed by one collection of replies after all messages are sent; an agent that has not replied at that collection, and that the harness has not reported unknown or finished, is `unknown` |
| 10 | root → coordinator | `{"repair-done": <episode key>, "handoff_digest": <sha256>}` after the root spawned the `/pae-repair` workflow agent (REQ-121, spec 22 REQ-54), applied its deltas, committed 17's checkpoints and built the DM-6 handoff with stage `repair` | Journal `agents.workflows` (the repair agent); the coordinator then sends row 6 |
| 11 | review agent → root (final report): the `/pav-check` workflow agent, the Validator of a serialized composite's child (final report only, no phase agent) or the spec 22 REQ-12 composite validation agent | The row 4 report plus `"review": {"draft": {"level", "step", "scope_key", "options": {the `prepare` options as C-1 of spec 15 names them}, "record": <spec 15 DM-7 draft object>} \| null, "none_reason": null \| "unavailable" \| "disabled" \| "helper-error" \| "multi-repository" \| "blocked"}`; `draft` is null only with a `none_reason` (spec 15 DM-8 reasons) | REQ-155, REQ-156: write the draft file, run `record`, then apply the verdict and notes deltas and append the `verification:` entry from the `record` result; or append the `none` entry |
| 12 | root → phase agent (reply replacing row 4's after a review report that REQ-156 handles) | `{"stage-redo": "pav-check", "record": "refused" \| "unusable" \| "error", "reasons": [<spec 15 refusal reasons, `draft-invalid` for an unusable draft, or the `record` error code for exit 2, 3 or 4>], "helper": "on" \| "off"}` | The phase agent requests `pav-check` again (row 3); the root spawns the fresh agent with `reasons` and `helper`; the composite validation agent and the Validator of a serialized composite's child have no phase agent, so the root respawns them directly with the same fields |

Messages that do not match the expected next row for the attempt are ignored and recorded in the
journal attempt as `unexpected_messages` (count); a second report for the same workflow with the
same handoff digest is a duplicate and ignored. A different report for an already completed stage blocks that stage.

## Non-Functional Requirements

- Isolation is verified with separate Git indexes and a single orchestrator writer. A second writer must fail before changing refs or shared state.
- Reproducibility is verified by exact SHA-bound checkpoint and check receipts, deterministic topological integration order and retry without duplicate merge records.
- Concurrency is verified with a barrier fixture in which two eligible workers start before either finishes, with a peak no greater than the requested N. Report the effective limit, peak and wait/fallback reasons using the existing execution report and logging rules.

## Edge Cases & Failure Modes

| Case | Expected outcome |
|---|---|
| Completed queue or no remaining runnable work after successful reconciliation | Return through normal phase finalization with zero new workers if all required work is accepted. Outstanding blockers suppress finalization. REQ-11 |
| Declared empty composite or malformed child list | Apply spec 22 REQ-44 and stop before branch creation. REQ-12 |
| Unknown dependency, cycle, invalid limit or missing capabilities | Reject before dispatch and unsafe mutation. REQ-02, REQ-12 |
| Stale or asymmetric overlap evidence, interface coupling, out-of-scope path or exclusive resource | Serialize when safe or preserve the existing blocker. REQ-02, REQ-12 |
| Clean textual merge with semantic regression | Checks fail and the target stays at its prior accepted head. REQ-09 |
| Ambiguous conflict, conflict outside listed overlap or unresolved index | Pause for a decision or use the existing serialization path as defined above. REQ-06, REQ-07, REQ-10 |
| Crash immediately before or after the target update, target moved externally, dirty or locked checkout | Reconcile from journal and Git evidence or stop with artifacts preserved. REQ-09, REQ-10 |
| Active worker during stop, lost worker or changed concurrency limit | Follow recorded attempt route and recover or drain under REQ-104 and REQ-127. REQ-10, REQ-12 |
| Protected ref, denied Git operation or missing approval | Preserve the candidate and report the blocker under prevailing Git rails. REQ-07, REQ-10 |

## Acceptance Criteria

- **AC-01 (REQ-01, REQ-11)** Given a full-tier composite fixture, when either caller selects parallel mode, then the same engine receives equivalent scheduling inputs. The standalone command reaches local finalization without remote writes, and spec-run opens a composite PR only with its existing authorization.
- **AC-02 (REQ-02, REQ-03, REQ-04)** Given two siblings with reciprocal overlap approval and a third depending on both, when the first two reach a test barrier, then they use distinct Git worktrees, the third has not started, and a second orchestrator cannot write. The third starts from a base containing both accepted integrations.
- **AC-03 (REQ-05)** Given a plan with a forward dependency and independent later work that completes first, when the children integrate or an unapproved overlap triggers serialization, then the first-parent chain follows pinned topological order, the accepted prefix stays intact, and the execution report records one acceptance per child. Superseded attempts never contribute acceptance records.
- **AC-04 (REQ-06, REQ-08, REQ-09)** Given allowed text overlap with fixtures for both intended behaviors, when the candidate conflicts, then the target is unchanged during resolution, both original checkpoint histories are reachable, review and checks bind to their exact new heads, and the accepted result passes both fixtures.
- **AC-05 (REQ-07, REQ-09)** Given separate runs with incompatible requirements and a clean textual merge that fails composite tests, when integration runs, then the first returns a decision blocker and the second returns a check blocker with the candidate retained. Neither advances the target.
- **AC-06 (REQ-09, REQ-10)** Given interruptions during resolution and on both sides of the target update, when each run resumes, then it reconciles the index and receipts with the recorded intent and produces at most one accepted merge and report entry. A separate fixture with an unexplained target move leaves the unexpected target and candidate intact.
- **AC-07 (REQ-02, REQ-12)** Given an invalid graph, unsupported explicit concurrency, asymmetric overlap, unauthorized clean overlap, or an unauthorized rename endpoint, when planning or execution detects it, then the first two reject with a cause before dispatch, and the remaining cases enter the specified serialized or blocked route without integrating the offending attempt. An omitted flag behaves sequentially.
- **AC-08 (REQ-13)** Given an existing plan and an explicit dry run, when spec-run runs preflight, then output reports the preflight result, per-composite safety rows, compatible overlaps, configured and effective limit, first admission set and branch/PR route, and refs, worktrees, journal and task files are byte-for-byte or identity-equivalent to their previous state.

- **AC-09 (REQ-08, REQ-09, REQ-10)** Given a receipt for another candidate head or proposed merge tree, when integration resumes, then the mismatching receipt cannot advance the target and the applicable check or review must run again on the pinned object.
- **AC-10 (REQ-09, REQ-12)** Given an empty composite, protected target, or target checked out by a foreign worktree, when the engine reaches the corresponding preflight or ref update, then the empty composite creates no branch and both target refusals leave the existing ref unchanged.

- **AC-11 (REQ-102, REQ-126)** Given a composite journal with completed, interrupted and undispatched attempts, when report and measurement run twice, then each terminal attempt has one aggregate, attempt intervals yield the reported concurrency, and unobserved values are reported as not measured.
- **AC-12 (REQ-109, REQ-152, REQ-125)** Given planned children and a missing capability, when planning, design and either preflight run, then the safety records reflect current evidence for unstarted children, started rows stay fixed and dispatch makes no writes on missing required capability.
- **AC-13 (REQ-120, REQ-121, REQ-122, REQ-128, REQ-169)** Given a testable child, when execution and validation cross workflow boundaries, then each required role has a distinct identity, packet and worktree match the attempt, RED precedes GREEN, and a corrupted handoff blocks transition.
- **AC-14 (REQ-104, REQ-127, REQ-162, REQ-171, REQ-172, REQ-149)** Given broad stop, lost and unknown agents, spawn refusal, probe mismatch and an unwritable worktree in separate fixtures, when execution resumes or drains, then it preserves work, restores only verified checkpoints, respects recorded capacity and serializes probe failures.
- **AC-15 (REQ-163, REQ-155, REQ-156)** Given an active repair policy and a refused review draft, when the corresponding paths run, then repair retains its episode and slot, review publication stays with the root, and refused drafts follow the bounded correction path.
- **AC-16 (REQ-158, REQ-170, REQ-161)** Given accepted and superseded worktrees and a denied or failed removal, when cleanup runs, then it preserves non-owned, dirty and refused artifacts, retains superseded branches, and removes handoffs only with authorized journal cleanup.
- **AC-17 (REQ-115)** Given owner-approved golden runs at limits 1 and 2, when the comparator runs, then required final assertions agree after declared aliases, and a fixture with a changed required outcome fails.

## Traceability

| Requirement | Criteria |
|---|---|
| REQ-01 | AC-01 |
| REQ-02 | AC-02, AC-07 |
| REQ-03 | AC-02 |
| REQ-04 | AC-02 |
| REQ-05 | AC-03 |
| REQ-06 | AC-04 |
| REQ-08 | AC-04, AC-09 |
| REQ-07 | AC-05 |
| REQ-09 | AC-04, AC-05, AC-06, AC-09, AC-10 |
| REQ-10 | AC-06, AC-09 |
| REQ-11 | AC-01 |
| REQ-12 | AC-07, AC-10 |
| REQ-13 | AC-08 |
| REQ-102 | AC-11 |
| REQ-126 | AC-11 |
| REQ-109 | AC-12 |
| REQ-152 | AC-12 |
| REQ-125 | AC-12 |
| REQ-120 | AC-13 |
| REQ-121 | AC-13 |
| REQ-122 | AC-13 |
| REQ-128 | AC-13 |
| REQ-169 | AC-13 |
| REQ-104 | AC-14 |
| REQ-127 | AC-14 |
| REQ-162 | AC-14 |
| REQ-171 | AC-14 |
| REQ-172 | AC-14 |
| REQ-149 | AC-14 |
| REQ-163 | AC-15 |
| REQ-155 | AC-15 |
| REQ-156 | AC-15 |
| REQ-158 | AC-16 |
| REQ-170 | AC-16 |
| REQ-161 | AC-16 |
| REQ-115 | AC-17 |

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Textual or clean merge changes sibling behavior | Regression | Medium | Both contracts reviewed and tested on the proposed result. |
| Integration crashes after the ref moves | Duplicate actions or inconsistent statuses | Medium | Durable intent, guarded target update and idempotent reconciliation. |
| Engine runs against an incorrect worktree | Shared state damage | Medium | Verify paths and repository identity, isolate indexes, enforce one writer and preserve dirty trees. |
| Changed capabilities or stale prerequisites | An attempt cannot run or is validated against stale code | Medium | Preflight current permissions and check exact integration ancestry. |

## Assumptions

- A-01 | Concurrency boundary | Resolved: children of one composite | Source: ADR-0009 Decision 4 and the recorded owner decision in the superseded spec 23 | Reversible: yes
- A-02 | Mode selection | Resolved: explicit positive parallelism with sequential compatibility | Source: former spec 23 and the current entry-point contract | Reversible: yes
- A-03 | State and workspace authority | Resolved: one orchestrator, isolated Git worktrees and local detached integration trial | Source: architecture principles P2/P4 and the retained worktree design | Reversible: yes
- A-04 | Shared-file eligibility | Resolved: reciprocal explicit path evidence and source-side merge resolution with class-A/B routing | Source: owner request, spec 22 REQ-64 and existing escalation policy | Reversible: yes
- A-05 | Delivery integration | Resolved: deterministic plan order and caller-owned delivery with no automatic publication from phase-execution | Source: current caller contracts and git-flow | Reversible: yes
- A-06 | Performance and recovery | Resolved: demonstrate bounded simultaneous admission and resume with a pinned journal, without a fixed latency target | Source: retained measurement and recovery design | Reversible: yes

## Decisions

N/A — auto mode. The proposed design and its limited ADR amendment are recorded in the linked ADR.

## Clarifications

### Session 2026-11-24

N/A — auto mode. Resolutions are in Assumptions.

## Open Questions

- **Q-01 (non-blocker for this design)** — When will the owner approve activation of the two limited amendments to ADR-0009 Decision 4? The spec is actionable as a proposal. Activation stays gated until the owner approves the broader entry point and compatible-overlap policy.

## Notes

- Prerequisites: spec 22 and the capability, journal, testing and peer interfaces listed in the roadmap. Spec 23 is superseded and is not a delivery dependency. Verify shipped support before implementation. This proposal extends ADR-0009 Decision 4 only for the entry point and specifically approved overlap inside the same composite. Record owner approval of that amendment before activation. This specification does not change the accepted ADR or schedule roadmap delivery.
- Update the canonical Git, orchestration and workflow contracts and their readers together. Add failing contract checks before edits and isolated Git fixture coverage for real conflicts, scope checks, denied writes, head changes and restart boundaries.
- Delivery slices: establish worktree, journal and worker infrastructure; enable the shared scheduler and caller routing; add reciprocal overlap, source-side resolution and guarded integration. These are slices of this specification and share its acceptance gates.
- Design record: [Shared composite execution proposal](../adr/0026-task-unknown-shared-composite-execution.md).

## Readiness Checklist

The earlier four-round review (79, 91, 94 and 100/100) covered the initial proposal. The consolidated contract was checked for identifiers, traceability, local links and roadmap dependencies. Its expanded scope has not received a fresh independent spec-draft review. Verify prerequisites and obtain approval for the proposed ADR amendments before activation.
