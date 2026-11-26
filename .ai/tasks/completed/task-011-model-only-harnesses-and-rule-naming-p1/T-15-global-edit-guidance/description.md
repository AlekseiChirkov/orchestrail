## Goal
Global instruction edit guidance: satisfy REQ-66 / AC-46 first-part clauses for the bounded phase-one component.

## Context
- Dependencies: T-14; run in the sequential reviewed stack.
- Constraints: Implement REQ-66 / AC-46 first-part clauses and the corresponding specification contracts. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Global instruction edit guidance; the exact first-part clauses identified above.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** rules/language.md, docs/USAGE.md, scripts/check-lint-instructions.py

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions.
4. Run the frozen tests and focused regression checks; return any shared knowledge delta to the Orchestrator.

## Acceptance Criteria
- Active guidance no longer tells users to edit either ownership-protected global always-on file.
- The language rule and usage guide both state that sync manages the global files and stops with ownership-conflict after an edit, without changing unrelated language requirements.

## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Scan active language and user guidance for both former global-edit instructions and verify the replacement points to an existing local mechanism.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
