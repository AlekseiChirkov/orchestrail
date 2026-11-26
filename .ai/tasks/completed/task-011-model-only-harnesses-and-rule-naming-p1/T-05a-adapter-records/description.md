## Goal
Define the two harness adapters and canonical capability records without removing existing lines.

## Context
- Dependencies: T-04; child of T-05.
- Constraints: REQ-35, REQ-38, REQ-62; AC-23 record fixtures and AC-40. The existing source moves are deferred to T-05b.
- Reason: Declaration validation is independently testable in fixtures before the Git move.

Off-limits: Real-home deployment, source moves, unsupported capability claims and removal of existing capability lines.

## Scope
- **In scope:** Adapter configuration and canonical capability records.
- **Out of scope:** Always-on source relocation and consumer updates.
- **Target files:** harness/claude/deploy.env, harness/codex/deploy.env, harness/claude/capabilities.md, harness/codex/capabilities.md, scripts/check-lint-instructions.py

## Steps
1. Inspect DM-4/DM-5 and current capability declarations.
2. Write fixture tests and establish failure for absent canonical records.
3. Add the adapter declarations and only evidence-backed or unknown capability records; use the checker implemented in T-03.
4. Run fixtures and preserve existing declaration lines.

## Acceptance Criteria
- Both adapters declare the correct paths and each capability file has six canonical records in order, preserving every prior line and matching hooks and always-on-path values.
- The actual adapter files pass T-03 capability validation; fixtures with an absent canonical record or a hooks/path mismatch yield capability-key-missing or the corresponding mismatch code.

## Test Plan
- **Level:** contract.
- **Scenarios:**
  - First criterion → parse both declarations and compare prior line subsequences and canonical key order.
  - Second criterion → run each missing-record and mismatch fixture through the existing checker and assert the exact diagnostic.
- **Edge cases:** Unknown support, missing or duplicated records and path mismatch.
