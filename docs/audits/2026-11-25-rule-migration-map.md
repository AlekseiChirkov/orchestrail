# Rule migration semantics record

This record starts with support for inventory amendments. Section mappings will be recorded as the source rules move.

| Source | Section | SHA-256 | Target | Target section | Consumers | Evidence | Reviewed |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Superseded checks

The inventory amendment compatibility change has zero superseded checks.

| Key | Before | After | Requirement | Verdict |
| --- | --- | --- | --- | --- |

## Retained old names

| Path | Line text | Reason |
| --- | --- | --- |
| `scripts/audit-instructions.py` | ` under harness/ plus templates/codex-global-AGENTS.md (adapter), each reached through real ` | Preserves the historical audit adapter grammar and report format. |
| `scripts/audit-instructions.py` | ` ADAPTER_FILES = ("templates/codex-global-AGENTS.md",) ` | Preserves the historical audit adapter grammar and report format. |
| `scripts/audit-instructions.py` | `                            r"[A-Za-z0-9_*./-]*[A-Za-z0-9_*]\|templates/codex-global-AGENTS\.md" ` | Preserves the historical audit adapter grammar and report format. |
| `scripts/audit-instructions.py` | ``     "`templates/codex-global-AGENTS.md`); readers {readers} (active {active}, " `` | Preserves the historical audit adapter grammar and report format. |
| `scripts/check-audit-instructions.py` | `         self.fx.write("templates/codex-global-AGENTS.md", "# Essentials\n") ` | Synthetic fixture for historical adapter discovery and references. |
| `scripts/check-audit-instructions.py` | `         self.assertEqual(self.row(inventory, "templates/codex-global-AGENTS.md")["set"], ` | Synthetic fixture for historical adapter discovery and references. |
| `scripts/check-audit-instructions.py` | `         self.assertNotIn("templates/codex-global-AGENTS.md", readers) ` | Synthetic fixture for historical adapter discovery and references. |
| `scripts/check-audit-instructions.py` | `     "templates/codex-global-AGENTS.md": "# Codex essentials\n", ` | Synthetic fixture for historical adapter discovery and references. |
| `scripts/check-audit-instructions.py` | ``             "`templates/codex-global-AGENTS.md`", "`rules/*.md`", "`rules/*/*.md`", `` | Synthetic fixture for historical adapter discovery and references. |
| `scripts/check-audit-instructions.py` | `             edge(s, lines, lines[3], "templates/codex-global-AGENTS.md", "path", "resolved", ` | Synthetic fixture for historical adapter discovery and references. |
| `scripts/check-audit-instructions.py` | `                  ["templates/codex-global-AGENTS.md"]), ` | Synthetic fixture for historical adapter discovery and references. |
| `scripts/check-audit-instructions.py` | `             "Adapter templates/codex-global-AGENTS.md here.", ` | Synthetic fixture for historical adapter discovery and references. |
| `scripts/check-audit-instructions.py` | `             edge(s, lines, lines[7], "templates/codex-global-AGENTS.md", "path", "resolved", ` | Synthetic fixture for historical adapter discovery and references. |
| `scripts/check-audit-instructions.py` | `                  ["templates/codex-global-AGENTS.md"], context=text), ` | Synthetic fixture for historical adapter discovery and references. |
| `scripts/check-audit-instructions.py` | `         template = self.write_lines("templates/codex-global-AGENTS.md", ["Codeium and devin."]) ` | Synthetic fixture for legacy integration detection at the historical adapter. |
| `scripts/check-audit-instructions.py` | `             legacy_mention("templates/codex-global-AGENTS.md", 1, template[0], "Codeium"), ` | Synthetic fixture for legacy integration detection at the historical adapter. |
| `scripts/check-audit-instructions.py` | `             legacy_mention("templates/codex-global-AGENTS.md", 1, template[0], "devin"), ` | Synthetic fixture for legacy integration detection at the historical adapter. |
| `scripts/check-audit-instructions.py` | ``     "`templates/codex-global-AGENTS.md`); readers {readers} (active {active}, " `` | Expected historical audit report format. |
| `scripts/check-audit-instructions.py` | ` ADAPTER_FILE = "templates/codex-global-AGENTS.md" ` | Synthetic fixture for historical adapter path boundaries and symlinks. |
| `scripts/check-audit-instructions.py` | `             "Backup templates/codex-global-AGENTS.md.bak here.", ` | Synthetic fixture for historical adapter path boundaries and symlinks. |
| `scripts/check-audit-instructions.py` | `             "Older templates/codex-global-AGENTS.md-old here.", ` | Synthetic fixture for historical adapter path boundaries and symlinks. |
| `scripts/check-audit-instructions.py` | `             "Adapter templates/codex-global-AGENTS.md. Also templates/codex-global-AGENTS.md, too.", ` | Synthetic fixture for historical adapter path boundaries and symlinks. |
| `scripts/check-audit-instructions.py` | `         (outside / "codex-global-AGENTS.md").write_text( ` | Synthetic fixture for historical adapter path boundaries and symlinks. |
| `scripts/validate-contracts.sh` | `   'global-claude.md:harness/claude/always-on.md' ` | Preserves the frozen output label while reading the relocated source. |
| `scripts/validate-contracts.sh` | `   'codex-global-AGENTS.md:harness/codex/always-on.md' ` | Preserves the frozen output label while reading the relocated source. |
| `scripts/validate-contracts.sh` | ` for rule in rules/*.md 'global-claude.md'; do ` | Preserves the frozen collision result and excludes the always-on body from project-rule checks. |
| `scripts/validate-contracts.sh` | `   [ "$name" = "global-claude.md" ] && continue   # deployed as ~/.claude/CLAUDE.md, not as a project rule ` | Preserves the frozen collision result and excludes the always-on body from project-rule checks. |
| `scripts/validate-contracts.sh` | `   "$(tr '\n' ' ' < rules/workflow-globals.md 2>/dev/null \| tr -s ' ' \| grep -q 'A skill is model-invoked, not always-on' && echo pass \|\| echo 'workflow-globals does not record that deploying an always_on rule as a skill changes its trigger semantics — the reason the always-on essentials stay in global-claude/AGENTS.md')" ` | Preserves the frozen validator result expression, including its failure text. |
| `scripts/validate-contracts.sh` | `   "$(grep -q 'skills/rule-<name>/SKILL.md' docs/USAGE.md 2>/dev/null && echo pass \|\| echo 'docs/USAGE.md section 2 deployment matrix still says rules reach Claude Code only as global-claude and Codex not at all')" ` | Preserves the frozen validator result expression, including its failure text. |

## Bootstrap size exceptions

| Rule | Words | Reason |
| --- | --- | --- |

## Pre-existing reference defects

| Path:line | Reference | Fix |
| --- | --- | --- |

Signed: Independent validator 2026-11-25 bf2957d2146e81d5f87efc005cbc2018b745a90a
