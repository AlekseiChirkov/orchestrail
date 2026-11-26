## Goal
Registered project links: satisfy REQ-08, REQ-09, REQ-44 / AC-03, AC-04 and AC-45 registry clauses for the bounded phase-one component.

## Context
- Dependencies: T-08; run in the sequential reviewed stack.
- Constraints: Implement REQ-08, REQ-09, REQ-44 / AC-03, AC-04 and AC-45 registry clauses and the corresponding specification contracts. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Registered project links; the exact first-part clauses identified above.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** scripts/deploy-skills.py, scripts/check-deploy-skills.py

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions.
4. Run the frozen tests and focused regression checks; return any shared knowledge delta to the Orchestrator.

## Acceptance Criteria
- The project pass reads the registry without writing it, deduplicates canonical roots, reports missing roots and updates only permitted links and ignore lines.
- A relative registry entry returns registry-invalid without writes; foreign links, legacy directories and profile files remain untouched.

## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Run registry fixtures for duplicate, missing, invalid and overlapping roots and compare both registry and protected project bytes.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
