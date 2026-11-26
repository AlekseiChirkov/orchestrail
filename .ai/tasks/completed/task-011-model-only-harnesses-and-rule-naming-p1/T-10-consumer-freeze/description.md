## Goal
Active consumer deployment freeze: satisfy REQ-43, REQ-59 / AC-04, AC-25, AC-38 active clauses for the bounded phase-one component.

## Context
- Dependencies: T-09; run in the sequential reviewed stack.
- Constraints: Implement REQ-43, REQ-59 / AC-04, AC-25, AC-38 active clauses and the corresponding specification contracts. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Active consumer deployment freeze; the exact first-part clauses identified above.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** scripts/deploy-skills.py, scripts/check-deploy-skills.py

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions.
4. Run the frozen tests and focused regression checks; return any shared knowledge delta to the Orchestrator.

## Acceptance Criteria
- An active registered project blocks all global updates without --force, including when its links target those global files; successful deployment emits the required residual-race note.
- A state that cannot be read or decoded as UTF-8 is conservatively active. Readable state counts only when it has an exact DM-8 in-progress line within `## Phases`. Missing roots are inactive. `--force` overrides only the global freeze and active-project skip.

## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Exercise active, inactive, malformed, missing and forced fixtures with before/after global byte snapshots.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
