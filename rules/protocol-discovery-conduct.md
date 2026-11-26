---
description: Apply the Discovery reading budget and decision modes
load: on-demand
---

# Discovery Conduct

## Codebase Reading Rules

- Use `.ai/memory/architecture.md` to scope source reads. Read affected source when verifying behavior, freshness, or a concrete pattern; an inventory description alone is not implementation evidence.
- Budget: max 12 files (8 entry-points + 4 one-level-deeper). Hard limit.
- Document every file read with reason: "read to verify <specific behavior or gap>."
- Stop reading when affected parts are understood.

## Decision Protocol

Discovery runs **autonomously by default**; `--step-by-step` switches it to
manual review. See `/discovery → ## Execution Modes` (the workflow, not this rules file).

**Autonomous mode (default):**
- Task requirements unclear → resolve by research in this order: `.ai/principles/*`
  → `.ai/adr/` → `.ai/memory/*` → existing codebase patterns → general best
  practice. Record the resolution in `## Task Analysis → ### Assumptions`.
  Never infer intent silently — inferring is allowed, hiding it is not.
- Decomposition boundary or architectural choice ambiguous → generate 2–3 options
  and resolve them with `protocol-autonomous-decision → ## Autonomous Decision Protocol`.
  Record the scoring and rationale.
- Steps 1→4 run back-to-back. A step's completion report is not a handoff.
- Stop only on the Autonomous Decision Protocol's escalation conditions or a
  Guard confirmation that would overwrite existing artifacts.

**Step-by-step mode (`--step-by-step`):**
- Task requirements unclear → ask before proceeding. Never infer intent silently.
- Decomposition boundary ambiguous → present 2–3 options with trade-offs, wait for decision.
- Architectural variants → present, wait for the user's choice.
- After each of Steps 1–4 → stop and wait for review.
