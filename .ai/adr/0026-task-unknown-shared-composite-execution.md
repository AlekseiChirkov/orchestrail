# ADR-0026: Decisions for Task unknown — Shared composite execution

## Status

Provisional

## Date

2026-11-24

## Related Task

- Task: [Shared parallel execution specification](../specs/26-shared-parallel-execution.md)
- Related files: `workflows/spec-run.md`, `workflows/phase-execution.md`, `workflows/pe-execute.md`

## Summary

Propose a common composite scheduler for the two execution entry points, with isolated worktrees and source-side conflict resolution for explicitly compatible overlap.

## Context

ADR-0009 Decision 4 establishes composite branch ownership and limits parallel work to disjoint children under spec-run. The new design request adds standalone execution and asks for recovery when parallel candidates edit the same file.

## Decisions

### Decision 1: Share the composite execution loop

**What was decided:**

Reuse the composite branch and journal model. Let both callers use the same scheduler and local integration gate. Keep each caller in charge of subsequent phases and publication.

**Why:**

A shared execution loop provides consistent admission, workspace ownership, check gates and recovery across both entry points.

**Alternatives:**

Independent scheduler loops duplicate recovery. Speculation across top-level stack units changes the accepted stacking boundary.

**Consequences:**

Delivery depends on the sequential composite branch and peer contracts. Parallel execution stays inside one composite.

**Related files:**

- [Parallel subtask execution design](../../docs/analysis/2026-11-24-parallel-phase-execution.md)

### Decision 2: Resolve compatible overlap on the candidate branch

**What was decided:**

Allow previously reviewed overlap on exact paths between independently deliverable children. Resolve conflicts against the pinned composite tip in the candidate worktree, then verify the changed candidate and proposed integration before advancing the target.

**Why:**

Candidate-side resolution preserves both sets of changes and keeps partial edits away from the accepted target.

**Alternatives:**

Restarting every conflicted attempt from the latest target remains the fallback for unapproved overlap. Resolving directly on the target exposes the accepted branch to incomplete work.

**Consequences:**

The target update and evidence reconciliation remain serial. Contract conflicts require an owner decision.

**Related files:**

- [Shared parallel execution specification](../specs/26-shared-parallel-execution.md)

## Questions and Answers

No interactive design decisions recorded.

## Rejected Options

Separate schedulers, cross-stack speculation and target-side conflict edits.

## Implications for Future Work

Verify the prerequisites and obtain approval for the limited amendment before activating the new route. ADR-0009 Decision 4 stays accepted. The proposed amendment covers standalone phase execution and reviewed same-file overlap inside one composite.

## Verification

Not yet verified — decision recorded before implementation completed.

## References

- [ADR-0009](0009-task-unknown-roadmap-decisions-2026-09.md)
- [Composite branch model](../specs/22-composite-branch-model.md)
- [Historical parallel composite children](../specs/23-composite-branch-model-and-parallel-children.md)
