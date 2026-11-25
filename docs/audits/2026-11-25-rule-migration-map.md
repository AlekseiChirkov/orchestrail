# Rule migration semantics record

This record starts with support for inventory amendments. Section mappings will be recorded as the source rules move.

| Source | Section | SHA-256 | Target | Target section | Consumers | Evidence | Reviewed |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Superseded checks

The deployment entry point changes below await an independent verdict. The [inventory amendment](../../tests/fixtures/validator-runtime/inventory-amendment.json) records their complete source text.

| Key | Before | After | Requirement | Verdict |
| --- | --- | --- | --- | --- |
| `TDD: scripts/sync.sh deploys tdd.md to projects` | Named rule in the sync shell script | Installed TDD rule prefix and source bytes across declared targets | REQ-05 | Pending independent validation. |
| `TDD: scripts/setup-new-project.sh deploys tdd.md` | Named rule in the setup shell script | Actual links to the installed TDD rule from a fresh project | REQ-06 | Pending independent validation. |
| `ORCH: $f deploys git-flow.md and orchestration.md` | Named orchestration rules in both shell scripts | Installed orchestration rule bytes and links from a fresh project | REQ-05 | Pending independent validation. |
| `test_sync_preserves_repository_knowledge_policy` | Extracted shell ignore policy | Two actual registered-project passes using isolated Git repositories | REQ-09 | Pending independent validation. |
| `DEPLOY: scripts/setup-new-project.sh copies $name` | Named rule copy in setup | Actual new-project link to each installed rule skill | REQ-06 | Pending independent validation. |
| `DEPLOY: scripts/sync.sh refreshes $name in existing projects` | Named rule copy in the sync shell loop | Actual registered-project refresh link to each installed rule skill | REQ-09 | Pending independent validation. |
| `DEPLOY: scripts/sync.sh deploys every rule as a Claude Code rule-* skill` | Hard-coded Claude Code copy loop | Actual Claude skill target with every prefixed rule and exact bytes | REQ-05 | Pending independent validation. |
| `DEPLOY: scripts/sync.sh deploys every rule as a Codex rule-* skill` | Hard-coded Codex copy loop | Actual Codex skill target with every prefixed rule and exact bytes | REQ-05 | Pending independent validation. |
| `DEPLOY: the $root rule deployment uses the rule- prefix` | Hard-coded provider-specific rule prefix | Actual rule prefix and source bytes in each named adapter target | REQ-05 | Pending independent validation. |
| `test_shell_paths_relocated_checkout_preserves_overrides` | Relocated source with legacy helper dependencies | Relocated sources with declared adapters, engine and reporter | REQ-05 | Pending independent validation. |

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
