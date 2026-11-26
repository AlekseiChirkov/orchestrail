## Goal
Unowned leftover reporting: satisfy REQ-57 / AC-37 for the bounded phase-one component.

## Context
- Dependencies: T-11; run in the sequential reviewed stack.
- Constraints: Implement REQ-57 / AC-37 and the corresponding specification contracts. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Unowned leftover reporting; the exact first-part clauses identified above.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** scripts/deploy-skills.py, scripts/check-deploy-skills.py

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions.
4. Run the frozen tests and focused regression checks; return any shared knowledge delta to the Orchestrator.

## Acceptance Criteria
- Existing old-name skill directories that are not current installed names are reported as leftovers.
- Leftover directories with unproven ownership are never removed or overwritten on first or subsequent runs.

## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Seed old workflow and rule skill directories in an isolated home, run deployment twice and compare bytes.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
