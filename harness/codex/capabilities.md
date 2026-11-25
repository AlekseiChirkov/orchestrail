# Codex logging capabilities

hooks: no

This release installs no native Codex logging adapter. This declaration describes
the shipped implementation and does not assert a permanent platform limitation.
Installation and native checkpoint coverage are unavailable here. Every workflow
step retains prompt logging with `note: approximate`; run start and run end remain
prompt driven. Unknown capabilities are unavailable. Mechanism support, installation
status and accepted checkpoint coverage must be assessed separately.

git-rails: none (textual rules only)

This release installs no command-level git enforcement for Codex. Git safety rails
apply as textual rules only.

## Capability records

always-on-path: $HOME/.codex/AGENTS.md

name: sub-agents
state: unknown

Limitations: Spawning a separate worker context lacks versioned verification.

name: concurrent-sub-agents
state: unknown

Limitations: Multiple simultaneous workers lack versioned verification.

name: agent-messaging
state: unknown

Limitations: Sending a follow-up to a worker that retains context lacks versioned verification.

name: hooks
state: no
runtime: Codex CLI 0.170.0
verified: 2026-11-25
evidence: tests/hook-install.sh

Limitations: The shipped adapter uses prompt logging. Assess installation and checkpoint coverage separately.

name: worktrees
state: unknown

Limitations: Isolated Git worktrees for workers lack versioned verification.

name: git
state: unknown

Limitations: Session Git tool access lacks versioned verification.
