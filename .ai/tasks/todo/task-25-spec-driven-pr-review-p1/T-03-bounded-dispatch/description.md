## Goal
Document bounded dispatch and recovery with reproducible evidence for AC-49.

## Context
- Dependencies: T-02
- Constraints: Use local procedure and controlled fixtures, with identical approved inputs across review variants.
- Reason: Establish a separately verifiable protocol checkpoint before integrating the rehearsal.

Off-limits: Historical case execution, production workflow edits, automated scheduling, hosted services and merge gating.

## Scope
- **In scope:** Document bounded dispatch and recovery and its synthetic verification.
- **Out of scope:** Live data, external publication and deferred service requirements.
- **Target files:** docs/offline-review/dispatch.md, docs/offline-review/fixtures/

## Steps
1. Define locked admission settings and operator reservation and attempt records.
2. Specify ready review and adjudication selection, reconciliation and terminal cutoff handling.
3. Verify two slots, fitting work, exact cap equality, uncertain timeout across restart and queued work at cutoff.

## Acceptance Criteria
- AC-49 — Ready reviews and blinded adjudications use free slots while unrelated work is active. At 7 of 10 units a 3-unit job fits and a 4-unit job queues.
- AC-49 — Unverified termination retains both slot and liability across restart without resubmission. At cutoff, queued reviews are not started and unfinished adjudications are incomplete.

## Test Plan
- **Level:** contract
- **Scenarios:**
  - Run the nominal fixture and check: Ready reviews and blinded adjudications use free slots while unrelated work is active. At 7 of 10 units a 3-unit job fits and a 4-unit job queues.
  - Run the boundary or failure fixtures and check: Unverified termination retains both slot and liability across restart without resubmission. At cutoff, queued reviews are not started and unfinished adjudications are incomplete.
- **Edge cases:** Preserve fixture isolation and verify exact counts, states and evidence where applicable.
