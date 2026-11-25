# Parallel execution specification review

> Historical analysis from commit `40b8b4bd48286b8f286a001b5435bf790e9c2d79`.
> Its composite-only, opt-in design has been superseded by the owner's later direction.
> The current planned contract is [parallel execution](../../.ai/specs/027-parallel-execution-program.md).
> Earlier file paths and identifiers below describe the recorded source revision.

Reviewed the open numbered specifications against the historical shared parallel execution draft (`git show 40b8b4b:.ai/specs/26-shared-parallel-execution.md`), using the roadmap and task state to distinguish historical records and partially delivered work. The scope is execution of implementation subtasks in a composite. Other subsystems can run concurrent work under their own contracts.

| Specifications | Review outcome |
|---|---|
| 09 | Owns capability vocabulary and fallback messages. Spec 26 owns parallel preflight wiring for both entry points. |
| 10 | Owns golden-run schema and fixtures. Spec 26 owns the parallel case variant and comparison. |
| 11 | Context tiering has no scheduler contract. |
| 12–14 | Context packets, checkpoint proposals and the concurrent output store remain peer interfaces. Spec 26 owns their worktree integration and dispatch order. |
| 15–17 | Verification owns record format and verification semantics. Effort policy v1 retains its existing roles. Repair owns episode lifecycle. Spec 26 owns orchestration and integration of those interfaces in parallel attempts. |
| 18 | Decomposition owns dependency, path, interface and resource evidence. Spec 26 renders Parallel Safety, governs overlap and makes admission decisions. |
| 19–21 | Reference generation, installation and release do not implement subtask scheduling. |
| 22 | Retains sequential composite branches, child commits, base journal and PR ancestry. Parallel journal evolution and pre-update proposal checks belong to spec 26. |
| 23 | Superseded. Transferred parallel orchestration and worker contracts to spec 26. The old path preserves source provenance and maps requirement identifiers to their owners. |
| 25 | Parallel review sessions and fair sharing across review runs belong to the review system. Development subtask scheduling points to spec 26. |

Checked nearby records as well. Spec 08 was delivered. Spec 24 concerns finalization and safe cleanup. The closed partial validator-runtime record describes parallel acceptance-suite checks, a different workload. The unnumbered review design describes review agents and provider capacity rather than development subtasks.

The consolidated scheduler integrates in pinned topological order, admits an eligible prefix and drains at a blocker. Reciprocal exact-path approval can admit same-file edits. Incompatible or unauthorized overlap serializes from the accepted prefix, and a compatible conflict is resolved on the candidate with fresh validation. The proposal must pass checks before advancing the target. The provisional ADR and existing owner approval boundary remain applicable.
