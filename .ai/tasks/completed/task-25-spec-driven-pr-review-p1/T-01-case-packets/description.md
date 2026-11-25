## Goal
Pin approved case packets with reproducible evidence for AC-45.

## Context
- Dependencies: —
- Constraints: Use local procedure and controlled fixtures, with identical approved inputs across review variants.
- Reason: Establish a separately verifiable protocol checkpoint before integrating the rehearsal.

Off-limits: Historical case execution, production workflow edits, automated scheduling, hosted services and merge gating.

## Scope
- **In scope:** Pin approved case packets and its synthetic verification.
- **Out of scope:** Live data, external publication and deferred service requirements.
- **Target files:** docs/offline-review/case-packet.md, docs/offline-review/fixtures/

## Steps
1. Define the shared packet and coordinator manifest fields, including versioned approvals and feature grouping.
2. Specify canonical digest pinning and masking at admission for PR and integrated milestone compositions.
3. Build synthetic examples for PR, milestone and missing approval and verify parity and exclusion.

## Acceptance Criteria
- AC-45 — Eligible PR and milestone cases each pin a single digest used by both variants. The milestone pins target, integrated tree and constituent revisions.
- AC-45 — A missing approval excludes its case with the missing approval identified.

## Test Plan
- **Level:** contract
- **Scenarios:**
  - Run the nominal fixture and check: Eligible PR and milestone cases each pin a single digest used by both variants. The milestone pins target, integrated tree and constituent revisions.
  - Run the boundary or failure fixtures and check: A missing approval excludes its case with the missing approval identified.
- **Edge cases:** Preserve fixture isolation and verify exact counts, states and evidence where applicable.
