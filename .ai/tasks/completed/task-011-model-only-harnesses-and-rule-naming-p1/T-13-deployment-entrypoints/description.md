## Goal
Deployment and setup entry points: satisfy REQ-05, REQ-06, REQ-07, REQ-36, REQ-47, REQ-56, REQ-65 / AC-02, AC-03, AC-22 assembly, AC-27 isolation, AC-36, AC-43 for the bounded phase-one component.

## Context
- Dependencies: T-12; run in the sequential reviewed stack.
- Constraints: Implement REQ-05, REQ-06, REQ-07, REQ-36, REQ-47, REQ-56, REQ-65 / AC-02, AC-03, AC-22 assembly, AC-27 isolation, AC-36, AC-43 and the corresponding specification contracts. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Deployment and setup entry points; the exact first-part clauses identified above.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** scripts/sync.sh, scripts/setup-new-project.sh, scripts/setup-all-repos.sh, scripts/deploy-skills.py, tests/hook-install.sh, tests/model-workflow.py, scripts/check-finalization-safety.py, scripts/check-finalization-workflow.py, scripts/check-deploy-skills.py, scripts/check-lint-instructions.py, scripts/validate-contracts.sh, tests/validator-runtime-oracle.py, tests/validator-runtime-allowlist.py, tests/validator-runtime-integrated.py, tests/validator-runtime-sourceguard-allowlist.py, tests/fixtures/validator-runtime/inventory-amendment.json, docs/audits/2026-11-25-rule-migration-map.md, tests/fixtures/validator-runtime/source_guard.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, .ai/memory/architecture.md

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions.
4. Run the frozen tests and focused regression checks; return each exact changed frozen-check amendment and provisional DM-20 verdict to the Orchestrator for independent Validator review before publication.
5. Return the shared architecture update for the Orchestrator to apply to `.ai/memory/architecture.md`, including the reporter, planning and transaction boundaries, and the registered project pass.

## Acceptance Criteria
- A fixture sync deploys the declared harnesses including an added demo adapter without creating legacy paths; setup preserves legacy objects and points to the existing /phase-discovery command.
- The existing `--stage` form retains its isolation and empty-target gate while rendering only the supported harnesses. Both normal and staged paths retain the mandatory finalization acceptance checks on a supported runtime.
- Project registration retains its existing coordination lock. Adapter and project link destinations cannot replace it, including its declared and resolved addresses.
- Python 3.10 causes sync to fail before writes and setup to warn and continue; each deployed always-on file equals the DM-14 assembly with the capability declaration exactly once, and the Claude assembly includes exactly one actual hook-installation result.

- Both standalone suites run with HOME, XDG_CONFIG_HOME and XDG_STATE_HOME redirected, leave real-home timestamps unchanged, and their source checks reject network imports and non-allowlisted subprocess programs.

- Every changed frozen check is reconstructed by its exact schema-2 amendment, retains its frozen description and has an independently reviewed pass verdict in DM-20 before the branch is published.
- Existing rule delivery checks verify actual installed outputs and project links. The installed model guidance fixtures load the same deployed skill layout and retain their existing assertions.

- The source-guard refresh preserves all unaffected reviewed entries, reviews every changed call site and passes the guard, its regression/external-source suites and inventory oracle using the documented procedure.

## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Use redirected fixture homes for adapter discovery, setup, unavailable Python, hook installation and unchanged legacy paths.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
  - Third criterion → run the isolated AC-27 source checks and compare protected home timestamps before and after both suites.
  - Additional criterion → independently inspect each frozen before/after entry and run the oracle with the updated partial DM-20 record.
  - Source-guard criterion → independently review the exact source diff and each changed exception, recompute only reviewed hashes and run the documented guard and oracle suites.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
