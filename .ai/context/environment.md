# environment.md — environments, paths, and configuration

## Purpose
Where the workflow system runs and what it assumes about the host. Read before any
change to `scripts/sync.sh`, `scripts/setup-*.sh`, `scripts/log-step.sh`, or to a path mentioned in a rule.

## Environments

The source declares two model harnesses, Claude Code and Codex. Project setup
initializes consumer repositories and creates declared skill links.

### Claude Code (primary)
- Workflows → `~/.claude/skills/<name>/SKILL.md`
- Rules → `~/.claude/skills/rule-<name>/SKILL.md`; principles → `principle-<name>`
- The Claude adapter assembles `~/.claude/CLAUDE.md` from its always-on source,
  capability declaration and hook installation result. Sync checks ownership before replacing it.
- Per project: `CLAUDE.md` (pointer or two-level protocol), `.claude/skills/<name>` symlinks
  to the global skills (workaround: a project-local `.claude/skills/` hides global skills)
- Workflows invoke skills when needed. Capability records and current tooling govern
  whether a run can use sub-agents and messaging.

### OpenAI Codex
- Same three skill layouts under `~/.codex/skills/`
- The Codex adapter assembles `~/.codex/AGENTS.md` from its always-on source and
  capability declaration and unavailable native-hook result. Sync checks ownership before replacing it.
- Project setup seeds `AGENTS.md` from `templates/AGENTS.md` and preserves existing files.
- Check worker and messaging support in the current session.

### Retired Windsurf and Devin integrations
- Sync reports legacy paths for review. The deployment engine manages the targets
  declared by the Claude Code and Codex adapters.

### Consumer projects
- Seeded by `scripts/setup-new-project.sh`: `CLAUDE.md`, `AGENTS.md`, `.ai/` (from
  `templates/.ai/`, never overwrites), `.gitignore` entries (`.ai/`, `.claude/skills/`,
  `.env`, `*.pyc`, `__pycache__/`, and the state tool's `.state-tool.lock` and
  `.state.md.*.tmp`); the script skips the `.ai/` entry where `git ls-files .ai` lists a tracked file.
- Consumer projects are recorded in the local registry; none is named here.

## Configuration

| Variable / path | Used by | Default | Notes |
|---|---|---|---|
| `ORCHESTRAIL_HOME` | `scripts/sync.sh`, `scripts/setup-*.sh` | the repository root (parent of `scripts/`) | Empty values use the default; `scripts/sync.sh --from <dir>` and `--from=<dir>` override it; relative paths resolve from the caller directory |
| `ORCHESTRAIL_LOG_ROOT` | `scripts/log-step.sh`, `/retro` | `<repo>/logs` | store is gitignored |
| `ORCHESTRAIL_HOME` helper resolution | `rules/contract-run-log.md`, orchestrator workflows, artifact checks | unset: skip optional logging | Configure one shared checkout; required artifact checks need a configured source |
| `$HOME/.claude`, `$HOME/.codex` | `scripts/sync.sh`, `scripts/setup-new-project.sh` | — | declared harness locations |
| `.ai/context/runbook.md → ## Commands` (per consumer project) | `atomic-execution-implement`, `atomic-execution-tests`, `bugfix` | — | `test:` required for TDD |

Local configuration belongs under `~/.config/orchestrail/`. Keep machine settings
outside the checkout; configure `ORCHESTRAIL_HOME` with the checkout location and
`ORCHESTRAIL_LOG_ROOT` when selecting a different shared log store. These variables
are read from the environment; scripts do not automatically source configuration files.
Setup helpers normalize the selected source before invoking children. A missing
source directory fails before project initialization. `scripts/log-step.sh path` only prints
the selected path and never creates the store; an empty log override uses `<root>/logs`.

## Host
- Linux, bash, `jq` (required for run-log digests and `/retro`), `git`; `gh` is required
  for authoritative finalization PR reads and for authorized PR publication.
  `shellcheck` is optional. Finalization mechanics require Python 3.11+ and Linux
  no-overwrite rename support; unavailable required mechanisms block mutations.
- Development host: the maintainer's workstation.
- Local Git history exists. Publication authority is task-specific. On 2026-11-18
  the owner authorized merging the validated finalization stack and its pinned
  multi-repository dependency into main, followed by ordinary origin/main publication.
  This does not authorize live consumer installation or unrelated work integration.
- Isolated verification uses `PATH=/usr/bin:/bin` and `/usr/bin/python3` on this host.
  Do not select an uninstalled mise version to run checks.

## Scrub note (2026-09-17)

Mutable repository content uses neutral placeholders and configured helper paths.
The public-hygiene validator scans tracked files with maintainer-local patterns; only the
source specification is exempt. Local logs, machine settings, and Git internals are
outside the manual sweep. The local checkout location remains private.

## Isolated provider generation

`scripts/sync.sh --from <source-tree> --stage <directory>` runs mandatory preflight
and generates the declared Claude Code and Codex outputs in the selected empty
directory. Staging preserves live hook settings and consumer projects. The exported
files are review artifacts. The source checkout remains the implementation authority.
