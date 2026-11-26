## Goal
Knowledge inventory relocations: satisfy REQ-72 / AC-53 for the bounded phase-one component.

## Context
- Dependencies: —; run in the sequential reviewed stack.
- Constraints: Implement REQ-72 / AC-53 and the corresponding specification contracts. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Knowledge inventory relocations; the exact first-part clauses identified above.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** scripts/validate-contracts.sh, scripts/knowledge_inventory.py, scripts/check-knowledge-inventory.py, tests/fixtures/validator-runtime/source_guard.py, tests/fixtures/validator-runtime/source_guard_exceptions.json

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions.
4. Run the frozen tests and focused regression checks; return any shared knowledge delta to the Orchestrator.

## Acceptance Criteria
- In disposable repositories, a tracked unchanged original and both existing task/spec archival fallbacks pass; each verified task rename, including rename plus archival, resolves to exactly one tracked file.
- Absent originals with no resolution, multiple existing candidates and untracked targets fail; the pinned baseline and frozen check name/expression remain unchanged.

- The source-guard refresh preserves all unaffected reviewed entries, reviews every changed call site and passes the guard, its regression/external-source suites and inventory oracle using the documented procedure.

## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Exercise direct, archival, 12 recorded mappings and combined relocation fixtures; compare the check inventory before and after.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
  - Source-guard criterion → independently review the exact source diff and each changed exception, recompute only reviewed hashes and run the documented guard and oracle suites.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
