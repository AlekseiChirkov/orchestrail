## Goal
Deployment source revision: satisfy REQ-58 / AC-38 source-revision clauses for the bounded phase-one component.

## Context
- Dependencies: T-10; run in the sequential reviewed stack.
- Constraints: Implement REQ-58 / AC-38 source-revision clauses and the corresponding specification contracts. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Deployment source revision; the exact first-part clauses identified above.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** scripts/deploy-skills.py, scripts/check-deploy-skills.py

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions.
4. Run the frozen tests and focused regression checks; return any shared knowledge delta to the Orchestrator.

## Acceptance Criteria
- For a fixture Git source, the deploy manifest records the exact source HEAD as source_revision.
- For a fixture source without usable Git provenance, the manifest records null and does not infer a revision.

## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Run Git and non-Git source fixtures in temporary directories and compare manifest values.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
