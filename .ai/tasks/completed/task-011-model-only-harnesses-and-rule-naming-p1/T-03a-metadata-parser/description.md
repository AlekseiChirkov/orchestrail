## Goal
Instruction metadata checker: satisfy REQ-12, REQ-13, REQ-30, REQ-50, REQ-54 / AC-07, AC-30, AC-34 for the bounded phase-one component.

## Context
- Dependencies: T-02; child of T-03; run in the sequential reviewed stack.
- Constraints: Implement REQ-12, REQ-13, REQ-30, REQ-50, REQ-54 / AC-07, AC-30, AC-34 and the corresponding specification contracts. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Instruction metadata checker; the exact first-part clauses identified above.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** scripts/lint-instructions.py, scripts/check-lint-instructions.py

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions.
4. Run the frozen tests and focused regression checks; return any shared knowledge delta to the Orchestrator.

## Acceptance Criteria
- Fixtures with valid rule/workflow metadata including step 2.5, 4b and "-" produce no metadata findings; a 1,200-word always-on body passes.
- Missing, repeated, unknown or invalid metadata and multiline descriptions emit their specified codes; a 1,201-word body emits always-on-size even when capability bytes are present.


## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Run standalone checker fixtures for each valid and invalid front-matter form and exact body-size boundaries.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
