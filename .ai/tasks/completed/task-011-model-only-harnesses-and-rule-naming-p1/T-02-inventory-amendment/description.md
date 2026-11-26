## Goal
Inventory amendment compatibility: satisfy REQ-51, REQ-52, REQ-61, REQ-69, REQ-71 / AC-31, AC-32, AC-49, AC-52 first-part fixtures for the bounded phase-one component.

## Context
- Dependencies: T-01; run in the sequential reviewed stack.
- Constraints: Implement REQ-51, REQ-52, REQ-61, REQ-69, REQ-71 / AC-31, AC-32, AC-49, AC-52 first-part fixtures and the corresponding specification contracts. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Inventory amendment compatibility; the exact first-part clauses identified above.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** tests/validator-runtime-oracle.py, tests/fixtures/validator-runtime/inventory-amendment.json, docs/audits/2026-11-25-rule-migration-map.md, docs/README.md, tests/fixtures/validator-runtime/source_guard.py, tests/fixtures/validator-runtime/source_guard_exceptions.json

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions.
4. Run the frozen tests and focused regression checks; return any shared knowledge delta to the Orchestrator.

## Acceptance Criteria
- Schema 1 and schema 2 accept the existing approved added entries and anchors; schema 2 accepts valid same-class path changes and a valid REQ-12 contract change.
- Unknown additions, wrong anchors, wrong map digest, cross-class swaps, duplicate targets and pass-only replacements raise ValueError; each delivered contract change has an independent pass in the dated indexed DM-20 record.

- The source-guard refresh preserves all unaffected reviewed entries, reviews every changed call site and passes the guard, its regression/external-source suites and inventory oracle using the documented procedure.

## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Run isolated oracle fixtures including known valid and invalid amendments; independently verify every partial semantics-record verdict before delivering its amendment.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
  - Source-guard criterion → independently review the exact source diff and each changed exception, recompute only reviewed hashes and run the documented guard and oracle suites.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
