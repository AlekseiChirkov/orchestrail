---
description: Apply the atomic execution obligations after loading context
load: on-demand
---

# Atomic Execution Conduct

## Conduct after bootstrap

- The cycle is test-first: `/atomic-execution-tests` (RED) → `/atomic-execution-implement` (GREEN) → `/atomic-execution-finalize`. See the `contract-tdd` rule.
- `principles/coding.md` must be loaded before writing any code — tests included. If missing → note "No coding principles" in `notes:` and flag it.
- Classify the test level before requiring a command. For testable work, a missing or placeholder `test:` **stops** `/atomic-execution-tests`; it never implies level `none`. Independently justified `none` may proceed without a test runner, retaining manual evidence. Missing `lint:` is reported, never claimed as a passing check.
- Read target files (from `T-XX/description.md → ## Scope → Target files`) AFTER context is loaded, not before.
- Out-of-scope discovery → stop immediately, report, wait for user decision.
- Update parent `## Subtask Progress` after every step.
