## Goal
Ownership-safe deployment planning: satisfy REQ-10, REQ-42, REQ-44, REQ-63 / AC-05, AC-24, AC-41, AC-45 for the bounded phase-one component.

## Context
- Dependencies: T-06; run in the sequential reviewed stack.
- Constraints: Implement REQ-10, REQ-42, REQ-44, REQ-63 / AC-05, AC-24, AC-41, AC-45 and the corresponding specification contracts. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Ownership-safe deployment planning; the exact first-part clauses identified above.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** scripts/deploy-skills.py, scripts/check-deploy-skills.py

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions.
4. Run the frozen tests and focused regression checks; return any shared knowledge delta to the Orchestrator.

## Acceptance Criteria
- A complete plan validates all harness adapters, manifest ownership and target containment before any target write; removing an owned source plans only the authorized deletion.
- Symbolic links, invalid manifest or adapter, changed owned bytes, foreign new targets and a bad second harness return the specified refusal and leave both harnesses unchanged.

## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Exercise all AC-24 and AC-41 fixtures in redirected homes, including exact exit codes and byte snapshots.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
