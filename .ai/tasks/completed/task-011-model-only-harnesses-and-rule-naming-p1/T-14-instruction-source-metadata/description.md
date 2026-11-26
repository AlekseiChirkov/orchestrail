## Goal
Source instruction metadata: satisfy REQ-12, REQ-13, REQ-54 / AC-07, AC-34 and phase-one checker gate for the bounded phase-one component.

## Context
- Dependencies: T-13; run in the sequential reviewed stack.
- Constraints: Implement REQ-12, REQ-13, REQ-54 / AC-07, AC-34 and the phase-one checker gate. Finish REQ-11 in active instructions after the entry-point changes and verify the checker's DM-5 adapter input handling for REQ-35 and REQ-44. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Source instruction metadata, removal of remaining active legacy integration mentions and the final Phase 1 checker evidence.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** rules/*.md, workflows/*.md, CLAUDE.md, docs/USAGE.md, scripts/lint-instructions.py, scripts/check-lint-instructions.py, scripts/validate-contracts.sh, tests/validator-runtime-oracle.py, tests/fixtures/validator-runtime/inventory-amendment.json, docs/audits/2026-11-25-rule-migration-map.md, tests/fixtures/validator-runtime/source_guard.py, tests/fixtures/validator-runtime/source_guard_exceptions.json

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions.
4. Run the frozen tests and focused regression checks; return each exact changed frozen-check amendment and provisional DM-20 verdict to the Orchestrator for independent Validator review before publication.

## Acceptance Criteria
- Phase-one rule and workflow sources have the specified metadata while retaining their existing names until phase 2.
- The checker treats `deploy.env` as data, reports `deploy-env-invalid` and `adapter-incomplete` for the DM-5 invalid fixtures, and ignores an orphaned `always-on.md`. The inherited delivered-capability tests supply complete adapter fixtures on this branch.
- Active documentation and instruction sources satisfy the legacy-mention scan. The usage guide records retirement under `## Removed integrations`. Existing authority and history are preserved, including the approved identity ledger location.
- The strict checker diagnostic list and status are saved and independently reviewed per the Phase 1 contract; unrelated invalid metadata or references prevent phase validation.
- The two existing orchestration references to the Implementer subsection resolve through the real subtask-loop heading. Preserve the step 4.2 locator in prose and record the pre-existing defects in DM-20, without renaming any command or heading.

- Every changed frozen check is reconstructed by its exact schema-2 amendment, retains its frozen description and has an independently reviewed pass verdict in DM-20 before the branch is published.

- The source-guard refresh preserves all unaffected reviewed entries, reviews every changed call site and passes the guard, its regression/external-source suites and inventory oracle using the documented procedure.

## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Run metadata fixtures and the strict checker against the phase-one tree; independently map every permitted deferred diagnostic to a specific phase-two source or table.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
  - Additional criterion → independently inspect each frozen before/after entry and run the oracle with the updated partial DM-20 record.
  - Source-guard criterion → independently review the exact source diff and each changed exception, recompute only reviewed hashes and run the documented guard and oracle suites.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
