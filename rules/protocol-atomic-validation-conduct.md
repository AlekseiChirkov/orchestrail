---
description: Apply the atomic validation obligations after loading context
load: on-demand
---

# Atomic Validation Conduct

## Conduct after bootstrap

- Read `target_files` from parent `state.md → ## Subtask Progress → T-XX → target_files:` AFTER context is loaded.
- ADR violations → always `critical` severity.
- Architectural principle violations → `critical` severity.
- Coding principle violations → `important` severity.
- Domain rule violations → `critical` severity.
- Run `runbook.md → test:` and `lint:` if available before issuing verdict.
