---
description: Context loading rules for discovery phase — load when running /discovery, /discovery-analyze, /discovery-decompose, /discovery-design, /discovery-finalize
load: on-demand
---

# Phase: Discovery — Context Rules

## Context Bootstrap

Run before analyzing any codebase file. Skip missing files without error.
In multi-repo projects: load umbrella (`../.ai/`) first, then local (`.ai/`) — local overrides.
Report at end: "Discovery context loaded: [files read]"

| # | File | What to extract |
|---|------|-----------------|
| 1 | `.ai/memory/architecture.md` | System components, service boundaries, constraints |
| 2 | `.ai/memory/state.md` | Active tasks, blockers, in-flight work |
| 3 | `.ai/principles/architecture.md` | Architectural patterns, boundaries, what NOT to build |
| 4 | `.ai/principles/coding.md` | Naming standards, forbidden patterns — shapes decomposition |
| 5 | `.ai/principles/domain.md` | Domain rules, ubiquitous language, business constraints |
| 6 | `.ai/adr/index.md` | Past decisions index — read full ADR only if directly relevant |
| 7 | `.ai/memory/progress.md` | Previous session context — only if resuming interrupted work |

**Conditional — load only if the task statement mentions external services, third-party
APIs, or environment-specific setup:**

| # | File | Load when |
|---|------|-----------|
| 8 | `.ai/context/integrations.md` | Task touches external services / third-party APIs / cross-service contracts |
| 9 | `.ai/context/environment.md` | Task depends on environment-specific config (envs, secrets, infra topology) |

Skip both without error if not applicable or file missing.

After loading: state which architectural constraints apply to the current task before touching code.


## Phase Behaviors

Load the `protocol-discovery-conduct` rule before acting.
