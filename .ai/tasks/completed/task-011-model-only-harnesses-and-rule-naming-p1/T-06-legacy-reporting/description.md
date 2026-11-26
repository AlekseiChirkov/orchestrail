## Goal
Read-only legacy artifact reporter: satisfy REQ-07, REQ-11, REQ-29 / AC-03 reporter and AC-06 for the bounded phase-one component.

## Context
- Dependencies: T-05; run in the sequential reviewed stack.
- Constraints: Implement REQ-07, REQ-11, REQ-29 / AC-03 reporter and AC-06 and the corresponding specification contracts. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Read-only legacy artifact reporter; the exact first-part clauses identified above.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** scripts/report-legacy-artifacts.sh, scripts/check-deploy-skills.py, docs/USAGE.md

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions.
4. Run the frozen tests and focused regression checks; return any shared knowledge delta to the Orchestrator.

## Acceptance Criteria
- Given existing legacy objects, the reporter prints the specified safely quoted lines and does not create, modify, delete or follow them; docs contain the Removed integrations section.
- Missing objects produce no object lines and symlinks are reported without traversal; the reporter and the removed-integrations section do not trigger legacy-mention.

## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Run the reporter on absent, existing, spaced and symlinked fixture paths and compare directory snapshots before and after.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
