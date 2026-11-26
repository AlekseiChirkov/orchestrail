---
description: Classify and decompose subtasks
load: on-demand
---

# Subtask Classification

## Autonomous Subtask Classifier

Called by `pd-decompose` after producing the initial candidate list. The AI decides whether each candidate becomes a leaf, a composite (Type 2), or part of a vertical re-slice (Type 3). **No user prompt is issued for this decision.** The rationale is recorded in `plan.md → ## Decomposition Decisions`.

### Signals (compute per candidate subtask)

| Signal | Definition |
|--------|-----------|
| S1 | Number of implementation steps in `## Steps` |
| S2 | Count of independently-testable components — groups of work that each have their own verifiable done-state and could be validated in isolation |
| S3 | Count of distinct capabilities or domain areas covered (each with its own meaning to the system) |
| S4 | Boolean — does the subtask span cross-repo work or reference a shared frozen external contract? |
| S5 | Count of separable Acceptance Criteria clusters — groups of AC items that test distinct components, where each cluster can pass/fail independently |

### Classification rules (evaluated in order)

S1, S2, S3 and S5 are nonnegative integer counts; S4 is boolean. Resolve uncertain
component/criteria groupings before classification. Apply these steps in order:

1. **Type 3 — vertical re-slice pairs first.** Consider pairs whose S4 is true and
   that reference the same shared frozen contract. Re-slice only when each track has
   S1 > 8 or S2 ≥ 2, the contract defines their interface, and S3 ≥ 2 shared capabilities
   provide a split. This takes priority over Type 2 nesting.
   - Extract work shared across ALL capabilities into one prerequisite leaf; never
     duplicate contract/schema/common infrastructure work into each capability.
   - When Type 3 applies, emit a producer leaf and consumer leaf per capability; derive those roles
     from the contract, not client/server labels. Consumer Depends On producer.
   - Let `base = min(AA, BB)`. Capability i gets `T-(base+i-1)a` (producer) and
     `T-(base+i-1)b` (consumer). Shift `base` upward by 1 until the full range is free
     of colliding IDs belonging to non-dissolved subtasks. Record capability names in plan Slice.
2. **Leaf-health invariant.** Classify remaining candidates, including generated slices:
   a leaf requires S2 = 1 AND S5 = 1. Size uncertainty alone does not force nesting.
3. **Type 2 — nest into composite** when S2 ≥ 2 AND S5 ≥ 2. Create sibling child
   directories T-XXa, T-XXb, …, each with one component and one coherent AC cluster;
   the parent owns integration-level criteria.
4. **Mismatched clusters.** If only S2 or S5 exceeds 1, align criteria with testable
   components and recount. Merge genuinely inseparable work; otherwise split criteria
   and steps into coherent siblings. Never retain an unhealthy leaf.
5. **Depth-2 cap.** A composite's children are leaves. Redistribute an unhealthy child
   across more sibling children rather than nesting a third tier. Merge undersized work
   only when it remains one testable component; preserve acceptance coverage and the
   Decomposition Rules below.

### Runtime self-correction (tripwire)

During atomic execution of a leaf (`pae-implement`), if any of these conditions arise:
- Steps balloon: more implementation steps are discovered than originally listed, crossing the leaf-health boundary.
- A second independently-testable component appears that was not anticipated during decomposition.
- Acceptance Criteria actually split into two or more independent verifiable clusters.

Then invoke the **Composite Promotion Protocol**:
1. Stop current atomic execution immediately.
2. Re-classify the current leaf as a composite. Update its `description.md → ## Context` to add `type: composite`.
3. Redistribute the leaf's steps into sibling children: create T-XXa, T-XXb, … directories with `description.md` files containing the redistributed steps and scoped AC.
4. Update `plan.md`: change the T-XX row `Type` to `composite`; add child rows (T-XXa, T-XXb, …) with `Type: leaf`.
5. Update `state.md → ## Subtask Progress`: replace the leaf block with a composite block; add leaf blocks for each child.
6. Depth-2 cap holds — do not promote a child of a composite.
7. Stop after recording the promotion and preserve existing test evidence. In orchestrated mode, return shared-artifact deltas instead of writing them. Report the proposed first child (T-XXa) and wait for the required promotion decision; do not start it automatically.

### Decision record format (written to `plan.md → ## Decomposition Decisions`)

```
## Decomposition Decisions

| Subtask | Decision | Signals | Rationale |
|---------|----------|---------|-----------|
| T-XX | leaf | S1=N, S2=1, S5=1 | Single coherent component; fits one atomic cycle |
| T-YY | composite (Type 2) | S1=N, S2=3, S5=3 | Three independently-testable components, three AC clusters |
| T-YY + T-ZZ | Type 3 re-slice | S4=true, S3=3 | Cross-repo pair sharing frozen contract with 3 capabilities; D6 conditions met |
```

---

## Decomposition Rules

A subtask (T-XX) must represent a logical unit of work, not an individual operation.

Criteria for a valid subtask:
- Groups related operations around a single domain or module
  (e.g., "Terraform staging module" — NOT "create variables.tf" + "create outputs.tf" as separate tasks)
- Contains between 3 and 15 implementation steps internally
- Is independently verifiable (has a clear done-state)
- Is NOT split by operation type (create / configure / validate must live together inside one subtask)

Decomposition limits:
- Target 8 subtasks per task (soft guidance, not a hard limit)
- If natural decomposition produces more than 8, compare coherent merges with splitting the task. In `--step-by-step` mode, present both options and wait for explicit user decision. In autonomous Discovery, use the Autonomous Decision Protocol and record the choice; do not merge unrelated components merely to reach 8.
- If a candidate has fewer than 3 steps, merge it only with a coherent neighbor that
  preserves one testable component and one AC cluster. If no such merge exists, re-slice
  the boundaries through the Autonomous Decision Protocol. If the minimum and leaf-health
  constraints cannot both hold, stop and report that conflict for an explicit decision.
  Never pad steps or merge independent components solely to reach the minimum.

These rules apply strictly during `/pd-decompose` and must be enforced before `/pd-finalize` runs.

---
