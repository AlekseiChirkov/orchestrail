## Goal
Move both always-on source files with history and keep existing consumers functional.

## Context
- Dependencies: T-05a; child of T-05.
- Constraints: REQ-55, REQ-61 and AC-35; maintain partial DM-20 verdicts and oracle compatibility.
- Reason: The two moves and all existing consumer changes must be one atomic checkpoint.

Off-limits: Worker Git commands, real-home deployment, lost source content and phase-two command or rule renames.

## Scope
- **In scope:** Both Git moves, active readers of both source files, exact historical fixture retention and the reviewed oracle record.
- **Out of scope:** Global deployment engine and final command names.
- **Target files:** rules/global-claude.md, templates/codex-global-AGENTS.md, harness/claude/always-on.md, harness/codex/always-on.md, scripts/sync.sh, scripts/validate-contracts.sh, scripts/check-lint-instructions.py, scripts/check-finalization-workflow.py, tests/hook-install.sh, tests/validator-runtime-oracle.py, tests/fixtures/validator-runtime/inventory-amendment.json, docs/audits/2026-11-25-rule-migration-map.md, docs/USAGE.md, rules/workflow-globals.md, .ai/context/environment.md, .ai/context/integrations.md, .ai/context/runbook.md, .ai/memory/architecture.md, .ai/principles/architecture.md, tests/fixtures/validator-runtime/source_guard.py, tests/fixtures/validator-runtime/source_guard_exceptions.json

## Steps
1. Inspect the old source paths, existing sync consumers, frozen expressions and partial DM-20 record.
2. Write isolated consumer and history acceptance tests and report RED.
3. After the test-only commit, the Orchestrator performs the two explicit git mv operations; the worker performs no Git commands.
4. Repoint active script, fixture, and documentation readers. Record exact retained source lines for the historical adapter grammar and synthetic audit fixtures in the migration semantics record. Return the shared knowledge paths and exact deltas to the Orchestrator. Update the oracle amendment and obtain an independent pass for each delivered contract change.
5. Verify isolated sync and the oracle; the Orchestrator stages both source deletions and destination files explicitly in the implementation commit.

## Acceptance Criteria
- Both files retain history via the two moves; their contents change only as permitted by REQ-55. Sync, its finalization preflight, the hook fixture, and active documentation resolve the new source paths, with exact DM-20 exceptions for necessary historical literals.
- Existing frozen checks retain their descriptions and continue to pass through the schema-2 amendment. Every changed contract entry has an independently reviewed pass in the partial DM-20 record.

- The source-guard refresh preserves all unaffected reviewed entries, reviews every changed call site and passes the guard, its regression/external-source suites and inventory oracle using the documented procedure.

## Test Plan
- **Level:** integration and contract.
- **Scenarios:**
  - First criterion → isolated sync and finalization fixtures read the new paths; strict stale-name output has no unresolved references to either old path. After commit the Orchestrator checks git log --follow.
  - Second criterion → run oracle amendment fixtures and independently compare each verdict against the delivered change.
  - Source-guard criterion → independently review the exact source diff and each changed exception, recompute only reviewed hashes and run the documented guard and oracle suites.
- **Edge cases:** A missing source, changed user content, duplicated amendment and invalid source path.
