## Goal
Persist and score a queued review's terminal cutoff observation without inventing an attempt ID.

## Context
- Dependencies: T-05 completed the full offline fixture stack. T-02, T-03 and T-04 define capture, cutoff and scoring.
- Constraints: Preserve frozen observations and the existing public record format.
- Reason: Stack-tip review found an incompatible interpretation of the existing nullable attempt field.

Off-limits: Historical execution, changes to installed review workflows and automated scheduling.

## Scope
- **In scope:** Validate and capture the not-started cutoff record and check its scoring result.
- **Out of scope:** Changes to adjudication or dispatch policy and all historical processing.
- **Target files:** docs/offline-review/fixtures/paired_review.py, docs/offline-review/fixtures/test_cutoff_observation.py, docs/offline-review/paired-reviews.md

## Steps
1. Reproduce the capture failure with a cutoff row emitted by the dispatch fixture.
2. Align validation and capture with an unstarted review's absent attempt, elapsed time and report.
3. Run the cutoff record through scoring and check that launched statuses still require an attempt ID.

## Acceptance Criteria
- A dispatch cutoff yields a persistable first observation with null attempt and report digests. The scorer retains the observation and marks the affected pair incomplete.
- Launched observations without an attempt ID are rejected and an unstarted observation cannot be captured with a previously frozen report.

## Test Plan
- **Level:** contract
- **Scenarios:**
  - Run a queued review through cutoff, capture and reporting. Assert the original no-attempt observation is retained.
  - Attempt to capture a launched record without an ID or an unstarted record with report evidence. Assert capture fails.
- **Edge cases:** Invalid metadata is rejected without creating a terminal observation.
