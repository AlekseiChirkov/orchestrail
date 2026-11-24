## Goal
Verify isolated paired reviews with reproducible evidence for AC-46, AC-47.

## Context
- Dependencies: T-01
- Constraints: Use local procedure and controlled fixtures, with identical approved inputs across review variants.
- Reason: Establish a separately verifiable protocol checkpoint before integrating the rehearsal.

Off-limits: Historical case execution, production workflow edits, automated scheduling, hosted services and merge gating.

## Scope
- **In scope:** Verify isolated paired reviews and its synthetic verification.
- **Out of scope:** Live data, external publication and deferred service requirements.
- **Target files:** docs/offline-review/paired-reviews.md, docs/offline-review/fixtures/

## Steps
1. Provide matched variant instructions and one first-observation record format.
2. Define the allowed packet and output boundaries, evidence disposition rows and separate future roster.
3. Verify isolation and first artifact capture with seeded out-of-packet markers and check the four-criterion coverage fixture.

## Acceptance Criteria
- AC-46, AC-47 — The session reads only its allowed packet and writes only its own output. Both seeded sources remain inaccessible, and each terminal observation preserves the first report digest when present.
- AC-46, AC-47 — The treatment records exactly three due rows with positive evidence, an omission outside the diff and a named evidence gap. The future criterion appears separately.

## Test Plan
- **Level:** contract
- **Scenarios:**
  - Run the nominal fixture and check: The session reads only its allowed packet and writes only its own output. Both seeded sources remain inaccessible, and each terminal observation preserves the first report digest when present.
  - Run the boundary or failure fixtures and check: The treatment records exactly three due rows with positive evidence, an omission outside the diff and a named evidence gap. The future criterion appears separately.
- **Edge cases:** Preserve fixture isolation and verify exact counts, states and evidence where applicable.
