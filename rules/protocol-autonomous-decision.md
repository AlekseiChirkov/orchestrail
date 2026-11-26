---
description: Resolve workflow decisions through the autonomous scoring and escalation protocol
load: on-demand
---

# Autonomous Decision

## Autonomous Decision Protocol

Canonical definition. Used by any workflow running in autonomous mode
(`/phase-pipeline` at all times; `/phase-discovery` unless `--step-by-step`
is passed) whenever an architectural or design choice is required. It replaces
"present options, wait for user" at that decision point.

### Step 1 — Generate variants (2–3)
Describe each variant with approach summary, advantages, disadvantages, risks.

### Step 2 — Score on 5 lenses (1–5, higher = better)

| Lens | Question to answer |
|---|---|
| **Simplicity** | How much new code, concepts, or abstractions does this add? Fewer = better. |
| **Reversibility** | How hard is it to change this decision later without breaking things? Easier = better. |
| **Codebase fit** | How well does it align with patterns, standards, and abstractions already present in the repo? |
| **Testability** | How easy is it to write fast, deterministic, isolated tests for this? |
| **Blast radius** | How many existing files / modules need to change? Fewer = better. |

Scoring inputs, in priority order: `.ai/principles/*`, `.ai/adr/` (past decisions
on the same subject are binding unless the task explicitly supersedes them),
`.ai/memory/architecture.md`, patterns already present in the codebase, and
only then general best practice.

### Step 3 — Apply anti-overengineering filter
If the highest-scoring variant introduces an abstraction or pattern NOT already
present in the codebase, verify it solves a *current, concrete* problem stated in
the task description — not a hypothetical future one. If it only addresses a
hypothetical, reduce its Simplicity score by 2 before totalling.

### Step 4 — Select winner
Highest total score wins. On a tie → the simpler variant wins (lowest
Simplicity-score variant is eliminated). If still tied → the variant with best
Codebase fit wins.

### Step 5 — Check escalation threshold
Escalate to the user (pause and wait) ONLY when:
- A hard blocker appears that cannot be resolved without external information
  (missing secret, unavailable external service, requirement with no reasonable default).
- The decision would break an external API contract already consumed by clients.
- Two or more variants score identically on all 5 lenses AND have fundamentally
  different user-visible trade-offs that the simplicity tie-breaker cannot resolve.

Anything else → decide and continue. Do not escalate merely because a choice
feels significant.

### Step 6 — Document decision
Write the standard `## Solution Design` sections, and add inside it:

```
### Autonomous Decision
| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| Variant 1 | N | N | N | N | N | N |
| Variant 2 | N | N | N | N | N | N |

**Winner:** Variant X — <one-sentence rationale>
**Anti-overengineering check:** passed / adjusted (reason)
**Evidence:** <principles / ADRs / codebase patterns that drove the scores>
```

---
