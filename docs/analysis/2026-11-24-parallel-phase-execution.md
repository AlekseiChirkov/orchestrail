# Parallel subtask execution design

> Historical analysis from commit `40b8b4bd48286b8f286a001b5435bf790e9c2d79`.
> Its composite-only, opt-in design has been superseded by the owner's later direction.
> The current planned contract is [parallel execution](../../.ai/specs/027-parallel-execution-program.md).
> Earlier file paths and identifiers below describe the recorded source revision.

Source baseline: `4aaf005cf293cd236510cd368b8684d4e1d48322`.

## Existing paths

- `phase-execution` calls `pe-execute` and then `pe-finalize` for full tasks. Quick tasks run inline (`workflows/phase-execution.md:82-97`). The leaf loop is serial and treats a leaf marked `done` or `reviewed` as a satisfied prerequisite (`workflows/pe-execute.md:29-38`). A parallel worker needs the prerequisite's code on its Git base, so the proposed scheduler requires accepted integration.
- `spec-run` performs its own leaf loop. It creates each branch from the previous reviewed leaf, resolves repository routing and opens gated draft PRs (`workflows/spec-run.md:209-217`, `:264-284`, `:388-399`). Reusing the existing sequential leaf loop directly would lose these delivery rules.
- Spec 22 designs composite branches and source-branch conflict recovery (`.ai/specs/22-composite-branch-model.md:273-292`). Spec 23 designs parallel children for `spec-run`, using disjoint write sets and retry on conflict (`.ai/specs/23-composite-branch-model-and-parallel-children.md:899-903`, `:1334-1336`). ADR-0009 Decision 4 limits the feature to one composite and `spec-run` (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:143-160`). These are prerequisites and amendment points, not evidence of shipped support.

## Alternatives

| Design | Effect |
|---|---|
| Independent parallel loops in each workflow | Each caller would need its own admission, ownership and crash recovery. The same task could receive different treatment depending on the entry point. |
| One composite execution engine with caller-owned delivery | Both entry points use the same scheduler, isolated worktrees, conflict journal and acceptance gate. The outer stack and publication policies stay with their callers. |
| Speculate across top-level stack entries and materialize the stack later | Increases potential concurrency, but changes the branch-base and validation model for every speculative stack entry. It extends beyond the owner-deferred boundary in spec 23. |

Choose the shared composite engine. Treat explicit, reviewed overlap on named files as an exception to disjoint-path admission. A shared interface, ordering dependency or exclusive resource still prevents concurrent admission. The caller's authority governs conflict resolution and publication.

## Conflict workflow

After a candidate passes its own validation, serialize integration in plan order. If the composite and candidate conflict, preserve the composite tip and bring the pinned composite tip into the candidate's worktree. Resolve on the candidate side, as in a pull request update. Re-run validation there and the composite checks on the proposed merge tree before accepting. The candidate's test and implementation commits remain in history. Journal the base, heads, conflict paths, resolution and check outcomes. A changed target invalidates integration evidence, and a decision that changes a requirement or reconciles two incompatible intentions goes to the owner.

Git clean merges can still produce semantic regressions. The composite acceptance check applies even when the two sibling changes merge without textual conflicts.

Historical draft: `git show 40b8b4b:.ai/specs/26-shared-parallel-execution.md`.
