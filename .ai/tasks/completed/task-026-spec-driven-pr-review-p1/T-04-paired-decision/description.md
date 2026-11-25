## Goal
Derive blinded paired decisions with reproducible evidence for AC-50.

## Context
- Dependencies: T-03
- Constraints: Use local procedure and controlled fixtures, with identical approved inputs across review variants.
- Reason: Establish a separately verifiable protocol checkpoint before integrating the rehearsal.

Off-limits: Historical case execution, production workflow edits, automated scheduling, hosted services and merge gating.

## Scope
- **In scope:** Derive blinded paired decisions and its synthetic verification.
- **Out of scope:** Live data, external publication and deferred service requirements.
- **Target files:** docs/offline-review/adjudication-and-report.md, docs/offline-review/fixtures/

## Steps
1. Define opaque finding projection, evidence checks and verdict freeze before unblinding.
2. Provide report fields for pair eligibility, deduplication, signed deltas, shared spend and decision thresholds.
3. Verify equality, individual threshold breaches and incomplete or contaminated fixture outcomes.

## Acceptance Criteria
- AC-50 — The valid pair yields deltas of 1 defect, 1 false finding, 20 seconds and 4 units, shared exposure of 13 units and trial at equality. Each isolated threshold breach yields no trial.
- AC-50 — Contamination, a missing scored measurement and unfinished adjudication each yield insufficient evidence on the only pair. The unfinished case retains first reports and charges and records pending claims as gaps.

## Test Plan
- **Level:** contract
- **Scenarios:**
  - Run the nominal fixture and check: The valid pair yields deltas of 1 defect, 1 false finding, 20 seconds and 4 units, shared exposure of 13 units and trial at equality. Each isolated threshold breach yields no trial.
  - Run the boundary or failure fixtures and check: Contamination, a missing scored measurement and unfinished adjudication each yield insufficient evidence on the only pair. The unfinished case retains first reports and charges and records pending claims as gaps.
- **Edge cases:** Preserve fixture isolation and verify exact counts, states and evidence where applicable.
