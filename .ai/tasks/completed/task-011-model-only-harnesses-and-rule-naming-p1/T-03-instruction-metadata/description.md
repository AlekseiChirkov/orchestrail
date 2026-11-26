## Goal
Provide a strict checker for instruction metadata and harness capability records.

## Context
- Dependencies: T-02.
- Constraints: REQ-12, REQ-13, REQ-30, REQ-38, REQ-50, REQ-54 and REQ-62.
- Reason: Metadata syntax and capability-record semantics are independently testable.
- type: composite
- children: T-03a, T-03b

Off-limits: Weakening final strict validation or altering unrelated names.

## Scope
- **In scope:** Metadata and capability-record parsing and diagnostics.
- **Out of scope:** Name/reference scanner and adapter source migration.
- **Target files:** scripts/lint-instructions.py, scripts/check-lint-instructions.py

## Steps
See children: T-03a metadata syntax; T-03b capability-record validation.

## Acceptance Criteria
- The combined checker accepts valid instruction metadata and canonical capability fixtures with their declared consistency rules.
- The combined checker reports each invalid metadata or malformed capability fixture with the exact corresponding code.

## Test Plan
- **Level:** integration and contract.
- **Scenarios:**
  - First criterion → run valid metadata and capability fixtures through the combined checker.
  - Second criterion → run the malformed metadata and capability fixtures and compare exact diagnostic codes.
- **Edge cases:** Missing, duplicate and invalid fields and records.
