#!/usr/bin/env python3
"""Check the instruction lint command with isolated source trees."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().with_name("lint-instructions.py")
RULE = '---\ndescription: Check the contract\nload: on-demand\n---\n'


def workflow(step: str, phase: str = "discovery", name: str = "demo") -> str:
    return (
        f'---\ndescription: A workflow\nphase: {phase}\nstep: {step}\n---\n\n'
        f'Invocation: `/{name}`\n'
    )


def words(count: int) -> str:
    return " ".join(["word"] * count)


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

    def run_checker(self) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, "-I", str(CHECKER), "--root", str(self.root)],
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
