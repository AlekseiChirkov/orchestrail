# ADR-0027: Decisions for Task 011 — Evidence-bound knowledge relocations

## Status

Provisional

## Date

2026-11-25

## Related Task

- Task: `.ai/tasks/todo/task-011-model-only-harnesses-and-rule-naming-p1/`
- Related pull request: not yet created
- Related files: `scripts/validate-contracts.sh`, the knowledge-inventory baseline and relocation fixtures

## Summary

The planned inventory repair retains the existing pinned baseline while resolving verified
historical task-directory relocations through an exact, fail-closed mapping. Implementation and
verification are pending.

## Context

The existing identity inventory checks baseline paths and only supports archival fallbacks
(`scripts/validate-contracts.sh:4923-4948`). A later committed task renumbering changed tracked
paths, including a task whose finalization journal retains its prior location. Simply changing
the baseline could hide unrelated removals. REQ-72 and AC-53 specify the proposed mapping and
negative cases; read-only finalization-journal recovery belongs to the later phase.

## Decisions

### Decision 1: Preserve the baseline and verify relocations

**What was decided:** Retain the original baseline and verify exact approved old-to-new task
paths, preserving archival fallback, path suffixes, tracking and ambiguity checks.

**Why:** This preserves detection of unrelated loss while recognizing evidenced moves.

**Alternatives:** Resetting the baseline was rejected because it would hide intervening
removals; a broad numeric-name rewrite was rejected because it would accept unverified moves.

**Consequences:** Mappings and their source history need review; unknown or conflicting paths
fail closed. The separate finalization journal is not modified or deemed recovered.

**Related files:**
- `.ai/specs/011-model-only-harnesses-and-rule-naming.md`
- `docs/analysis/2026-11-25-task-specification-numbering.md`

## Questions and Answers

| Question | Answer | Impact on implementation |
|---|---|---|
| How should discovered blockers be handled? | The owner requested autonomous repair. | Preserve the original safety guarantee while testing the specific relocation. |

## Rejected Options

Rebaseline without proving every historical path, or treat a matching number alone as proof.

## Implications for Future Work

New relocations require exact evidence and regression coverage. Journal identity and snapshots
remain independently protected.

## Verification

Not yet verified — decision recorded before implementation completed.

## References

- Task: `.ai/tasks/todo/task-011-model-only-harnesses-and-rule-naming-p1/`
- Pull request: not yet created
- Related documents: ADR-0025 and the specification's REQ-72 and AC-53.
