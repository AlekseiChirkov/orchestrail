#!/usr/bin/env python3
"""Check the instruction lint command with isolated source trees."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().with_name("lint-instructions.py")
SOURCE = CHECKER.parents[1]
RULE = '---\ndescription: Check the contract\nload: on-demand\n---\n'
CAPABILITY_KEYS = (
    "sub-agents",
    "concurrent-sub-agents",
    "agent-messaging",
    "hooks",
    "worktrees",
    "git",
)
ALWAYS_ON_RELOCATIONS = (
    ("rules/global-claude.md", "harness/claude/always-on.md"),
    ("templates/codex-global-AGENTS.md", "harness/codex/always-on.md"),
)


def workflow(step: str, phase: str = "discovery", name: str = "demo") -> str:
    return (
        f'---\ndescription: A workflow\nphase: {phase}\nstep: {step}\n---\n\n'
        f'Invocation: `/{name}`\n'
    )


def words(count: int) -> str:
    return " ".join(["word"] * count)


def capability_record(name: str, state: str) -> str:
    fields = f"name: {name}\nstate: {state}"
    if state != "unknown":
        fields += "\nruntime: Fixture runtime 1.0\nverified: 2024-02-29\nevidence: docs/example.md"
    return f"{fields}\n\nLimitations: none known"


def capability_declaration(name: str, hooks: str) -> str:
    states = {"hooks": hooks, "worktrees": "unknown"}
    records = "\n\n".join(capability_record(key, states.get(key, "yes")) for key in CAPABILITY_KEYS)
    return (
        f"# Fixture capabilities\n\nhooks: {hooks}\n\n## Capability records\n\n"
        f"always-on-path: $HOME/{name}/instructions.md\n\n{records}"
    )


class InstructionMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.workspace = Path(workspace.name)
        self.root = self.workspace / "source tree"
        self.root.mkdir()
        self.environment = os.environ.copy()
        for variable in ("HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME"):
            directory = self.workspace / variable.lower()
            directory.mkdir()
            self.environment[variable] = str(directory)

    def write(self, relative: str, contents: str | bytes) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        data = contents.encode("utf-8") if isinstance(contents, str) else contents
        path.write_bytes(data)

    def run_checker(self, root: Path | None = None) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, "-I", str(CHECKER), "--root", str(self.root if root is None else root)],
            cwd=self.workspace,
            env=self.environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
        return result

    def assert_finding(self, result: subprocess.CompletedProcess[str], code: str, relative: str) -> None:
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertTrue(
            any(line.startswith(f"{code} {relative}:") for line in result.stdout.splitlines()),
            f"Expected {code} for {relative}. Output:\n{result.stdout}{result.stderr}",
        )

    def test_accepts_valid_rule_and_workflow_metadata(self) -> None:
        self.write("rules/contract-demo.md", RULE)
        for name, step in (("demo-decimal", "2.5"), ("demo-letter", "4b"), ("demo-entry", '"-"')):
            phase = "entry" if name == "demo-entry" else "discovery"
            self.write(f"workflows/{name}.md", workflow(step, phase, name))
        self.write("workflows/finalization.md", workflow('"-"', "finalization", "finalization"))

        result = self.run_checker()

        scoped = ("metadata-", "trigger-present ", "invocation-")
        self.assertFalse(any(line.startswith(scoped) for line in result.stdout.splitlines()), result.stdout)

    def test_rejects_missing_duplicate_unknown_and_malformed_metadata(self) -> None:
        fixtures = {
            "missing-load": (RULE.replace("load: on-demand\n", ""), "metadata-missing-field"),
            "trigger": (RULE.replace("load:", "trigger: always_on\nload:"), "trigger-present"),
            "repeated-key": (RULE.replace("load: on-demand", "load: on-demand\nload: always"), "metadata-duplicate-key"),
            "unknown-key": (RULE.replace("load:", "unregistered: value\nload:"), "metadata-unknown-field"),
            "invalid-value": (RULE.replace("on-demand", "sometimes"), "metadata-invalid-value"),
            "bad-delimiter": (RULE.removesuffix("---\n"), "metadata-syntax"),
            "continuation": (RULE.replace("contract\n", "contract\n  another line\n"), "metadata-syntax"),
            "tab": (RULE.replace("load: ", "load:\t"), "metadata-syntax"),
            "missing-description": (RULE.replace("description: Check the contract\n", ""), "metadata-missing-field"),
        }
        for label, (contents, _) in fixtures.items():
            self.write(f"rules/contract-{label}.md", contents)

        result = self.run_checker()

        for label, (_, code) in fixtures.items():
            with self.subTest(fixture=label):
                self.assert_finding(result, code, f"rules/contract-{label}.md")

    def test_rejects_invalid_workflow_steps_phases_and_invocations(self) -> None:
        fixtures = {
            "zero-step": (workflow("0", name="zero-step"), "metadata-invalid-value"),
            "multiple-decimals": (workflow("2.5.1", name="multiple-decimals"), "metadata-invalid-value"),
            "unknown-phase": (workflow("1", "editor", "unknown-phase"), "metadata-invalid-value"),
            "unknown-extension": (
                workflow("1", name="unknown-extension").replace("step:", "unregistered: value\nstep:"),
                "metadata-unknown-field",
            ),
            "missing-invocation": (workflow("1").split("Invocation:")[0], "invocation-missing"),
            "duplicate-invocation": (workflow("1", name="duplicate-invocation") * 2, "invocation-duplicate"),
        }
        for label, (contents, _) in fixtures.items():
            self.write(f"workflows/{label}.md", contents)

        result = self.run_checker()

        for label, (_, code) in fixtures.items():
            with self.subTest(fixture=label):
                self.assert_finding(result, code, f"workflows/{label}.md")

    def write_adapter(self, name: str, body: str, capabilities: str) -> None:
        directory = f"harness/{name}"
        self.write(
            f"{directory}/deploy.env",
            f"skills_dir=$HOME/{name}/skills\nalways_on_path=$HOME/{name}/instructions.md\n",
        )
        self.write(f"{directory}/capabilities.md", capabilities + "\n")
        self.write(f"{directory}/always-on.md", body)

    def test_counts_only_the_always_on_body_at_the_size_limit(self) -> None:
        capabilities = words(1607)
        self.write_adapter("at-limit", words(1200), capabilities)
        self.write_adapter("over-limit", words(1201), capabilities)
        self.write_adapter("embedded", words(1000) + "\n\n" + capabilities, capabilities)

        result = self.run_checker()

        self.assert_finding(result, "always-on-size", "harness/over-limit/always-on.md")
        findings = [line for line in result.stdout.splitlines() if line.startswith("always-on-size ")]
        self.assertEqual(len(findings), 1, result.stdout)

    def test_reports_invalid_utf8_and_forbidden_word_separators(self) -> None:
        self.write("rules/contract-invalid-utf8.md", b"\xff\n")
        self.write("workflows/invalid-separator.md", workflow("1").replace("A workflow", "A\x1cworkflow"))

        result = self.run_checker()

        self.assert_finding(result, "input-encoding", "rules/contract-invalid-utf8.md")
        self.assert_finding(result, "input-encoding", "workflows/invalid-separator.md")

    def test_checks_capability_records_for_each_adapter(self) -> None:
        first = capability_declaration("fixture-first", "yes").replace(
            "evidence: docs/example.md", "evidence: docs/example.md\nevidence: docs/another.md", 1,
        )
        second = capability_declaration("fixture-second", "no")
        self.write_adapter("fixture-first", "Fixture instructions", first)
        self.write_adapter("fixture-second", "Fixture instructions", second)

        baseline = self.run_checker()
        self.assertEqual(baseline.returncode, 0, baseline.stdout + baseline.stderr)

        disabled_hooks = capability_record("hooks", "no")
        mutations = {
            "yes without evidence": (
                second.replace("\nevidence: docs/example.md", "", 1), "capability-schema",
            ),
            "no without evidence": (
                second.replace(disabled_hooks, disabled_hooks.replace("\nevidence: docs/example.md", "")),
                "capability-schema",
            ),
            "impossible date": (second.replace("2024-02-29", "2023-02-29", 1), "capability-schema"),
            "duplicate record": (f"{second}\n\n{capability_record('git', 'yes')}", "capability-schema"),
            "duplicate records section": (
                f"{second}\n\n## Capability records\n\n{capability_record('extension', 'unknown')}",
                "capability-schema",
            ),
            "invalid state": (second.replace("state: unknown", "state: maybe"), "capability-schema"),
            "missing limitations": (
                second.replace("\n\nLimitations: none known", "", 1), "capability-schema",
            ),
            "missing canonical record": (
                second.removesuffix(f"\n\n{capability_record('git', 'yes')}"), "capability-key-missing",
            ),
            "different location": (
                second.replace("always-on-path: $HOME/fixture-second", "always-on-path: $HOME/fixture-first"),
                "always-on-path-mismatch",
            ),
            "different hook state": (second.replace("\nhooks: no\n", "\nhooks: yes\n"), "hooks-state-mismatch"),
        }
        for label, (declaration, code) in mutations.items():
            with self.subTest(mutation=label):
                self.write("harness/fixture-second/capabilities.md", declaration + "\n")
                self.assert_finding(self.run_checker(), code, "harness/fixture-second/capabilities.md")

    def test_delivers_harness_adapter_paths(self) -> None:
        adapters = {
            "claude": {
                "skills_dir": "$HOME/.claude/skills",
                "always_on_path": "$HOME/.claude/CLAUDE.md",
                "project_skills_link_dir": ".claude/skills",
            },
            "codex": {
                "skills_dir": "$HOME/.codex/skills",
                "always_on_path": "$HOME/.codex/AGENTS.md",
            },
        }
        for name, expected in adapters.items():
            with self.subTest(adapter=name):
                relative = f"harness/{name}/deploy.env"
                adapter = SOURCE / relative
                self.assertTrue(adapter.is_file(), f"Missing delivered adapter declaration: {relative}")
                lines = adapter.read_bytes().decode("utf-8").split("\n")
                actual = [line for line in lines if line and not line.startswith("#")]
                self.assertCountEqual(actual, [f"{key}={value}" for key, value in expected.items()])

    def test_delivered_capabilities_preserve_prior_text_and_validate(self) -> None:
        # Hash the original prefix to protect existing text without copying it into the fixtures.
        originals = {
            "claude": (11057, "c46c9d152c9e62c4a2961c3860e49302fc232ff7509d133f3e0e995c33779f3c", "yes"),
            "codex": (672, "3c646d8e248e84f846900f785338a58104809201789b47da7279ee2971f16613", "no"),
        }
        for name, (length, digest, hooks) in originals.items():
            with self.subTest(adapter=name):
                relative = f"harness/{name}/capabilities.md"
                declaration = (SOURCE / relative).read_bytes()
                self.assertEqual(hashlib.sha256(declaration[:length]).hexdigest(), digest)
                lines = declaration[length:].decode("utf-8").lstrip("\n").splitlines()
                self.assertTrue(lines and lines[0] == "## Capability records", f"Missing records in {relative}")
                record_names = [line.removeprefix("name: ") for line in lines if line.startswith("name: ")]
                canonical = [key for key in record_names if key in CAPABILITY_KEYS]
                self.assertEqual(canonical, list(CAPABILITY_KEYS))

                adapter = f"harness/{name}/deploy.env"
                self.assertTrue((SOURCE / adapter).is_file(), f"Missing delivered adapter declaration: {adapter}")
                self.write(adapter, (SOURCE / adapter).read_bytes())
                self.write(relative, declaration)
                result = self.run_checker()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

                text = declaration.decode("utf-8")
                path_line = next(line for line in lines if line.startswith("always-on-path: "))
                other_hooks = "no" if hooks == "yes" else "yes"
                mutations = {
                    "capability-key-missing": text.replace("\nname: git\n", "\nname: auxiliary-git\n"),
                    "always-on-path-mismatch": text.replace(path_line, "always-on-path: $HOME/other/instructions.md"),
                    "hooks-state-mismatch": text.replace(f"\nhooks: {hooks}\n", f"\nhooks: {other_hooks}\n", 1),
                }
                for code, invalid in mutations.items():
                    self.write(relative, invalid)
                    self.assert_finding(self.run_checker(), code, relative)
                self.write(relative, declaration)

    def test_reports_legacy_mentions_with_source_lines_and_exclusions(self) -> None:
        self.write("rules/contract-guide.md", RULE + "\n\nWindsurf integration\n")
        self.write("scripts/report-legacy-artifacts.sh", "Windsurf integration\n")
        self.write(
            "docs/USAGE.md",
            "# Usage\n\n## Removed integrations\n\nWindsurf\n\n### Notes\nDevin\n"
            "\n## Setup\nCODEIUM and developing projects\n",
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        locations = {line.split()[1] for line in result.stdout.splitlines() if line.startswith("legacy-mention ")}
        self.assertEqual(locations, {"rules/contract-guide.md:7", "docs/USAGE.md:11"}, result.stdout)

    def test_delivers_relocated_always_on_sources(self) -> None:
        for former, current in ALWAYS_ON_RELOCATIONS:
            with self.subTest(source=current):
                source = SOURCE / current
                self.assertTrue(source.is_file(), f"Missing relocated source: {current}")
                self.assertTrue(source.read_text(encoding="utf-8").strip(), f"Empty relocated source: {current}")
                self.assertFalse((SOURCE / former).exists(), f"Former source still exists: {former}")

    def test_accepts_current_always_on_source_references(self) -> None:
        former_sources = {former for former, _ in ALWAYS_ON_RELOCATIONS}

        result = self.run_checker(SOURCE)

        findings = []
        for line in result.stdout.splitlines():
            if line.startswith("stale-name "):
                names = line.partition(" Stale names: ")[2].removesuffix(".").split(", ")
                if former_sources.intersection(names):
                    findings.append(line)
        self.assertFalse(findings, "References to former always-on sources:\n" + "\n".join(findings))

    def test_rejects_invalid_name_maps_without_hiding_metadata_errors(self) -> None:
        valid_row = {"kind": "rule", "old": "guide", "new": ["contract-guide"]}
        invalid_rows = {
            "missing target": [{**valid_row, "new": []}],
            "workflow split": [{**valid_row, "kind": "workflow", "new": ["main", "extra"]}],
            "unknown row field": [{**valid_row, "reason": "Move"}],
            "malformed name": [{**valid_row, "old": "Guide"}],
            "unsafe file path": [{"kind": "file", "old": "../README.md", "new": ["docs/Guide.md"]}],
            "duplicate identity": [valid_row, {**valid_row, "new": ["contract-reference"]}],
            "duplicate target in a row": [{**valid_row, "new": ["contract-guide", "contract-guide"]}],
            "duplicate target across rows": [valid_row, {**valid_row, "old": "reference"}],
            "target is an old name": [valid_row, {**valid_row, "old": "contract-guide", "new": ["main"]}],
            "unsorted rows": [{**valid_row, "old": "reference", "new": ["contract-reference"]}, valid_row],
        }
        invalid_maps = {label: json.dumps({"schema_version": 1, "rows": rows}) for label, rows in invalid_rows.items()}
        invalid_maps.update({
            "duplicate JSON key": '{"schema_version": 1, "rows": [], "rows": []}',
            "incorrect schema version": '{"schema_version": true, "rows": []}',
            "invalid JSON": "[",
        })
        self.write("rules/contract-unrelated.md", RULE.replace("load: on-demand\n", ""))

        for label, document in invalid_maps.items():
            with self.subTest(mutation=label):
                self.write("docs/name-map.json", document)

                result = self.run_checker()

                self.assert_finding(result, "metadata-missing-field", "rules/contract-unrelated.md")
                self.assert_finding(result, "name-map-invalid", "docs/name-map.json")

    def test_requires_the_usage_table_to_list_each_split_target(self) -> None:
        self.write("docs/name-map.json", json.dumps({
            "schema_version": 1,
            "rows": [{"kind": "rule", "old": "guide", "new": ["contract-guide", "contract-guide-extra"]}],
        }))
        heading = "## Renamed commands and rules\n\n| Kind | Old | New |\n| --- | --- | --- |\n"
        row = "| rule | `guide` | `contract-guide`"
        self.write("docs/USAGE.md", f"{heading}{row} |\n")

        self.assert_finding(self.run_checker(), "usage-map-mismatch", "docs/USAGE.md")

        self.write("docs/USAGE.md", f"{heading}{row}, `contract-guide-extra` |\n")
        aligned = self.run_checker()
        self.assertEqual(aligned.returncode, 0, aligned.stdout + aligned.stderr)

    def test_resolves_executable_references_and_section_order(self) -> None:
        self.write("rules/contract-target.md", RULE + "\n## Guide — Notes\n### Run\n#### Finish\n## End\n")
        self.write("workflows/run.md", workflow("1", name="run"))
        examples = (
            ("Invoke `/run.md --dry-run`.", "reference-md-suffix"),
            ("Read `contract-target.md → ## Guide`.", "reference-md-suffix"),
            ("Invoke `/absent --dry-run`.", "reference-missing"),
            ("Read `no-such-stem → ## Guide`.", "reference-missing"),
            ("Load `rule-contract-absent`.", "reference-missing"),
            ("Load `contract-absent` rules.", "reference-missing"),
            ("Read `rules/contract-absent.md`.", "reference-missing"),
            ("Read `contract-target → ## End → ### Run`.", "heading-missing"),
            ("Read `contract-target → ## Absent`.", "heading-missing"),
            ("Run `/run --dry-run` and read `rules/contract-target.md`.", None),
            ("Read `/contract-target → ## Guide → ### Run → #### Finish`.", None),
            ("Read `state.md → ## Guide` and `principles/consumer.md`.", None),
            ("`` Rule `rule-contract-absent` goes in the example. ``", None),
            ("~~~md\n`/fenced-example`\n~~~", None),
        )
        source = "rules/contract-source.md"
        self.write(source, RULE + "\n" + "\n".join(example for example, _ in examples) + "\n")
        expected = {
            f"{code} {source}:{i}"
            for i, (_, code) in enumerate(examples, start=6) if code is not None
        }

        result = self.run_checker()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual({" ".join(line.split()[:2]) for line in result.stdout.splitlines()}, expected, result.stdout)

    def test_reports_stale_names_with_scan_and_retention_exceptions(self) -> None:
        self.write("docs/name-map.json", json.dumps({"schema_version": 1, "rows": [
            {"kind": "file", "old": "workflows/GUIDE.md", "new": ["docs/GUIDE.md"]},
            {"kind": "rule", "old": "guide", "new": ["contract-guide"]},
            {"kind": "workflow", "old": "old-command", "new": ["new-command"]},
        ]}))
        self.write(
            "docs/USAGE.md",
            "## Renamed commands and rules\n\n| Kind | Old | New |\n| --- | --- | --- |\n"
            "| file | `workflows/GUIDE.md` | `docs/GUIDE.md` |\n"
            "| rule | `guide` | `contract-guide` |\n"
            "| workflow | `old-command` | `new-command` |\n",
        )
        self.write("README.md", "Use /old-command\nSee docs/GUIDE.md\nSee workflows/GUIDE.md\n")
        self.write("templates/.ai/example.md", "Load `guide` rule.\nUse my-old-command.\nUse guide.\n")
        self.write("tests/fixtures/validator-runtime/source.txt", "old-command\n")
        self.write("scripts/check-lint-instructions.py", "old-command\n")
        self.write(
            "scripts/validate-contracts.sh",
            '  # old-command\ncheck "old-command" "$(old-command)"\nkeep old-command\n',
        )
        self.write(
            "docs/audits/2024-02-29-rule-migration-map.md",
            "## Retained old names\n\n| Path | Line text | Reason |\n| --- | --- | --- |\n"
            "| `scripts/validate-contracts.sh` | `keep old-command` | Fixed historical label |\n",
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        locations = {line.split()[1] for line in result.stdout.splitlines() if line.startswith("stale-name ")}
        self.assertEqual(locations, {
            "README.md:1", "README.md:3", "templates/.ai/example.md:1", "scripts/validate-contracts.sh:2",
        }, result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
