---
description: Load the Orchestrail language convention for repository artifacts.
load: always
---

# Language Rule (always-on)

Before creating or modifying ANY file or text artifact, apply this rule first.

**All content written to project files must be in English.** This covers every file
type and every kind of text produced during development: source code, comments,
docstrings, commit messages, configuration files, shell scripts, Terraform HCL, YAML,
JSON, Markdown docs, README/ADR/state files, test names and fixtures, and any other
artifact created or edited in the project.

If existing content in a file is not in English, keep new content English and do not
mirror the other language.

This rule applies ONLY to generated code and project files.

Chat language is user-specific. Set the preference in the project-local `CLAUDE.md`
for Claude Code or `AGENTS.md` for Codex.

`scripts/sync.sh` manages the global always-on files `~/.claude/CLAUDE.md` and
`~/.codex/AGENTS.md`. An edit to either deployed file makes the next sync stop
with `ownership-conflict`.
