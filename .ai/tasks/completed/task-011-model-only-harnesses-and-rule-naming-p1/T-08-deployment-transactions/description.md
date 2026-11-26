## Goal
Deployment transactions and recovery: satisfy REQ-10, REQ-42, REQ-45, REQ-63 / AC-05, AC-26, AC-45 for the bounded phase-one component.

## Context
- Dependencies: T-07; run in the sequential reviewed stack.
- Constraints: Implement REQ-10, REQ-42, REQ-45, REQ-63 / AC-05, AC-26, AC-45 and the corresponding specification contracts. Retain phase-two delivered-tree clauses as pending.
- Reason: The leaf owns one independently verifiable component or incremental interface.

Off-limits: Real-home deployment; deletion of legacy or unowned files; rewriting history; new frozen validator checks; phase-two command or rule renames.

## Scope
- **In scope:** Deployment transactions and recovery; the exact first-part clauses identified above.
- **Out of scope:** Other leaf components and phase-two delivery.
- **Target files:** scripts/deploy-skills.py, scripts/check-deploy-skills.py

## Steps
1. Inspect the cited REQ/AC and data-model contracts, current component and applicable fixtures.
2. Write isolated acceptance tests for the two criteria below and observe their expected failure before implementation.
3. Implement only the bounded component, preserving existing contracts and ownership restrictions.
4. Run the frozen tests and focused regression checks; return any shared knowledge delta to the Orchestrator.

## Acceptance Criteria
- The transaction rejects collisions between adapter targets, manifests, and the reserved lock and journal paths before writing artifacts. An otherwise valid harness whose manifest would occupy the journal path is refused.
- A second interruption during recovery leaves enough journal evidence to resume. Already-applied objects whose manifests still record the prior digest remain recognizable even when the recomputed plan has no further action for them.
- A held lock returns deploy-locked with no writes; a valid half-applied journal recovers to the new digests and is removed.
- An edited recovery target returns journal-mismatch without writes; every successful or failed fixture leaves no temporary files and each target at an old or new digest.

## Test Plan
- **Level:** contract and integration.
- **Scenarios:**
  - First criterion → Inject crashes and conflicting edits in isolated temporary homes and assert lock, journal, digest and cleanup outcomes.
  - Second criterion → use the negative or boundary fixtures stated in that criterion and assert its exact result.
- **Edge cases:** Missing and malformed inputs, duplicate identities, unsafe paths, partial failure and retries wherever the cited contract applies.
