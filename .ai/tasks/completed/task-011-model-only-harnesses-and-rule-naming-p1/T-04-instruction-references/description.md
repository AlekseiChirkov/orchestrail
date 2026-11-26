## Goal
Instruction name and reference checks: satisfy REQ-29, REQ-50, REQ-68 / AC-06, AC-30, AC-48 first-part fixtures for the bounded phase-one component.

## Context
- Dependencies: T-03; run in the sequential reviewed stack.
- Constraints: Implement REQ-29, REQ-50, REQ-68 / AC-06, AC-30, AC-48 first-part fixtures and the corresponding specification contracts. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Instruction name and reference checks; the exact first-part clauses identified above.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** scripts/lint-instructions.py, scripts/check-lint-instructions.py, docs/name-map.json, tests/validator-runtime-oracle.py, tests/fixtures/validator-runtime/inventory-amendment.json, tests/fixtures/validator-runtime/source_guard.py, tests/fixtures/validator-runtime/source_guard_exceptions.json

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions. If the first map is added, pin its exact bytes in the inventory amendment, update the amendment pin and review the resulting source-guard changes in the same commit.
4. Run the frozen tests and focused regression checks; return any shared knowledge delta to the Orchestrator.

## Acceptance Criteria
- A fixture legacy mention on line 7 reports legacy-mention with its path and line, while excluded removed-integration documentation and reporter do not.
- Invalid name-map rows, mismatched split targets and stale or nonexistent references produce the codes required by DM-1 and DM-16/17 without hiding unrelated diagnostics.
- The real map and pinned inventory amendment agree byte-for-byte by SHA-256. The existing inventory oracle and source guard pass without broadening their approved inputs.

## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Run isolated path, name-map, reference and legacy scan fixtures; leave renamed-tree assertions for phase 2.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
  - Third criterion → run the existing inventory oracle and source guard against the new map and its exact matching pin.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
