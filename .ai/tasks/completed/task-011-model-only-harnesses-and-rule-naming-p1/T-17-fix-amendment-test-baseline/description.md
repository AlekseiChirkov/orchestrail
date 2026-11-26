## Goal
Keep the standalone synthetic inventory amendment checks runnable on a source tree that already contains reviewed contract amendments.

## Context
- Dependency: T-16-fix-preserve-public-identity and the reviewed stack.
- The existing standalone suite failed all three cases on isolated exact candidate `7a521a4edb333ce4b41085712cd785a2efee2839`. Receipt `/tmp/orchestrail-amendment-preflight.ZBcUdd/result.log`, SHA-256 `22447c6cd4594b4cd1273900cce3bfedcb62710f6e093aaf4cfbe65f90c5056c`.
- The fixture drops delivered source amendments from its synthetic schema but builds the synthetic cases from the already amended validator. The original production oracle accepts the real delivered amendment. REQ-51, REQ-52 and REQ-71 require separate negative and compatibility evidence.
- Off-limits: Frozen runtime inventory, delivered amendment and guard pins, the production validator and oracle, runtime behavior, and real-home deployment.

## Scope
- In scope: Standalone test setup and a focused baseline regression in `scripts/check-inventory-amendment.py`.
- Out of scope: All other files and Phase 2.

## Steps
1. Add a focused regression showing the synthetic validator fixture should start from an exact reconstruction of the reviewed delivered expression data. Run it before editing fixture setup, retain the three original failing cases, and return the test-only checkpoint.
2. Reuse the production oracle's existing read-only amendment validation and reconstruction functions before manufacturing synthetic rows in the temporary tree. Use the original working tree's reviewed name map and pinned amendment for this step.
3. Run all original tests and the new regression, the production oracle, source guard, and whitespace checks with isolated HOME and XDG paths. Preserve the delivery files and all original test assertions.

## Acceptance Criteria
- The synthetic starting point preserves the frozen inventory even when the current validator already contains reviewed source replacements.
- One schema 1 and schema 2 compatibility control and every original positive and negative synthetic mask or contract assertion pass, while unauthorized changes still fail.
- Real delivered oracle and pinned source evidence remain byte-identical and pass their original verification.

## Test Plan
- Level: contract with isolated source-tree integration.
- RED: independently assert the synthetic input contains exact restored expressions from the delivered amendment. Observe the actual mismatch and retain test-only bytes.
- GREEN: all four focused amendment cases, original oracle, and source guard. Compare the absence of production changes with the Git base.
