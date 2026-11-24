## Goal
Verify offline rehearsal readiness with reproducible evidence for AC-48.

## Context
- Dependencies: T-02, T-03, T-04
- Constraints: Use local procedure and controlled fixtures, with identical approved inputs across review variants.
- Reason: Establish a separately verifiable protocol checkpoint before integrating the rehearsal.

Off-limits: Historical case execution, production workflow edits, automated scheduling, hosted services and merge gating.

## Scope
- **In scope:** Verify offline rehearsal readiness and its synthetic verification.
- **Out of scope:** Live data, external publication and deferred service requirements.
- **Target files:** docs/offline-review/README.md, docs/offline-review/fixtures/, docs/README.md

## Steps
1. Run three synthetic rehearsal cases with six independent observations using the preceding procedure and artifacts.
2. Verify fail-closed readiness for mismatch, exposure and missing main approvals or locked settings.
3. Record reproducible fixture results and index the operator entry point.

## Acceptance Criteria
- AC-48 — The six first observations for three rehearsal cases reject a packet mismatch and historical-label exposure individually with case ID and reason.
- AC-48 — A fresh valid rehearsal permits main dispatch only with approved main inputs and locked settings. Synthetic verification can pass while missing prerequisites keep historical execution pending.

## Test Plan
- **Level:** contract
- **Scenarios:**
  - Run the nominal fixture and check: The six first observations for three rehearsal cases reject a packet mismatch and historical-label exposure individually with case ID and reason.
  - Run the boundary or failure fixtures and check: A fresh valid rehearsal permits main dispatch only with approved main inputs and locked settings. Synthetic verification can pass while missing prerequisites keep historical execution pending.
- **Edge cases:** Preserve fixture isolation and verify exact counts, states and evidence where applicable.
