---
description: Context loading rules for atomic-execution — load when running /atomic-execution, /atomic-execution-tests, or /atomic-execution-implement standalone (without parent /execution)
load: on-demand
---

# Phase: Atomic Execution — Context Rules

## Context Bootstrap

This phase runs inside a parent context or standalone. Reuse sources already loaded
in this session for the same resolved project only while their content remains available
and current. Reload changed sources and missing phase-specific context. Standalone and
fresh sub-agent invocations perform the full bootstrap; another agent's receipt alone
does not provide context.

**Step 0 — Resolve paths first:**
Read `T-XX/description.md → ## Context → working_dir:` before loading any context.
- If `working_dir:` present: `WORK_DIR = <resolved absolute path>`, `AI_DIR = WORK_DIR/.ai`
- If absent: `WORK_DIR = <absolute invocation directory>`, `AI_DIR = WORK_DIR/.ai`
- Umbrella: if `<WORK_DIR>/../.ai/` exists → load umbrella FIRST, then `AI_DIR` (local overrides)
- Runbook: `AI_DIR/context/runbook.md` when it exists; otherwise the umbrella's `context/runbook.md`
  (a multi-repository project whose repositories have no local `.ai/`). Run a local runbook's
  commands in `WORK_DIR` and an umbrella runbook's commands from the umbrella root `<WORK_DIR>/..`,
  where they are written. Every later mention of the runbook means this resolved runbook.

Report before continuing: "WORK_DIR=<path>, AI_DIR=<path>"

**Then load in order** (skip missing files, report what was loaded):

| # | File | What to extract |
|---|------|-----------------|
| 1 | `AI_DIR/memory/architecture.md` | Component boundaries, integration points |
| 2 | `AI_DIR/memory/state.md` | Current task status, active blockers |
| 3 | `AI_DIR/principles/architecture.md` | Patterns to enforce |
| 4 | `AI_DIR/principles/coding.md` | **REQUIRED** — style, naming, error-handling, forbidden patterns |
| 5 | `AI_DIR/principles/domain.md` | Domain rules, terminology |
| 6 | `AI_DIR/adr/index.md` | Decisions that constrain this implementation |
| 7 | `AI_DIR/context/runbook.md` | **REQUIRED** — `test:` for the TDD RED step, test/lint/build for Final Verification |

Report: "Atomic execution context loaded from AI_DIR=<path>: [files read]"

After loading: state which scope constraints apply (from `description.md` + loaded principles).

## Phase Behaviors

Load the `protocol-atomic-execution-conduct` rule before acting.
