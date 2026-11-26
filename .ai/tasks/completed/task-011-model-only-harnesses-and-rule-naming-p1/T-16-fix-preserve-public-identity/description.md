## Goal
Preserve the exact public-identity ledger and the test of the historical setup line.

## Context
- Dependency: T-15, the reviewed stack tip.
- Phase-level validation of candidate `7a521a4edb333ce4b41085712cd785a2efee2839` reported that the new instruction-checker fixture duplicated the historical repository identity outside the approved ledger. The independent source log is `/tmp/orchestrail-harness-stack-final.ZK67vs/staging.log`.
- The original public documentation line remains approved at `docs/USAGE.md:256`. The standalone instruction suite must continue comparing those exact bytes. Scope is REQ-72 and the phase-level invariant that the pinned inventory must remain intact.
- Off-limits: Amend the approved identity ledger, relax the public scanner, move the approved source line, add a new frozen validator registration, deploy to a real home, or use runtime code changes to hide obsolete names.

## Scope
- In scope: `scripts/check-knowledge-inventory.py` targeted source integration regression and `scripts/check-lint-instructions.py` approved line assertion.
- Out of scope: The durable ledger, product files, unrelated test behavior, source guard classifications and Phase 2.

## Steps
1. Extend the existing standalone knowledge inventory suite with a focused integration case that runs the real public identity function against the source checkout, using temporary HOME and XDG paths. Observe the exact current ledger failure before the fix and retain existing knowledge cases.
2. After the test-only commit, replace the duplicated literal in the instruction fixture with a byte-exact checksum assertion for the single approved source line as the reasoned test amendment. Preserve all other tests and their behavior.
3. Rerun both standalone suites with isolated paths, independently verify positive and changed-byte rejection, and run whitespace and relevant oracle checks.

## Acceptance Criteria
- The source identity checker passes with the original ledger, source layout and pin intact. The focused regression fails on the predecessor only for the newly duplicated source identity occurrence.
- The instruction checker still requires the exact bytes of the approved line. An altered line continues to fail. Existing instruction-suite and knowledge-inventory assertions remain intact.

## Test Plan
- Level: contract with isolated source-tree integration.
- Focused RED/GREEN: use the pinned existing identity function on the source checkout. Read candidate Git state only. Redirect HOME and XDG to the suite fixture.
- Compare the source line and its SHA-256 with the approved evidence. Demonstrate a changed byte is rejected in a disposable copy and preserve existing identity tests.
