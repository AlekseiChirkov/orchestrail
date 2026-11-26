# integrations.md — harnesses and external tools the workflows depend on

## Purpose
Everything outside this repository that a workflow talks to, and the assumptions it
makes about each. Consult before changing a workflow that spawns agents, calls a CLI, or
searches the web.

## Integrations

### Claude Code (Anthropic) — agent harness
- Purpose: primary execution environment; skills, `CLAUDE.md`, sub-agents, hooks.
- Interface: `~/.claude/skills/<name>/SKILL.md` with front-matter `description:`;
  `~/.claude/CLAUDE.md` global instructions; per-project `CLAUDE.md`.
- Used by: every workflow; `/spec-run` relies on spawning sub-agents, keeping the Arbiter
  alive and addressing it by message, and pausing the Implementer mid-run.
- The Claude always-on source carries essential instructions. The adapter declares
  `.claude/skills/` as its project link directory. The published hook records describe
  native hook support and the current installation result.
- Docs: https://docs.claude.com/en/docs/claude-code

### OpenAI Codex — agent harness
- Interface: `~/.codex/AGENTS.md`, `~/.codex/skills/<name>/SKILL.md`, per-project `AGENTS.md`.
- Workflows use the installed skills and the available orchestration capabilities.
  Project setup preserves an existing project-local `AGENTS.md`.

### Adapter declarations and session capabilities
- Deployment reads each `harness/<name>/deploy.env` as data to resolve that adapter's
  targets. `scripts/report-legacy-artifacts.sh` reports previous installation paths
  for owner review.
- Workflows read `capabilities.md` records from the installed always-on instructions.
  Each record declares a state, with runtime, verification date and evidence for an
  established state. A declared `yes` also requires the actual session tool and
  permission at dispatch. Verify access without network probing. Record fresh evidence
  before changing a capability record.
- The installed skill name is shared across harnesses. `docs/name-map.json` records
  the migration from old names to canonical source names and the instruction checker
  verifies the mapping against the shipped command reference.

### git — version control of consumer repositories
- Used by development, restack, and finalization workflows with distinct Git authority.
  Finalization returns exact checkout, fast-forward and cleanup commands from its
  evidence-bound plan. The Git rails define protected refs and task-scoped exceptions.

### GitHub CLI (`gh`) — pull requests
- Used by `/spec-run --allow-pr` and `/restack --allow-pr` for publication.
  Finalization uses repository-bound PR reads to verify integration.
- Assumptions: remote `origin` exists and `gh auth status` succeeds; PR bodies follow
  `contract-git-flow → ## Pull requests` and carry no attribution.

### `jq` — JSON processing
- Used by: `scripts/log-step.sh` (digest generation; degrades to a stub without it), `/retro`
  (all aggregation).

### Web search — model catalog
- Used by: `/discovery-select-model` Step 0, every run, by explicit rule (no cached catalog).
- Cost observed: up to 3 h in run b905a8a5. See `specs/completed/04-model-catalog-cache.md`.

### Web fetch — spec and defect sources
- Used by: `/spec-draft` and `/bugfix` when given a URL (issue tracker, Sentry, docs).
- Assumption: a URL that cannot be fetched stops the workflow and asks for text.

### Consumer project `.ai/` — the knowledge base contract
- Every phase performs the Context Bootstrap from `rules/bootstrap-*.md`: `principles/*`,
  `memory/architecture.md`, `memory/state.md`, `adr/index.md`, `context/runbook.md`,
  conditionally `context/integrations.md`, `context/environment.md`.
- `context/runbook.md → ## Commands` keys `test:`, `lint:`, `typecheck:`, `build:` drive
  automated verification; `test:` is mandatory for the TDD step.
