## Goal
Validate harness capability records and their consistency with adapter paths and hook declarations.

## Context
- Dependencies: T-03a; child of T-03.
- Constraints: DM-4, REQ-38, REQ-62, AC-23 record cases and AC-40 record cases.
- Reason: Capability record blocks are independently testable from instruction front matter.

Off-limits: Fabricating capability evidence, changing source adapter declarations or relaxing schema errors.

## Scope
- **In scope:** Capability-record parsing and exact checker diagnostics.
- **Out of scope:** Instruction front matter and actual adapter source changes.
- **Target files:** scripts/lint-instructions.py, scripts/check-lint-instructions.py

## Steps
1. Inspect DM-4 record grammar and existing checker entry points.
2. Write valid and invalid isolated capability fixtures and establish RED.
3. Implement canonical record, evidence, date, order and consistency validation.
4. Run the frozen fixtures and metadata regression checks.

## Acceptance Criteria
- Valid canonical capability records with matching hooks and always-on paths produce no capability findings.
- Missing evidence for yes, invalid dates or duplicate records produce capability-schema; absent records and mismatched hooks or paths produce their specified exact codes.

## Test Plan
- **Level:** contract.
- **Scenarios:**
  - First criterion → parse complete valid fixture declarations for both harnesses.
  - Second criterion → inject each invalid record and mismatch separately and assert its exact diagnostic.
- **Edge cases:** Unknown states, repeated blocks, invalid dates, missing evidence and mismatched adapter paths.
