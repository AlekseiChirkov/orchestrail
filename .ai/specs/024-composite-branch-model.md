# 024. One branch per composite subtask, with sequential children on temporary branches

## Source

- Owner request of 2026-11-16 to separate the composite branch model into an
  independently deliverable specification. Earlier material remains in Git history.
- ADR-0009 Decision 4 records one branch and one PR per composite.
- This specification covers sequential child integration, verification, the
  composite journal, recovery and verified cleanup.

## Context & Problem

Verified at worktree revision `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff` (2026-11-13).

**Current branch model.** `/spec-run` treats a composite row as a container that "get[s] no
branch and no agent; their children appear in the order as ordinary leaves"
(`workflows/spec-run.md:162-165`). Every leaf, composite children included, gets its own
stacked branch cut from the previous reviewed leaf's tip (`workflows/spec-run.md:200-206`,
`rules/git-flow.md:52-58`) and, with `--allow-pr`, its own draft pull request whose base is the
previous subtask's branch (`workflows/spec-run.md:305-308`, `rules/git-flow.md:173-180`). When
the last child closes, `/pav-close` step 5 calls `/phase-composite-validation` from inside the
Validator, "on the current branch — the tip already contains every child. Do not create a
branch for the composite" (`workflows/spec-run.md:301-303`, `workflows/pav-close.md:53-66`).
The composite integration check takes "the union of all files changed by any child" from the
children's `target_files:` as its surface (`workflows/phase-composite-validation.md:57`).

**Current execution model.** The runner executes leaves sequentially. One Implementer
runs `/pae-tests`, pauses at RED, then continues `/pae-implement` and `/pae-finalize`
with a separate Validator (`workflows/spec-run.md:261`, `:480`). Shared-state deltas
are applied by the root (`rules/orchestration.md`).

**Current state format.** A leaf block carries `branch:`, `base_branch:`, `base_commit:`,
`commits:`, `pr:` in orchestrated mode (`rules/workflow-globals.md:175-186`); a composite block
carries only `children:`, `blocker:`, `notes:` (`rules/workflow-globals.md:210-219`). Composites
are never nested (depth-2 cap, `.ai/principles/domain.md:20`).

**Current git rails.** Branch deletion is "Owner approval required; a verified temporary
child-branch exception is planned" (`rules/git-flow.md:228`), and the contract validator pins
that exact wording (`scripts/validate-contracts.sh:5614`). The hook routes R22 (`git branch
-d/-D`) and R23 (`git update-ref -d`) through a replaceable `DELETION_VERIFIER` whose shipped
implementation `no_exception_verifier` grants nothing (`hooks/git_rails.py:3066-3096`,
`:3284-3290`, `:3336-3354`); the git-rails suite asserts that default
(`tests/git-rails.sh:2801-2802`). Spec 007 reserved this extension point for this spec and
prefers `git update-ref -d refs/heads/<b> <expected-sha>` (completed spec 007 §8.7).
`git merge` is checked only when the current branch is protected (R27,
`hooks/git_rails.py:3385-3387`). `/restack` collects every branch-owning subtask block in plan
order (`workflows/restack.md:21-23`) and uses one recovery-journal pattern that the hook
verifies (`workflows/restack.md:38-107`). `git worktree remove --force` is not enforced by the
hook (`harness/claude/capabilities.md:73`, X3).

**Decided but not built.** ADR-0009 Decision 4 records one branch and one PR per composite.

**Consequence.** A composite's children are reviewed as separate stacked pull requests although
their integration criteria apply only to their union; every independent child waits for its
predecessor; and the git rails still ask the owner to delete any temporary branch the pipeline
creates.

## Goal

Give every composite subtask run by `/spec-run` one permanent branch and, when publication is
authorized, one pull request: each child runs, one at a time, on a temporary, run-owned
branch, passes its own atomic cycle, and is merged into the composite branch with a `--no-ff`
merge commit that keeps its test-first commits, after which the run deletes the temporary
branch only when the git-rails hook can verify the deletion; a composite journal lets an
interrupted run resume without duplicate merges or lost work.

## Scope

1. The per-composite branch model for new `/spec-run` tasks in sequential mode (N = 1):
   composite branch, temporary child branches, `--no-ff` integration,
   post-merge checks, composite validation on the composite branch, one PR per composite.
2. The `branch_model:` task field and the additive git fields of composite and child blocks,
   with backward compatibility for tasks run under the per-leaf stack.
3. The composite journal (schema, location, stages, atomic write) and resume reconciliation.
4. Cleanup of temporary branches, and a git-rails `DELETION_VERIFIER` that
   allows exactly one verified deletion form.

9. The optional helper `scripts/composite_run.py` with the subcommands `--version`,
   `validate`, `reconcile` and `post-merge-commands`.
10. `/restack` handling of per-composite tasks.
11. Rule, workflow, principle, vocabulary and documentation updates, the superseding ADR, and
    deterministic contract and fixture checks.

**Scheduling.** This spec starts only when the owner schedules it. Hard prerequisites,
checked at Discovery: spec 011 delivered (its DM-9 `contract_changes` mechanism and REQ-69,
which C-5 uses) and spec 012 delivered (the `composite` golden case files C-5 rebuilds); specs
02, 03 and 05 are completed. Specs 014, 017 and 019 are optional: A-18 states the behaviour
before each is delivered.

## Out of Scope

- Changes to execution scheduling and unrelated task or repository modes.
- A separate integration branch, wave branches, or a task-level branch.
- Pushing or opening pull requests for temporary child branches.
- Merging any pull request, locally or through `gh` (unchanged rail, `rules/git-flow.md:180`).
- The state tool of spec 009 (ADR-0021); the root may use it as its writer when available, but
  nothing here depends on it.
- Defining the capability keys or their declaration format (spec 011), the context packet
  (spec 014), checkpoint envelopes and derived proposals (spec 015), verification scope (spec 017),
  repair attempts (spec 019), independence evidence content (spec 020), telemetry attribution
  (spec 006), effort (spec 018) and golden evaluation (spec 012).
- Changing the run-log vocabulary or adding run-log fields (`rules/run-log.md`, spec 003).
- Migrating a task that already recorded per-leaf branches to the new model.
- Preserving merge commits through `/restack` (Q-02); the exact verified replay form stays.
- Any speedup, token or cost target, and any paid comparison run.
- Changing existing tasks, branches or history in this repository.

## Actors & Roles

| Actor | Allowed actions | Forbidden |
|---|---|---|
| Owner | Invokes `/spec-run` with or without `--allow-pr`; answers class-B questions; approves or rejects hook asks; merges PRs | — |
| Orchestrator (root) | Sequencing, admission, every git operation, every write under `.ai/` and to the composite journal, spawning agents, applying deltas, running the helper | Writing code or tests; resolving class-B questions; merging PRs; force or rebase outside `/restack` |
| Arbiter | Answers class-A questions with citations (unchanged, `rules/orchestration.md:38-54`) | Writing anything |
| Implementer / Validator (effective limit 1) | Unchanged roles (`rules/orchestration.md:56-92`), working in the root worktree on the checked-out child branch | Git operations; shared-file writes beyond the existing own-block carve-out |
| Composite validation agent | A fresh validation sub-agent that runs `/phase-composite-validation` on the composite branch and returns deltas | Writing shared files; git operations |
| git-rails hook | Decides deletion commands through the replaced `DELETION_VERIFIER` | Writing any file |
| `scripts/composite_run.py` | Reads plan, journal and repository; prints decisions | Writing files; git write commands; spawning models |

## Terminology

| Term | Definition | Source |
|---|---|---|
| **Branch model** | Task-level `branch_model:` value: `per-leaf` (every leaf, composite children included, gets a stacked branch; the shipped behaviour) or `per-composite` (this spec). | New; REQ-16 |
| **Composite branch** | The one stacked branch of a composite subtask in a `per-composite` task, cut like any stack branch and named `<type>/<feature-slug>` from the composite's Goal. | ADR-0009 D4; REQ-06 |
| **Child** | A leaf listed in a composite block's `children:`. | `rules/workflow-globals.md:210-219` |
| **Attempt** | One execution of a child on one temporary branch. Under this spec every child has exactly one attempt. Not a repair attempt of spec 019. | New |
| **Child branch** | The temporary, run-owned, never-pushed branch of one attempt: `<composite-branch>--<child-slug>` for attempt 1. `<child-slug>` follows the branch slug rules of `rules/git-flow.md:60-71` (collisions between children are refined from their Goals); the `--` separator is exempt from repeat-collapsing. | Original §8.1; REQ-30 |
| **Integration** | The verified `--no-ff` merge of a child attempt's exact tip into the composite branch, accepted only after post-merge checks pass and state is recorded. Synonym "inclusion" in the original. | Original §4; REQ-03 |
| **Post-merge check** | Running, on the merged composite tree, the recorded test command of every child accepted so far plus the merged child. A child-branch result, including a spec 017 receipt, never stands for it (A-28). | REQ-03 |
| **Composite journal** | The JSON recovery record `<git-common-dir>/orchestrail-composite/<sha256(task_path)>.json` owned by the root. | REQ-13 |
| **Stage** | A journal-only lifecycle value of an attempt (DM-3). Not a task status. | Original §11 |
| **Root** | The Orchestrator of `/spec-run`. | `.ai/principles/domain.md:32` |
| **Episode key** | Spec 019's `episode_id` (019 DM-2). This spec defines no key of its own: DM-3 `repair_episode` holds that value. | REQ-54; 019 C-10 row 23, A-34 |

Rejected synonyms: "integration branch", "wave branch", "task branch" (no such branches exist);
"sub-PR" (children get no PR); "lock" for a reservation (no file lock is used); "retry" or
"attempt" for a spec 019 repair (a repair is not an attempt).

## Requirements

The requirements apply to `/spec-run` tasks using `branch_model: per-composite`.
Identifiers preserve their meanings; this specification covers sequential children.

### Shared state and accounting

- **REQ-53 Context packet.** WHERE spec 014's `packet` command is delivered, WHEN the root
  dispatches an execution or validation agent for a child, THE SYSTEM [root] SHALL build the
  agent's packet per 014 C-8 with `--work` set to the root worktree, `--ai-dir` set to the root worktree's `.ai/`,
  `--base-commit` set to the attempt's `base_commit`, and `--role implementer` for execution
  workflows or `--role validator` for validation workflows, and pass that packet as the
  agent's context in addition to the dispatch items `/spec-run` already passes; when `packet` exits non-zero (including
  014's `working-dir-mismatch`, 014 REQ-50), it dispatches without a packet as 014 REQ-40/REQ-41
  provide.
- **REQ-43 Tracked task records.** WHERE the repository tracks `.ai/` paths, THE SYSTEM [root]
  SHALL commit pending tracked `.ai/` changes as `chore: update task records`, staging explicit
  paths under `rules/git-flow.md:156-165`, at exactly four points: (a) on the child branch,
  before switching the root worktree to the composite branch, after which it writes no tracked
  `.ai/` file until the merge commit exists, except a point (d) stop; (b) on the composite branch, after recording an
  accepted integration (REQ-39) and before cutting the next child branch or dispatching
  composite validation; (c) on the composite branch, after applying the deltas of composite
  validation and before REQ-08 pushes; (d) on the branch then checked out, immediately before the
  run stops with a `blocker:` (REQ-35, REQ-36, REQ-51, the `inspect-worker` action), so that a
  stopped run leaves no uncommitted tracked change for the clean-tree gate. The owner who clears
  `blocker:` commits that edit on the same branch. The SHA of a record commit is first added to the block's `pending_commits` in the journal
  (DM-3, a REQ-42 write before any further git operation) and is moved from there to the block's
  `commits:` at the next record write, also in a later run, never inside that commit; the switch that cuts the next
  stack branch makes no record commit, pending records carry over and are staged with the next
  commit as today, and the next stack branch is cut from the composite tip that includes commit
  (c), which is the tip REQ-08 pushes.
- **REQ-65 Attempt tip.** WHEN the root makes a commit on a child branch, THE SYSTEM [root]
  SHALL write that commit's SHA as the attempt's `tip` in the next journal write (REQ-42) and
  before its next git operation.

### Branches and integration

- **REQ-06 Composite branch.** WHEN the stack reaches a composite whose block has no
  `branch:` and whose `children:` list is non-empty, THE SYSTEM [root] SHALL create the
  composite branch from the reviewed tip of the previous top-level stack branch (the default
  branch for the first) and record `branch:`, `base_branch:`, `base_commit:`, `commits:`
  (empty) and `pr: none` in the composite block before any child starts.
- **REQ-44 Empty composite.** IF a composite's `children:` list is empty or lists an id with no
  plan row or leaf block, THEN THE SYSTEM [root] SHALL stop before creating its branch with
  `**stop**: "Composite <id> has no runnable children. Re-run /pd-decompose."`.
- **REQ-30 Child branch.** WHEN the root starts a child attempt, THE SYSTEM [root] SHALL create
  the attempt's child branch (Terminology) at the composite branch's current tip SHA and record
  that SHA as the attempt's `base_commit` in the journal and in the child block, using the C-2
  form for the root worktree.
- **REQ-07 Merge form.** WHEN a child attempt is ready to integrate, THE SYSTEM [root] SHALL
  merge it from the root worktree with the composite branch checked out, using exactly
  `git merge --no-ff -m "Merge branch '<child-branch>' into <composite-branch>" <child-branch>`
  as its own Bash call, never squash, rebase or fast-forward.
- **REQ-03 Post-merge checks.** WHEN a merge commit for a child attempt is created, THE SYSTEM
  [root] SHALL run in the root worktree, on that commit's tree, the recorded `test_command`
  (DM-3) of every child already accepted in the composite and of the merged child, in
  `## Subtasks` row order and skipping `null` commands, and accept the integration only if
  every command exits 0.
- **REQ-35 Post-merge failure.** IF a post-merge check fails, THEN THE SYSTEM [root] SHALL keep
  the merge commit, set the attempt stage `check-failed` with the failing command, set the
  composite block `blocker:` to that command and child, integrate no further child of that
  composite, and stop the run.
- **REQ-45 Post-merge recovery.** WHEN a run resumes a composite whose block `blocker:` the
  owner has set back to `none` and whose child is `check-failed` (`reconcile` returning `none`
  after any `record-tip` or `record-composite-tip`), THE SYSTEM [root] SHALL rerun
  the REQ-03 command list on the current composite tip and, if every command exits 0, apply
  REQ-39, which sets the attempt `accepted`, or keep `check-failed` and stop again otherwise.
- **REQ-36 Merge conflict.** IF `git merge` reports a conflict, THEN THE SYSTEM [root] SHALL run
  `git merge --abort`, record the conflicting paths and stage `conflict` in the journal, keep
  the child branch, set the composite block `blocker:` to `conflict: <child id>: <first
  conflicting path>`, and stop the run (A-30).
- **REQ-64 Owner-cleared conflict.** WHEN a run resumes a child whose latest attempt is
  `conflict` and whose composite block `blocker:` the owner has set to `none`, THE SYSTEM [root]
  SHALL, if `reconcile` returns `none` for it (after any `record-tip` or
  `record-composite-tip`), switch the root worktree to the child branch (C-2), set the attempt
  back to `dispatched` and restart it at atomic validation with fresh agents on the current
  child tip, after which the attempt follows REQ-07 again; while `blocker:` is not `none` the
  attempt stays `conflict`. The owner resolves in this order: commit the cleared `blocker:` on
  the composite branch, then switch to the child branch and merge the composite tip into it,
  resolving the conflict there.
- **REQ-39 State recording.** WHEN an integration is accepted, THE SYSTEM [root] SHALL record
  `merge_commit: <sha>` in the child block, append `<sha> merge: <child domain name>` to the
  composite block's `commits:`, and only then set the journal stage `accepted`.
- **REQ-41 Test-first per child.** THE SYSTEM [root] SHALL keep, on every child branch, the
  commit sequence `git-flow → ## Commits` prescribes for the child's `atomic-tests:` mode: a
  `test:` commit before the implementation commit for `red` and `pinned`, a single
  implementation commit for `n-a`, and the `pre-TDD task, TDD step skipped` note without a
  retroactive RED for a legacy in-progress block.
- **REQ-46 Test command record.** WHEN `/pae-tests` reaches `red` or `pinned` for a child, THE
  SYSTEM [`/pae-tests`] SHALL report the exact command that observed the result, and the root
  SHALL record it as the notes line `tdd: command — <command>` in the child block and as the
  attempt's `test_command` in the journal.

### Publication and cleanup

- **REQ-08 One PR per composite.** WHERE `--allow-pr` is given, WHEN a composite reaches
  `reviewed`, THE SYSTEM [root] SHALL push only the composite branch and open one draft PR whose
  base is the previous top-level stack branch (the default branch for the first), or reuse the
  PR already recorded in the composite block's `pr:`, and record it there; child blocks keep
  `pr: none` and child branches are never pushed.
- **REQ-33 PR body.** WHEN the root builds a composite PR body, THE SYSTEM [root] SHALL include
  the composite's Goal and integration Acceptance Criteria, one stack-position line naming
  predecessors by branch, and one section per accepted child with its domain name, Goal,
  Acceptance Criteria, test level and `test:` commit SHA (or the `n-a` justification), with no
  pipeline identifier (`rules/git-flow.md:129-154`).
- **REQ-31 Cleanup.** WHEN an attempt's stage is `accepted` and its `cleanup.failure` is null,
  THE SYSTEM [root] SHALL first confirm the C-4 checks 1 and 4–8 for the child branch from the
  journal and read-only git, then run `git update-ref -d refs/heads/<child-branch> <attempt tip>`
  as its own Bash call, set stage `cleaned` when the ref no longer exists afterwards (an
  owner-approved hook ask included), and otherwise — a failed confirmation, an owner-rejected
  ask, a deny or a git error — keep the branch, record the reason in `cleanup.failure`, never
  retry or rephrase it in this or a later run, and continue.
- **REQ-32 Deletion verifier.** WHEN the git-rails hook evaluates an R22 or R23 deletion, THE
  SYSTEM [hook] SHALL grant the exception only for `git update-ref -d refs/heads/<b> <sha>`
  whose ref, expected SHA and repository pass every check of `## Contracts & Interfaces →
  ### C-4`, and otherwise keep the shipped `ask` decision.
- **REQ-47 Journal retention.** WHEN the task's Execution phase is complete and every attempt
  is `cleaned`, THE SYSTEM [root] SHALL first make a record write that empties
  every `pending_commits` list into `commits:`, then delete the task's composite journal
  after the Step 8 report; otherwise it keeps it.

### Composite validation

- **REQ-12 Single composite validation.** WHEN every child of a composite has its latest
  attempt `accepted` or `cleaned` and plan status `reviewed`, THE SYSTEM [root] SHALL check out
  the composite branch in the root worktree and dispatch one fresh validation agent to run
  `/phase-composite-validation` once for that composite tip, whose integration surface is
  `git diff --name-only <composite base_commit>..<composite tip> -- . ':(exclude).ai'` (a full
  review; spec 017 scope `full-integration`, A-28).
- **REQ-40 Close signal.** WHILE a task is `per-composite`, WHEN `/pav-close` finds every
  sibling child complete, THE SYSTEM [`/pav-close`] SHALL return the signal
  `composite-ready: <composite id>` to its caller instead of invoking
  `/phase-composite-validation`.
- **REQ-67 Fix sibling.** WHEN composite validation returns NEEDS WORK and a fix sibling is
  approved under the existing protocol (`workflows/phase-composite-validation.md:89-143`), THE
  SYSTEM [root] SHALL run the fix sibling as the next child under REQ-51 (its branch from the
  current composite tip, the normal cycle and merge) and then run REQ-12 again on the new
  composite tip.

### Planning

- **REQ-51 Sequential children.** THE SYSTEM [root] SHALL run a composite's children one at a
  time in the existing stack order (topological order over `Depends On`, ties in `## Subtasks`
  row order, `workflows/spec-run.md:162-163`), and IF a child's atomic validation returns NEEDS
  WORK, its `/pae-tests` reports `atomic-tests: failed`, or the child is blocked, THEN stop
  the run as today (`workflows/spec-run.md:297-299`), setting the attempt `failed` (`needs-work` or `tests-failed`) or `blocked` (`blocker`)
  and writing `blocker: <blocked_reason>: <one-line detail>` in the child block.
- **REQ-54 Repair policy.** WHERE spec 019's repair policy is active for the run (17
  REQ-01 not applying), IF a child's atomic validation returns NEEDS WORK, THEN THE SYSTEM [root]
  SHALL run 019's repair loop (019 C-5) for that child instead of the REQ-51 stop: the attempt
  stays `dispatched` and records 019's episode in `repair_episode`; a child whose attempt is
  `merged`, `accepted` or `cleaned` is never repaired (integration failures follow REQ-35/REQ-45
  and the composite-validation fix siblings of E-31,
  `workflows/phase-composite-validation.md:89-143`); merged siblings are not touched; an
  accepted repair sets the attempt `validated` and then follows REQ-07 and REQ-36 unchanged; and
  a repair loop that ends without acceptance applies the REQ-51 stop. Without the active policy, REQ-51 applies exactly as
  written.
- **REQ-50 Owner-cleared resume.** WHEN a run resumes a child whose latest attempt is `failed`
  or `blocked` and whose block `blocker:` the owner has set to `none`, THE SYSTEM [root] SHALL,
  if `reconcile` returns `none` for it (after any `record-tip` or `record-composite-tip`), switch
  the root worktree to the child branch (C-2), set the attempt back to `dispatched` and restart it with
  fresh agents in the root worktree at the stage the DM-3 resume table gives for its
  `blocked_reason`; while `blocker:` is not `none` the attempt stays as
  it is.

### Recovery, migration, measurement

- **REQ-13 Journal and reconciliation.** WHEN `/spec-run` resumes a `per-composite` task, THE
  SYSTEM [root] SHALL validate the composite journal and reconcile every attempt against the
  repository with the C-3 `reconcile` table (running the helper when it is available, otherwise
  applying the same table itself) before any new git operation, and SHALL then take, for each
  attempt, exactly the root action C-3 → Root actions gives for the resulting action.
- **REQ-66 Missing journal.** IF `/spec-run` resumes a `per-composite` task whose journal is
  absent, THEN THE SYSTEM [root] SHALL stop with `**stop**: "Composite journal missing for
  <task>; inspect the composite branches before resuming."` when any composite block records
  `branch:` and the Execution phase is not complete, and SHALL otherwise continue without a
  journal (no composite started yet, or REQ-47 deleted it after Execution), deleting no branch.
- **REQ-42 Atomic journal write.** WHEN the root changes the journal, THE SYSTEM [root] SHALL
  write the complete new document to `<journal>.tmp` in the same directory and rename it over
  the journal, writing the stage that precedes a git operation before running that operation.
- **REQ-16 Branch model selection.** WHEN `/spec-run` reaches Step 3 for a task whose
  `state.md` has no `branch_model:`, THE SYSTEM [root] SHALL write `branch_model: per-leaf` if
  any block already records `branch:`, otherwise `branch_model: per-composite`, and never change
  an existing value.
- **REQ-34 Restack.** WHEN `/restack` runs on a `per-composite` task, THE SYSTEM [`/restack`]
  SHALL treat only composite blocks and top-level leaf blocks with `branch:` as stack branches,
  skip child blocks, record a replayed composite branch's new own-range commits in its
  `commits:` as for any branch, append to every child block of that composite the note
  `restack <date>: merge history linearized; child commit and merge hashes superseded`, and
  report that the composite's merge commits were linearized.
- **REQ-37 Promotion.** WHEN a leaf with a recorded `branch:` is promoted to a composite by the
  approved Composite Promotion Protocol in a `per-composite` task, THE SYSTEM [root] SHALL keep
  that branch, its `base_branch:`, `base_commit:` and `commits:` as the composite block's git
  fields, write (creating the journal when absent) a composite object with those `branch`,
  `base_branch` and `base_commit` values and `tip` = the branch's current tip before the first
  child starts, and start its children from that tip.

## Data Model

### DM-1 Task `state.md` top-of-file field (new)

`branch_model: per-leaf | per-composite`, placed after `flow:`. Written once by `/spec-run`
Step 3 (REQ-16). Reader rule (backward compatibility, P3): absent and any block with `branch:`
→ `per-leaf`; absent and no `branch:` → not yet chosen; ordinary manual runs never write or
require it. Canonical definition goes in `rules/workflow-globals.md → ## Canonical Status
Formats`.

### DM-2 Progress block fields (existing blocks, additive fields)

| Block | Field | Type | Writer | Rule |
|---|---|---|---|---|
| Composite | `branch:` | branch name | root (REQ-06, REQ-37) | Written once; only `/restack` rewrites |
| Composite | `base_branch:` | branch name | root | Previous top-level stack branch or default branch |
| Composite | `base_commit:` | 40/64-hex SHA | root | Written once, never recomputed |
| Composite | `commits:` | `<sha> merge: <child domain name>` (a label of this field only, not a git-flow commit type; the commit's subject is the REQ-07 message) and `<sha> chore: update task records`, comma-separated | root (REQ-39, REQ-43) | Appended per commit the root makes on the composite branch, at the next record write |
| Composite | `pr:` | `#N draft \| #N ready \| none` | root (REQ-08) | — |
| Child | `branch:` | child branch of the attempt | root (REQ-30) | Written when the attempt starts |
| Child | `base_branch:` | composite branch | root | — |
| Child | `base_commit:` | SHA | root | The latest attempt's base |
| Child | `commits:` | existing format | root | Commits of the attempt: the `test:` and implementation SHAs are appended on the child branch as `/spec-run` Step 4.2 does today (`workflows/spec-run.md:263`, `:271-272`) and are committed by the point (a) record commit; the point (a) record commit's own SHA is appended after the merge commit exists (E-43); the last listed commit is the attempt `tip`, which spec 012 SA-10 compares with the merge's second parent |
| Child | `merge_commit:` | SHA or `none` | root (REQ-39) | New field; `none` until accepted |
| Child | `pr:` | always `none` | root | — |
| Child | `notes:` line `tdd: command — <command>` | text | root (REQ-46) | Protected `tdd:` line; absent for `n-a` and legacy |

All new fields are protected like the existing git fields (`rules/workflow-globals.md:233-236`)
and listed in `rules/workflow-reference.md → ## Protected Sections Contract`. Status
vocabularies are unchanged; `rollup` and `integration-validation` keep their meaning.

### DM-3 Composite journal (new)

Lifecycle: the root creates the journal (REQ-42 write) immediately before running the first
REQ-06 command of the task, or at the REQ-37 promotion write, and deletes it per REQ-47. An absent journal file means "no
composite started": `reconcile` treats it as empty, `validate` reports `journal-missing`, and
REQ-66 decides a resume.

Path `<git-common-dir>/orchestrail-composite/<sha256 hex of UTF-8 canonical task_path>.json`;
regular file ≤ 1 MiB, strict UTF-8 JSON without duplicate keys or NaN/Infinity. Every SHA is a
full lowercase 40- or 64-hex object name; every timestamp is `YYYY-MM-DDTHH:MM:SSZ` copied from
`date -u +%Y-%m-%dT%H:%M:%SZ` output or `null`.

```json
{
  "schema_version": 1,
  "repository_common_dir": "/abs/canonical/.git",
  "task_path": "/abs/canonical/.ai/tasks/todo/task-NN-slug",
  "branch_model": "per-composite",
  "composites": [
    {
      "id": "T-03",
      "branch": "feat/oauth-login",
      "base_branch": "feat/oauth-token-service",
      "base_commit": "<sha>",
      "tip": "<sha>",
      "pending_commits": [],
      "children": [
        {
          "id": "T-03a",
          "attempts": [
            {
              "attempt": 1,
              "branch": "feat/oauth-login--token-route",
              "base_commit": "<sha>",
              "tip": "<sha>",
              "stage": "dispatched",
              "test_mode": "red",
              "test_command": "python3 -m pytest tests/test_token_route.py",
              "pending_commits": [],
              "untracked_at_dispatch": [],
              "dispatched_at": "2026-11-20T10:00:00Z",
              "ended_at": null,
              "merge": null,
              "cleanup": null,
              "blocked_reason": null
            }
          ]
        }
      ]
    }
  ]
}
```

| Object | Field | Type | Required | Writer | Value under this spec |
|---|---|---|---|---|---|
| journal | `schema_version` | integer `1` | yes | root | `1` |
| journal | `repository_common_dir`, `task_path` | absolute canonical path | yes | root | — |
| journal | `branch_model` | `per-composite` | yes | root | — |
| journal | `composites` | list | yes | root | One object per started composite |
| composite | `id`, `branch`, `base_branch`, `base_commit`, `tip` | text / SHA | yes | root (REQ-06, REQ-39, REQ-43) | `tip` = the composite branch SHA after the root's last commit or merge on it |
| composite | `children` | list | yes | root | — |
| composite | `pending_commits` | list of `<sha> <subject>` | yes | root (REQ-43, `record-composite-tip`) | Commits on the composite branch not yet copied to the composite block's `commits:`; written before `tip` moves past them and emptied by the next record write |
| child | `id`, `attempts` | text / list | yes | root | Exactly one attempt |
| attempt | `attempt` | integer ≥ 1 | yes | root | `1` |
| attempt | `branch`, `base_commit` | text / SHA | yes | root (REQ-30) | — |
| attempt | `tip` | SHA | yes | root (REQ-30, REQ-65) | `base_commit` until the first commit |
| attempt | `pending_commits` | list of `<sha> <subject>` | yes | root (REQ-43, `record-tip`) | Commits on the child branch not yet copied to the child block's `commits:`; same rule as the composite field |
| attempt | `stage` | stage vocabulary | yes | root (REQ-42) | — |
| attempt | `test_mode` | `red \| pinned \| n-a \| legacy` | yes | root | — |
| attempt | `test_command` | text or null | yes | root (REQ-46) | null only for `n-a` and `legacy` |
| attempt | `untracked_at_dispatch` | sorted list of repository paths | yes | root | `[]` while `branched`; the untracked, non-ignored paths outside `.ai/` when the attempt was dispatched, replaced at each REQ-50 or REQ-64 restart (`git status --porcelain=v1 -z --untracked-files=all`); preflight permits untracked files (`rules/git-flow.md:22-23`) |
| attempt | `dispatched_at`, `ended_at` | timestamp or null | yes | root | `ended_at` set when the attempt first reaches `accepted`, `failed`, `blocked`, `check-failed` or `conflict`, cleared on REQ-50/REQ-64 restart |
| attempt | `merge` | object or null | yes | root (REQ-07, REQ-35, REQ-36, REQ-39) | `{"expected_target": <composite tip before merge>, "commit": <sha\|null>, "tree": <sha\|null>, "conflict_paths": [...], "checks": "pass\|fail\|null", "failed_command": <text\|null>, "check_failures": <int>}`; `check_failures` counts failed REQ-03/REQ-45 runs |
| attempt | `cleanup` | object or null | yes | root (REQ-31) | `{"worktree_removed": false, "branch_deleted": bool, "failure": <text\|null>}` |
| attempt | `blocked_reason` | null or reason | yes | root | `needs-work`, `tests-failed`, `blocker` or `uncommitted-work` |
| attempt | `repair_episode` | null or spec 019 `episode_id` | no | root (REQ-54) | Written only while 019's repair policy is active; absence reads as null |

`validate` rejects a missing required field, a wrong type, an unknown `stage` or
`blocked_reason` value, or a field not named by this table.

**Stages (journal vocabulary, one anchored line in the workflow):** `branched` | `dispatched` |
`validated` | `merge-intent` | `merged` | `accepted` | `cleaned` | `check-failed` | `conflict` |
`failed` | `blocked`.

| From | To | Trigger |
|---|---|---|
| — | `branched` | REQ-30 branch created; written before the git command per REQ-42 |
| `branched` | `dispatched` | First agent spawned |
| `dispatched` | `validated` | Atomic validation `complete` applied to state |
| `dispatched` | `failed` | NEEDS WORK (`needs-work`) or `atomic-tests: failed` (`tests-failed`) |
| `dispatched` | `blocked` | Worker blocker (`blocker`) or the `inspect-worker` root action (`uncommitted-work`) |
| `failed` / `blocked` | `dispatched` | REQ-50 owner-cleared resume |
| `validated` | `merge-intent` | `merge.expected_target` recorded before `git merge` |
| `merge-intent` | `merged` | Merge commit created; `merge.commit` and `merge.tree` recorded |
| `merge-intent` | `conflict` | REQ-36 after `git merge --abort` |
| `conflict` | `dispatched` | REQ-64 owner-cleared conflict |
| `merged` | `accepted` | REQ-03 pass and REQ-39 state recorded |
| `merged` | `check-failed` | REQ-35 |
| `check-failed` | `accepted` | REQ-45 rerun passes |
| `accepted` | `cleaned` | REQ-31 deletion done |

Terminal: `cleaned`. `accepted` with a cleanup failure stays `accepted`.

Resume stage after an owner-cleared `blocker:` (REQ-50):

| `blocked_reason` | Restart at |
|---|---|
| `needs-work` | Atomic validation, fresh agents, on the current child tip (owner fixes, if any, are commits on the child branch) |
| `tests-failed` | `/pae-tests` |
| `uncommitted-work`, `blocker` | The first workflow after the last root checkpoint commit (`/pae-tests` when there is none) |

### Migration impact

No existing file is migrated. Tasks with recorded per-leaf branches stay `per-leaf` (REQ-16).
The journal lives only in the git common directory and is never committed.

## Contracts & Interfaces

### C-1 `/spec-run` invocation (changed)

`/spec-run <path-to-spec> [--allow-pr] [--dry-run]` — the invocation is unchanged; this spec
adds no flag. Step changes:

| Step | Change |
|---|---|
| Step 0 | The existing clean-tree gate runs first, unchanged (`workflows/spec-run.md:66-69`); then, for a `per-composite` task, validate the journal (REQ-66) and run `reconcile` and its root actions (REQ-13, C-3) before any other action |
| Step 3 | Write `branch_model:` (REQ-16); the stack plan prints a composite as one stack entry with its children indented as temporary branches |
| Step 4 | Composite: REQ-44, REQ-06, then children one at a time (REQ-51) per REQ-30/REQ-07/REQ-03/REQ-39/REQ-43/REQ-31; the existing one-Implementer two-checkpoint handoff runs on the checked-out child branch and the Validator receives `git diff <attempt base_commit>..<child tip>` |
| Step 4.4 | Replaced: composite validation per REQ-12 on `composite-ready`; a fix sibling per REQ-67 |
| Step 4.5 | PRs only for top-level leaves and composites (REQ-08) |
| Step 8 | Per composite: children, merge commits, child-branch disposition (deleted, or kept with reason); REQ-47 journal deletion |
| Never list | "Never deletes a branch" becomes "Never deletes a branch except the verified temporary child-branch deletion of cleanup"; the existing execution-order restriction remains unchanged |

### C-2 Git command forms used by the root (each its own Bash call)

| Purpose | Command |
|---|---|
| Composite branch | `git switch -c <composite-branch> <previous reviewed tip sha>` |
| Child branch in the root worktree | `git switch -c <child-branch> <composite tip sha>` |
| Existing child branch (REQ-50, REQ-64 restart) | `git switch <child-branch>` |
| Task-record commit (REQ-43) | `git add <explicit .ai paths>` then `git commit -m "chore: update task records"` |
| Return to composite | `git switch <composite-branch>` |
| Integrate | `git merge --no-ff -m "Merge branch '<child-branch>' into <composite-branch>" <child-branch>` |
| Abort conflict | `git merge --abort` |
| Delete child branch | `git update-ref -d refs/heads/<child-branch> <attempt tip sha>` |

Forbidden in this flow: `git branch -D`, `git worktree remove --force`, `git reset --hard`,
`git clean`, `git stash`, `git rebase`, any push of a child branch. Policy: each git write is its
own Bash call; the hook's same-command state mark denies some, not all, later reads in the same
command (`harness/claude/capabilities.md` X15), so the policy does not rely on it.

### C-3 `scripts/composite_run.py` (new, optional helper)

Invoked as `python3 "$ORCHESTRAIL_HOME/scripts/composite_run.py"`, like the logging helper
(`workflows/spec-run.md:31`); it is run from the source root, not deployed by `scripts/sync.sh`.
Optional: when the helper is unavailable (missing, or `python3` older than 3.11), the root
applies the `reconcile` table and the `post-merge-commands` list itself (A-12). Python ≥ 3.11, standard library only, one file. It never writes a file, never runs a git command
that writes, and never spawns a model. Read-only git it may run: `diff`, `status`,
`rev-parse`, `merge-base --is-ancestor`, `worktree list --porcelain`, `cat-file`. Output: one
JSON object on stdout with sorted keys. Exit 0 = result printed; exit 2 = invalid input or git
read failure, stdout empty, stderr lines `composite-run: <code>: <detail>` (under Python older
than 3.11 every subcommand exits 2 with `composite-run: usage: python 3.11 or newer required`) with codes
`usage`, `journal-missing`, `journal-invalid`, `plan-invalid`, `unknown-composite`,
`unknown-child`, `git-failed`.

| Subcommand | Arguments | Result |
|---|---|---|
| `--version` | — | `{"version": "1"}` |
| `validate` | `--journal P` | `{"valid": true, "attempts": n}`; any DM-3 violation → exit 2 `journal-invalid` |
| `reconcile` | `--journal J --repo D` | `{"attempts": [{"child", "attempt", "stage", "action", "detail"}]}` |
| `post-merge-commands` | `--plan P --journal J --composite ID --child ID` | `{"commands": [{"child", "command"}]}`: the REQ-03 list in `## Subtasks` row order |

`reconcile` actions per latest attempt; the first matching row wins (rows marked "any" are
evaluated in table position):

| Journal stage | Observation | Action |
|---|---|---|
| `branched` | branch absent | `redo-branch` |
| `dispatched` | the root worktree has an untracked file outside `.ai/` that the repository does not ignore and that is not in the attempt's `untracked_at_dispatch` (tracked changes are stopped earlier by the clean-tree gate, `workflows/spec-run.md:66-69`) | `inspect-worker` |
| `branched`/`dispatched`/`failed`/`blocked`/`conflict` | branch tip ≠ journal `tip` and the journal tip is an ancestor (for example owner fix commits) | `record-tip` |
| `merge-intent` | composite tip = `expected_target`, no `MERGE_HEAD` | `redo-merge-precheck` |
| `merge-intent` | composite tip is a merge commit with parents (`expected_target`, `tip`) | `record-merged` |
| `merge-intent`/`merged` | `MERGE_HEAD` present in the root worktree | `stop-merge-in-progress` |
| `merged` | composite tip contains `merge.commit` | `run-post-merge-checks` |
| `accepted` | `cleanup.failure` is set | `none` |
| `accepted` | branch still present | `cleanup-pending` |
| any | composite branch tip ≠ journal composite `tip` but descends from it | `record-composite-tip` |
| any | composite branch does not contain an accepted attempt's `merge.commit`, or a recorded ref is at a commit no row above explains | `stop-mismatch` |
| otherwise | — | `none` |

Before the attempt rows, each composite of the journal is checked: a composite whose `branch`
does not exist (an interruption between the journal write and REQ-06's `git switch -c`) gives
the composite action `redo-composite-branch`.

Root actions (REQ-13), at an effective limit of 1:

| Action | Root action |
|---|---|
| `redo-composite-branch` | Run REQ-06's `git switch -c` again from the recorded composite `base_commit` |
| `redo-branch` | Run REQ-30's `git switch -c` again from the recorded attempt `base_commit` |
| `record-tip` | Write the branch tip as the attempt `tip` (REQ-42), add the commits between the old and the new tip (`git rev-list --first-parent --reverse <old>..<new>`) to the attempt's `pending_commits` in the same journal write, then evaluate the table again for that attempt |
| `inspect-worker` | Set the attempt `blocked` with `uncommitted-work`, write `blocker: uncommitted-work: <paths>`, make the REQ-43 point (d) record commit and stop; the owner commits or removes the files and clears `blocker:` |
| `redo-merge-precheck` | Confirm that the composite tip equals `merge.expected_target` and the child branch tip equals the attempt `tip`, then run REQ-07; on a mismatch act as for `stop-mismatch` |
| `record-merged` | Record `merge.commit` and `merge.tree`, set `merged`, then run REQ-03 |
| `stop-merge-in-progress` | Stop with `**stop**: "A merge is in progress on <composite-branch>; abort or finish it, then resume."` |
| `run-post-merge-checks` | Run REQ-03 |
| `cleanup-pending` | Run REQ-31 |
| `record-composite-tip` | Write the composite branch tip as the composite `tip`, add the commits between the old and the new tip (first parent) to the composite's `pending_commits` in the same journal write, then evaluate the table again for every attempt of that composite |
| `stop-mismatch` | Stop with `**stop**: "Recorded state of <ref> does not match the repository; inspect it before resuming."` |
| `none` | Continue from the stage: `branched` → dispatch the Implementer; `dispatched` → resume the child as `/spec-run` resumes a leaf today; `validated` → REQ-07; `failed`/`blocked` → REQ-50, `conflict` → REQ-64, `check-failed` → REQ-45 when the owner cleared `blocker:`, otherwise stop and report the blocker; `accepted` with a cleanup failure, `cleaned` → nothing |

### C-4 git-rails `DELETION_VERIFIER` (changed)

`hooks/git_rails.py` replaces the default `DELETION_VERIFIER` with a composite-journal verifier
of the existing signature `(DeletionRequest, Invocation, Context) → DeletionVerdict`. It returns
`exception=True` only when all hold, checked in this order; otherwise `exception=False` with the
named failure:

| # | Check | Failure text |
|---|---|---|
| 1 | `request.forced` is false, exactly one ref, it starts with `refs/heads/`, and its expected value is a full SHA (the `update-ref -d <ref> <sha>` form) | `unsupported-deletion-form` |
| 2 | `state_changed(invocation)` is false | `state-changed` |
| 3 | Every regular file directly in `<common-dir>/orchestrail-composite/` (subdirectories and `.tmp` files ignored) named 64 hex + `.json` is a usable journal (DM-3 schema, size, encoding, name = SHA-256 of `task_path`, `repository_common_dir` = this common dir), using the restack journal reader rules | `composite-journal-unusable` |
| 4 | Exactly one journal holds exactly one attempt whose `branch` equals the ref's branch name | `no-matching-attempt` |
| 5 | That attempt's stage is `accepted` and `merge.commit` is non-null | `not-accepted` |
| 6 | Expected SHA = attempt `tip` = current value of the ref | `tip-mismatch` |
| 7 | `<merge.commit>^2` = `tip` and `merge.commit` is an ancestor of the current composite branch tip | `not-integrated` |
| 8 | No worktree in `git worktree list --porcelain` has the branch checked out | `checked-out` |

Every git read uses the existing sanitized read layer and budgets. When the verifier refuses, the
decision stays `ask` with the shipped reason code and rule id (R22/R23). `git branch -d`,
`-D` and remote-tracking deletions always refuse at check 1. The test
`test_default_verifier_is_the_no_exception_implementation` (`tests/git-rails.sh:2801-2802`) is
replaced by one asserting the new default, and `no_exception_verifier` stays importable.

### C-5 Contract-file changes (canonical first, then readers)

This table is canonical for the composite branch model.

| File | Change |
|---|---|
| `rules/git-flow.md` | `## Branch model`: per-composite paragraph, child branches and their naming; merge-commit message form; `## Commits`: the three record-commit points of REQ-43; `## Pull requests`: composite PR, body and a fenced composite PR-body example; `## Safety rails`: the deletion row's Policy cell becomes exactly "**Owner approval required, except the verified temporary child-branch deletion below, which is allowed only inside `/spec-run` cleanup.** Deleting any other branch on the agent's own initiative is forbidden; branches are deleted by the human when merging", a new row "`git update-ref -d refs/heads/<child> <sha>` of a temporary child branch the composite journal verifies" with Policy "Only inside `/spec-run` cleanup" and Enforcement `hook: allow with composite journal`, which is added to the anchored Enforcement vocabulary line; `## Recorded state`: new fields; restack linearization note |
| `rules/orchestration.md` | `## Roles`: "Four roles" becomes "Five roles", adding the composite validation agent (Actors & Roles) (`:20`); the shared-file row for `/phase-composite-validation` (`:115`) names the root's dispatch on `composite-ready` in a `per-composite` task and keeps `/pav-close` step 5 for `per-leaf` tasks; the sequential statements are unchanged |
| `rules/workflow-globals.md` | `branch_model:`; composite and child fields; protected fields |
| `rules/workflow-reference.md` | Protected Sections Contract additions; the canonical leaf block (`:205-224`) gains `merge_commit:` for child blocks |
| `rules/tdd.md` | None; REQ-41 cites it unchanged |
| `workflows/spec-run.md` | C-1, C-2, the Step 4 composite procedure, journal, reconcile root actions, REQ-43 record points, Never list |
| `workflows/pav-close.md`, `workflows/phase-composite-validation.md` | REQ-40; REQ-12 surface; REQ-67; `/spec-run` becomes the per-composite invoker |
| `workflows/pae-tests.md` | REQ-46 command line in the report and notes |
| `workflows/restack.md` | REQ-34 |
| `scripts/validate-contracts.sh` | No new check. Changed expressions, each a spec 011 DM-9 `contract_changes` entry with a `requirement` value `spec-024 REQ-NN` added under 011 REQ-69 and a DM-20 verdict row: `:5456` (Enforcement vocabulary line, REQ-32), `:5614` (deletion-row wording, REQ-31, REQ-32). Expressions that stay true with the new text: `:1454` (`workflows/pav-close.md` keeps its `call ./phase-composite-validation` line for `per-leaf` tasks and `workflows/spec-run.md` names the workflow without that call form), `:712`, `:977` (`^  base_commit:` in the canonical leaf block), `:1386` (the deletion row still contains "forbidden" and "only inside"), `:5617` (no reader keeps the old ban phrases). |
| `tests/validator-runtime-oracle.py` | Extend the closed `requirement` set with those `spec-024 REQ-NN` values (011 REQ-69), update `AMENDMENT_SHA256` and re-pin the source guard |
| `tests/git-rails.sh` | Replace the default-verifier test (C-4); re-pin the source guard per `tests/fixtures/validator-runtime/README.md` |
| `scripts/README.md` | List `composite_run.py`, `check-composite-branch-model.sh` and `check-composite-run.py` |
| `.ai/principles/domain.md` | Terms of `## Terminology`; Composite, Stack and Orchestrator rows |
| `tests/golden/cases/composite/reference/spec-run/` and `tests/expected/composite/spec-run/projection.json` (spec 012 DM-1) | Rebuilt by the change that delivers this spec, because new `/spec-run` tasks then record `per-composite` (REQ-16) and the pair exercises 012's `per-composite` SA-10/SA-11 rules at N = 1 (012 REQ-51) |
| `docs/USAGE.md`, `docs/SPEC-RUN-QUICKSTART.md`, `workflows/PIPELINE.md` | Composite branch model |
| `.ai/adr/NNNN-…` | One new ADR recording ADR-0005 Decision 1's amendment (one branch and one pull request per composite) as implemented, ADR-0004 Decision 1's fifth role (the composite validation agent), the optional helper (ADR-0001 implication) and the verified deletion exception to the git rails (ADR-0017). |

File and command names are the current ones. If spec 011's migration lands first, each change
applies to the file spec 011 gives that section: rule files become `<kind>-<subject>`
(`rules/git-flow.md` → `contract-git-flow`; the `workflow-reference` sections → their split
files such as `contract-state-files`; always-on content → `harness/<name>/always-on.md`), and
commands are renamed (ADR-0009 Decision 3, `.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:116-130`: `/phase-composite-validation` →
`composite-validation`, `/phase-atomic-execution` → `atomic-execution`,
`/phase-atomic-validation` → `atomic-validation`, child steps such as `/pae-tests` →
`atomic-execution-tests`).

## Non-Functional Requirements

| Id | Attribute | Target or standard | Verification |
|---|---|---|---|
| NFR-01 | Determinism | Identical helper inputs produce byte-identical stdout | Fixture runs each subcommand twice and compares bytes |
| NFR-02 | Hook budget | The verifier uses the existing git read layer: 2 s per read and the 5 s event budget (`hooks/git_rails.py` constants `GIT_READ_SECONDS` and `WALL_CLOCK_SECONDS`, `:3786`) | Fixture with a slow fake git sees `ask`/deny within the existing budget, as the shipped suite does for other verifiers |
| NFR-03 | Non-blocking telemetry | Logging failures never block (P9, `.ai/principles/architecture.md`) | Contract check that the workflow keeps the existing logging clause |
| NFR-05 | Compatibility | `per-leaf` tasks behave exactly as today (P3; README gate G4) | Contract check plus helper/hook fixtures with legacy blocks |
| NFR-06 | Portability | Helper requires Python ≥ 3.11 and git; Linux is the verified platform; no other platform claim | [H] fixture: the helper's version check, called with a patched `sys.version_info` of 3.10 (`unittest.mock`), exits 2 with `composite-run: usage: python 3.11 or newer required`; [C] `workflows/spec-run.md` states the root's fallback when the helper is unavailable |
| NFR-07 | Performance | N/A — no speedup, token or cost target (README gate G8; ADR-0009 Decision 5) | — |

## Edge Cases & Failure Modes

| # | Case | Expected behaviour | REQ |
|---|---|---|---|
| E-05 | Composite with one child | One child branch, one merge, composite validation, one PR | REQ-06, REQ-12 |
| E-11 | Clean merge but post-merge test fails | `check-failed`, composite `blocker:` set, run stops; after the owner fixes the cause (for example by an approved fix child or a commit of their own) and clears `blocker:`, the rerun decides | REQ-35, REQ-45 |
| E-17 | Interruption after `merge-intent`, before `git merge` | `redo-merge-precheck` | REQ-13 |
| E-18 | Interruption after merge commit, before checks | `record-merged` / `run-post-merge-checks`; no second merge | REQ-13 |
| E-19 | Interruption during conflicted merge (`MERGE_HEAD` present) | `stop-merge-in-progress`; owner aborts or resolves | REQ-13 |
| E-22 | Journal unreadable or invalid | Resume stops; hook asks for every child deletion | REQ-13, REQ-32 |
| E-23 | Child branch tip moved after acceptance | Verifier `tip-mismatch` → ask; root keeps the branch and reports | REQ-31, REQ-32 |
| E-25 | Owner rejects a hook ask on deletion | Final for that branch; keep it; report | REQ-31 |
| E-26 | Child branch name collides with an unowned branch | Preflight stops (`rules/git-flow.md:30-31`); resume uses the journal-owned branch only | REQ-30 |
| E-27 | Composite PR already exists on resume | Reuse it; update by pushing the composite branch; no second PR | REQ-08 |
| E-28 | `/restack` after the composite's predecessor is squash-merged | Replay composite branch with the verified form; merges linearized and reported; child blocks skipped | REQ-34 |
| E-29 | Resume of a task started before this change | `branch_model: per-leaf`; old behaviour throughout | REQ-16 |
| E-30 | Leaf promoted to composite mid-run | Its branch becomes the composite branch; the journal gains its composite object before the first child | REQ-37 |
| E-54 | Run stops with a `blocker:` in a repository that tracks `.ai/` | The stop write is committed (REQ-43 point (d)); the clean-tree gate passes on resume once the owner commits the cleared `blocker:` | REQ-43 |
| E-31 | Composite integration validation NEEDS WORK, fix sibling approved | The fix sibling runs as the next child (branch from the composite tip, normal cycle, merge); composite validation then runs again on the new tip | REQ-12, REQ-67 |
| E-35 | Empty composite (`children:` empty) or a child id without plan row or block | Stop before creating the composite branch | REQ-44 |
| E-39 | A leftover journal of another task records an attempt with the same child-branch name | Verifier check 4 fails → `ask`; root keeps the branch and reports | REQ-32 |
| E-43 | Validation deltas pending when the root switches back to the composite branch | Committed on the child branch as `chore: update task records` (REQ-43 point (a)); no tracked `.ai/` write until the merge commit exists, so git never refuses the switch and `state.md` changes on one side of the merge only (after a conflict stop, the owner order of REQ-64 keeps it so) | REQ-43 |
| E-46 | Records pending after a top-level leaf or composite is reviewed and its PR recorded | No record commit on that branch; the records carry over to the next stack branch and go into its first commit, as today | REQ-43 |
| E-49 | Owner clears `blocker:` after a merge conflict | Attempt back to `dispatched`, atomic validation on the current child tip, then the merge again | REQ-64 |
| E-50 | Resume with no journal while a composite block records `branch:` | Stop with the REQ-66 message; no branch is deleted | REQ-66 |
| E-51 | Interruption between the journal write and the composite branch's `git switch -c` | `redo-composite-branch` | REQ-13 |
| E-52 | Owner approves the hook ask on a child-branch deletion | The ref is gone; stage `cleaned` | REQ-31 |
| E-48 | Merge conflict with an effective limit of 1 (the composite branch changed outside the run) | `git merge --abort`, stage `conflict`, composite `blocker: conflict: <child>: <path>`, run stops; child branch kept | REQ-36, A-30 |

## Acceptance Criteria

Verification vehicles (test-first, written and observed failing before implementation):
**[C]** contract checks in a new standalone `scripts/check-composite-branch-model.sh` (shell
builtins, like `scripts/check-spec-draft.sh`): each [C] criterion names the exact sentence or
anchored line the check matches, and the check fails on the unchanged files; **[H]** helper and
hook fixtures in a new standalone `scripts/check-composite-run.py` (Python standard library,
`unittest`) using disposable git repositories, journals and plans; **[G]** the existing
`tests/git-rails.sh` (one replaced test, C-4); **[L]** an owner-approved live spec 012 run, never
part of ordinary validation. Agent behaviour that only a live run can show is covered by [C]
for the instruction and [L] for the behaviour. A quoted text in a [C] criterion is a literal:
the check finds it verbatim in the named file (Markdown emphasis and line wrapping aside), and
the check fails on the unchanged files.

- [ ] **AC-02** (REQ-03, REQ-35, REQ-45) [H][C] Given a fixture composite with children A and B
  `accepted` (commands `cmdA`, `cmdB`) and C `merged` (command `cmdC`), plus D with `n-a`, when
  `post-merge-commands --child C` runs, then it returns `cmdA`, `cmdB`, `cmdC` in row order and
  no entry for D; and [C] `workflows/spec-run.md` contains "A failing post-merge check keeps the
  merge commit, sets the attempt `check-failed`, writes the failing command and child to the
  composite `blocker:` and stops the run." and "On resume with `blocker: none`, rerun the
  post-merge commands on the composite tip; when every command exits 0, record the integration
  and set `accepted`; otherwise stop again."
- [ ] **AC-04** (REQ-06, REQ-07, REQ-30, REQ-39) [H][C] Given a disposable repository driven
  through the C-2 command forms for one composite with two sequential children, then the
  composite branch starts at the previous tip, each child branch starts at the composite tip
  recorded as its `base_commit`, each merge commit has first parent = previous composite tip and
  second parent = child tip, every `test:` commit precedes its `feat:` commit in history, and
  `validate` accepts the journal whose child `merge.commit` values equal those merge commits;
  and [C] `workflows/spec-run.md` contains each C-2 command form of this spec verbatim and "Record
  `merge_commit:` in the child block and the merge in the composite block's `commits:`, and only
  then set the journal stage `accepted`."
- [ ] **AC-05** (REQ-08, REQ-33) [C] Given the changed files, then `rules/git-flow.md` contains
  "Only composite branches and top-level leaf branches are pushed; child branches are never
  pushed." and "A composite gets one draft pull request whose base is the previous top-level
  stack branch." and a fenced composite PR-body example under `## Pull requests` with one
  stack-position line and one section per child naming its test level and `test:` commit, in
  which no `T-` is followed by a digit; and `workflows/spec-run.md` contains "Reuse the pull
  request recorded in the composite block's `pr:`."
- [ ] **AC-08** (REQ-12, REQ-40) [C] Given the changed files, then `workflows/pav-close.md`
  contains "In a `per-composite` task, return `composite-ready: <composite id>` instead of
  invoking `/phase-composite-validation`."; `workflows/spec-run.md` contains "On
  `composite-ready`, dispatch one fresh validation agent on the composite branch to run
  `/phase-composite-validation` once for the composite tip."; and
  `workflows/phase-composite-validation.md` contains
  "git diff --name-only <composite base_commit>..<composite tip> -- . ':(exclude).ai'".
- [ ] **AC-09** (REQ-13, REQ-42, REQ-65) [H][C] Given journals and repositories prepared at
  each interruption point (composite branch absent after the journal write, `branched` without
  branch, `dispatched` with the branch tip one commit past the journal `tip`, `dispatched` with
  a new untracked, non-ignored file outside `.ai/` in the root worktree, `merge-intent` before the merge,
  `merge-intent` after the merge commit, `MERGE_HEAD` present, `merged` before checks,
  `accepted` with branch present, composite tip advanced by a later commit, recorded merge
  missing from the composite branch), when `reconcile` runs, then it returns
  `redo-composite-branch`, `redo-branch`, `record-tip`, `inspect-worker`,
  `redo-merge-precheck`, `record-merged`, `stop-merge-in-progress`, `run-post-merge-checks`,
  `cleanup-pending`, `record-composite-tip` and `stop-mismatch` respectively; given an
  interruption after a `record-tip` journal write, the new commits are in the attempt's
  `pending_commits` and the next record write lists them in `commits:`; given an absent
  journal it returns no attempts and `validate` exits 2 with `journal-missing`; a
  `<journal>.tmp` sibling is ignored by the verifier; and [C] `workflows/spec-run.md` contains
  "Write the journal stage that precedes a git operation before running that operation.",
  "After each commit on a child branch, record its SHA as the attempt `tip` in the journal
  before the next git operation.", "Add a record commit's SHA to `pending_commits` in the
  journal before the next git operation." and one root-action line per action of C-3 → Root actions,
  each naming the action.
- [ ] **AC-11** (REQ-16) [C] Given the changed `rules/workflow-globals.md` and
  `workflows/spec-run.md`, then the first contains the anchored line
  `branch_model: per-leaf | per-composite` and the sentence "A missing `branch_model:` reads as
  `per-leaf` when any block records `branch:`", and the second contains "Never change an existing
  `branch_model:` value."
- [ ] **AC-12** (REQ-41) [C] Given the changed `workflows/spec-run.md`, then it contains "On a
  child branch, commit `test:` before the implementation commit for `red` and `pinned`, make one
  implementation commit for `n-a`, and keep the `pre-TDD task, TDD step skipped` note for a
  legacy in-progress block."
- [ ] **AC-19** (REQ-12) [C] Given the changed workflows, then `workflows/spec-run.md` contains
  "Composite validation runs once per composite tip." and "A composite reaches `reviewed` only
  when every child's latest attempt is `accepted` or `cleaned` and composite validation passed on
  its tip.", and its `## Step 5` section is byte-identical to that section at the delivery's base commit on
  `main` (the commit the delivery's first branch is cut from).
- [ ] **AC-23** (REQ-31, REQ-32) [H][G] Given a disposable registered project and a valid
  journal, when the hook evaluates `git update-ref -d refs/heads/<child> <tip>` for an
  `accepted`, merged, not-checked-out child, then it allows; each single violation of C-4 checks
  1–8 (including `git branch -d`, a wrong expected SHA, a forged attempt in a second journal, an
  unusable journal file, a merge commit not reachable from the composite branch, a checked-out
  branch) yields `ask` with R22/R23; the replaced default-verifier test passes; and `reconcile`
  returns `none` for an `accepted` attempt whose `cleanup.failure` is set; and [C]
  `workflows/spec-run.md` contains "Set the attempt `cleaned` when the child ref no longer exists
  after the deletion, also after an owner-approved ask; otherwise keep the branch and record the
  reason once."
- [ ] **AC-24** (REQ-34) [C] Given the changed `workflows/restack.md`, then it contains "In a
  `per-composite` task, skip child blocks; collect only composite blocks and top-level leaf
  blocks with `branch:`.", the note text `restack <date>: merge history linearized; child commit
  and merge hashes superseded`, and "Report that the composite's merge commits were
  linearized."
- [ ] **AC-25** (REQ-36) [H] Given two child branches that conflict textually, when the C-2
  merge, abort and journal update are applied, then the composite tip equals
  `merge.expected_target`, no `MERGE_HEAD` exists, the child branch tip is unchanged, and
  `validate` accepts the journal with stage `conflict` and the conflicting path; and [C] `workflows/spec-run.md` contains
  `blocker: conflict: <child id>: <first conflicting path>`, "After a merge conflict, run `git merge
  --abort`, keep the child branch and stop the run." and the C-2 `Integrate` and `Abort
  conflict` forms verbatim.
- [ ] **AC-26** (REQ-37) [H][C] Given a journal written after a promotion (a composite object
  whose `branch`, `base_branch`, `base_commit` equal the promoted leaf's and whose `tip` is its
  tip), `validate` accepts it and `reconcile` returns no `stop-mismatch`; and [C]
  `workflows/spec-run.md` contains "A leaf promoted to a composite keeps its `branch:`,
  `base_branch:`, `base_commit:` and `commits:` as the composite block's fields, and its children
  start from its current tip." and "Write the composite to the journal before its first child
  starts."
- [ ] **AC-27** (REQ-43) [C] Given the changed `rules/git-flow.md`, then `## Commits` contains
  "Commit pending tracked task records as `chore: update task records` on the child branch
  before switching to its composite branch, and write no tracked task record until the merge
  commit exists.", "Commit them on the composite branch after recording an accepted
  integration and before cutting the next child branch or dispatching composite validation.",
  "Commit them on the composite branch after applying the composite validation deltas." and
  "The switch that cuts the next stack branch makes no record commit."
- [ ] **AC-28** (REQ-44) [C] Given the changed `workflows/spec-run.md`, then it contains
  the REQ-44 stop message verbatim before any branch creation step.
- [ ] **AC-29** (REQ-46) [C] Given the changed files, then `workflows/pae-tests.md` contains
  "Report the exact command that observed the `red` or `pinned` result." and
  `workflows/spec-run.md` contains `tdd: command — <command>`.
- [ ] **AC-30** (REQ-47) [H] Given a journal where every attempt is `cleaned`,
  `reconcile` returns `none` for all; and [C] Step 8 of `workflows/spec-run.md` contains "Delete the
  composite journal after the Step 8 report when Execution is complete and every attempt is
  `cleaned`, after a record write that empties every `pending_commits` list."
- [ ] **AC-32** (REQ-50, REQ-51) [H][C] Given a journal whose child attempt is `failed` and a
  repository that matches it, `reconcile` returns `none`; given the same journal with one owner
  commit on the child branch, `reconcile` returns `record-tip` and, after the tip is recorded,
  `none`; and [C] `workflows/spec-run.md`
  contains `blocker: <blocked_reason>: <one-line detail>`, "Restart a `failed` or `blocked`
  attempt only after the owner has set `blocker:` to `none`." and the resume rows for
  `needs-work`, `tests-failed`, `blocker` and `uncommitted-work` of the DM-3 resume table.
- [ ] **AC-34** (REQ-51, REQ-43) [C] Given the changed `workflows/spec-run.md`, then it contains
  "Run a composite's children one at a time in the stack order.", "Stop the run when a child's
  atomic validation returns NEEDS WORK, its `/pae-tests` reports `atomic-tests: failed`, or the
  child is blocked." and the four sentences of AC-27, and "The next stack branch starts from the
  composite tip that is pushed."
- [ ] **AC-36** (REQ-53) [C] Given the changed `workflows/spec-run.md`, then, in a passage
  conditioned on spec 014's `packet` command, it contains `--role implementer`, `--role
  validator`, `--base-commit` and "When `packet` exits non-zero, dispatch without a packet."
- [ ] **AC-37** (REQ-54) [C] Given the changed `workflows/spec-run.md`, then it contains "Only
  when the repair policy is active, run the repair loop on a child's NEEDS WORK; never repair a
  `merged`, `accepted` or `cleaned` attempt; an accepted repair sets the attempt `validated`."
  and "Without the repair policy, NEEDS WORK stops the run."
- [ ] **AC-47** (REQ-64) [H][C] Given a journal whose attempt is `conflict`, a composite block
  `blocker: none` committed by the owner on the composite branch, and a child branch with one
  owner commit that merges the composite tip, when
  `reconcile` runs, then it returns `record-tip` and `record-composite-tip` and, after both tips
  are recorded and the commits appended to `commits:`, `none`; and [C]
  `workflows/spec-run.md` contains "When the owner has cleared `blocker:` after a merge conflict, set the attempt `dispatched`, run atomic
  validation again on the current child tip, then merge again."
- [ ] **AC-48** (REQ-43) [H] Given a disposable repository that tracks `.ai/` with a task
  `state.md`, when two children are driven through the C-2 forms and the REQ-43 record points
  (child records committed before each switch, composite records committed after each accepted
  integration), then no `git switch` or `git merge` is refused or conflicts, each merge changes
  `state.md` on one side only, and the final `state.md` lists each child's commits including its
  record commit and its `merge_commit:`; and given a merge conflict stop instead, the stop's
  `blocker:` is committed (point (d)), `git status --porcelain` is empty after the stop, and a
  switch to the child branch succeeds; and when the owner then commits the cleared `blocker:` on
  the composite branch and merges the composite tip into the child branch, the REQ-64 second
  merge succeeds without a conflict in `state.md`; and after a REQ-51 stop and a resume, the
  point (d) record commit's SHA is listed in the child block's `commits:` and the attempt's
  `pending_commits` is empty.
- [ ] **AC-49** (REQ-66) [H][C] Given a `per-composite` task whose composite block records
  `branch:` and whose journal is absent, then `validate` exits 2 with `journal-missing`; and [C]
  `workflows/spec-run.md` contains the REQ-66 stop message verbatim and "Without a journal and
  with no composite started, or after Execution is complete, continue and delete no branch."
- [ ] **AC-50** (REQ-67) [C] Given the changed workflows, then `workflows/spec-run.md` contains "A
  fix sibling runs as the next child; composite validation then runs again on the new composite
  tip."

## Traceability

| REQ | AC |
|---|---|
| REQ-03 | AC-02 |
| REQ-06 | AC-04 |
| REQ-07 | AC-04 |
| REQ-08 | AC-05 |
| REQ-12 | AC-08, AC-19 |
| REQ-13 | AC-09 |
| REQ-16 | AC-11 |
| REQ-30 | AC-04 |
| REQ-31 | AC-23 |
| REQ-32 | AC-23 |
| REQ-33 | AC-05 |
| REQ-34 | AC-24 |
| REQ-35 | AC-02 |
| REQ-36 | AC-25 |
| REQ-37 | AC-26 |
| REQ-39 | AC-04 |
| REQ-40 | AC-08 |
| REQ-41 | AC-12 |
| REQ-42 | AC-09 |
| REQ-43 | AC-27, AC-34, AC-48 |
| REQ-44 | AC-28 |
| REQ-45 | AC-02 |
| REQ-46 | AC-29 |
| REQ-47 | AC-30 |
| REQ-50 | AC-32 |
| REQ-51 | AC-32, AC-34 |
| REQ-53 | AC-36 |
| REQ-54 | AC-37 |
| REQ-64 | AC-47 |
| REQ-65 | AC-09 |
| REQ-66 | AC-49 |
| REQ-67 | AC-50 |

## Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|---|
| R-2 | Hand-written journal drifts from the schema | Resume stops; deletions ask | Medium | `validate` after every write (when the helper is available); atomic rename (REQ-42); hook treats unusable journals as no exception |
| R-3 | The journal is forged or edited to pass the hook | A non-integrated branch could be deleted | Low | Outside the threat model as for the restack journal (`harness/claude/capabilities.md` X8); check 7 still requires reachability of the merge commit, so only fully integrated tips are deletable |
| R-4 | Post-merge checks are too narrow to catch a semantic interface break | Integration defect reaches composite validation | Medium | Composite validation on the final tree (REQ-12); spec 017 may widen the check set later |
| R-5 | `/restack` linearizes composite merge history | Reviewers lose the merge structure after a restack | Medium when predecessors are squash-merged | Reported (REQ-34); per-child test-first order survives (observed 2026-11-13, see Assumptions A-14); Q-02 |
| R-6 | Changing `tests/git-rails.sh` and `scripts/validate-contracts.sh:5614` disturbs the pinned source-guard inventory | Validator fails until re-pinned | High | Follow `tests/fixtures/validator-runtime/README.md` re-pin procedure in the same change; add no new test program under `tests/`; new or changed `.py`/`.sh` files among the spec 012 golden fixtures listed in this spec's C-5 are re-pinned by the same procedure |
| R-8 | Spec 012 structural assertions SA-10/SA-11 assume per-leaf stacking | Golden cases fail for `per-composite` runs | High once implemented | Adopted by 012 REQ-51 (DM-3 SA-10/SA-11 `per-composite` rules) from the facts in Notes → Follow-up changes |

## Assumptions

- A-03 | Does the per-composite model apply at N = 1 | Resolved: yes, for every new `/spec-run` task | Source: ADR-0009 Decision 4 | Reversible: yes
- A-04 | How legacy tasks are recognised | Resolved: `branch_model:` field written at Step 3; absent field with any recorded `branch:` reads as `per-leaf` | Source: P3 additive contracts (`.ai/principles/architecture.md`); original REQ-16 | Reversible: yes
- A-05 | Where child work happens at N = 1 | Resolved: on the child branch checked out in the root worktree, no worktree | Source: the sequential branch model | Reversible: yes
- A-07 | Merge then check, or check then commit | Resolved: commit-first `--no-ff` merge, then post-merge checks, with distinct `merged` and `accepted` stages | Source: original §9.3 permits this with distinct journal stages; smallest reversible choice (no `--no-commit` intermediate state to recover) | Reversible: yes
- A-08 | Merge commit message | Resolved: `Merge branch '<child-branch>' into <composite-branch>` | Source: git's standard merge message shape; branch names are permitted content (`rules/git-flow.md:149-150`); best practice | Reversible: yes
- A-09 | Which post-merge checks run | Resolved: the recorded test command of every accepted child plus the merged child | Source: original §9.3 step 7 ("affected deterministic checks"); smallest deterministic set until spec 017 | Reversible: yes
- A-28 | Check receipts on merged results | Resolved: the REQ-03 post-merge commands always run and never consult a receipt. Once spec 017 is delivered, its receipts are bound to content and worktree root, never to branch names or commits; a receipt from a child worktree is never reused for the merged composite tree (the worktree root is one of 017's inputs), and only the checks of the REQ-12 composite review, run in the root worktree, may reuse a receipt, when 017's reuse conditions hold (017 REQ-05); that review always runs at scope `full-integration` (017 REQ-15) | Source: spec 017 REQ-05, REQ-15 | Reversible: yes
- A-11 | Deletion form | Resolved: only `git update-ref -d refs/heads/<b> <sha>` | Source: completed spec 007 §8.7 | Reversible: yes
- A-12 | Deterministic decisions and their tests | Resolved: an optional stdlib helper `$ORCHESTRAIL_HOME/scripts/composite_run.py`, located like the logging helper; when the helper is unavailable the root applies the `reconcile` table itself, so the sequential path needs no helper | Source: README gates G4/G5/G6 (`.ai/specs/README.md` → "Shared acceptance gates"); ADR-0001 implications (a run-time script needs its own ADR) | Reversible: yes
- A-13 | Where new tests live | Resolved: standalone `scripts/check-composite-branch-model.sh` and `scripts/check-composite-run.py`; no new test program under `tests/` (the spec 012 golden reference and case entry listed in this spec's C-5 are fixtures, re-pinned per `tests/fixtures/validator-runtime/README.md` → "Maintaining the nested source guard" (steps 1–5) when they hold `.py`/`.sh` files); one existing test in `tests/git-rails.sh` replaced | Source: ADR-0019 Decision 3 (`.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:68-80`); source-guard README | Reversible: yes
- A-14 | `/restack` and merge commits | Resolved: keep the verified replay form; merge commits are linearized and reported | Source: `workflows/restack.md:91-98` exact form; disposable-repository observation on 2026-11-13 (git 2.53.0): `git rebase --onto` of a branch with two `--no-ff` merges replayed `test: a`, `feat: a`, `test: b`, `feat: b` in order and dropped the merges | Reversible: yes
- A-18 | Dependence on specs 014, 015, 017, 019 not yet delivered | Resolved: before each is delivered, workers bootstrap context themselves (existing rule), deltas use the existing report route, checks are those of REQ-03, and no repair attempt is made (NEEDS WORK stops per REQ-51). Once delivered: 014 → the root builds packets per REQ-53 (014 C-8); 017 → receipts per A-28; 019 → repair per REQ-54 when its policy is passed | Source: README prerequisites row for 024 (`.ai/specs/README.md` → "Dependency order"); G4 conservative path; peer contracts named | Reversible: yes
- A-19 | Telemetry | Resolved: no new run-log fields and no measurement in this spec | Source: spec 003/05 own the run-log contract; P9 (durations never model-written) | Reversible: yes
- A-21 | `/restack` classification of a composite branch | Resolved: unchanged; `git cherry` lists no merge commits, so the own range classifies by its child commits | Source: disposable-repository observation on 2026-11-13 (git 2.53.0): after squash-merging a composite branch with one `--no-ff` merge, `git cherry -v main <tip> <base>` printed only `- … test: a` | Reversible: yes
- A-24 | Commits of tracked task records | Resolved: as `chore: update task records` at the three REQ-43 triggers, at every N; otherwise with the root's next commit (existing rule) | Source: `rules/git-flow.md:156-165`; `workflows/spec-run.md:66-69` (dirty tracked bookkeeping stops a resume) | Reversible: yes
- A-25 | Remedy after `check-failed`, NEEDS WORK or a block | Resolved: the run stops; the owner fixes the cause and clears `blocker:`; the resumed run reruns the checks (REQ-45) or continues the attempt (REQ-50) | Source: `workflows/spec-run.md:297-299` (NEEDS WORK stops the run; branch and commits stay) | Reversible: yes
- A-30 | Merge conflict when the effective limit is 1 (added 2026-11-16 at the split) | Resolved: abort, record stage `conflict`, set the composite block `blocker:`, stop the run; the owner resolves the cause and clears `blocker:` as A-25 describes. At an effective limit of 1 the child branch starts at the composite tip and no sibling merges in between, so a conflict means the composite branch changed outside the run | Source: original §10 (preserve work, never resolve a conflict automatically); A-25 remedy; smallest reversible choice | Reversible: yes
- A-31 | Resolving a conflict at an effective limit of 1 (2026-11-16) | Resolved: the owner resolves by commits on the child branch; the attempt is revalidated on its new tip before the merge is retried | Source: original §10 (preserve work, never resolve automatically); REQ-50 restart pattern | Reversible: yes
- A-32 | Write order of tracked task records (2026-11-16) | Resolved: four record-commit points (point (d) for stops; the owner commits a cleared `blocker:`) and no tracked write between the child's record commit and the merge, so the merge changes `state.md` on one side only | Source: git refuses a switch that would overwrite a modified tracked file and a two-sided change conflicts; `rules/git-flow.md:156-165` | Reversible: yes
- A-33 | Resume without a journal (2026-11-16) | Resolved: stop when a composite branch exists and Execution is incomplete; continue without deleting branches otherwise | Source: REQ-47 deletes the journal after Execution; smallest conservative choice | Reversible: yes
- A-34 | Hook ask on a deletion (2026-11-16) | Resolved: the root pre-checks C-4 and judges the outcome by whether the ref still exists, so an owner-approved ask counts as done | Source: `rules/git-flow.md:228` (owner approval); the hook's ask is a permission prompt | Reversible: yes
- A-20 | Composite validation trigger | Resolved: `/pav-close` returns `composite-ready`; the root dispatches a fresh validation agent | Source: original REQ-12 and §9.4; `rules/orchestration.md:115` already routes its writes through the root | Reversible: yes

## Decisions

- D-02 | A child branch name that collides with an existing branch the journal does not own stops preflight; collisions between two children's slugs are refined from their Goals | Overrides: none (original §8.1 named both remedies; `rules/git-flow.md:30-31`, `:69-71` decide which applies where) | Rationale: an existing unowned branch is never reused | Follow-up: none

## Clarifications

### Session 2026-11-13

- N/A — auto mode; no question was asked. Every resolved gap is recorded under Assumptions.

### Session 2026-11-16

- N/A — autonomous refinement after the split; no question was asked. Resolved gaps are
  A-30–A-34 and the new requirements REQ-64–REQ-67.

## Open Questions

- **Q-02 (non-blocker)** | Should `/restack` preserve composite merge commits
  (`--rebase-merges`)? This would change the hook's exact replay form
  (`workflows/restack.md:91-98`) and the replay verifier. Current choice: linearize and report
  (A-14). Impact: review history after restacks only.

## Notes

### Constraints

- Every git write is a separate Bash call (policy, C-2).
- No pipeline identifier reaches branch names, commits or PR text (`rules/git-flow.md:129-154`);
  the journal lives in the git common directory and is never committed.
- `.ai/` tracking policy is unchanged; untracked consumer state is never staged
  (`rules/git-flow.md:156-165`).
- Contract changes follow `.ai/principles/coding.md → Changing a contract`: failing check first,
  canonical definition, readers, ADR.
- The validator's check inventory is not extended: `scripts/validate-contracts.sh` changes only
  the literals of existing checks listed in C-5, each through a 011 DM-9 `contract_changes` entry
  (011 REQ-69); follow the re-pin procedure in
  `tests/fixtures/validator-runtime/README.md`, and run the inventory oracle. The replaced `tests/git-rails.sh` test name appears only in
  `tests/git-rails.sh`, not in the source inventory or the source-guard exceptions (checked at
  `e3ba41a`).

### Implementation hints (nonbinding)

- Reuse the restack journal reader in `hooks/git_rails.py` (strict JSON, size and name rules,
  `JOURNAL_DIRECTORY` pattern at `:2402`) for the composite journal, with a second directory
  constant; share one fixture set between the hook verifier and `composite_run.py validate`.
- `model_plan.py` already parses `plan.md` tables (`scripts/model_plan.py`); the helper can
  follow its table parsing approach.

### Follow-up changes outside this spec

- Spec 012: adopted except the tracked-`.ai/` form of fact 2 (pending follow-up) — 012 REQ-51 and the DM-3 SA-10/SA-11 `per-composite` rules implement these
  branch-ancestry facts, which a `per-composite` run satisfies (kept here as their source):
  1. *Stack entries.* Top-level leaves and composites (a composite counts as one entry, its
     children do not) form the stack in plan order: the first entry's `base_branch` is the seed
     branch; each later entry's `base_branch` is the previous entry's `branch`, and its
     `base_commit` is that branch's tip when the entry was created (for a composite predecessor,
     the composite tip after composite validation, including the REQ-43 record commit when one
     is made).
  2. *Children.* A child block's `base_branch` is its composite's `branch`. Its `base_commit` is
     the composite tip when its latest attempt started. The first child started has the
     composite's start tip as `base_commit`: that is the composite's own `base_commit` when
     nothing was committed on the composite branch before, as for the `composite`/`spec-run`
     case spec 012 exercises (no promotion), and the promoted leaf's current tip, a descendant
     of the composite's `base_commit`, after a promotion (REQ-37). Every later child's
     `base_commit` equals the previous child's `merge_commit` when the repository does not track
     `.ai/` (the consumer default, ADR-0012); where it does, it is the REQ-43 point (b) record
     commit whose only parent is that `merge_commit`. Spec 012 SA-10 states only the first form
     (`.ai/specs/012-golden-run-tests.md:772`); adding the tracked-`.ai/` form there is a pending
     follow-up change to spec 012, not made here.
  3. *Merges.* Each accepted child has `merge_commit` with first parent = the composite tip
     before the merge and second parent = the child attempt's tip; every `merge_commit` is an
     ancestor of the composite branch tip; merge subjects are `Merge branch '<child-branch>'
     into <composite-branch>` and contain no `T-` identifier.
  4. *Chains (SA-11).* For a dependency chain inside one composite, the later child's
     `base_commit` descends from the earlier child's `merge_commit`; across
     stack entries fact 1 applies.
  Child blocks record `pr: none` and child branches are normally deleted after acceptance, so a
  child's `branch:` may name a branch that no longer exists.
- Spec 019: its repair policy is wired by REQ-54.
- Spec 014: none — wired by REQ-53.
- Spec 011: REQ-69's `requirement` grammar accepts the value `spec-024 REQ-NN` for the
  `contract_changes` entries of C-5.

### Change Log

#### 2026-11-16 — composite branch model specified

Historical source and review details are preserved in Git history.

## Readiness Checklist

The previous readiness review predates the scope update. Re-review the remaining contracts,
traceability and compatibility before implementation. Verdict: **NOT READY FOR DEVELOPMENT**.
