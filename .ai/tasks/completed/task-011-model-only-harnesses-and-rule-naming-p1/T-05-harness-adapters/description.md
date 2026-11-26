## Goal
Deliver both harness adapter declarations and safely relocate their always-on sources.

## Context
- Dependencies: T-04.
- Constraints: REQ-35, REQ-38, REQ-55, REQ-62; AC-22, AC-23 record fixtures, AC-35, AC-40.
- Reason: Adapter declarations and Git-preserving source relocation are independently testable components.
- type: composite
- children: T-05a, T-05b

Off-limits: Real-home deployment, history rewriting and phase-two naming changes.

## Scope
- **In scope:** Both adapter declarations and the source move with compatible consumers.
- **Out of scope:** Final deployment-engine integration and phase-two naming.
- **Target files:** The exact union of the two child descriptions.

## Steps
See children: T-05a adapter declarations; T-05b history-preserving moves and consumer compatibility.

## Acceptance Criteria
- Both declared adapters contain their complete moved sources and canonical records; parent capability lines remain in order and always-on-path/hooks values agree.
- Existing sync and frozen validator consumers use the moved files on the combined branch; the reviewed amendment record passes and Git history follows both moves.

## Test Plan
- **Level:** integration and contract.
- **Scenarios:**
  - First criterion → run isolated adapter and capability fixtures against the combined source tree.
  - Second criterion → run isolated sync, frozen oracle and history-following checks after both children are reviewed.
- **Edge cases:** Missing adapter files, invalid evidence and unexpected legacy source bytes.
